"""Split from test_scripts.py. Loaded by evals/test_scripts.py, and runnable on its own."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import classify  # noqa: E402
import recall  # noqa: E402


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / script), *args],
        capture_output=True, text=True, timeout=60,
    )


# ---------------------------------------------------------------- normalising


class TestQuestionKeys(unittest.TestCase):
    """A saved answer replays word for word only on an exact confirmed wording.

    The first version of this cache stripped filler words and hashed the rest.
    That collapsed "set up jira in claude code" and "in claude desktop" onto one
    key, and replayed a wrong answer with confidence. These tests pin the fix.
    """

    def test_only_case_punctuation_and_spelling_collapse(self):
        same = ["How do I set up Jira?", "how do i set up jira", "How do I setup Jira.",
                "HOW DO I SET-UP JIRA!!"]
        self.assertEqual(len({recall.key_for(q) for q in same}), 1)

    def test_look_alike_questions_get_different_keys(self):
        """Every pair here once collided. None may share a key now."""
        pairs = [
            ("set up jira in claude code", "set up jira in claude desktop"),
            ("install claude code", "install claude desktop"),
            ("set up jira", "set up jira mcp"),
            ("map the S drive", "map the H drive"),
            ("option A", "option B"),
            ("set up version control", "set up git"),
            ("how do I set up docker", "do I need to set up docker"),
            ("how do I set up docker", "can you set up docker for me"),
            ("how do I install docker", "how do I uninstall docker"),
            ("enable the setting", "disable the setting"),
            ("is it working", "is it not working"),
        ]
        for a, b in pairs:
            with self.subTest(a=a, b=b):
                self.assertNotEqual(recall.key_for(a), recall.key_for(b))

    def test_similarity_names_the_words_that_differ(self):
        score, only_a, only_b = recall.similarity("set up jira in claude code", "set up jira in claude desktop")
        self.assertGreaterEqual(score, recall.NEAR_MATCH)
        self.assertEqual(only_a, ["code"])
        self.assertEqual(only_b, ["desktop"])

    def test_key_shape(self):
        key = recall.key_for("anything")
        self.assertEqual(len(key), recall.KEY_LEN)
        self.assertTrue(all(c in "0123456789abcdef" for c in key))


# ---------------------------------------------------------------- routing


class TestClassifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = classify.load_table(SKILL / "assets" / "router-table.tsv")

    def pick(self, text: str) -> str:
        return classify.classify(text, self.rows)["archetype"]

    def test_known_requests_route_correctly(self):
        cases = [
            ("why is the nightly export failing for this customer", "wf-01"),
            ("what should I ask the customer before I can act", "wf-02"),
            ("write it up for dev so they don't bounce it", "wf-03"),
            ("summarize this for the board", "wf-04"),
            ("draft a KB article for this", "wf-05"),
            ("explain this stored procedure in plain English", "wf-06"),
            ("compare the two environments, they don't match", "wf-07"),
            ("what are the top issues across all these tickets", "wf-08"),
            ("how do I set up my development environment", "wf-09"),
            ("review this and poke holes in it", "wf-10"),
            ("list the edge cases for this screen", "wf-11"),
            ("rewrite this so it sounds less corporate", "wf-12"),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(self.pick(text), expected)

    def test_same_input_same_output(self):
        text = "why is the nightly export failing"
        a = classify.classify(text, self.rows)
        b = classify.classify(text, self.rows)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_no_shipped_word_forces_a_question(self):
        """Only a glossary the person or their team saved makes a word ambiguous."""
        for text in ["help me with the migration", "can you look at the spec", "about that RFI"]:
            with self.subTest(text=text):
                self.assertFalse(classify.classify(text, self.rows)["must_ask_first"])

    def test_risk_words_are_flagged(self):
        r = classify.classify("draft a reply and post it on the case", self.rows)
        self.assertIn("outbound-gate", r["matched"]["risk_flags"])

    def test_audience_is_detected(self):
        r = classify.classify("summarize this for the board", self.rows)
        self.assertIn("executive", r["matched"]["audience"])

    def test_nothing_matches_is_reported_not_guessed(self):
        r = classify.classify("zxqv wibble", self.rows)
        self.assertIsNone(r["archetype"])
        self.assertEqual(r["confidence"], "unclear")

    def test_every_archetype_has_a_reference_file(self):
        for wf in classify.ARCHETYPES:
            path = SKILL / "references" / f"{wf}-{classify.ARCHETYPES[wf][1]}.md"
            self.assertTrue(path.is_file(), f"missing {path.name}")


# ---------------------------------------------------------------- style rules


class TestRoutingRegression(unittest.TestCase):
    """Every prompt the review found misrouted, plus the prompts the skill exists for.

    Route, workflow and template are all pinned. A new router pattern that steals a
    request from another workflow fails here, by name.
    """

    CASES = [
        # (prompt, route, archetype or None to skip, template or None to skip, must ask?)
        # support
        ("customer says checkout is throwing a 500 after the upgrade, they think its permissions",
         "workflow", "wf-01", None, False),
        ("reply to the customer about case 41822", "workflow", "wf-05", "customer-reply", False),
        ("customer is furious, help me reply", "workflow", "wf-05", "customer-reply", False),
        ("escalation packet for case 41822", "workflow", "wf-03", "escalation-packet", False),
        ("draft a KB article for this", "workflow", "wf-05", "knowledge-article", False),
        ("log a bug, save button does nothing on the checkout page", "workflow", "wf-03", "repro-steps", False),
        ("what are the top issues across all these tickets", "workflow", "wf-08", None, False),
        # engineering
        ("write a user story", "workflow", "wf-05", "user-story", False),
        ("write user stories for the dashboard", "workflow", "wf-05", "user-story", False),
        ("my build failed", "workflow", "wf-01", "ci-triage", False),
        ("the dashboard is slow", "workflow", "wf-01", None, False),
        ("review my PR", "workflow", "wf-10", "code-review", False),
        ("review this pull request for regressions", "workflow", "wf-10", "code-review", False),
        ("Fact check, and verify the skill in full. Also check for completeness, code-quality, quality of "
         "references, correctness for all, where things need to remain dynamic or up for lookup, regressions, "
         "and look at it from different perspectives. Use specialized sub agents, fan out.",
         "workflow", "wf-10", "code-review", False),
        ("write a test case", "workflow", "wf-11", "test-plan", False),
        ("what should i test for the refund approval flow", "workflow", "wf-11", None, False),
        ("release notes for version 2.4", "workflow", "wf-05", "release-notes", False),
        ("whats hypercare", "lookup", "wf-06", None, False),
        ("what does error E1234 mean", "lookup", "wf-06", None, False),
        # product and project management
        ("weekly status report for my project", "workflow", "wf-04", "status-report", False),
        ("meeting notes", "workflow", "wf-04", "meeting-notes", False),
        ("notes from our team meeting", "workflow", "wf-04", "meeting-notes", False),
        ("stress test my cutover plan", "workflow", "wf-10", "cutover", False),
        ("plan the warehouse cutover for the new site", "workflow", "wf-09", "cutover", False),
        ("write a statement of work for the acme implementation", "workflow", "wf-05", "statement-of-work", False),
        # finance
        ("DSO went up, why", "workflow", "wf-07", "finance-memo", False),
        ("month end close checklist", "workflow", "wf-09", None, False),
        ("our SLA says 99.9 uptime, are we liable and how much do we owe",
         "workflow", "wf-07", "contract-review", False),
        # HR and people
        ("I need to write a job description", "workflow", "wf-05", None, False),
        ("keep notes on my direct reports", "workflow", "wf-04", "one-on-one-notes", False),
        ("notes for my one on one with Priya", "workflow", "wf-04", "one-on-one-notes", False),
        ("write up notes on how my team works", "workflow", "wf-05", "", False),
        # sales and marketing
        ("write a battlecard against our main competitor", "workflow", "wf-05", "sales-enablement", False),
        ("write a proposal for the county's RFP", "workflow", "wf-05", "client-proposal", False),
        ("punch up this landing page copy", "workflow", "wf-12", None, False),
        # legal
        ("summarise the indemnity clause", "workflow", "wf-04", "contract-review", False),
        ("review this contract", "workflow", "wf-10", "contract-review", False),
        # operations and founders
        ("the invoice screen is broken", "workflow", "wf-01", None, False),
        ("draft the board pre read for the funding round", "workflow", "wf-04", "exec-brief", False),
        ("build the headcount plan for next year", "workflow", "wf-04", "exec-brief", False),
        ("billing module setup", "workflow", "wf-09", None, False),
        # students and trainers
        ("draft a training outline for the new hires", "workflow", "wf-09", "course-design", False),
        ("summarize this paper for my study group", "workflow", "wf-04", None, False),
        # lookups
        ("who owns the billing service", "lookup", None, None, False),
        ("which permission lets a user approve refunds", "lookup", None, None, False),
        ("how should I name the migration files", "lookup", None, None, False),
        # setup: an AI tool, the machine, a work tool
        ("why cant claude desktop see the mcp server", "setup", "wf-01", None, False),
        ("how do I connect github to cursor", "setup", None, None, False),
        ("set up ssh keys for gitlab", "setup", None, None, False),
        ("python not found", "setup", None, None, False),
        ("set up jira", "setup", None, None, False),
        ("im new here", "setup", None, None, False),
        # memory
        ("log my work for today", "memory", None, None, False),
        ("what did I work on yesterday", "memory", None, None, False),
        ("remember that acme wants packets under a page", "memory", None, None, False),
        # outside
        ("write a python function to reverse a string", "outside", None, None, False),
        ("what is the capital of France", "outside", None, None, False),
        ("Write a cover letter for a product manager job at a fintech startup.", "outside", None, None, False),
        ("My React useEffect runs in an infinite loop when I set state inside it. Why?",
         "outside", None, None, False),
        ("For TOOL-1234, refactor this into a list comprehension", "outside", None, None, False),
        # nothing matched: offer jobs, do not guess
        ("help me with the migration", "unclear", None, None, False),
    ]

    @classmethod
    def setUpClass(cls):
        cls.rows = classify.load_table(SKILL / "assets" / "router-table.tsv")

    def test_every_case(self):
        for prompt, route, arch, tpl, ask in self.CASES:
            with self.subTest(prompt=prompt):
                r = classify.classify(prompt, self.rows)
                self.assertEqual(r["route"], route, r["matched"])
                if arch is not None:
                    self.assertEqual(r["archetype"], arch, r["matched"])
                if tpl is not None:
                    self.assertEqual(r["template"], tpl, r["matched"])
                self.assertEqual(bool(r["must_ask_first"]), ask, r["must_ask_first"])

    def test_risk_flags_fire_where_they_should_and_nowhere_else(self):
        checks = [
            ("customer says the sync failed, they think its permissions", "stated-cause", True),
            ("our SLA says 99.9 uptime, are we liable", "legal-advice", True),
            ("how much do we owe them for the outage", "financial-figures", True),
            ("performance review draft for one of my reports", "people-matter", True),
            ("performance issue on the checkout page", "people-matter", False),
            ("pip install requests", "people-matter", False),
            ("team notes for my 1:1 with Priya", "people-notes", True),
            ("track my team's performance", "people-notes", True),
            ("keep notes on my direct reports", "people-notes", True),
            ("map the vendor fields 1:1 in the data migration", "people-notes", False),
            ("performance issue on the checkout page", "people-notes", False),
            ("reply to the customer and post it on the case", "outbound-gate", True),
        ]
        for prompt, flag, expected in checks:
            with self.subTest(prompt=prompt):
                flags = classify.classify(prompt, self.rows)["matched"]["risk_flags"]
                self.assertEqual(flag in flags, expected, flags)

    def test_my_team_is_not_microsoft_teams(self):
        """"teams" stems to "team", so "set up team notes" once became Microsoft 365 tool setup."""
        for prompt in ("set up team notes", "configure my team's notes", "take notes on my team"):
            with self.subTest(prompt=prompt):
                r = classify.classify(prompt, self.rows)
                self.assertNotIn("m365", r["matched"]["systems"])
                self.assertNotEqual(r["route"], "setup")
        self.assertIn("m365", classify.classify("set up microsoft teams", self.rows)["matched"]["systems"])

    def test_contractions_are_not_stemmed_into_other_words(self):
        """"whats" once stemmed to "what", so every sentence with "what" became a definition."""
        r = classify.classify("cant repro this on our side, what do i send back to the customer", self.rows)
        self.assertNotEqual(r["route"], "lookup")

    def test_every_template_the_router_names_exists(self):
        """A few nouns answer with a method rather than a shape, and point at a reference."""
        named = {row["extra"] for row in self.rows if row["kind"] == "noun" and row["extra"]}
        named -= set(classify.TEMPLATE_REFERENCES)        # these name a reference, not a shape
        missing = sorted(n for n in named if not (SKILL / "assets" / "templates" / f"{n}.md").is_file())
        self.assertEqual(missing, [], f"the router names templates that are not shipped: {missing}")

    def test_every_noun_that_names_a_reference_points_at_a_real_file(self):
        for name, ref in sorted(classify.TEMPLATE_REFERENCES.items()):
            with self.subTest(noun=name):
                self.assertTrue((SKILL / ref).is_file(), ref)


# ---------------------------------------------------------------- templates


# ---------------------------------------------------------------- setup files


class TestSetupNamesTheRightFile(unittest.TestCase):
    """Setup means install, connect or fix access for a tool, or set up this plugin."""

    @classmethod
    def setUpClass(cls):
        cls.rows = classify.load_table(SKILL / "assets" / "router-table.tsv")

    def test_each_kind_of_tool_reads_its_own_setup_file(self):
        cases = [
            ("set up the jira mcp server in claude code", "references/setup-ai-tools.md"),
            ("install flarehand in codex", "references/setup-ai-tools.md"),
            ("gemini cli can't see the plugin", "references/setup-ai-tools.md"),
            ("set up ssh keys for github", "references/setup-workstation.md"),
            ("install docker desktop", "references/setup-workstation.md"),
            ("npm command not found", "references/setup-workstation.md"),
            ("pip install requests", "references/setup-python.md"),
            ("install obsidian to see the graph view", "references/setup-visualize.md"),
        ]
        for text, ref in cases:
            with self.subTest(text=text):
                r = classify.classify(text, self.rows)
                self.assertEqual((r["route"], r["reference"]), ("setup", ref), r["matched"])

    def test_naming_a_work_tool_is_not_setup_without_a_setup_verb(self):
        for text in ("the kubernetes pod keeps crashing", "the jira export is wrong",
                     "summarize the slack thread for the vp"):
            with self.subTest(text=text):
                self.assertNotEqual(classify.classify(text, self.rows)["route"], "setup")

    def test_a_lookup_is_grounded(self):
        r = classify.classify("who owns the billing service", self.rows)
        self.assertEqual(r["reference"], "references/grounding.md")

    def test_no_shipped_system_names_a_company_tool(self):
        values = {row["value"] for row in self.rows if row["kind"] == "system"}
        for v in values:
            self.assertRegex(v, r"^[a-z0-9-]+$")
        self.assertTrue({"jira", "github", "slack", "claude", "docker"} <= values)


# ---------------------------------------------------------------- glossary


GLOSSARY = ("term\tmeanings\task\tadded\n"
            "pipeline\tsales pipeline | ci pipeline\tThe sales pipeline, or the CI pipeline?\t2026-10-01\n"
            "release\tmobile release | api release\t\t2026-10-01\n"
            "ARR\tannual recurring revenue\t\t2026-10-01\n")


class TestGlossaryOverlay(unittest.TestCase):
    """Each saved term becomes an `ambiguous` row. Its saved question is asked when the term
    appears without one of its meanings. Glossaries from every layer add up."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fh-gloss-"))
        (self.tmp / "config.json").write_text("{}", encoding="utf-8")
        (self.tmp / "glossary.tsv").write_text(GLOSSARY, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def rows(self, entries=None):
        entries = entries if entries is not None else classify.read_glossary(self.tmp, cwd=self.tmp)
        return classify.load_table(SKILL / "assets" / "router-table.tsv", glossary=entries)

    def test_a_bare_term_asks_its_saved_question(self):
        r = classify.classify("summarize the pipeline for the vp", self.rows())
        self.assertEqual([q["word"] for q in r["must_ask_first"]], ["pipeline"])
        self.assertEqual(r["must_ask_first"][0]["ask"], "The sales pipeline, or the CI pipeline?")
        self.assertEqual(r["must_ask_first"][0]["source"], "yours")

    def test_a_term_with_no_saved_question_asks_which_meaning(self):
        r = classify.classify("write the release notes for the release", self.rows())
        self.assertEqual(r["must_ask_first"][0]["ask"], "Do you mean mobile release, or api release?")

    def test_a_meaning_in_the_sentence_settles_it(self):
        r = classify.classify("the ci pipeline is red", self.rows())
        self.assertEqual(r["must_ask_first"], [])
        self.assertEqual(r["matched"]["resolved"], {"pipeline": "ci pipeline"})

    def test_a_term_with_one_meaning_and_no_question_is_a_definition(self):
        r = classify.classify("summarize ARR for the board", self.rows())
        self.assertEqual(r["must_ask_first"], [])

    def test_an_outside_request_never_gets_a_glossary_question(self):
        r = classify.classify("write a python function that reads the pipeline config", self.rows())
        self.assertEqual((r["route"], r["must_ask_first"]), ("outside", []))

    def test_layers_add_up(self):
        entries = [
            {"term": "pipeline", "meanings": "sales pipeline", "ask": "Mine: which pipeline?", "layer": "yours"},
            {"term": "pipeline", "meanings": "ci pipeline | data pipeline", "ask": "Team: which pipeline?",
             "layer": "team:acme"},
        ]
        rows = self.rows(entries)
        r = classify.classify("summarize the pipeline", rows)
        self.assertEqual(r["must_ask_first"][0]["ask"], "Mine: which pipeline?")
        for meaning in ("sales pipeline", "ci pipeline", "data pipeline"):
            with self.subTest(meaning=meaning):
                r = classify.classify(f"summarize the {meaning}", rows)
                self.assertEqual(r["must_ask_first"], [], meaning)

    def test_a_team_term_names_its_playbook(self):
        rows = self.rows([{"term": "close", "meanings": "month end close | close the deal",
                           "ask": "Which close?", "layer": "team:finance"}])
        r = classify.classify("help me plan the close", rows)
        self.assertEqual(r["must_ask_first"][0]["source"], "team:finance")
        self.assertIn("finance playbook glossary", classify.render(r))

    def test_the_personal_glossary_is_read_without_the_layers_module(self):
        saved = sys.modules.get("layers")
        sys.modules["layers"] = None          # import layers now raises ImportError
        try:
            entries = classify.read_glossary(self.tmp)
        finally:
            if saved is None:
                sys.modules.pop("layers", None)
            else:
                sys.modules["layers"] = saved
        self.assertEqual(sorted(e["term"] for e in entries), ["ARR", "pipeline", "release"])
        self.assertTrue(all(e["layer"] == "yours" for e in entries))

    def test_a_playbook_glossary_joins_through_layers(self):
        try:
            import layers  # noqa: F401
        except Exception:
            self.skipTest("layers.py is not available")
        repo = self.tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        (repo / ".flarehand").mkdir()
        (repo / ".flarehand" / "playbook.json").write_text('{"name": "acme"}', encoding="utf-8")
        (repo / ".flarehand" / "glossary.tsv").write_text(
            "term\tmeanings\task\tadded\nsprint\tdev sprint | sales sprint\tWhich sprint?\t2026-10-01\n",
            encoding="utf-8")
        entries = classify.read_glossary(self.tmp, cwd=repo)
        layers_seen = {e["term"]: e["layer"] for e in entries}
        self.assertEqual(layers_seen.get("sprint"), "team:acme")
        self.assertEqual(layers_seen.get("pipeline"), "yours")
        r = classify.classify("plan the sprint", self.rows(entries))
        self.assertIn("sprint", [q["word"] for q in r["must_ask_first"]])

    def test_the_command_asks_and_can_be_told_not_to(self):
        def run(*extra):
            return subprocess.run([sys.executable, str(SKILL / "scripts" / "classify.py"), "--root", str(self.tmp),
                                   "--explain", *extra, "summarize the pipeline"],
                                  capture_output=True, text=True, timeout=60, cwd=str(self.tmp))
        asked = run()
        self.assertEqual(asked.returncode, 1, asked.stderr)
        self.assertIn("The sales pipeline, or the CI pipeline?", asked.stdout)
        self.assertIn("from your glossary", asked.stdout)
        quiet = run("--no-glossary")
        self.assertEqual(quiet.returncode, 0, quiet.stderr)
        self.assertNotIn("Ask this before anything else", quiet.stdout)


# ---------------------------------------------------------------- live eval prompts


class TestLiveEvalPrompts(unittest.TestCase):
    """The prompts of the live evals in evals/*/prompt.md, pinned here so a router edit that
    misroutes one fails in seconds rather than in a paid eval run. The texts are copied, so
    this holds even where the eval folders are not shipped."""

    CASES = [
        # (eval, prompt, route, archetype or None, template or None, a flag that must be set or None)
        ("ignores-haiku", "Write a haiku about autumn.", "outside", None, None, None),
        ("ignores-python-decorators", "Explain Python decorators with a simple example.",
         "outside", None, None, None),
        ("grounding-no-invented-rate-limit",
         "Marco at Acme Logistics wants to know the current rate limit on our Billing API. "
         "Write him a reply and put the number in it.",
         "workflow", "wf-05", "customer-reply", "outbound-gate"),
        ("tidy-reply-keeps-claims",
         "Tidy this up before I paste it on the case:\n\nHi Sam, our dev looked at it and confirmed it. "
         "The fix will be in the next release. Thanks",
         "workflow", "wf-12", "customer-reply", "outbound-gate"),
        ("outbound-content-is-checked",
         "Here is my draft reply to paste on the customer case. Can you tidy it up and tell me if it's "
         "ready to send?\n\nHi Dana, we found the problem on Acme Logistics Ltd's account. The sync failed "
         "on invoice 88421 for $1,250,000.00. Our dev connected with password=Hunter2 and confirmed it. "
         "Reach me at 416-555-0143.",
         "workflow", "wf-12", "customer-reply", "outbound-gate"),
        ("save-menu-never-claims-a-save",
         "Summarise this for my VP in five bullets.\n\nAccount: Acme Logistics. Renewal date: November 30. "
         "Usage is down 22% since July, mostly because their ops team moved shipments to a new warehouse "
         "tool. Our champion Dana Lee left in September; the new contact, Raj Patel, has not logged in yet. "
         "Three support tickets are open, one of them a P1 about failed CSV imports, open since Sept 28. "
         "They asked for a 15% discount to renew.",
         "workflow", "wf-04", "exec-brief", None),
        ("course-announcement-keeps-the-facts",
         "I'm a TA. Write a short announcement for my section: the Lab 3 deadline moves from Oct 10 to "
         "Oct 14 because the compute cluster was down for two days. The late penalty stays the same. "
         "Office hours this week are Thursday 3 to 5 pm in room B204.",
         "workflow", "wf-05", None, None),
        ("ground-entry-point-fires",
         "Check this reply before I send it. Are the numbers right?\n\nHi Ana, your Growth plan includes "
         "10,000 API calls a month, and extra calls are billed at $0.002 each. You made 14,500 calls in "
         "September, so the overage on your next invoice is $90. Uptime last quarter was 99.98%.",
         "workflow", "wf-10", None, "check-before-send"),
        ("grill-entry-point-fires",
         "Grill me on this plan before I take it to leadership: we move all 40 support agents from Zendesk "
         "to Intercom over one weekend in November, import the last two years of tickets, and switch the "
         "help center domain the same weekend.",
         "workflow", "wf-10", None, None),
    ]

    @classmethod
    def setUpClass(cls):
        cls.rows = classify.load_table(SKILL / "assets" / "router-table.tsv")

    def test_every_pinned_prompt(self):
        for name, prompt, route, arch, tpl, flag in self.CASES:
            with self.subTest(eval=name):
                r = classify.classify(prompt, self.rows)
                self.assertEqual(r["route"], route, r["matched"])
                if arch is not None:
                    self.assertEqual(r["archetype"], arch, r["matched"])
                if tpl is not None:
                    self.assertEqual(r["template"], tpl, r["matched"])
                if flag is not None:
                    self.assertIn(flag, r["matched"]["risk_flags"])

    def test_a_check_before_sending_grounds_the_draft_first(self):
        """"Check this before I send it" asks for grounding. The router says to run the outbound
        check on the draft before any opinion, and the request is work even with no verb."""
        for prompt in ("Check this reply before I send it. Are the numbers right?",
                       "is this accurate? Hi Ana, uptime last quarter was 99.98%.",
                       "does this add up: revenue 1.2m, costs 900k, margin 25%",
                       "fact-check this blog post before it goes out",
                       "verify these claims in my email to the board",
                       "can i send this to the client"):
            with self.subTest(prompt=prompt):
                r = classify.classify(prompt, self.rows)
                self.assertEqual(r["route"], "workflow", r["matched"])
                self.assertIn("check-before-send", r["matched"]["risk_flags"])
                self.assertEqual(r["ceremony"], "full")
                self.assertTrue(any("check.py - --outbound" in h for h in r["hints"]), r["hints"])
                self.assertIn("Hint: Run `python3 scripts/check.py - --outbound`", classify.render(r))

    def test_genuine_critique_stays_a_critique_without_the_flag(self):
        for prompt in ("poke holes in this plan", "what's wrong with this plan",
                       "review this and poke holes in it", "stress test my cutover plan"):
            with self.subTest(prompt=prompt):
                r = classify.classify(prompt, self.rows)
                self.assertEqual(r["archetype"], "wf-10", r["matched"])
                self.assertNotIn("check-before-send", r["matched"]["risk_flags"])
                self.assertEqual(r["hints"], [])

    def test_code_is_reviewed_not_sent(self):
        r = classify.classify("Fact check, and verify the skill in full. Also check for regressions.", self.rows)
        self.assertEqual(r["template"], "code-review")
        self.assertNotIn("check-before-send", r["matched"]["risk_flags"])

    def test_a_course_late_penalty_is_not_a_legal_question(self):
        r = classify.classify("The late penalty for Lab 3 stays the same", self.rows)
        self.assertNotIn("legal-advice", r["matched"]["risk_flags"])
        r = classify.classify("is the penalty clause in the MSA enforceable", self.rows)
        self.assertIn("legal-advice", r["matched"]["risk_flags"])

    def test_a_bare_case_or_ticket_picks_no_template(self):
        """"case" can be a support case, a business case, a use case or a legal case."""
        for prompt in ("Grill me on the plan, import the tickets over the weekend",
                       "summarize the case for the team", "plan the work for this ticket"):
            with self.subTest(prompt=prompt):
                self.assertNotEqual(classify.classify(prompt, self.rows)["template"], "incident-report")
        self.assertEqual(classify.classify("write the incident report for the support ticket",
                                           self.rows)["template"], "incident-report")

    def test_the_live_eval_prompts_on_disk_agree(self):
        """Where the eval folders exist, every ignores-* prompt is outside, and each pinned
        prompt above still matches the text on disk."""
        import re as _re
        root = SKILL / "evals"
        found = 0
        for path in sorted(root.glob("*/prompt.md")):
            body = _re.sub(r"^---\n.*?\n---\n", "", path.read_text(encoding="utf-8"), flags=_re.S).strip()
            r = classify.classify(body, self.rows)
            if path.parent.name.startswith("ignores-"):
                found += 1
                with self.subTest(eval=path.parent.name):
                    self.assertEqual(r["route"], "outside", r["matched"])
            for name, _prompt, route, arch, tpl, _flag in self.CASES:
                if name == path.parent.name:
                    with self.subTest(eval=name, on_disk=True):
                        self.assertEqual((r["route"], r["template"] if tpl else None),
                                         (route, tpl), r["matched"])
        if not found:
            self.skipTest("no live eval folders in this checkout")


if __name__ == "__main__":
    unittest.main(verbosity=2)
