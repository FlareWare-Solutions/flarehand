#!/usr/bin/env python3
"""tests_router.py - tier 0 checks for the router and the word normaliser.

Each test pins a prompt a review found misrouted. If one fails, a router row or a
stemmer rule has moved, and the prompt named in the failure tells you which.
"""

from __future__ import annotations

import re
import shutil
import tempfile
import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import classify  # noqa: E402
from _text import exact_form, tokens  # noqa: E402


class TestWordNormalising(unittest.TestCase):
    def test_letters_from_any_script_survive_in_the_exact_form(self):
        japanese = exact_form("東京オフィスの住所は？")
        russian = exact_form("Почему не работает?")
        self.assertTrue(japanese)
        self.assertTrue(russian)
        self.assertNotEqual(japanese, exact_form("大阪の電話番号は？"))
        self.assertNotEqual(japanese, russian)

    def test_ascii_exact_form_is_unchanged(self):
        """Saved answer keys depend on this. These values were taken before the change."""
        self.assertEqual(exact_form("How do I set up Jira?"), "how do i set up jira")
        self.assertEqual(exact_form("payroll isn't calculating overtime"), "payroll isnt calculating overtime")
        self.assertEqual(exact_form("map the S drive, e-mail me!"), "map the s drive e mail me")
        self.assertEqual(exact_form("What's the PR format for 12.0.34?"), "whats the pr format for 12 0 34")

    def test_contractions_expand_for_routing_only(self):
        self.assertEqual(tokens("isn't"), ["is", "not"])
        self.assertEqual(tokens("doesn't"), ["do", "not"])
        self.assertEqual(tokens("can't"), tokens("cannot"))
        self.assertEqual(tokens("won't load"), ["will", "not", "load"])
        self.assertEqual(exact_form("isn't"), "isnt")

    def test_stems_do_not_collide_with_router_words(self):
        pairs = [("themes", "theme"), ("them", "them"), ("fired", "fire"), ("firing", "fire"),
                 ("fire", "fire"), ("stuck", "stuck"), ("sticks", "stick"), ("noted", "note"),
                 ("added", "add"), ("fixed", "fix"), ("logged", "log"), ("created", "creat"),
                 ("create", "creat"), ("saved", "save"), ("accrued", "accru"), ("accrue", "accru")]
        for word, stem in pairs:
            with self.subTest(word=word):
                self.assertEqual(tokens(word), [stem])
        self.assertNotEqual(tokens("them"), tokens("theme"))
        self.assertNotEqual(tokens("sticks"), tokens("stuck"))


