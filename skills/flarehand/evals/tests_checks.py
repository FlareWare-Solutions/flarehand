#!/usr/bin/env python3
"""tests_checks.py - team F: contract and template checks in check_output.py, and the
template facts those checks protect. Loaded by evals/test_scripts.py."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import check_output  # noqa: E402
import kb  # noqa: E402

TEMPLATES = SKILL / "assets" / "templates"
CONTRACTS = check_output.load_contracts(SKILL / "assets" / "contracts.tsv")


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SKILL / "scripts" / "check_output.py"), *args],
                          capture_output=True, text=True, timeout=60)


def tmpfile(text: str) -> Path:
    f = Path(tempfile.mktemp(suffix=".md"))
    f.write_text(text, encoding="utf-8")
    return f


class TestContractSectionsAreHeadings(unittest.TestCase):
    """The checker's mechanics, against a fixed contract, so a change to the shipped table
    does not read as a change to how sections are matched."""

    FIXED = {"wf-03": {"sections": ["Summary", "Reproduction", "Evidence", "MISSING - you must supply"],
                       "markers": ["[verified:"]}}

    def messages(self, text: str, wf: str) -> list[str]:
        return [f["message"] for f in check_output.check_contract(text, wf, self.FIXED)]

    def test_words_in_prose_do_not_satisfy_a_section(self):
        text = ("The summary of this reproduction has evidence. MISSING - you must supply nothing. "
                "[verified: TOOL-1]\n")
        msgs = self.messages(text, "wf-03")
        self.assertEqual(len([m for m in msgs if "required section missing" in m]), 4, msgs)

    def test_headings_of_any_level_satisfy_a_section(self):
        text = ("# Packet\n\n## Summary\n\nx\n\n### Reproduction\n\n1.\n\n#### Evidence\n\n"
                "[verified: TOOL-1]\n\n## MISSING - you must supply\n\n-\n")
        self.assertEqual(self.messages(text, "wf-03"), [])

    def test_a_leading_number_on_a_heading_is_ignored(self):
        text = ("## 1. Summary\n\n## 2. Reproduction\n\n## 3. Evidence\n\n[verified: TOOL-1]\n\n"
                "## 4. MISSING - you must supply\n")
        self.assertEqual(self.messages(text, "wf-03"), [])

    def test_a_heading_that_starts_with_the_section_name_counts(self):
        text = ("## Summary\n\n## Reproduction\n\n## 6. Evidence and findings\n\n[verified: TOOL-1]\n\n"
                "## MISSING - you must supply\n")
        self.assertEqual(self.messages(text, "wf-03"), [])
        self.assertIn('required section missing: "Evidence" (a markdown heading)',
                      self.messages(text.replace("Evidence and findings", "Evidenced"), "wf-03"))

    def test_markers_still_match_anywhere(self):
        text = "## Summary\n\n## Reproduction\n\n## Evidence\n\n## MISSING - you must supply\n\nsee [verified: TOOL-1]\n"
        self.assertEqual(self.messages(text, "wf-03"), [])


class TestTemplateCheck(unittest.TestCase):
    def check(self, template: Path, text: str) -> dict:
        f = tmpfile(text)
        try:
            return json.loads(run("--template", str(template), "--json", str(f)).stdout)
        finally:
            f.unlink()

    def test_numbered_template_headings_match_unnumbered_artifact_headings(self):
        tpl = tmpfile("---\nworkflow: wf-03\nsource_status: sourced\n---\n# T\n\n## 0. Client\n\n## 1. Request\n\n"
                      "## Evidence\n\n## MISSING - you must supply\n")
        try:
            got = self.check(tpl, "# a\n\n## Client\n\nx\n\n## Request\n\ny\n\n## Evidence\n\n[verified: TOOL-1]\n\n"
                                  "## MISSING - you must supply\n\n-\n")
            self.assertEqual(got["errors"], 0, got)
        finally:
            tpl.unlink()

    def test_optional_sections_are_not_required(self):
        tpl = tmpfile("---\nworkflow: wf-04\nsource_status: general-practice\n---\n# T\n\n## The ask\n\n## What happened\n\n"
                      "## Detail\n\n## Team snapshot\n<!-- optional -->\n\n| a |\n\n## Route to HR\n\n<!-- optional -->\n\n- No\n")
        try:
            got = self.check(tpl, "# n\n\n## The ask\n\nx\n\n## What happened\n\ny\n\n## Detail\n\n- [fact] z [your input]\n")
            self.assertEqual(got["errors"], 0, got)
        finally:
            tpl.unlink()

    def test_general_practice_accepts_your_input_for_verified(self):
        tpl = tmpfile("---\nworkflow: wf-04\nsource_status: general-practice\n---\n# T\n\n## The ask\n\n## What happened\n\n## Detail\n")
        try:
            body = "# n\n\n## The ask\n\nx\n\n## What happened\n\ny\n\n## Detail\n\n- z\n"
            self.assertEqual(self.check(tpl, body + "\n[your input]\n")["errors"], 0)
            self.assertEqual(self.check(tpl, body)["errors"], 1)
        finally:
            tpl.unlink()

    def test_a_sourced_template_still_needs_a_citation(self):
        tpl = tmpfile("---\nworkflow: wf-04\nsource_status: sourced\n---\n# T\n\n## The ask\n\n## What happened\n\n## Detail\n")
        try:
            got = self.check(tpl, "# n\n\n## The ask\n\nx\n\n## What happened\n\ny\n\n## Detail\n\n- z [your input]\n")
            self.assertEqual(got["errors"], 1, got)
        finally:
            tpl.unlink()

    def test_a_minimal_one_to_one_note_passes_the_team_notes_template(self):
        note = ("# Team notes: 1:1 with A, 2026-09-14\n\n## The ask\n\nNo actions.\n\n## What happened\n\n"
                "Working on the AP export.\n\n## Commitments\n\n| # | Who | What | Due | Status |\n|---|---|---|---|---|\n\n"
                "## Detail\n\n- [fact] Shipped the AP export (source: Jira, on: 2026-09-10, status: confirmed) [your input]\n\n"
                "## MISSING - you must supply\n\n-\n")
        got = self.check(TEMPLATES / "one-on-one-notes.md", note)
        self.assertEqual(got["errors"], 0, got)

    def test_a_qbr_without_a_success_plan_passes_the_qbr_template(self):
        qbr = ("# QBR: X, Q3\n\n## Meeting\n\n- Type: QBR\n\n## The ask\n\nx\n\n## What happened\n\ny\n\n## Detail\n\n"
               "- Adoption: [your input]\n\n## Still open\n\n| a |\n")
        self.assertEqual(self.check(TEMPLATES / "business-review.md", qbr)["errors"], 0)

    def test_a_build_failure_passes_ci_triage_without_the_bucket_section(self):
        text = ("# CI triage: nightly, compile\n\n## Failure\n\n| a |\n\n## Reported cause (unverified)\n\nx\n\n"
                "## What the evidence shows\n\n- y\n\n## Hypotheses\n\nConfirming: a\nDisconfirming: b\n\n"
                "## What is missing\n\nz\n\n## Decision\n\n- Action: fix\n")
        self.assertEqual(self.check(TEMPLATES / "ci-triage.md", text)["errors"], 0)

    def test_a_single_clause_question_passes_contract_review(self):
        text = ("# Contract review: SLA credits\n\n## A single clause question\n\n- The question: x\n\n"
                "## Clause text, word for word\n\n> a\n\n## Differences that matter\n\nnone\n\n## Noise\n\nnone\n\n"
                "## What explains your symptom\n\nsee questions\n\n## Not stated here, on purpose\n\n- none\n\n"
                "## Could not compare\n\nnone\n\n## Questions for the lawyer\n\n1. Clause 4 [your input]\n")
        self.assertEqual(self.check(TEMPLATES / "contract-review.md", text)["errors"], 0)

    def test_every_shipped_template_passes_its_own_template_check(self):
        for path in sorted(TEMPLATES.glob("*.md")):
            with self.subTest(template=path.name):
                text = path.read_text(encoding="utf-8")
                _, spec = check_output.template_contract(path, CONTRACTS)
                masked = "\n".join(check_output.mask(text))
                self.assertEqual(check_output.check_contract(masked, "t", {"t": spec}), [])


class TestContractReadsRealContent(unittest.TestCase):
    """A contract is the structural guarantee, so it has to read the same masked text
    every other check reads. An example block is not an artifact."""

    def contract(self, archetype, text):
        f = tmpfile(text)
        try:
            return json.loads(run("--contract", archetype, "--json", str(f)).stdout)
        finally:
            f.unlink(missing_ok=True)

    FENCED = (
        "# Totally empty plan\n\nHere is what a plan looks like:\n\n"
        "```markdown\n## Steps\n1. do it (owner: someone)\n## Riskiest step\n## Rollback\n```\n"
    )
    REAL = (
        "# Plan: move the AP batch\n\n## What done looks like\nIt runs at 5pm.\n\n"
        "## Steps\n1. **Stop it** (owner: Priya)\n   Check it worked: the page says stopped.\n\n"
        "## Riskiest step\nStopping it during month end.\n\n## Rollback\nStart it again.\n\n"
        "## What is missing or assumed\nI assumed the scheduler role is already granted.\n"
    )

    def test_sections_inside_a_code_fence_do_not_count(self):
        out = self.contract("wf-09", self.FENCED)
        missing = {f["message"] for f in out["findings"] if f["rule"] == "contract-section"}
        self.assertEqual(len(missing), 4, out["findings"])

    def test_a_marker_inside_a_comment_does_not_count(self):
        body = self.REAL.replace("(owner: Priya)", "(by Priya)") + "\n<!-- remember the Owner -->\n"
        out = self.contract("wf-09", body)
        self.assertTrue(any(f["rule"] == "contract-marker" for f in out["findings"]), out)

    def test_a_real_artifact_still_passes(self):
        self.assertEqual(self.contract("wf-09", self.REAL)["errors"], 0)


class TestCodeIsCitable(unittest.TestCase):
    """A code review grounds in the file in front of you, so that has to be a source."""

    def cite(self, src, cwd=None, extra=()):
        d = Path(tempfile.mkdtemp(prefix="hww-cite-"))
        try:
            (d / "a.md").write_text(f"A finding [verified: {src}].\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(SKILL / "scripts" / "check_output.py"),
                                "--citations", "--json", "--root", str(d / "no-kb"), *extra, str(d / "a.md")],
                               capture_output=True, text=True, cwd=str(cwd or d))
            return json.loads(r.stdout)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_a_repository_path_with_a_line_range_is_a_source(self):
        for src in ("src/registry.rs:3-8", "scripts/kb.py:42", "lib/main.dart", "README.md",
                    "src/a.py#L10-L20", "src/a.py#L7", "Makefile"):
            with self.subTest(src=src):
                self.assertEqual(self.cite(src)["errors"], 0, src)

    def test_the_generic_shapes_are_sources(self):
        for src in ("https://docs.python.org/3/library/re.html", "git:4f2a9c1:src/registry.rs",
                    "git:HEAD~2:docs/a b.md", "mcp:tracker:ABC-123", "mcp:wiki:Pages/Release process",
                    "ABC-123"):
            with self.subTest(src=src):
                self.assertEqual(self.cite(src)["errors"], 0, src)

    def test_an_absolute_windows_path_is_not_a_source(self):
        self.assertEqual(self.cite("C:/Users/x/file.txt")["errors"], 1)

    def test_a_bare_name_colon_path_is_not_a_source(self):
        for src in ("wiki:docs/x.md#a", "PKG:DA.X#y", "some-index:path/to/page.md"):
            with self.subTest(src=src):
                self.assertEqual(self.cite(src)["errors"], 1, src)

    def test_a_cited_file_that_is_not_there_warns_rather_than_fails(self):
        out = self.cite("src/nothere.rs:3")
        self.assertEqual(out["errors"], 0)
        self.assertEqual([f["rule"] for f in out["findings"]], ["citation-unreadable"])

    def test_a_git_ref_that_does_not_exist_warns_inside_a_repository(self):
        repo = Path(tempfile.mkdtemp(prefix="hww-git-"))
        try:
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (repo / "a.txt").write_text("x\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "a.txt"], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com",
                            "commit", "-qm", "x"], check=True)
            ok = self.cite("git:HEAD:a.txt", extra=("--repo-root", str(repo)))
            self.assertEqual(ok["findings"], [])
            gone = self.cite("git:HEAD:missing.txt", extra=("--repo-root", str(repo)))
            self.assertEqual([f["rule"] for f in gone["findings"]], ["citation-unreadable"])
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_prose_is_still_not_a_source(self):
        for src in ("the API guide", "case 41822", "Jira TOOL-9059"):
            with self.subTest(src=src):
                self.assertEqual(self.cite(src)["errors"], 1, src)

    def test_a_ledger_id_needs_a_ledger(self):
        out = self.cite("S3")
        self.assertEqual([f["rule"] for f in out["findings"]], ["citation-ledger"])

    def test_ledger_ids_are_checked_against_the_ledger(self):
        d = Path(tempfile.mkdtemp(prefix="hww-ledger-"))
        try:
            (d / "sources.jsonl").write_text(json.dumps({"id": "S1"}) + "\n" + json.dumps({"id": "S2"}) + "\n",
                                             encoding="utf-8")
            for src, errors in (("S1", 0), ("S1+S2", 0), ("S1+S9", 1), ("S7", 1)):
                with self.subTest(src=src):
                    self.assertEqual(self.cite(src, extra=("--ledger", str(d)))["errors"], errors, src)
            f = d / "b.md"
            f.write_text("A [weak: S9] and [conflict: S1 vs S2] and [inference from S1, S8].\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(SKILL / "scripts" / "check_output.py"), "--citations", "--json",
                                "--ledger", str(d / "sources.jsonl"), str(f)], capture_output=True, text=True)
            msgs = [x["message"] for x in json.loads(r.stdout)["findings"]]
            self.assertEqual(len(msgs), 2, msgs)
            self.assertTrue(any("S9" in m for m in msgs) and any("S8" in m for m in msgs))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_two_markers_on_one_line_are_judged_separately(self):
        """The placeholder check reads the raw line at the marker's own offset. Falling back
        to the first marker on the line would skip a real source sitting beside a placeholder."""
        out = self.cite("<source>] and a real [verified: the API guide")
        self.assertEqual(out["errors"], 1, out["findings"])

    def test_a_template_placeholder_is_not_a_claim(self):
        self.assertEqual(self.cite("<source>")["errors"], 0)
        self.assertEqual(self.cite("evidence/<hash>.txt")["errors"], 0)
        self.assertEqual(self.cite("S<n>")["errors"], 0)
        self.assertEqual(self.cite("")["errors"], 1)      # a genuinely empty marker


class TestPersonalFilesCannotNarrowAChecK(unittest.TestCase):
    """references/adaptation.md: a personal file may widen what gets searched and may never
    narrow what gets checked. A one-line contracts.tsv used to turn off shipped checks."""

    def kb_with(self, contracts: str):
        d = Path(tempfile.mkdtemp(prefix="hww-own-"))
        subprocess.run([sys.executable, str(SKILL / "scripts" / "kb.py"), "init",
                        "--root", str(d), "--name", "t", "--role", "qa"],
                       capture_output=True, text=True, timeout=60)
        (d / "contracts.tsv").write_text(contracts, encoding="utf-8")
        return d

    def check(self, root, archetype, body):
        f = root / "artifact.md"
        f.write_text(body, encoding="utf-8")
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "check_output.py"),
                            "--root", str(root), "--contract", archetype, "--json", str(f)],
                           capture_output=True, text=True, timeout=60)
        return json.loads(r.stdout)

    def test_a_personal_row_cannot_remove_a_shipped_section(self):
        d = self.kb_with("archetype\tsections\tmarkers\nwf-09\tSteps\t\n")
        try:
            out = self.check(d, "wf-09", "# P\n\n## Steps\n1. do it\n")
            missing = {f["message"] for f in out["findings"]}
            self.assertTrue(any("What is missing" in m for m in missing), missing)
            self.assertTrue(any("Owner" in m for m in missing), missing)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_a_personal_row_can_still_add_one(self):
        d = self.kb_with("archetype\tsections\tmarkers\nwf-09\tSigned off\t\n")
        try:
            out = self.check(d, "wf-09", "# P\n\n## Steps\n1. do it (owner: me)\n")
            self.assertTrue(any("Signed off" in f["message"] for f in out["findings"]))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_a_name_of_their_own_is_theirs_outright(self):
        d = self.kb_with("archetype\tsections\tmarkers\nmy-recon\tTotals\t\n")
        try:
            self.assertEqual(self.check(d, "my-recon", "# R\n\n## Totals\nx\n")["errors"], 0)
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestTemplateFacts(unittest.TestCase):
    def frontmatter(self, name: str) -> dict:
        return kb.parse_frontmatter((TEMPLATES / name).read_text(encoding="utf-8"))[0]

    def test_every_template_has_a_team_sources_key(self):
        for path in sorted(TEMPLATES.glob("*.md")):
            with self.subTest(template=path.name):
                self.assertIn("team_sources", self.frontmatter(path.name))

    def test_no_customer_case_number_anywhere_in_a_template(self):
        for path in sorted(TEMPLATES.glob("*.md")):
            with self.subTest(template=path.name):
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"\bCase\s+\d{5,}")

    def test_every_shipped_template_passes_the_citation_check(self):
        """A template is copied into artifacts, so a source shape it shows must be one the check accepts."""
        paths = sorted(TEMPLATES.rglob("*.md"))
        r = run("--citations", "--json", "--max", "500", *[str(p) for p in paths])
        got = json.loads(r.stdout)
        self.assertEqual(got["errors"], 0, [f"{f['file']}: {f['message']}" for f in got["findings"]][:10])

    def test_generic_templates_carry_every_section_of_their_reference_output_block(self):
        for path in sorted(TEMPLATES.glob("wf-*.md")):
            ref = SKILL / "references" / path.name
            if not ref.is_file():
                continue
            with self.subTest(template=path.name):
                text = ref.read_text(encoding="utf-8")
                m = re.search(r"^## Output\s*\n+```markdown\n(.*?)^```", text, re.S | re.M)
                self.assertIsNotNone(m, "no Output block")
                wanted = [check_output.heading_text(l) for l in m.group(1).splitlines() if l.startswith("## ")]
                have = [check_output.heading_text(l) for l in path.read_text(encoding="utf-8").splitlines()
                        if l.startswith("## ")]
                self.assertEqual(wanted, have)

    def test_people_templates_ask_jurisdiction_and_reviews_leave_the_rating_blank(self):
        for name in ("one-on-one-notes.md", "hr-document.md", "performance-review.md"):
            with self.subTest(template=name):
                learn = " ".join(self.frontmatter(name)["learn"]).lower()
                self.assertIn("province or state", learn)
        self.assertIn("Rating: <left blank", (TEMPLATES / "performance-review.md").read_text(encoding="utf-8"))

    def test_statement_of_work_learn_questions_are_split_by_artifact(self):
        learn = self.frontmatter("statement-of-work.md")["learn"]
        prefixes = {q.split(":")[0] for q in learn}
        self.assertTrue({"Any draft", "Statement of work", "Change order"} <= prefixes, prefixes)


if __name__ == "__main__":
    unittest.main()
