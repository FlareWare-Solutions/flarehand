"""Split from test_scripts.py. Loaded by tests/test_scripts.py, and runnable on its own."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "flarehand"
sys.path.insert(0, str(SKILL / "scripts"))

import review  # noqa: E402


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / script), *args],
        capture_output=True, text=True, timeout=60,
    )


# ---------------------------------------------------------------- normalising


class TestReviewGrading(unittest.TestCase):
    """The same verified findings always give the same grades, in the same order."""

    def grade(self, lines, *extra):
        f = Path(tempfile.mktemp(suffix=".jsonl"))
        f.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
        try:
            return run("review.py", "--root", str(f.parent / "no-kb-here"), "grade", str(f), "--json", *extra)
        finally:
            f.unlink()

    def lens_grades(self, r):
        return {x["lens"]: x["grade"] for x in json.loads(r.stdout)["lenses"]}

    def finding(self, lens, severity, verdict, **kw):
        base = {"lens": lens, "severity": severity, "verdict": verdict, "where": "a.py:1", "finding": f"{lens} {severity}",
                "fix": "do it", "evidence": "line 1 shows it", "to_confirm": "run it"}
        base.update(kw)
        return base

    def test_the_grading_rule(self):
        r = self.grade([
            {"lens": "correctness", "checked": True},
            self.finding("regressions", "blocking", "confirmed"),
            self.finding("completeness", "blocking", "plausible"),
            self.finding("quality", "should-fix", "confirmed"),
            self.finding("references", "should-fix", "plausible"),
            self.finding("freshness", "blocking", "rejected"),
            {"lens": "perspectives", "checked": False, "reason": "no second reader"},
        ])
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.lens_grades(r), {
            "correctness": "pass", "regressions": "fail", "completeness": "concerns", "quality": "concerns",
            "references": "pass", "freshness": "pass", "perspectives": "not checked"})
        self.assertEqual(json.loads(r.stdout)["overall"], "fail")

    def test_a_lens_nobody_recorded_is_never_a_pass(self):
        r = self.grade([{"lens": "correctness", "checked": True}], "--only", "correctness,regressions")
        self.assertEqual(r.returncode, 0)
        out = json.loads(r.stdout)
        self.assertEqual(self.lens_grades(r), {"correctness": "pass", "regressions": "not checked"})
        self.assertEqual(out["not_checked"], ["regressions"])

    def test_outside_the_change_is_listed_not_graded(self):
        r = self.grade([{"lens": "quality", "checked": True},
                        self.finding("quality", "blocking", "confirmed", outside_change=True)], "--only", "quality")
        self.assertEqual(self.lens_grades(r), {"quality": "pass"})

    def test_same_findings_in_any_order_give_the_same_report(self):
        lines = [self.finding("quality", "minor", "confirmed", where="b.py:9"),
                 self.finding("regressions", "blocking", "confirmed", where="a.py:20"),
                 self.finding("regressions", "blocking", "confirmed", where="a.py:3"),
                 {"lens": "quality", "checked": True}, {"lens": "regressions", "checked": True}]
        a = self.grade(lines, "--only", "regressions,quality").stdout
        b = self.grade(list(reversed(lines)), "--only", "regressions,quality").stdout
        self.assertEqual(a, b)
        order = [f["where"] for f in json.loads(a)["findings"]]
        self.assertEqual(order, ["a.py:3", "a.py:20", "b.py:9"])

    def test_bad_findings_are_refused_not_graded(self):
        cases = [
            {"lens": "nope", "checked": True},
            self.finding("quality", "blocking", "confirmed", evidence=""),
            self.finding("quality", "blocking", "plausible", to_confirm=""),
            self.finding("quality", "urgent", "confirmed"),
            self.finding("quality", "minor", "confirmed", fix=""),
        ]
        for bad in cases:
            with self.subTest(bad=bad):
                self.assertEqual(self.grade([bad]).returncode, 2)

    def test_every_lens_has_a_brief_and_the_verifier_has_its_own(self):
        lenses = json.loads(run("review.py", "lenses", "--json").stdout)
        self.assertEqual([l["lens"] for l in lenses], ["correctness", "regressions", "completeness", "quality",
                                                         "references", "freshness", "perspectives"])
        for lens in lenses:
            with self.subTest(lens=lens["lens"]):
                brief = run("review.py", "brief", lens["lens"]).stdout
                self.assertIn(f'"lens": "{lens["lens"]}", "checked": true', brief)
                self.assertIn("plausible", brief)
        verify = run("review.py", "brief", "--verify").stdout
        self.assertIn("You did not write them", verify)
        self.assertIn("Do not add new findings", verify)

    def test_a_personal_lens_list_adds_to_the_shipped_one(self):
        tmp = Path(tempfile.mkdtemp(prefix="hww-lens-"))
        try:
            root = tmp / "memory"
            run("kb.py", "init", "--root", str(root))
            (root / "templates" / "review-lenses.tsv").write_text(
                "lens\tname\tquestion\tlook_for\tstandard\nsecurity\tSecurity\tCan it be abused?\tInput.\tOWASP\n",
                encoding="utf-8")
            got = json.loads(run("review.py", "--root", str(root), "lenses", "--json").stdout)
            keys = [l["lens"] for l in got]
            self.assertEqual(keys[-1], "security")
            self.assertIn("correctness", keys, "a personal list must never hide a shipped lens")
            (root / "templates" / "review-lenses.tsv").write_text(
                "lens\tname\tquestion\tlook_for\tstandard\ncorrectness\tMine\tq\tl\ts\n", encoding="utf-8")
            r = run("review.py", "--root", str(root), "lenses", "--json")
            self.assertIn("is a shipped lens", r.stderr)
            self.assertNotIn("Mine", r.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestReviewHouseRulesAndStandards(unittest.TestCase):
    """Reviews judge against the team's house rules and public standards, never a vendor's."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fh-review-"))
        self.root = self.tmp / "kb"
        self.root.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_house_rules_parse_by_area(self):
        text = ("# House rules\n\n## Pull requests\n\n- One ticket per PR.\n- Title says what changed.\n\n"
                "Some prose that is not a rule.\n\n## Writing\n\n* No em dashes.\n\n```\n- not a rule\n```\n")
        got = review.parse_house_rules(text)
        self.assertEqual(got, [{"area": "Pull requests", "rule": "One ticket per PR."},
                               {"area": "Pull requests", "rule": "Title says what changed."},
                               {"area": "Writing", "rule": "No em dashes."}])

    def test_rules_from_the_knowledge_base_reach_every_lens_brief(self):
        (self.root / "house-rules.md").write_text("## Pull requests\n\n- One ticket per PR.\n", encoding="utf-8")
        rules = json.loads(run("review.py", "--root", str(self.root), "rules", "--json").stdout)["rules"]
        self.assertEqual([(r["area"], r["rule"], r["layer"]) for r in rules],
                         [("Pull requests", "One ticket per PR.", "yours")])
        for lens in ("correctness", "quality", "perspectives"):
            with self.subTest(lens=lens):
                out = run("review.py", "--root", str(self.root), "brief", lens).stdout
                self.assertIn("One ticket per PR. [yours]", out)
        got = json.loads(run("review.py", "--root", str(self.root), "brief", "quality", "--json").stdout)
        self.assertEqual(got["lens"], "quality")
        self.assertEqual(got["house_rules"][0]["rule"], "One ticket per PR.")

    def test_rules_add_up_and_repeats_are_kept_once(self):
        a, b = self.tmp / "a.md", self.tmp / "b.md"
        a.write_text("## PRs\n- One ticket per PR.\n", encoding="utf-8")
        b.write_text("## PRs\n- one ticket per pr.\n- Squash before merge.\n", encoding="utf-8")
        orig = review.house_rule_files
        review.house_rule_files = lambda root=None, cwd=None: [("yours", a), ("team:web", b)]
        try:
            got = [(r["rule"], r["layer"]) for r in review.house_rules()]
        finally:
            review.house_rule_files = orig
        self.assertEqual(got, [("One ticket per PR.", "yours"), ("Squash before merge.", "team:web")])

    def test_without_layers_the_knowledge_base_is_still_read(self):
        (self.root / "house-rules.md").write_text("## Security\n- No secrets in logs.\n", encoding="utf-8")
        saved = sys.modules.get("layers")
        sys.modules["layers"] = None  # makes `import layers` fail, as before area B ships it
        try:
            got = review.house_rule_files(self.root, self.tmp)
        finally:
            if saved is None:
                sys.modules.pop("layers", None)
            else:
                sys.modules["layers"] = saved
        self.assertEqual(got, [("yours", self.root / "house-rules.md")])

    def test_no_rules_says_so(self):
        out = run("review.py", "--root", str(self.root), "brief", "quality").stdout
        self.assertIn("House rules: none saved", out)
        self.assertIn("No house rules saved", run("review.py", "--root", str(self.root), "rules").stdout)

    def test_repo_configs_are_found_at_the_git_root(self):
        repo = self.tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        (repo / "src").mkdir()
        (repo / ".editorconfig").write_text("root = true\n", encoding="utf-8")
        (repo / "ruff.toml").write_text("", encoding="utf-8")
        got = json.loads(run("review.py", "configs", "--repo", str(repo / "src"), "--json").stdout)
        self.assertEqual([c["file"] for c in got], [".editorconfig", "ruff.toml"])
        out = run("review.py", "--root", str(self.root), "brief", "quality", "--repo", str(repo)).stdout
        self.assertIn("ruff.toml (Ruff)", out)

    def test_the_quality_standard_cites_public_sources_by_url(self):
        lenses = {l["lens"]: l for l in json.loads(run("review.py", "--root", str(self.root),
                                                       "lenses", "--json").stdout)}
        std = lenses["quality"]["standard"]
        for url in ("https://owasp.org/Top10/", "https://peps.python.org/pep-0008/",
                    "https://owasp.org/www-project-application-security-verification-standard/"):
            self.assertIn(url, std)
        # No tracker is assumed. tools/release_check.py guards the rest.
        for lens in lenses.values():
            self.assertNotRegex(lens["standard"] + lens["look_for"], r"(?i)\bjira\b")

    def test_ticket_fills_the_verdict_and_the_old_flag_still_works(self):
        f = self.tmp / "f.jsonl"
        f.write_text(json.dumps({"lens": "correctness", "checked": True}) + "\n", encoding="utf-8")
        for flag in ("--ticket", "--jira"):
            with self.subTest(flag=flag):
                r = run("review.py", "--root", str(self.root), "grade", str(f), flag, "PROJ-12")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("| Ticket | PROJ-12 |", r.stdout)
        self.assertNotIn("--jira", run("review.py", "grade", "--help").stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