class TestRouterFixes(unittest.TestCase):
    """(prompt, route, archetype or None to skip, template or None to skip)."""

    CASES = [
        # contractions
        ("payroll isn't calculating overtime", "workflow", "wf-01", ""),
        ("payroll is not calculating overtime", "workflow", "wf-01", ""),
        ("the export to the warehouse doesn't load for one user", "workflow", "wf-01", ""),
        ("my teams chat isnt loading", "workflow", "wf-01", ""),
        ("customer says the invoice total is wrong after the upgrade", "workflow", "wf-01", ""),
        # AI tools are set up the same way, whichever one it is
        ("set up codex with the jira mcp server", "setup", None, None),
        ("codex can't see the mcp server", "setup", None, None),
        ("write a runbook for the codex rollout", "workflow", "wf-09", None),
        # a language on its own is about code
        ("in python how do I read a json file", "outside", None, None),
        ("my python code throws KeyError", "outside", None, None),
        ("can you build a python script to parse csv", "outside", None, None),
        ("write a python script that reads the jira api", "outside", None, None),
        ("python not found", "setup", None, None),
        ("pip install requests", "setup", None, None),
        ("set up flutter with fvm on my new laptop", "setup", None, None),
        # infrastructure is the work itself unless they ask to set it up
        ("the kubernetes pod keeps crashing", "workflow", "wf-01", None),
        ("install docker desktop", "setup", None, None),
        # finance
        ("why doesn't AR tie to GL this month and how much do we need to accrue", "workflow", "wf-07", "finance-memo"),
        ("how much do we need to accrue", "workflow", "wf-07", "finance-memo"),
        # containing rows give the swallowed noun its template back
        ("review my test script for the UAT", "workflow", "wf-10", "test-plan"),
        ("review my uat script", "workflow", "wf-10", "test-plan"),
        ("review the demo script for the prospect", "workflow", "wf-10", "sales-enablement"),
        ("review the version script before the build", "workflow", "wf-10", "sql-build"),
        ("review the cost code structure for the job", "workflow", "wf-10", ""),
        ("audit the GL account code mapping before go live", "workflow", "wf-10", ""),
        ("review the error code E1234 with support", "workflow", "wf-10", ""),
        ("review my code", "workflow", "wf-10", "code-review"),
        ("the fields map 1:1 with the vendor table", "workflow", "wf-07", ""),
        ("one on one mapping between the accounts and the contracts", "workflow", "wf-07", ""),
        ("notes for my 1:1 with Priya", "workflow", "wf-04", "one-on-one-notes"),
        # a noun swallowed by a verb of another kind sets no template
        ("list the edge cases for the refund approval flow", "workflow", "wf-11", ""),
        ("log a bug, save button does nothing on the checkout page", "workflow", "wf-03", "repro-steps"),
        # ties between nouns
        ("create a runbook for the nightly build", "workflow", "wf-09", "runbook"),
        ("the nightly build is red again", "workflow", "wf-01", "ci-triage"),
        ("cutover plan for the acme go live", "workflow", "wf-09", "cutover"),
        # proposals, renewals, and the teams that share a template
        ("write a proposal for the county's RFP", "workflow", "wf-05", "client-proposal"),
        ("prepare the renewal proposal and true up for a customer", "workflow", "wf-05", "deal-summary"),
        ("write a renewal recap for acme", "workflow", "wf-05", "deal-summary"),
        ("true up for the acme renewal", "workflow", "wf-05", "deal-summary"),
        ("prepare the true up for the quarter close", "workflow", "wf-07", "finance-memo"),
        ("go no go for the acme go live", "workflow", "wf-04", "exec-brief"),
        ("write the go/no-go decision for Friday", "workflow", "wf-04", "exec-brief"),
        ("write a technical design for the new approval flow", "workflow", "wf-05", "design-doc"),
        ("draft the solution design for the integration", "workflow", "wf-05", "design-doc"),
        ("write the functional spec for the export screen", "workflow", "wf-05", "functional-spec"),
        # templates added for a general audience
        ("write a postmortem for yesterday's outage", "workflow", "wf-05", "postmortem"),
        ("write the monthly investor update", "workflow", "wf-05", "investor-update"),
        ("help me write my thesis research proposal", "workflow", "wf-05", "research-proposal"),
        ("write a creative brief for the spring campaign", "workflow", "wf-05", "creative-brief"),
        ("write a job description for a senior designer", "workflow", "wf-05", "job-description"),
        ("draft a 30 60 90 day plan for my new hire", "workflow", "wf-05", "onboarding-plan"),
        ("write an ADR for moving to postgres", "workflow", "wf-05", "decision-record"),
        ("we need a policy on remote work", "workflow", "wf-05", "policy"),
        ("write the status page update for the outage", "workflow", "wf-05", "incident-comms"),
        ("run a sprint retro for the team", "workflow", "wf-05", "retrospective"),
        ("write an SOP for onboarding new vendors", "workflow", "wf-05", "sop"),
        ("write a vendor evaluation for our CRM shortlist", "workflow", "wf-05", "vendor-evaluation"),
        ("write a help article for the new settings page", "workflow", "wf-05", "knowledge-article"),
        ("write a statement of work for the acme implementation", "workflow", "wf-05", "statement-of-work"),
        ("write the project closeout report for the client", "workflow", "wf-05", "project-closeout"),
        # code objects go to the code review method
        ("review the stored procedure before I commit", "workflow", "wf-10", "code-review"),
        ("review the changes to the orders REST endpoint", "workflow", "wf-10", "code-review"),
        # memory phrasings
        ("log that we decided to use postgres", "memory", None, None),
        ("remember we decided to use postgres", "memory", None, None),
        ("log that we picked provider over riverpod", "memory", None, None),
        ("record that acme wants packets under a page", "memory", None, None),
        # a lookup that covers the noun
        ("how should I name the migration files", "lookup", None, None),
        ("which permission lets a user approve refunds", "lookup", None, None),
        ("write the migration script for the new column", "workflow", "wf-09", "sql-build"),
        # the pronoun "them" is not the verb "theme"
        ("send them the updated invoice", "unclear", None, None),
    ]

    @classmethod
    def setUpClass(cls):
        cls.rows = classify.load_table(SKILL / "assets" / "router-table.tsv")

    def go(self, text: str) -> dict:
        return classify.classify(text, self.rows)

    def test_every_case(self):
        for prompt, route, arch, tpl in self.CASES:
            with self.subTest(prompt=prompt):
                r = self.go(prompt)
                self.assertEqual(r["route"], route, r["matched"])
                if arch is not None:
                    self.assertEqual(r["archetype"], arch, r["matched"])
                if tpl is not None:
                    self.assertEqual(r["template"], tpl, r["matched"])

    def test_risk_flags(self):
        checks = [
            ("why doesn't AR tie to GL this month and how much do we need to accrue", "financial-figures", True),
            ("how much do we need to accrue", "financial-figures", True),
            ("AR doesn't tie out to GL", "financial-figures", True),
            ("invoke the orders endpoint with a POST to reproduce", "production-write", True),
            ("call the orders endpoint POST to create an order in dev", "production-write", True),
            ("force push the fix to main", "production-write", True),
            ("answer this security questionnaire from a prospect", "outbound-gate", True),
            ("answer this security questionnaire from a prospect", "security-claim", True),
            ("write a proposal for the county's RFP", "outbound-gate", True),
            ("write a proposal for the prospect", "outbound-gate", True),
            ("summarise the indemnity clause", "legal-advice", True),
            ("answer the soc 2 questionnaire", "security-claim", True),
            ("keep notes on my direct reports", "people-notes", True),
            ("notes for my 1:1 with Priya", "people-notes", True),
            ("the fields map 1:1 with the vendor table", "people-notes", False),
            ("one on one mapping between the accounts and the contracts", "people-notes", False),
            ("the trigger fired twice on save", "people-matter", False),
            ("we need to fire him before the review", "people-matter", True),
            ("send them the updated invoice", "financial-figures", False),
            ("where do I find the api key for the staging server", "credentials", True),
            ("rotate the client secret before the demo", "credentials", True),
            ("write the release notes for 2.4", "credentials", False),
            ("we are planning a layoff next quarter", "people-matter", True),
        ]
        for prompt, flag, expected in checks:
            with self.subTest(prompt=prompt, flag=flag):
                flags = self.go(prompt)["matched"]["risk_flags"]
                self.assertEqual(flag in flags, expected, flags)

    def test_the_shipped_table_asks_about_no_word(self):
        """Words with two meanings come from glossaries the person or their team saved."""
        self.assertEqual([r for r in self.rows if r["kind"] in ("ambiguous", "context")], [])
        for prompt in ("help me with the migration", "can you look at the spec", "close the deal",
                       "what role do I need for the billing screen", "the pipeline is red"):
            with self.subTest(prompt=prompt):
                self.assertEqual(self.go(prompt)["must_ask_first"], [])

    def test_a_legal_question_ends_with_legal(self):
        r = self.go("does this SLA breach mean we owe credits")
        self.assertIn("legal-advice", r["matched"]["risk_flags"])
        self.assertEqual(r["next_step"]["name"], "Legal")
        self.assertNotIn("differ", r["next_step"]["why"])
        text = classify.render(r)
        self.assertIn("Offer next: Legal", text)
        # the usual chain still applies without the flag
        self.assertEqual(self.go("DSO went up, why")["next_step"]["archetype"], "wf-01")

    def test_the_table_is_hand_edited_and_nothing_writes_it(self):
        for path in (SKILL / "scripts").glob("*.py"):
            src = path.read_text(encoding="utf-8")
            if "router-table" in src:
                self.assertNotIn("TABLE.write", src, path.name)
                self.assertNotIn("TABLE.open(", src, path.name)
        doc = (SKILL / "references" / "router.md").read_text(encoding="utf-8")
        self.assertIn("by hand", doc)
        self.assertIn("There is no generator", doc)



