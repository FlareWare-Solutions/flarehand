"""Split from test_scripts.py. Loaded by tests/test_scripts.py, and runnable on its own."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "flarehand"
sys.path.insert(0, str(SKILL / "scripts"))



def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / script), *args],
        capture_output=True, text=True, timeout=60,
    )


# ---------------------------------------------------------------- normalising


class TestEvidence(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hww-ev-"))
        self.root = self.tmp / "memory"
        run("kb.py", "init", "--root", str(self.root))

    def tearDown(self):
        run("evidence.py", "--root", str(self.root), "discard", "--all")
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ev(self, *args):
        return run("evidence.py", "--root", str(self.root), *args)

    def kept_files(self):
        return list((self.root / "evidence").glob("*.txt"))

    def test_add_stages_and_writes_nothing_to_the_knowledge_base(self):
        out = json.loads(self.ev("add", "--text", "some log text", "--source", "case 1", "--json").stdout)
        self.assertEqual(out["status"], "staged")
        self.assertEqual(self.kept_files(), [])

    def test_same_text_gives_the_same_reference(self):
        a = json.loads(self.ev("add", "--text", "some log text", "--source", "case 1", "--json").stdout)
        b = json.loads(self.ev("add", "--text", "some log text", "--source", "case 1", "--json").stdout)
        self.assertEqual(a["hash"], b["hash"])
        self.assertEqual(b["status"], "already staged")

    def test_keep_moves_it_in_and_the_reference_does_not_change(self):
        h = json.loads(self.ev("add", "--text", "evidence body", "--source", "s", "--json").stdout)["hash"]
        self.assertEqual(self.ev("keep", h).returncode, 0)
        self.assertEqual([p.stem for p in self.kept_files()], [h])
        self.assertEqual(self.ev("get", f"evidence/{h}.txt").stdout, "evidence body")

    def test_saving_an_answer_keeps_the_evidence_it_cites(self):
        h = json.loads(self.ev("add", "--text", "cited text", "--source", "s", "--json").stdout)["hash"]
        r = run("answers.py", "--root", str(self.root), "write", "a question", "--source", "https://example.com/x",
                "--body", f"Claim [verified: evidence/{h}.txt].")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([p.stem for p in self.kept_files()], [h])

    def test_editing_a_kept_snapshot_is_detected(self):
        out = json.loads(self.ev("add", "--text", "original", "--source", "s", "--keep", "--json").stdout)
        self.assertEqual(self.ev("verify").returncode, 0)
        (self.root / "evidence" / f"{out['hash']}.txt").write_text("tampered", encoding="utf-8")
        self.assertNotEqual(self.ev("verify").returncode, 0)

    def test_snapshotting_the_skill_itself_is_refused(self):
        r = self.ev("add", "--file", str(SKILL / "references" / "grounding.md"), "--source", "a page")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Refused", r.stderr)

    def test_stage_is_the_one_path_and_records_extra_fields(self):
        sys.path.insert(0, str(SKILL / "scripts"))
        import evidence
        got = evidence.stage(self.root, "staged by a function", source="https://example.com/a",
                             kind="web", extra={"ground_kind": "web", "hash": "not overwritten"})
        self.assertEqual(got["status"], "staged")
        row = [r for r in evidence.read_ledger(evidence.staging_dir(self.root)) if r["hash"] == got["hash"]][0]
        self.assertEqual(row["ground_kind"], "web")
        self.assertEqual(row["hash"], got["hash"])
        refused = evidence.stage(self.root, (SKILL / "references" / "evidence.md").read_text(encoding="utf-8"))
        self.assertEqual(refused.get("code"), 1)
        self.assertEqual(evidence.stage(self.root, "   ").get("code"), 2)

    def test_a_crafted_reference_cannot_escape(self):
        for bad in ("../../etc/passwd", "evidence/../../x.txt", "abc"):
            with self.subTest(bad=bad):
                self.assertEqual(self.ev("get", bad).returncode, 2)


# ---------------------------------------------------------------- packaging


class TestSourceComparison(unittest.TestCase):
    """A re-check compares text exactly, so it gives the same verdict whoever runs it."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hww-compare-"))
        self.root = self.tmp / "memory"
        run("kb.py", "init", "--root", str(self.root))
        r = run("evidence.py", "--root", str(self.root), "add", "--text", "The tool registers once through the CLI.",
                "--source", "https://example.com/setup", "--keep", "--json")
        self.hash = json.loads(r.stdout)["hash"]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def compare(self, now):
        f = self.tmp / "now.txt"
        f.write_text(now, encoding="utf-8")
        return run("evidence.py", "--root", str(self.root), "compare", self.hash, "--file", str(f))

    def test_identical_whitespace_and_changed(self):
        same = self.compare("The tool registers once through the CLI.")
        self.assertEqual((same.returncode, "Identical" in same.stdout), (0, True))
        spacing = self.compare("The tool  registers once\nthrough the CLI.")
        self.assertEqual((spacing.returncode, "spacing" in spacing.stdout), (0, True))
        moved = self.compare("The tool registers through the desktop app settings.")
        self.assertEqual(moved.returncode, 1)
        self.assertIn("+The tool registers through the desktop app settings.", moved.stdout)

    def test_verified_resets_the_answer_clock_without_touching_the_answer(self):
        q = "how do I register the tool"
        run("answers.py", "--root", str(self.root), "write", q, "--source", "https://example.com/setup",
            "--body", f"Once, through the CLI [verified: evidence/{self.hash}.txt].")
        run("answers.py", "--root", str(self.root), "approve", q)
        path = next((self.root / "answers").glob("*.md"))
        path.write_text(re.sub(r"generated_at: .*", "generated_at: 2026-01-01", path.read_text(encoding="utf-8")),
                        encoding="utf-8")
        run("answers.py", "--root", str(self.root), "approve", q)
        before = json.loads(run("recall.py", "--root", str(self.root), q).stdout)
        self.assertEqual(before["verdict"], "recheck")
        body_before = path.read_text(encoding="utf-8").split("\n---", 1)[-1]
        self.assertEqual(run("answers.py", "--root", str(self.root), "verified", q).returncode, 0)
        after = json.loads(run("recall.py", "--root", str(self.root), q).stdout)
        self.assertEqual(after["verdict"], "replay")
        self.assertEqual(path.read_text(encoding="utf-8").split("\n---", 1)[-1], body_before)

    def test_verified_refuses_an_answer_marked_out_of_date(self):
        q = "how do I register the tool"
        run("answers.py", "--root", str(self.root), "write", q, "--source", "https://example.com/setup",
            "--body", f"Once [verified: evidence/{self.hash}.txt].")
        run("answers.py", "--root", str(self.root), "invalidate", q, "--why", "the page moved")
        self.assertNotEqual(run("answers.py", "--root", str(self.root), "verified", q).returncode, 0)


