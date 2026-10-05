#!/usr/bin/env python3
"""tests_style.py - the style checker's newer rules, the google profile, and checking a reply
from standard input. Loaded by tests/test_scripts.py.

A 2026-09 review found three of the nine voice rules invisible to the checker, a word list
that could never match a term ending in a period, and no way to check a chat reply at all.
These tests pin the fixes, and the google profile added in the same change.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "flarehand"
sys.path.insert(0, str(SKILL / "scripts"))

import check_output  # noqa: E402


def check(text: str, *args: str, stdin: bool = False) -> dict:
    """Run the real script, the way the pipeline does, and return its JSON."""
    if stdin:
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "check_output.py"), "--style", "--json",
                            "--max", "500", *args, "-"], input=text, capture_output=True, text=True, timeout=60)
    else:
        f = Path(tempfile.mktemp(suffix=".md"))
        f.write_text(text, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(SKILL / "scripts" / "check_output.py"), "--style", "--json",
                                "--max", "500", *args, str(f)], capture_output=True, text=True, timeout=60)
        finally:
            f.unlink(missing_ok=True)
    return json.loads(r.stdout)


def rules(result: dict) -> set:
    return {f["rule"] for f in result["findings"]}


class TestTheCheckerSeesEveryRule(unittest.TestCase):
    def test_a_filler_opener_is_an_error(self):
        for text in ("Great question! The batch is locked.\n", "I hope this helps.\n",
                     "Certainly, here is the plan.\n", "Happy to help with that.\n"):
            with self.subTest(text=text):
                r = check(text)
                self.assertIn("filler", rules(r))
                self.assertGreater(r["errors"], 0)

    def test_a_real_first_sentence_is_not_filler(self):
        for text in ("The batch is locked by user JSMITH.\n", "Certainly not before month end.\n",
                     "Of course-level detail belongs in the appendix.\n"):
            with self.subTest(text=text):
                self.assertNotIn("filler", rules(check(text)))

    def test_a_wall_of_text_is_warned(self):
        text = " ".join(f"Sentence number {i} says one small thing." for i in range(9)) + "\n"
        self.assertIn("long-paragraph", rules(check(text)))

    def test_a_list_is_not_a_wall(self):
        text = "\n".join(f"- Item {i} says one small thing." for i in range(12)) + "\n"
        self.assertNotIn("long-paragraph", rules(check(text)))


class TestDefaultRulesFromTheGoogleReview(unittest.TestCase):
    def test_a_numeric_date_is_an_error(self):
        r = check("The cutover runs on 04/05/26 at noon.\n")
        self.assertIn("date", rules(r))
        self.assertGreater(r["errors"], 0)

    def test_a_written_or_iso_date_passes(self):
        for text in ("The cutover runs on April 5, 2026.\n", "The cutover runs on 2026-04-05.\n",
                     "Use 3/4 of the budget.\n", "See version 12/3.\n"):
            with self.subTest(text=text):
                self.assertNotIn("date", rules(check(text)))

    def test_optional_plurals_and_double_negatives_are_warned(self):
        self.assertIn("optional-plural", rules(check("Attach the file(s) to the case.\n")))
        self.assertIn("double-negative", rules(check("It is not uncommon for the batch to lock.\n")))

    def test_a_term_ending_in_a_period_now_matches(self):
        words = check_output.load_style_words(SKILL / "assets" / "style-words.tsv")
        hits = {term for pat, term, _, _ in words for text in ("Use a tool, e.g. grep.", "GL, AP, etc. are in.")
                if pat.search(text)}
        self.assertIn("e.g", hits)
        self.assertIn("etc", hits)

    def test_a_screen_label_with_a_listed_word_is_not_an_error(self):
        r = check("Open the Terminate Employees screen.\n")
        self.assertEqual(r["errors"], 0, r["findings"])

    def test_inclusive_language_terms_warn_and_never_fail(self):
        text = "Add the address to the whitelist. Remove it from the blacklist.\n"
        hits = [f for f in check(text)["findings"] if f["rule"] == "word"]
        self.assertTrue(hits)
        self.assertTrue(all(h["severity"] == "warn" for h in hits), hits)

    def test_no_company_or_product_rows_are_shipped(self):
        """The shipped lists are generic. A team adds its own names in its house rules."""
        for name in ("style-words.tsv", "style-words-google.tsv"):
            rows = [ln for ln in (SKILL / "assets" / name).read_text(encoding="utf-8").splitlines()
                    if not ln.startswith("#")]
            text = "\n".join(rows).lower()
            for word in ("screen name",):
                with self.subTest(file=name, word=word):
                    self.assertNotIn(word, text)

    def test_the_google_list_carries_its_attribution(self):
        head = (SKILL / "assets" / "style-words-google.tsv").read_text(encoding="utf-8")[:600]
        self.assertIn("CC BY 4.0", head)
        self.assertIn("developers.google.com/style", head)


class TestGoogleProfile(unittest.TestCase):
    DOC = ("## How To Post A Batch.\n\nThe screen will display the total, as shown below. "
           "The lock clears - then the batch posts. You should just click on **Post**!\n")

    def test_the_profile_adds_document_rules(self):
        natural, google = rules(check(self.DOC)), rules(check(self.DOC, "--profile", "google"))
        for rule in ("heading-case", "heading-period", "future-tense", "directional", "spaced-hyphen", "exclamation"):
            with self.subTest(rule=rule):
                self.assertNotIn(rule, natural)
                self.assertIn(rule, google)

    def test_the_profile_word_list_loads_only_with_the_profile(self):
        natural = [f for f in check(self.DOC)["findings"] if f["rule"] == "word"]
        google = [f for f in check(self.DOC, "--profile", "google")["findings"] if f["rule"] == "word"]
        self.assertGreater(len(google), len(natural))
        self.assertTrue(any('"should"' in f["message"] for f in google))

    def test_the_profile_never_removes_a_house_rule(self):
        text = "The batch failed — on 04/05/26.\n"
        for args in ((), ("--profile", "google")):
            with self.subTest(args=args):
                self.assertTrue({"em-dash", "date"} <= rules(check(text, *args)))

    def test_a_sentence_case_heading_passes(self):
        for heading in ("## Post a batch", "## Set up Jira in Claude Code", "## AP and GL: what ties out"):
            with self.subTest(heading=heading):
                self.assertNotIn("heading-case", rules(check(heading + "\n", "--profile", "google")))

    def test_case_sensitive_names(self):
        hits = [f["message"] for f in check("Push it to Github and port it to Typescript.\n",
                                            "--profile", "google")["findings"]]
        self.assertTrue(any("GitHub" in h for h in hits), hits)
        self.assertTrue(any("TypeScript" in h for h in hits), hits)
        clean = [f for f in check("Push it to GitHub and port it to TypeScript.\n", "--profile", "google")["findings"]
                 if f["rule"] == "word"]
        self.assertEqual(clean, [])

    def test_every_profile_term_is_warn_only(self):
        for _pat, term, _repl, sev in check_output.load_style_words(SKILL / "assets" / "style-words-google.tsv"):
            with self.subTest(term=term):
                self.assertIn(sev, ("warn", "error"))
        errors = [t for _, t, _, s in check_output.load_style_words(SKILL / "assets" / "style-words-google.tsv")
                  if s == "error"]
        self.assertLessEqual(len(errors), 1, errors)  # only "slave" is an error


class TestAReplyCanBeChecked(unittest.TestCase):
    def test_standard_input(self):
        r = check("Sure thing! Here is the fix — run it.\n", stdin=True)
        self.assertTrue({"filler", "em-dash"} <= rules(r))
        self.assertTrue(all(f["file"] == "<stdin>" for f in r["findings"]))

    def test_a_clean_reply_exits_zero(self):
        p = subprocess.run([sys.executable, str(SKILL / "scripts" / "check_output.py"), "--style", "-"],
                           input="The batch is locked. Clear the lock in the batch screen, then post it again.\n",
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stdout)


class TestTheProfilesAreDocumented(unittest.TestCase):
    """plain is the default, google and none are choices, and the em-dash gate is opt-in."""

    VOICE = (SKILL / "references" / "voice.md").read_text(encoding="utf-8")
    GOOGLE = (SKILL / "references" / "voice-google.md").read_text(encoding="utf-8")

    def test_plain_is_the_default_and_every_profile_is_named(self):
        self.assertIn("**It is the default.**", self.VOICE)
        for name in ("`plain`", "`google`", "`none`"):
            with self.subTest(profile=name):
                self.assertIn(name, self.VOICE)

    def test_the_plain_rules_keep_no_em_dashes(self):
        self.assertIn("3. **No em dashes.**", self.VOICE)

    def test_the_em_dash_gate_is_opt_in(self):
        self.assertIn("opt-in", self.VOICE)
        self.assertIn("kb.py config --voice-gate on", self.VOICE)

    def test_the_google_profile_is_attributed(self):
        self.assertIn("CC BY 4.0", self.GOOGLE)
        self.assertIn("https://developers.google.com/style", self.GOOGLE)
        self.assertIn("opt-in", self.GOOGLE)


class TestVoiceHooks(unittest.TestCase):
    """The reminder runs by default once the skill ran. The blocking gate runs only when turned on."""

    @classmethod
    def setUpClass(cls):
        import os
        cls.tmp = Path(tempfile.mkdtemp(prefix="hww-gate-"))
        (cls.tmp / "with.jsonl").write_text(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": "flarehand:flarehand"}}]}}) + "\n")
        (cls.tmp / "without.jsonl").write_text(json.dumps({"type": "assistant", "message": {
            "role": "assistant", "content": [{"type": "text", "text": "hi"}]}}) + "\n")
        cls.home_off = cls.tmp / "home-off"
        cls.home_on = cls.tmp / "home-on"
        for home, gate in ((cls.home_off, None), (cls.home_on, True)):
            env = dict(os.environ, HOME=str(home))
            subprocess.run([sys.executable, str(SKILL / "scripts" / "kb.py"), "init"], env=env, capture_output=True,
                           text=True, timeout=180)
            if gate:
                subprocess.run([sys.executable, str(SKILL / "scripts" / "kb.py"), "config", "--voice-gate", "on"],
                               env=env, capture_output=True, text=True, timeout=180)

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def hook(self, payload: dict, *args: str, home=None) -> str:
        import os
        env = dict(os.environ, HOME=str(home or self.home_off))
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "voice_gate.py"), *args], input=json.dumps(payload),
                           capture_output=True, text=True, timeout=180, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def test_the_reminder_waits_until_the_skill_ran(self):
        self.assertIn("no em dashes", self.hook({"transcript_path": str(self.tmp / "with.jsonl")}, "--remind"))
        self.assertEqual(self.hook({"transcript_path": str(self.tmp / "without.jsonl")}, "--remind"), "")

    def test_the_blocking_gate_is_off_by_default(self):
        payload = {"transcript_path": str(self.tmp / "with.jsonl"), "last_assistant_message": "It failed \u2014 again."}
        self.assertEqual(self.hook(payload), "")

    def test_the_gate_blocks_once_when_turned_on(self):
        payload = {"transcript_path": str(self.tmp / "with.jsonl"), "last_assistant_message": "It failed \u2014 again."}
        self.assertEqual(json.loads(self.hook(payload, home=self.home_on))["decision"], "block")
        self.assertEqual(self.hook(dict(payload, stop_hook_active=True), home=self.home_on), "")

    def test_the_gate_ignores_code_and_other_sessions(self):
        code = {"transcript_path": str(self.tmp / "with.jsonl"), "last_assistant_message": "Run `a \u2014 b` now."}
        other = {"transcript_path": str(self.tmp / "without.jsonl"), "last_assistant_message": "It failed \u2014 again."}
        self.assertEqual(self.hook(code, home=self.home_on), "")
        self.assertEqual(self.hook(other, home=self.home_on), "")

    def test_garbage_input_does_nothing(self):
        import os
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "voice_gate.py")], input="not json",
                           capture_output=True, text=True, timeout=180, env=dict(os.environ, HOME=str(self.home_on)))
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_the_plugin_hooks_match_the_shipped_copy(self):
        plugin_hooks = ROOT / "hooks" / "hooks.json"
        shipped = SKILL / "assets" / "plugin-hooks.json"
        if plugin_hooks.is_file() and shipped.is_file():
            self.assertEqual(json.loads(plugin_hooks.read_text()), json.loads(shipped.read_text()))


class TestTheMissingHeadingFitsTheProfile(unittest.TestCase):
    """The google profile writes headings in sentence case, so the contract accepts that form of MISSING."""

    def contract(self, text: str) -> int:
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "check_output.py"), "--contract", "wf-05", "--json", "-"],
                           input=text, capture_output=True, text=True, timeout=60)
        return json.loads(r.stdout)["errors"]

    def test_either_form_satisfies_the_contract(self):
        for heading in ("## MISSING - you must supply", "## Missing: you must supply", "## Missing, you must supply"):
            with self.subTest(heading=heading):
                self.assertEqual(self.contract(f"## Draft\nx\n\n{heading}\n- y\n"), 0)

    def test_another_heading_does_not(self):
        self.assertGreater(self.contract("## Draft\nx\n\n## Missing bits\n- y\n"), 0)



if __name__ == "__main__":
    unittest.main(verbosity=2)