class TestLookupStaysALookup(unittest.TestCase):
    def route(self, text):
        return classify.classify(text, classify.load_table(SKILL / "assets" / "router-table.tsv"))

    def test_a_lookup_carries_no_workflow_or_template(self):
        """SKILL.md gives a lookup steps 4, 5 and 7 only. A workflow riding along invites
        the shape of an artifact nobody asked for."""
        r = self.route("how should I name the migration files")
        self.assertEqual(r["route"], "lookup")
        self.assertFalse(r["archetype"], r["archetype"])
        self.assertFalse(r["template"], r["template"])

    def test_a_definition_still_keeps_wf_06(self):
        """Explaining a term really is the translate workflow, so that pairing stays."""
        for text in ("whats hypercare", "what does error E1234 mean"):
            with self.subTest(text=text):
                r = self.route(text)
                self.assertEqual((r["route"], r["archetype"]), ("lookup", "wf-06"))


class TestPersonalRouterRows(unittest.TestCase):
    def rows(self, personal: str):
        d = Path(tempfile.mkdtemp(prefix="hww-rt-"))
        (d / "router-table.tsv").write_text(personal, encoding="utf-8")
        try:
            return classify.load_table(SKILL / "assets" / "router-table.tsv",
                                       classify.personal_table(d))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_a_personal_risk_row_is_kept(self):
        """A risk row widens what gets checked, which a personal file is allowed to do."""
        rows = self.rows("kind\tpattern\tvalue\tweight\textra\n"
                         "risk\tacme pricing\tfinancial-figures\t9\t\n")
        self.assertTrue([r for r in rows if r.get("personal") and r["kind"] == "risk"])
        r = classify.classify("send the acme pricing summary", rows)
        self.assertIn("financial-figures", r["matched"]["risk_flags"])

    def test_a_personal_route_row_cannot_lower_a_risky_request(self):
        rows = self.rows("kind\tpattern\tvalue\tweight\textra\n"
                         "route\treply to the customer\tmemory\t0\t\n")
        r = classify.classify("draft a reply to the customer about their invoice dispute", rows)
        self.assertNotEqual(r["route"], "memory")
        self.assertEqual(r["ceremony"], "full")

    def test_a_personal_row_cannot_answer_a_glossary_question(self):
        """Where intent is unclear the skill asks. A data file must not answer for the person."""
        rows = self.rows("kind\tpattern\tvalue\tweight\textra\n"
                         "context\tthe release\trelease\t0\tmobile\n")
        rows += classify.glossary_rows([{"term": "release", "meanings": "mobile release | api release",
                                         "ask": "Which release?", "layer": "yours"}])
        r = classify.classify("the customer says the cause is the release", rows)
        self.assertIn("release", [q["word"] for q in r["must_ask_first"]])

    def test_a_personal_route_row_is_kept(self):
        rows = self.rows("kind\tpattern\tvalue\tweight\textra\n"
                         "noun\tap reconciliation\tmy-recon\t9\tmy-recon\n")
        self.assertTrue([r for r in rows if r.get("personal") and r["value"] == "my-recon"])

    def test_a_personal_noun_cannot_suppress_a_guardrail(self):
        rows = self.rows("kind\tpattern\tvalue\tweight\textra\n"
                         "noun\tindemnity clause review\tmy-thing\t20\t\n")
        r = classify.classify("please do an indemnity clause review", rows)
        self.assertIn("legal-advice", r["matched"]["risk_flags"])
        self.assertEqual(r["ceremony"], "full")


