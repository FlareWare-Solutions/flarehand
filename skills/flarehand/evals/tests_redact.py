"""Tests for redact.py and assets/redact-patterns.tsv: redaction and privacy.

Loaded by evals/test_scripts.py alongside the main suite.
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

import redact  # noqa: E402


def run_redact(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, str(SKILL / "scripts" / "redact.py"), *args],
                          input=stdin, capture_output=True, text=True, env=env)


class RedactBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patterns = redact.load_patterns(SKILL / "assets" / "redact-patterns.tsv")

    def rules(self, text: str) -> set:
        return {f["rule"] for f in redact.scan(text, self.patterns, "low")}

    def assert_rule(self, text: str, rule: str):
        self.assertIn(rule, self.rules(text), f"expected {rule} on {text!r}")

    def assert_clean(self, text: str):
        found = redact.scan(text, self.patterns, "low")
        self.assertFalse(found, f"false positive on {text!r}: {[(f['rule'], f['text']) for f in found]}")


class TestCredentials(RedactBase):
    def test_password_written_in_prose(self):
        self.assert_rule("the password is Welcome123!", "password-prose")
        self.assert_rule("Database password for the test copy is Welcome123!", "password-prose")
        self.assert_rule("the API key was Abc123xyz789", "password-prose")

    def test_password_reset_instructions_are_not_a_password(self):
        self.assert_clean("password reset instructions are in the KB")
        self.assert_clean("the password is unchanged")
        self.assert_clean("password is the same as before")
        self.assert_clean("the token: expires after an hour")

    def test_key_prefixes(self):
        for sample in ("sk_" "live_4eC39HqLyjWDarjtT1zdp7dc", "API key sk_" "test_4eC39HqLyjWDarjtT1zdp7dc",
                       "xox" "b-1234567890-abcdefghij", "xox" "p-1234567890-abcdefghij-zz",
                       "AIza" "SyA1234567890abcdefghijklmnopqrstuv", "sk-ant-" "api03-abcdefghijklmnopqrstuvwxyz0123"):
            with self.subTest(sample=sample):
                self.assert_rule(sample, "key-prefix")
        self.assert_rule("ghp" "_abcdefghijklmnopqrstuv", "github-token")
        self.assert_rule("github" "_pat_11ABCDEFG0123456789abcdefgh", "github-token")

    def test_basic_auth_header(self):
        self.assert_rule("Authorization: Basic c2NvdHQ6dGlnZXI=", "basic-auth")
        self.assert_clean("Basic Configuration Settings")

    def test_env_style_assignments(self):
        self.assert_rule("aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "password-assign")
        self.assert_rule("export TOKEN=abc123def456ghi789", "password-assign")
        self.assert_rule("API_KEY=abcd1234", "password-assign")
        self.assert_rule("password: Welcome123!", "password-assign")
        self.assert_rule("password=Hunter2Hunter2", "password-assign")

    def test_oracle_connect_string_without_a_port(self):
        self.assert_rule("scott/tiger@ORCL", "oracle-connect")
        self.assert_rule("sqlplus scott/tiger@host:1521/db", "oracle-connect")
        self.assert_clean("and/or the config@home")

    def test_every_credential_rule_triggers_the_rotation_note(self):
        samples = {
            "password-assign": "password=Hunter2Hunter2",
            "password-prose": "the password is Welcome123!",
            "key-prefix": "sk_" "live_4eC39HqLyjWDarjtT1zdp7dc",
            "basic-auth": "Authorization: Basic c2NvdHQ6dGlnZXI=",
            "oracle-connect": "scott/tiger@ORCL",
            "aws-key": "AKIA" "IOSFODNN7EXAMPLE",
        }
        for rule, sample in samples.items():
            with self.subTest(rule=rule):
                self.assertIn(rule, redact.CREDENTIAL_RULES)
                r = run_redact("-", stdin=sample + "\n")
                self.assertEqual(r.returncode, 1)
                self.assertIn("rotate", r.stdout)


class TestHealth(RedactBase):
    def test_health_and_absence_reasons_are_flagged(self):
        for sample in ("Priya is out on medical leave next week.", "off sick today", "on sick leave until Monday",
                       "Sam was diagnosed with something", "going on maternity leave", "back from surgery",
                       "took a leave of absence", "bereavement leave", "in therapy on Tuesdays",
                       "paternity leave starts in May", "a disability accommodation"):
            with self.subTest(sample=sample):
                found = [f for f in redact.scan(sample, self.patterns, "low") if f["rule"] == "health"]
                self.assertTrue(found, sample)
                self.assertEqual(found[0]["severity"], "high")
                self.assertIn("never keep", found[0]["means"])

    def test_ordinary_sentences_are_not_health(self):
        for sample in ("sick of this bug", "the feature is disabled", "we diagnosed the issue",
                       "the St. Mary's Medical Center project", "the diagnostic run finished"):
            with self.subTest(sample=sample):
                self.assertNotIn("health", self.rules(sample))

    def test_apply_blanks_the_reason_and_keeps_the_availability(self):
        cleaned, n = redact.apply_redactions("Priya is out on medical leave next week.", self.patterns, "low")
        self.assertEqual(cleaned, "Priya is out on [REASON REMOVED] next week.")
        self.assertEqual(n, 1)

    def test_report_tells_the_person_to_remove_the_sentence(self):
        r = run_redact("-", stdin="Priya is out on medical leave next week.\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("remove the whole sentence", r.stdout)

    def test_clean_report_states_the_limits(self):
        r = run_redact("-", stdin="The posting failed on the cloud environment.\n")
        self.assertEqual(r.returncode, 0)
        self.assertIn("bare customer", r.stdout)


class TestFalsePositives(RedactBase):
    def test_version_numbers_are_not_ip_addresses(self):
        for sample in ("Upgrade from 12.2.1.4 to 12.2.1.6", "version 1.2.3.4.5", "v2.2.1.4 shipped",
                       "patch 12.2.1.4", "release 12.2.1.4 notes"):
            with self.subTest(sample=sample):
                self.assertNotIn("ipv4", self.rules(sample))
        cleaned, _ = redact.apply_redactions("Upgrade from 12.2.1.4 to 12.2.1.6", self.patterns, "low")
        self.assertEqual(cleaned, "Upgrade from 12.2.1.4 to 12.2.1.6")

    def test_real_ip_addresses_are_still_found(self):
        self.assert_rule("server 8.8.4.4.", "ipv4")
        self.assert_rule("ping 93.184.216.34 first", "ipv4")

    def test_private_addresses_get_their_own_rule_once(self):
        for sample in ("server 10.42.8.19.", "ping 192.168.0.1 first", "host 172.16.5.4 and"):
            with self.subTest(sample=sample):
                rules = [f["rule"] for f in redact.scan(sample, self.patterns, "low")]
                self.assertEqual(rules, ["private-ip"], rules)
        # 172.32 is outside the private block, so it is an ordinary address
        self.assertEqual(self.rules("host 172.32.1.1 and"), {"ipv4"})
        self.assertNotIn("private-ip", self.rules("Upgrade to 10.2.1.4 tonight"))

    def test_years_are_not_reference_numbers(self):
        self.assertNotIn("customer-number", self.rules("invoice 2024 and contract 2025 renewal"))
        self.assert_rule("invoice #2024 sent", "customer-number")
        self.assert_rule("invoice 123456 sent", "customer-number")
        self.assert_rule("customer no. 4471", "customer-number")

    def test_generic_words_before_a_suffix_are_not_a_company(self):
        for sample in ("Project Group phase 2", "The Group meets on Friday", "Our Partners program",
                       "Customer Holdings report", "Northgate Logistics starts", "Sales Technologies"):
            with self.subTest(sample=sample):
                self.assertNotIn("company-suffix", self.rules(sample))
        for sample in ("Northgate Industries reported it", "Acme Inc. reported it", "Blue Fern GmbH said",
                       "Harbor Bridge LLC filed", "Kestrel Holdings wrote", "Northgate Logistics Ltd. paid"):
            with self.subTest(sample=sample):
                self.assert_rule(sample, "company-suffix")

    def test_card_keeps_the_trailing_space(self):
        cleaned, n = redact.apply_redactions("Card 4111 1111 1111 1111 and", self.patterns, "low")
        self.assertEqual(cleaned, "Card [CARD] and")
        self.assertEqual(n, 1)


class TestOpinionLines(RedactBase):
    def test_apply_leaves_an_opinion_line_in_place(self):
        f = Path(tempfile.mktemp(suffix=".md"))
        f.write_text("[opinion] Sam is slow on tickets\n", encoding="utf-8")
        out = f.with_suffix(".md.redacted")
        try:
            r = run_redact(str(f), "--apply")
            self.assertEqual(r.returncode, 1)
            self.assertEqual(out.read_text(encoding="utf-8"), "[opinion] Sam is slow on tickets\n")
            self.assertNotIn("OPINION REMOVED", out.read_text(encoding="utf-8"))
            self.assertIn("whose", r.stdout)
        finally:
            f.unlink()
            if out.exists():
                out.unlink()

    def test_keep_replacement_is_not_counted(self):
        cleaned, n = redact.apply_redactions("[opinion] Sam is slow on tickets", self.patterns, "low")
        self.assertEqual(n, 0)
        self.assertEqual(cleaned, "[opinion] Sam is slow on tickets")


class TestContract(RedactBase):
    def test_scan_dicts_keep_the_agreed_keys(self):
        f = redact.scan("password=Hunter2Hunter2", self.patterns, "low")[0]
        for key in ("name", "severity", "line", "means"):
            self.assertIn(key, f)

    def test_every_pattern_compiles_and_has_a_severity(self):
        for p in self.patterns:
            self.assertIn(p["severity"], redact.ORDER, p["name"])
            self.assertTrue(p["means"], p["name"])


class TestInternalDomains(RedactBase):
    """Internal hosts are flagged from config, from house rules in any layer, and by generic
    shapes that need no list. Public domains are never flagged by these rules."""

    INTERNAL = {"internal-domain", "internal-host", "private-ip"}

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fh-redact-"))
        self.root = self.tmp / "kb"
        self.root.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def hits(self, text: str, extra=()) -> set:
        pats = redact.load_all(self.root, extra, cwd=self.tmp)
        return {f["rule"] for f in redact.scan(text, pats, "low")}

    def test_generic_internal_hosts_need_no_config(self):
        for sample in ("see db01.prod.internal", "open http://jira.corp/browse/X-1", "printer.office.lan",
                       "https://wiki.example.intranet/page", "on intranet.northgate.com today", "nas.home.local"):
            with self.subTest(sample=sample):
                self.assert_rule(sample, "internal-host")

    def test_code_and_public_domains_are_not_internal(self):
        for sample in ("threading.local() is per thread", "self.internal = True", "package com.acme.internal;",
                       "see https://github.com/org/repo", "mail example.com", "docs at https://example.com/x",
                       "the internal team", "a local copy"):
            with self.subTest(sample=sample):
                self.assertFalse(self.hits(sample) & self.INTERNAL, sample)

    def test_domains_from_config_are_flagged(self):
        (self.root / "config.json").write_text(json.dumps({"prefs": {"internal_domains": ["northgate.com"]}}),
                                               encoding="utf-8")
        self.assertIn("internal-domain", self.hits("open https://wiki.northgate.com/x"))
        self.assertIn("internal-domain", self.hits("build.northgate.com:8080/job/1"))
        self.assertNotIn("internal-domain", self.hits("northgate.community is public"))
        self.assertNotIn("internal-domain", self.hits("see github.com and example.com"))

    def test_domains_from_house_rules_are_flagged(self):
        (self.root / "house-rules.md").write_text(
            "# House rules\n\n## Internal domains\n\n- *.fernco.io\n- https://corp.fernco.net/\n\n"
            "## Pull requests\n\n- not-a-domain.example rule text\n", encoding="utf-8")
        self.assertEqual(redact.internal_domains(self.root, cwd=self.tmp), ["corp.fernco.net", "fernco.io"])
        self.assertIn("internal-domain", self.hits("ping api.fernco.io now"))
        self.assertIn("internal-domain", self.hits("https://corp.fernco.net/wiki"))

    def test_rules_add_up_across_sources(self):
        (self.root / "config.json").write_text(json.dumps({"prefs": {"internal_domains": "one.test, two.test"}}),
                                               encoding="utf-8")
        (self.root / "house-rules.md").write_text("## Internal domains\n- three.test\n", encoding="utf-8")
        got = redact.internal_domains(self.root, ["four.test", "not a domain"], cwd=self.tmp)
        self.assertEqual(got, ["four.test", "one.test", "three.test", "two.test"])

    def test_no_domains_means_no_domain_rule(self):
        self.assertEqual(redact.domain_rule([]), [])
        self.assertEqual(redact.internal_domains(self.root, cwd=self.tmp), [])

    def test_apply_redacts_an_internal_url(self):
        pats = redact.load_all(self.root, ["northgate.com"], cwd=self.tmp)
        cleaned, n = redact.apply_redactions("see https://wiki.northgate.com/a/b. Thanks", pats, "low")
        self.assertEqual(cleaned, "see [INTERNAL-URL]. Thanks")
        self.assertEqual(n, 1)

    def test_domain_flag_on_the_command_line(self):
        r = run_redact("--root", str(self.root), "--domain", "northgate.com", "-",
                       stdin="see https://wiki.northgate.com/x\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("internal", r.stdout)
        r = run_redact("--root", str(self.root), "--domain", "not a domain", "-", stdin="x\n")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestMoneyWithACurrencyMark(unittest.TestCase):
    """voice.md tells people to write US$ or CA$ when $ is ambiguous. The money rule must still see it."""

    def test_marked_amounts_are_flagged(self):
        pats = redact.load_patterns(redact.PATTERNS)
        for text in ("It costs US$1,250,000.00.", "Budget CA$4,000 for it.", "About 5,000 CAD.", "USD 2,000 up front."):
            with self.subTest(text=text):
                self.assertTrue(any(h["name"] == "money" for h in redact.scan(text, pats, "low")))


class TestReservedExampleDataIsNotFlagged(unittest.TestCase):
    """privacy.md tells people to use reserved example values. Flagging them made the check noise."""

    def hits(self, text: str) -> list[str]:
        return [h["text"] for h in redact.scan(text, redact.load_patterns(redact.PATTERNS), "low")]

    def test_reserved_values_pass(self):
        text = ("Write to dana@example.com or ops@support.example.org. Call 800-555-0100. "
                "Server 192.0.2.10, 198.51.100.7 or 203.0.113.250. Example Organization and Example Logistics Ltd.")
        self.assertEqual(self.hits(text), [])

    def test_real_values_are_still_flagged(self):
        text = "Write to dana@acme.ca. Call 416-555-0199x or 416-555-2368. Server 10.1.2.3. Northgate Logistics Ltd."
        hits = self.hits(text)
        for value in ("dana@acme.ca", "10.1.2.3", "Northgate Logistics Ltd"):
            with self.subTest(value=value):
                self.assertTrue(any(value in h for h in hits), hits)
        self.assertTrue(any("2368" in h for h in hits), hits)

    def test_redaction_leaves_reserved_values_alone(self):
        cleaned, n = redact.apply_redactions("Mail dana@example.com and bob@acme.ca", redact.load_patterns(redact.PATTERNS), "low")
        self.assertIn("dana@example.com", cleaned)
        self.assertNotIn("bob@acme.ca", cleaned)
        self.assertEqual(n, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