# ---------------------------------------------------------------- code review grading


class TestKeepHonoursSessionOnly(unittest.TestCase):
    """'Just this session' means nothing reaches the knowledge base, evidence included."""

    def test_keep_is_refused_in_a_session_only_session(self):
        tmp = Path(tempfile.mkdtemp(prefix="fh-ev-"))
        try:
            root = tmp / "kb"
            env = {**os.environ, "FLAREHAND_SESSION": "s1", "FLAREHAND_SESSION_DIR": str(tmp / "sessions"),
                   "PYTHONDONTWRITEBYTECODE": "1"}

            def go(script, *a):
                return subprocess.run([sys.executable, str(SKILL / "scripts" / script), *a],
                                      capture_output=True, text=True, timeout=60, env=env)

            self.assertEqual(go("kb.py", "init", "--root", str(root), "--name", "T", "--no-detect").returncode, 0)
            self.assertEqual(go("kb.py", "--root", str(root), "session", "only").returncode, 0)
            src = tmp / "page.txt"
            src.write_text("The limit is 100 requests per minute.\n", encoding="utf-8")
            self.assertEqual(go("evidence.py", "--root", str(root), "add", "--file", str(src),
                                "--source", "https://example.com/limits").returncode, 0)
            r = go("evidence.py", "--root", str(root), "keep", "--all")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertFalse(list((root / "evidence").glob("*.txt")) if (root / "evidence").is_dir() else [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