class TestSaveThisKnowsWhatItIs(unittest.TestCase):
    """Seven stores with different write commands and freshness rules. "Save this" used to
    collapse to one bucket, and three kinds never reached it at all."""

    def kind(self, text):
        r = classify.classify(text, classify.load_table(SKILL / "assets" / "router-table.tsv"))
        return r["route"], r.get("memory_kind", "")

    def test_the_kind_is_named_when_the_words_say_it(self):
        for text, want in (("save these steps as a chain", "chain"),
                           ("save this answer so I get it again", "answer"),
                           ("save a copy of this error log", "snapshot"),
                           ("remember that Priya owns the billing service", "person"),
                           ("log today's work", "log"),
                           ("save this as my template", "template"),
                           ("add pipeline to my glossary", "glossary"),
                           ("when i say close i mean the month end close", "glossary"),
                           ("our rule is one ticket per pull request, save it as a house rule", "rule")):
            with self.subTest(text=text):
                self.assertEqual(self.kind(text), ("memory", want))

    def test_a_chain_no_longer_starts_a_planning_interview(self):
        """`step` is a wf-09 verb, so this used to route to a plan and ask four questions."""
        self.assertEqual(self.kind("save these steps as a chain")[0], "memory")

    def test_a_memory_phrase_inside_a_work_request_does_not_hijack_it(self):
        """These all routed to memory once: route rows win on presence, whatever their weight."""
        for text, route in (("draft the SOW and keep a copy of the pricing table", "workflow"),
                            ("use this shape for the release notes", "workflow"),
                            ("my version of the status report is late, help me write it", "workflow"),
                            ("write the runbook the way we did it in march", "workflow"),
                            ("next time i ask for a test plan include edge cases", "workflow"),
                            ("next time i ask about installing docker give me this", "setup")):
            with self.subTest(text=text):
                self.assertEqual(self.kind(text)[0], route)

    def test_a_product_workflow_question_is_not_a_request_to_write_a_skill_workflow(self):
        r = classify.classify("how do I create a workflow in Jira for PO approvals",
                              classify.load_table(SKILL / "assets" / "router-table.tsv"))
        self.assertNotEqual(r["reference"], "references/wf-authoring.md")

    def test_a_bare_save_names_no_kind_so_the_model_asks(self):
        self.assertEqual(self.kind("save this"), ("memory", ""))


