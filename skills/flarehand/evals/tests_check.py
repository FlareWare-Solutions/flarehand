"""tests_check.py - check.py, the one command for step 8, and the template's author-only sections.

Loaded by evals/test_scripts.py, and runnable on its own:
    python3 -m unittest evals.tests_check -v
"""

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

import check_output  # noqa: E402
import evidence  # noqa: E402

ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def run(script: str, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SKILL / "scripts" / script), *args], input=stdin,
                          capture_output=True, text=True, timeout=60, env=ENV)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fh-check-"))
        self.root = self.tmp / "kb"          # never created: check.py works without a knowledge base

    def tearDown(self):
        shutil.rmtree(evidence.staging_dir(self.root.resolve()), ignore_errors=True)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def check(self, text, *extra):
        return run("check.py", "-", "--root", str(self.root), *extra, stdin=text)

    def check_json(self, text, *extra):
        r = self.check(text, "--json", *extra)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        return json.loads(r.stdout)

    def ground(self, *args):
        r = run("ground.py", "--root", str(self.root), *args)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r


class TestCheck(Base):
    def test_a_clean_draft_passes_with_no_knowledge_base_and_no_ledger(self):
        r = self.check("Plain advice with nothing specific in it.\n")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(r.stdout.startswith("PASS"))
        self.assertLessEqual(len(r.stdout.splitlines()), 3)
        self.assertFalse(self.root.exists())

    def test_without_a_ledger_lint_lists_unlabelled_specifics(self):
        got = self.check_json("The limit is 100 per minute.\n\nIt ships in 3.12.1.\n")
        self.assertFalse(got["pass"])
        self.assertEqual([f["check"] for f in got["fixes"]], ["lint", "lint"])
        self.assertNotIn("claims", got["checked"])

    def test_the_fix_list_is_numbered_and_names_the_line(self):
        r = self.check("Fine sentence.\n\nThe limit is 100 per minute — roughly.\n")
        self.assertEqual(r.returncode, 1)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], "FIX:")
        self.assertTrue(lines[1].startswith("1. line 3: "), lines)
        self.assertTrue(any("em dash" in l for l in lines))
        self.assertTrue(lines[-1].startswith("Checked:") or lines[-1].startswith("Worth a look"))

    def test_an_unseen_url_is_a_fix_and_seen_url_clears_it(self):
        text = "Read the page [your input] at https://example.com/a?utm_source=x [your input].\n"
        got = self.check_json(text)
        self.assertEqual([f["check"] for f in got["fixes"]], ["urls"])
        self.assertTrue(self.check_json(text, "--seen-url", "https://example.com/a")["pass"])

    def test_a_ledger_claim_must_be_earned(self):
        self.ground("source", "add", "--kind", "user", "--locator", "the person", "--text", "The limit is 100 per minute.")
        self.ground("claim", "add", "The limit is 100 per minute.", "--type", "number", "--source", "S1",
                    "--quote", "The limit is 100 per minute.")
        draft = "The limit is 100 per minute [verified: S1].\n\n## Sources\n\n- S1. The person, T0.\n"
        got = self.check_json(draft)
        self.assertEqual(sorted({f["check"] for f in got["fixes"]}), ["lint", "verify"])
        self.assertIn("checker-brief C1", " ".join(f["message"] for f in got["fixes"]))
        self.ground("verdict", "C1", "SUPPORTED", "--by", "checker-1")
        got = self.check_json(draft)
        self.assertTrue(got["pass"], got["fixes"])
        self.assertEqual(got["checked"]["claims"], 1)

    def test_outbound_reports_and_changes_nothing(self):
        text = "Send the export to jane.doe@acme-corp.com. password=hunter2hunter2 [your input]\n"
        quiet = self.check_json(text)
        self.assertNotIn("outbound", [f["check"] for f in quiet["fixes"]])
        loud = self.check_json(text, "--outbound")
        out = [f for f in loud["fixes"] if f["check"] == "outbound"]
        self.assertGreaterEqual(len(out), 2)
        self.assertTrue(any("password" in f["message"].lower() or "key" in f["message"].lower() for f in out))
        self.assertEqual(loud["checked"]["outbound"], len(out) + sum(
            1 for n in loud["notes"] if "outbound-low" in n))

    def test_contract_and_template_are_checked_when_given(self):
        got = self.check_json("Nothing here.\n", "--contract", "wf-09")
        self.assertTrue(any(f["check"] == "contract-section" for f in got["fixes"]))
        tpl = self.tmp / "t.md"
        tpl.write_text("---\ntemplate: t\n---\n# T\n\n## Ask\n\n## Detail\n", encoding="utf-8")
        got = self.check_json("# x\n\n## Ask\n\nok\n", "--template", str(tpl))
        self.assertEqual([f["message"] for f in got["fixes"]], ['required section missing: "Detail" (a markdown heading)'])

    def test_profile_none_keeps_only_fact_rules(self):
        text = "We should utilize it — now.\n"
        self.assertFalse(self.check_json(text)["pass"])
        self.assertTrue(self.check_json(text, "--profile", "none")["pass"])

    def test_usage_errors(self):
        self.assertEqual(run("check.py", str(self.tmp / "missing.md")).returncode, 2)
        self.assertEqual(self.check("x\n", "--template", str(self.tmp / "nope.md")).returncode, 2)
        self.assertEqual(run("check.py", "--help").returncode, 0)


