"""Split from test_scripts.py. Loaded by tests/test_scripts.py, and runnable on its own."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "flarehand"
sys.path.insert(0, str(SKILL / "scripts"))

import redact  # noqa: E402


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / script), *args],
        capture_output=True, text=True, timeout=60,
    )


# ---------------------------------------------------------------- normalising


class TestRedaction(unittest.TestCase):
    def test_an_opinion_about_a_person_is_flagged_before_it_leaves(self):
        f = Path(tempfile.mktemp(suffix=".md"))
        f.write_text("- [fact] Missed the 2026-09-10 due date (source: Jira, on: 2026-09-11, status: confirmed)\n"
                     "- [opinion] Not ready to lead yet (source: two missed dates, on: 2026-09-12, status: suspected)\n",
                     encoding="utf-8")
        try:
            r = run("redact.py", str(f))
            self.assertIn("own assessment", r.stdout + r.stderr)
            self.assertNotIn("Missed the 2026-09-10", (r.stdout + r.stderr).split("own assessment", 1)[-1])
        finally:
            f.unlink()

    @classmethod
    def setUpClass(cls):
        cls.patterns = redact.load_patterns(SKILL / "assets" / "redact-patterns.tsv")

    def rules_hit(self, text: str) -> set:
        return {f["rule"] for f in redact.scan(text, self.patterns, "low")}

    def test_finds_the_dangerous_things(self):
        text = ("password=Hunter2Hunter2\njdbc:oracle:thin:@host:1521/db\n"
                "dana@northgate.ca\n416-555-2368\n$1,250,000.00\n10.42.8.19\n")
        # Not example.com or 555-01xx: those are reserved for documentation, and redact.py lets them through.
        hits = self.rules_hit(text)
        for expected in ("password-assign", "jdbc", "email", "phone", "money", "private-ip"):
            with self.subTest(expected=expected):
                self.assertIn(expected, hits)

    def test_random_digits_are_not_a_card_number(self):
        self.assertNotIn("card", self.rules_hit("order 1234567890123456 shipped"))

    def test_a_real_card_number_is_caught(self):
        self.assertIn("card", self.rules_hit("card 4111111111111111 declined"))

    def test_clean_text_is_clean(self):
        self.assertFalse(self.rules_hit("The posting failed on the cloud environment."))

    def test_apply_replaces_and_counts(self):
        cleaned, n = redact.apply_redactions("mail me at dana@northgate.ca", self.patterns, "low")
        self.assertNotIn("dana@northgate.ca", cleaned)
        self.assertEqual(n, 1)


# ---------------------------------------------------------------- knowledge base


if __name__ == "__main__":
    unittest.main(verbosity=2)