class TestWorkflowGraph(unittest.TestCase):
    """The chain between workflows is data now, so it can be checked against the prose
    that describes it, and it cannot walk a two-step loop for ever."""

    def graph(self):
        rows = classify._rows(SKILL / "assets" / "workflow-graph.tsv", 4)
        out = {}
        for r in rows:
            out.setdefault(r[0], []).append(r[1])
        return out

    def test_the_table_matches_the_chains_to_sections(self):
        for path in sorted((SKILL / "references").glob("wf-[0-9][0-9]-*.md")):
            src = path.name[:5]
            prose = sorted(set(re.findall(r"wf-\d\d",
                                          path.read_text(encoding="utf-8").split("## Chains to")[-1])))
            with self.subTest(workflow=src):
                self.assertEqual(sorted(set(self.graph().get(src, []))), prose)

    def test_every_edge_names_a_real_workflow(self):
        known = set(classify.ARCHETYPES)
        for src, tos in self.graph().items():
            self.assertIn(src, known)
            for to in tos:
                self.assertIn(to, known, f"{src} -> {to}")

    def test_no_two_workflows_offer_each_other_first(self):
        """Following only the first offer used to bounce wf-09 to wf-11 and back."""
        first = {s: t[0] for s, t in self.graph().items()}
        for a, b in first.items():
            with self.subTest(edge=f"{a} -> {b}"):
                self.assertNotEqual(first.get(b), a, f"{a} and {b} offer each other first")

    def test_every_loop_of_first_offers_says_when_to_stop(self):
        """Every workflow has a next step, so following first offers always cycles somewhere.
        What keeps that from running forever is a stop line the check can decide."""
        first = {s: t[0] for s, t in self.graph().items()}
        for start in first:
            seen, cur = [], start
            while cur in first and cur not in seen:
                seen.append(cur)
                cur = first[cur]
            loop = seen[seen.index(cur):] if cur in seen else []
            with self.subTest(loop=loop):
                stops = [w for w in loop if "Stop when `check_output.py` passes" in
                         next((SKILL / "references").glob(f"{w}-*.md")).read_text(encoding="utf-8")
                         .split("## Chains to")[-1]]
                self.assertTrue(stops or not loop, f"{loop} never says when to stop")

    def test_a_personal_row_naming_an_unknown_workflow_does_not_crash(self):
        tmp = Path(tempfile.mkdtemp(prefix="hww-wf99-"))
        try:
            mine = tmp / "router-table.tsv"
            mine.write_text("kind\tpattern\tvalue\tweight\textra\n"
                            "noun\tap reconciliation\twf-99\t9\tap-recon\n", encoding="utf-8")
            rows = classify.load_table(SKILL / "assets" / "router-table.tsv", mine)
            for text in ("write the ap reconciliation", "why is the ap reconciliation failing",
                         "review the ap reconciliation for the controller"):
                with self.subTest(text=text):
                    r = classify.classify(text, rows)
                    self.assertIsInstance(r["archetype_name"], str)
            self.assertIn("not a workflow", classify.classify("write the ap reconciliation", rows)["archetype_name"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_their_own_template_file_is_named_first(self):
        tmp = Path(tempfile.mkdtemp(prefix="hww-mytpl-"))
        try:
            (tmp / "templates").mkdir()
            (tmp / "templates" / "runbook.md").write_text("mine", encoding="utf-8")
            classify.load_personal_workflows(tmp)
            rows = classify.load_table(SKILL / "assets" / "router-table.tsv")
            got = classify.classify("write a runbook for the nightly job", rows)
            self.assertEqual(got["template_file"], str(tmp / "templates" / "runbook.md"))
        finally:
            classify.load_personal_workflows(None)
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_personal_workflow_is_known_by_name(self):
        tmp = Path(tempfile.mkdtemp(prefix="hww-mywf-"))
        try:
            (tmp / "workflows.tsv").write_text("id\tname\tslug\nap-recon\tMonthly AP reconciliation\tap-recon\n",
                                               encoding="utf-8")
            classify.load_personal_workflows(tmp)
            self.assertIn("ap-recon", classify.ARCHETYPES)
            self.assertIn("Monthly AP reconciliation", classify.archetype_name("ap-recon"))
        finally:
            classify.load_personal_workflows(None)
            shutil.rmtree(tmp, ignore_errors=True)

    def test_an_unknown_workflow_degrades_instead_of_crashing(self):
        for text in ("write a widget report", "why is the widget report failing"):
            with self.subTest(text=text):
                r = classify.classify(text, classify.load_table(
                    SKILL / "assets" / "router-table.tsv"))
                self.assertIsInstance(r["archetype_name"], str)



class TestRewordingsHold(unittest.TestCase):
    """The same request, worded the way different people type it, lands on the same route.

    A 2026-09 review reworded every eval prompt three ways. 38 of 48 kept their route,
    and a customer's theory stated as "is sure" or "insists" carried no stated-cause flag,
    so the rule that keeps it unverified never fired. These pin the fix.
    """

    GROUPS = [
        ("workflow", "wf-10", ["Review this change before I merge it", "Can you review my diff before merging?",
                               "code review this PR for me",
                               "Look over this change and tell me if it breaks anything before I merge"]),
        ("workflow", "wf-05", ["Draft a KB article on how to clear a stuck import batch.",
                               "Can you write up a help article for fixing a stuck import batch?",
                               "How do I write a project closeout report for the customer?",
                               "help me write the go-live wrap up for the client",
                               "What goes in a post go-live summary for a customer?"]),
        ("outside", None, ["How do I reverse a string in JavaScript?", "Give me a regex that matches an email address",
                           "Help me write a short birthday message for my sister.",
                           "write a happy birthday note for my mom", "Help me write a wedding toast for my best friend",
                           "Can you write a thank you card for my neighbour?",
                           "Write a cover letter for a product manager job at a fintech startup.",
                           "Write a SQL query that returns the top 10 customers by total order value from orders(customer_id, amount).",
                           "My React useEffect runs in an infinite loop when I set state inside it. Why?",
                           "For TOOL-1234, refactor this into a list comprehension: def f(xs): return [x for x in xs]",
                           "Write me a Python function that reverses a string."]),
        ("memory", None, ["store everything to the knowledge base", "save everything to notes",
                          "save all of this to my knowledge base", "put this in my knowledge base",
                          "keep a note of all this",
                          "Replay the answer you saved last week for how do I unlock a user in the admin console",
                          "What did you tell me last time about unlocking a user?",
                          "Give me the saved answer for unlocking a user in the admin console"]),
        ("lookup", None, ["at what dollar amount does a purchase order need approval",
                          "Which permission lets someone approve refunds?",
                          "who approves expense reports over the limit"]),
        ("workflow", "wf-12", ["Here is my draft reply to paste on the customer case. Can you tidy it up?",
                               "clean up this reply before I send it to the client",
                               "Proofread my response to the customer and tell me if it's good to go"]),
        ("workflow", "wf-01", ["Checkout fails for one customer. They are sure it's their permission setup. Why?"]),
    ]

    RISKS = [
        ("Checkout fails for one customer. They are sure it's their permission setup. Why?", "stated-cause", True),
        ("customer insists it's a bug in our code", "stated-cause", True),
        ("Client is convinced the upgrade broke their payroll", "stated-cause", True),
        ("I'm sure it's the permission setup", "stated-cause", True),
        ("they blame the upgrade for the sync error", "stated-cause", True),
        ("Make sure the batch runs before Friday", "stated-cause", False),
        ("Are you sure this is right?", "stated-cause", False),
        ("Here is my draft reply to paste on the customer case. Can you tidy it up and tell me if it's ready to send?",
         "outbound-gate", True),
        ("email the client that the fix ships Friday", "outbound-gate", True),
        ("Proofread my response to the customer and tell me if it's good to go", "outbound-gate", True),
        ("clean up this reply before I send it to the client", "outbound-gate", True),
        ("clean up this SQL before I run it", "outbound-gate", False),
    ]

    @classmethod
    def setUpClass(cls):
        cls.rows = classify.load_table(SKILL / "assets" / "router-table.tsv")

    def test_every_wording_keeps_its_route(self):
        for route, arch, prompts in self.GROUPS:
            for prompt in prompts:
                with self.subTest(prompt=prompt):
                    r = classify.classify(prompt, self.rows)
                    self.assertEqual(r["route"], route, r["matched"])
                    if arch is not None:
                        self.assertEqual(r["archetype"], arch, r["matched"])

    def test_every_wording_of_a_theory_or_an_outbound_draft_is_flagged(self):
        for prompt, flag, expected in self.RISKS:
            with self.subTest(prompt=prompt, flag=flag):
                flags = classify.classify(prompt, self.rows)["matched"]["risk_flags"]
                self.assertEqual(flag in flags, expected, flags)

    def test_a_flagged_theory_or_outbound_draft_gets_full_ceremony(self):
        for prompt in ("customer insists it's a bug in our code", "email the client that the fix ships Friday"):
            with self.subTest(prompt=prompt):
                self.assertEqual(classify.classify(prompt, self.rows)["ceremony"], "full")


class TestTheCatalogIsRoutable(unittest.TestCase):
    """docs/template-catalog.tsv lists each template's trigger words. Each template is
    reachable from the router by the first of them, except where the word is also a verb."""

    CATALOG = SKILL.parent.parent / "docs" / "template-catalog.tsv"
    VERB_FIRST = {"themes-report"}      # "themes" is the wf-08 verb, and the verb wins

    def test_every_template_is_reachable_by_its_first_trigger(self):
        if not self.CATALOG.is_file():
            self.skipTest("no template catalog in this checkout")
        rows = classify.load_table(SKILL / "assets" / "router-table.tsv")
        lines = self.CATALOG.read_text(encoding="utf-8").splitlines()[1:]
        self.assertTrue(lines)
        for line in lines:
            cells = line.split("\t")
            template, triggers = cells[0], cells[5]
            if template in self.VERB_FIRST:
                continue
            first = triggers.split(",")[0].strip()
            with self.subTest(template=template, trigger=first):
                r = classify.classify(f"help me with the {first}", rows)
                self.assertEqual(r["template"], template, r["matched"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
