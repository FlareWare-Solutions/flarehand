"""tests_core_sources.py - the parts of sources.py other scripts rely on.

kb.py about-me reads usage_counts and the learning thresholds, ground.py reads tier_for_url and
sources_rows, and the order's JSON shape is what SKILL.md tells the agent to read. Loaded by
evals/test_scripts.py, and runnable on its own.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import sources  # noqa: E402


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SKILL / "scripts" / script), *args],
                          capture_output=True, text=True, timeout=60)


class TestInterface(unittest.TestCase):
    """Names other areas import. Renaming one breaks them quietly, so pin them here."""

    def test_the_names_other_scripts_use_exist(self):
        for name in ("usage_counts", "LEARN_MIN_CITES", "LEARN_MIN_DAYS", "learning_state", "load_tiers",
                     "detect_roles", "current_roles", "tier_for_url", "kind_of", "sources_rows",
                     "team_preferences", "detect_project", "build_order", "KINDS"):
            with self.subTest(name=name):
                self.assertTrue(hasattr(sources, name))

    def test_learning_needs_several_days(self):
        self.assertGreaterEqual(sources.LEARN_MIN_DAYS, 3)
        self.assertGreaterEqual(sources.LEARN_MIN_CITES, sources.LEARN_MIN_DAYS)

    def test_the_kinds_are_the_designed_nine(self):
        self.assertEqual(sources.KINDS, ("user", "kb", "repo", "git", "playbook", "mcp", "official",
                                         "secondary", "forum"))


class TestWithAKnowledgeBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fh-csrc-"))
        self.root = self.tmp / "memory"
        run("kb.py", "init", "--root", str(self.root), "--role", "support analyst")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_order_json_has_the_keys_the_skill_reads(self):
        r = run("sources.py", "--root", str(self.root), "--json", "order", "hello", "--path", str(self.tmp))
        self.assertEqual(r.returncode, 0, r.stderr)
        got = json.loads(r.stdout)
        for key in ("roles", "role_source", "project", "order", "domains", "hints", "notes", "rule",
                    "usage_log", "role_suggestions", "pin_suggestions", "excluded"):
            with self.subTest(key=key):
                self.assertIn(key, got)
        for row in got["order"]:
            self.assertEqual(set(row) >= {"kind", "tier", "reasons", "only_if_weak", "how"}, True, row)
        self.assertEqual(got["roles"], ["support"])

    def test_usage_counts_reads_saved_work_even_with_learning_off(self):
        ledger = self.root / "evidence" / "index.jsonl"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        days = [(date.today() - timedelta(days=d)).isoformat() for d in (1, 2, 3)]
        ledger.write_text("".join(json.dumps({"hash": f"{i:012x}", "source": "https://docs.python.org/3/x",
                                              "kept_on": d}) + "\n" for i, d in enumerate(days)), encoding="utf-8")
        counts = sources.usage_counts(self.root)
        self.assertEqual(counts["official"]["cites"], 3)
        self.assertEqual(counts["docs.python.org"]["cites"], 3)
        self.assertTrue(sources.is_learned(counts["official"]))

    def test_usage_outside_the_window_does_not_count(self):
        run("sources.py", "--root", str(self.root), "learning", "--on")
        (self.root / ".index" / "usage.jsonl").write_text(
            json.dumps({"kind": "forum", "domain": "", "day": "2020-01-01"}) + "\n", encoding="utf-8")
        self.assertNotIn("forum", sources.usage_counts(self.root))

    def test_sources_tsv_in_the_knowledge_base_is_read(self):
        (self.root / "sources.tsv").write_text("type\tkey\tvalue\texpect\tnote\n# a comment\n"
                                               "prefer\tForum\tnever\t\t\n"
                                               "pin\trelease\thttps://example.com/r\tShips Tuesday\t\n",
                                               encoding="utf-8")
        rows = sources.sources_rows(self.root, self.tmp)
        self.assertEqual([r["type"] for r in rows], ["prefer", "pin"])
        self.assertEqual(sources.team_preferences(self.root, self.tmp)["forum"][0], "never")

    def test_a_missing_knowledge_base_is_a_clear_error(self):
        r = run("sources.py", "--root", str(self.tmp / "nope"), "order", "x")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("kb.py init", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_learning_state_is_asked_once(self):
        r = run("sources.py", "--root", str(self.root), "learning")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Not asked yet", r.stdout)
        run("sources.py", "--root", str(self.root), "learning", "--off")
        self.assertEqual(run("sources.py", "--root", str(self.root), "learning").returncode, 0)

    def test_kinds_lists_every_kind(self):
        r = run("sources.py", "--root", str(self.root), "--json", "kinds", "--path", str(self.tmp))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([k["kind"] for k in json.loads(r.stdout)["kinds"]], list(sources.KINDS))

    def test_help_works_for_every_command(self):
        for cmd in ("role", "kinds", "project", "order", "pin", "learning", "used"):
            with self.subTest(cmd=cmd):
                self.assertEqual(run("sources.py", cmd, "--help").returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