class TestAuthorOnlySections(unittest.TestCase):
    """A template's author-only sections, such as a draft's status or reviewer notes, are left
    out of the published artifact, so the template check does not require them."""

    def contract(self, template_text: str) -> list[str]:
        d = Path(tempfile.mkdtemp(prefix="fh-author-"))
        try:
            (d / "t.md").write_text(template_text, encoding="utf-8")
            _, spec = check_output.template_contract(d / "t.md", {})
            return spec["sections"]
        finally:
            shutil.rmtree(d, ignore_errors=True)

    BODY = "# T\n\n## Draft status\n\n## Content\n\n## Next steps\n\n## Accuracy and upkeep\n"

    def test_every_section_is_required_by_default(self):
        self.assertEqual(self.contract("---\nworkflow: wf-05\n---\n" + self.BODY),
                         ["Draft status", "Content", "Next steps", "Accuracy and upkeep"])

    def test_frontmatter_lists_author_only_sections_inline_or_as_a_block(self):
        inline = "---\nworkflow: wf-05\nauthor_only: [Draft status, \"Accuracy and upkeep\"]\n---\n" + self.BODY
        block = "---\nworkflow: wf-05\nauthor_only:\n  - Draft status\n  - Accuracy and upkeep\n---\n" + self.BODY
        for text in (inline, block):
            with self.subTest(form=text.splitlines()[2]):
                self.assertEqual(self.contract(text), ["Content", "Next steps"])

    def test_a_marker_after_the_heading(self):
        body = "# T\n\n## Draft status\n<!-- author-only -->\n\n## Content\n"
        self.assertEqual(self.contract("---\nworkflow: wf-05\n---\n" + body), ["Content"])

    def test_everything_after_reviewer_notes(self):
        body = "# T\n\n## Content\n\n## Next steps\n\n<!-- reviewer-notes -->\n\n## Draft status\n\n## Accuracy and upkeep\n"
        self.assertEqual(self.contract("---\nworkflow: wf-05\n---\n" + body), ["Content", "Next steps"])

    def test_an_artifact_without_the_author_sections_passes(self):
        d = Path(tempfile.mkdtemp(prefix="fh-author-"))
        try:
            (d / "t.md").write_text("---\ntemplate: t\n---\n# T\n\n## Content\n\n<!-- reviewer-notes -->\n\n"
                                    "## Draft status\n", encoding="utf-8")
            (d / "a.md").write_text("# Article\n\n## Content\n\nText.\n", encoding="utf-8")
            r = run("check_output.py", "--template", str(d / "t.md"), "--json", str(d / "a.md"))
            self.assertEqual(json.loads(r.stdout)["errors"], 0, r.stdout)
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestDoctorFoldsInDetect(unittest.TestCase):
    def test_capabilities_include_what_kb_detect_reads(self):
        r = run("doctor.py", "--capabilities", "--json")
        out = json.loads(r.stdout)
        for key in ("timezone", "locale", "date_format", "os"):
            self.assertIn(key, out["detected"])
        self.assertIn("You ", run("doctor.py", "--capabilities").stdout)
        self.assertEqual(run("kb.py", "detect").returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
