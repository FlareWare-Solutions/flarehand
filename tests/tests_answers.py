#!/usr/bin/env python3
"""tests_answers.py - saved answers and evidence. Loaded by test_scripts.py.

Each test here pins a fix from the review: credentials never land in the knowledge
base unless the person chose to keep them, only write and approve bless a body, staging is private and re-hashed on keep,
CRLF text hashes the same before and after a round trip, nothing blocks on a terminal,
and a wording that belongs to another saved question is a collision, not a replacement.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "flarehand"
sys.path.insert(0, str(SKILL / "scripts"))

import answers  # noqa: E402
import evidence  # noqa: E402
import recall  # noqa: E402


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / script), *args],
        capture_output=True, text=True, timeout=60,
    )


SECRET = "Hunter2xyz"
SOURCE = "https://docs.example.com/setup#keys"


class _Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hww-ansb-"))
        self.root = self.tmp / "memory"
        run("kb.py", "init", "--root", str(self.root))
        if not (self.root / "config.json").is_file():
            # the scripts under test only need the marker file; kb.py init is someone else's area
            self.root.mkdir(parents=True, exist_ok=True)
            (self.root / "config.json").write_text("{}", encoding="utf-8")

    def tearDown(self):
        run("evidence.py", "--root", str(self.root), "discard", "--all")
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ans(self, *args):
        return run("answers.py", "--root", str(self.root), *args)

    def ev(self, *args):
        return run("evidence.py", "--root", str(self.root), *args)

    def recall(self, q):
        return json.loads(run("recall.py", q, "--root", str(self.root)).stdout)

    def write(self, q, body, *extra):
        return self.ans("write", q, "--source", SOURCE, "--body", body, *extra)

    def stage(self, text, *extra):
        return json.loads(self.ev("add", "--text", text, "--source", "case 1", "--json", *extra).stdout)

    def answer_file(self, q):
        return self.root / "answers" / f"{recall.key_for(q)}.md"

    def root_holds(self, needle: str) -> bool:
        return any(needle in p.read_text(encoding="utf-8", errors="replace")
                   for p in self.root.rglob("*") if p.is_file())


# ---------------------------------------------------------------- credentials

class TestCredentialsAreTheirCall(_Base):
    """Their knowledge base, so keeping a credential is their choice. The skill asks once,
    never decides for them, and says so every time it acts on the answer."""

    def choose(self, key, value):
        return run("kb.py", "--root", str(self.root), "choice", key, value)

    def test_staging_a_credential_warns_and_says_rotate(self):
        r = self.ev("add", "--text", f"jdbc:oracle:thin:scott/tiger@db1:1521/orcl password={SECRET}",
                    "--source", "ticket X")
        self.assertEqual(r.returncode, 0)
        self.assertIn("WARNING", r.stderr)
        self.assertIn("rotate", r.stderr)
        self.assertNotIn(SECRET, r.stdout + r.stderr, "the secret itself must never be printed")

    def test_keeping_a_credential_asks_first(self):
        h = self.stage(f"password = {SECRET}")["hash"]
        r = self.ev("keep", h)
        self.assertEqual(r.returncode, 1)
        self.assertIn("kb.py choice credentials_in_notes", r.stderr)
        self.assertNotIn(SECRET, r.stdout + r.stderr)
        self.assertFalse(self.root_holds(SECRET))
        self.assertEqual(self.ev("add", "--text", f"password = {SECRET}", "--source", "s", "--keep").returncode, 1)
        self.assertFalse(self.root_holds(SECRET))

    def test_redact_points_at_redact(self):
        self.choose("credentials_in_notes", "redact")
        h = self.stage(f"password = {SECRET}")["hash"]
        r = self.ev("keep", h)
        self.assertEqual(r.returncode, 1)
        self.assertIn("redact.py --apply", r.stderr)
        self.assertFalse(self.root_holds(SECRET))

    def test_keep_keeps_it_and_says_so(self):
        self.choose("credentials_in_notes", "keep")
        h = self.stage(f"password = {SECRET}")["hash"]
        r = self.ev("keep", h)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("as you chose on", r.stdout + r.stderr)

    def test_a_password_answer_does_not_cover_a_card_number(self):
        self.choose("credentials_in_notes", "keep")
        r = self.ev("add", "--text", "Card 4111 1111 1111 1111", "--source", "s", "--keep")
        self.assertEqual(r.returncode, 1)
        self.assertIn("kb.py choice ids_in_notes", r.stderr)

    def test_an_answer_citing_a_credential_snapshot_asks_first(self):
        h = self.stage(f"api_key={SECRET}")["hash"]
        r = self.write("what is the db string", f"See [verified: evidence/{h}.txt]")
        self.assertEqual(r.returncode, 1)
        self.assertIn("kb.py choice credentials_in_notes", r.stderr)
        self.assertFalse(self.root_holds(SECRET))
        self.assertEqual(list((self.root / "answers").glob("*.md")), [], "nothing may be saved when the write is refused")

    def test_an_answer_body_with_a_credential_follows_the_choice(self):
        r = self.write("q", f"use Bearer {'a' * 32} to call it")
        self.assertEqual(r.returncode, 1)
        self.assertIn("kb.py choice credentials_in_notes", r.stderr)
        self.assertFalse(self.root_holds("a" * 32))
        self.choose("credentials_in_notes", "redact")
        r = self.write("q", f"use Bearer {'a' * 32} to call it")
        self.assertIn("redact.py --apply", r.stderr)
        self.assertFalse(self.root_holds("a" * 32))
        self.choose("credentials_in_notes", "keep")
        r = self.write("q", f"use Bearer {'a' * 32} to call it")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("as you chose on", r.stdout + r.stderr)


class TestComparisonsAreRemembered(_Base):
    def test_a_changed_source_shows_up_in_list(self):
        h = json.loads(self.ev("add", "--text", "the limit is 50k", "--source", SOURCE,
                               "--keep", "--json").stdout)["hash"]
        now = self.tmp / "now.txt"
        now.write_text("the limit is 75k", encoding="utf-8")
        self.assertEqual(self.ev("compare", h, "--file", str(now)).returncode, 1)
        out = self.ev("list").stdout
        self.assertIn("CHANGED at the source", out)
        self.assertEqual(json.loads(self.ev("list", "--json").stdout)[0]["last_compare"]["verdict"], "changed")
        now.write_text("the limit is 50k", encoding="utf-8")
        self.ev("compare", h, "--file", str(now))
        self.assertNotIn("CHANGED", self.ev("list").stdout, "the latest comparison wins")


# ---------------------------------------------------------------- hand edits

class TestOnlyWriteAndApproveBless(_Base):
    def hand_edit(self, q="hand edit q"):
        self.write(q, "original body")
        self.ans("approve", q)
        path = self.answer_file(q)
        path.write_text(path.read_text(encoding="utf-8").replace("original body", "EDITED body"), encoding="utf-8")
        return path

    def test_alias_refuses_a_hand_edited_answer(self):
        self.hand_edit()
        r = self.ans("alias", "hand edit question", "--to", "hand edit q")
        self.assertEqual(r.returncode, 1)
        self.assertIn("approve", r.stderr)
        self.assertEqual(self.recall("hand edit q")["verdict"], "recheck", "an unreviewed edit must not replay")
        self.assertNotEqual(self.recall("hand edit question")["verdict"], "replay")

    def test_verified_and_invalidate_refuse_a_hand_edited_answer(self):
        self.hand_edit()
        self.assertEqual(self.ans("verified", "hand edit q").returncode, 1)
        self.assertEqual(self.ans("invalidate", "hand edit q", "--why", "x").returncode, 1)
        self.assertEqual(self.recall("hand edit q")["verdict"], "recheck")

    def test_approve_blesses_the_edit_and_then_the_rest_work(self):
        self.hand_edit()
        self.assertEqual(self.ans("approve", "hand edit q").returncode, 0)
        self.assertEqual(self.recall("hand edit q")["verdict"], "replay")
        self.assertEqual(self.ans("alias", "hand edit question", "--to", "hand edit q").returncode, 0)
        self.assertEqual(self.ans("verified", "hand edit q").returncode, 0)
        self.assertEqual(self.ans("verify").returncode, 0)

    def test_write_records_a_hash_that_survives_a_crlf_round_trip(self):
        self.write("crlf q", "line a\r\nline b\r\n")
        self.ans("approve", "crlf q")
        self.assertEqual(self.ans("verify").returncode, 0)
        self.assertEqual(self.recall("crlf q")["verdict"], "replay")
        self.assertNotIn("\r", self.answer_file("crlf q").read_bytes().decode("utf-8"))


# ---------------------------------------------------------------- staging

class TestStagingIsPrivateAndChecked(_Base):
    def test_keep_rehashes_and_refuses_a_changed_staged_file(self):
        h = self.stage("staged snapshot text one")["hash"]
        (evidence.staging_dir(self.root) / f"{h}.txt").write_text("tampered", encoding="utf-8")
        r = self.ev("keep", h)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no longer matches", r.stderr)
        self.assertEqual(list((self.root / "evidence").glob("*.txt")) if (self.root / "evidence").is_dir() else [], [])

    @unittest.skipIf(os.name == "nt", "file modes are a POSIX thing")
    def test_staged_files_are_readable_by_this_user_only(self):
        h = self.stage("private text")["hash"]
        folder = evidence.staging_dir(self.root)
        self.assertEqual(folder.stat().st_mode & 0o777, 0o700)
        self.assertEqual((folder / f"{h}.txt").stat().st_mode & 0o777, 0o600)
        self.assertEqual((folder / evidence.LEDGER).stat().st_mode & 0o777, 0o600)

    def test_staged_files_older_than_seven_days_are_dropped_on_the_next_add(self):
        old = self.stage("old one")["hash"]
        path = evidence.staging_dir(self.root) / f"{old}.txt"
        stamp = time.time() - (evidence.STAGING_MAX_AGE_DAYS + 1) * 86400
        os.utime(path, (stamp, stamp))
        self.stage("new one")
        self.assertFalse(path.exists())
        self.assertNotIn(old, [r["hash"] for r in evidence.read_ledger(evidence.staging_dir(self.root))])
        self.assertEqual(self.ev("get", old).returncode, 2)

    def test_crlf_text_kept_from_stdin_still_matches_its_hash(self):
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "evidence.py"), "--root", str(self.root),
                            "add", "--source", "T", "--keep"], input="line one\r\nline two\r\n",
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.ev("verify").returncode, 0, self.ev("verify").stdout)

    def test_evidence_is_kept_only_after_the_answer_is_saved(self):
        h = self.stage("cited text")["hash"]
        shutil.rmtree(self.root / "answers", ignore_errors=True)
        (self.root / "answers").write_text("not a folder", encoding="utf-8")  # makes the save fail
        r = self.write("a question", f"Claim [verified: evidence/{h}.txt].")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(evidence.locate(self.root, h)[1], "staged", "a failed save must not keep its evidence")


# ---------------------------------------------------------------- never block, never guess

class TestNeverBlocksOrGuesses(_Base):
    class _Tty:
        def isatty(self):
            return True

        def read(self):
            raise AssertionError("read standard input from a terminal")

    def in_process(self, module, *argv):
        saved, sys.stdin = sys.stdin, self._Tty()
        from io import StringIO
        err, sys.stderr = sys.stderr, StringIO()
        try:
            rc = module.main(["--root", str(self.root), *argv])
            return rc, sys.stderr.getvalue()
        finally:
            sys.stdin, sys.stderr = saved, err

    def test_stdin_fallbacks_refuse_a_terminal(self):
        h = self.stage("some text")["hash"]
        for module, argv, flag in ((answers, ["write", "q", "--source", "s"], "--body"),
                                   (evidence, ["add", "--source", "s"], "--text"),
                                   (evidence, ["compare", h], "--file")):
            with self.subTest(argv=argv):
                rc, err = self.in_process(module, *argv)
                self.assertEqual(rc, 2)
                self.assertIn(flag, err)

    def test_the_suggested_approve_command_is_safe_for_any_question(self):
        r = self.write('say "hi"', "x")
        self.assertEqual(r.returncode, 0, r.stderr)
        hint = [l for l in r.stdout.splitlines() if "approve" in l and "answers.py" in l][0]
        self.assertNotIn('"', hint)
        self.assertIn(recall.key_for('say "hi"'), hint)
        self.assertEqual(self.ans("approve", recall.key_for('say "hi"')).returncode, 0)

    def test_a_wording_with_no_words_is_refused(self):
        self.write("real question", "x")
        for r in (self.write("???", "x"), self.ans("alias", "!!!", "--to", "real question"),
                  run("recall.py", "???", "--root", str(self.root))):
            with self.subTest(cmd=r.args[2:4]):
                self.assertEqual(r.returncode, 2)
                self.assertIn("no words", r.stderr)


# ---------------------------------------------------------------- replacement and collision

class TestReplaceAndCollide(_Base):
    def test_the_same_question_replaces_and_becomes_a_draft_again(self):
        self.write("set up the runner", "old")
        self.ans("approve", "set up the runner")
        r = self.write("Set up the runner?", "new")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Replaced", r.stdout)
        self.assertEqual(self.recall("set up the runner")["verdict"], "recheck")
        self.assertEqual(self.ans("get", "set up the runner").stdout.strip(), "new")
        self.assertEqual(len(list((self.root / "answers").glob("*.md"))), 1)

    def test_an_alias_of_another_question_is_a_collision_unless_replace(self):
        self.write("set up the runner", "runner steps")
        self.ans("alias", "configure the runner", "--to", "set up the runner")
        r = self.write("configure the runner", "other")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--replace", r.stderr)
        self.assertEqual(self.ans("get", "set up the runner").stdout.strip(), "runner steps")
        r = self.write("configure the runner", "other", "--replace")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.ans("get", "set up the runner").stdout.strip(), "other")


# ---------------------------------------------------------------- just this session

class TestSessionOnly(_Base):
    """After `kb.py session only`, answers.py writes nothing either."""

    def test_session_only_refuses_every_answer_write(self):
        sys.path.insert(0, str(SKILL / "scripts"))
        import kb
        if not hasattr(kb, "session_only_refusal"):
            self.skipTest("kb.py has no session-only mode yet")
        env = {**os.environ, "FLAREHAND_SESSION": f"test-answers-{self.tmp.name}"}

        def go(script, *args):
            return subprocess.run([sys.executable, str(SKILL / "scripts" / script), "--root", str(self.root), *args],
                                  capture_output=True, text=True, timeout=60, env=env)

        self.assertEqual(go("kb.py", "session", "only").returncode, 0)
        try:
            r = go("answers.py", "write", "set up the runner", "--source", SOURCE, "--body", "steps")
            self.assertEqual(r.returncode, 1)
            self.assertEqual(len(r.stderr.strip().splitlines()), 1, r.stderr)
            self.assertFalse(list((self.root / "answers").glob("*.md")))
        finally:
            go("kb.py", "session", "end")
        r = go("answers.py", "write", "set up the runner", "--source", SOURCE, "--body", "steps")
        self.assertEqual(r.returncode, 0, r.stderr)


class TestLedgerOutlivesTheSession(_Base):
    """[verified: S1] only means something inside one session. A saved answer keeps the slice of
    the ledger it cites, so replay and recheck still know what S1 was."""

    def tearDown(self):
        shutil.rmtree(evidence.staging_dir(self.root), ignore_errors=True)
        super().tearDown()

    def ground(self, *args):
        return run("ground.py", "--root", str(self.root), *args)

    def test_the_ledger_is_kept_and_mapped_to_its_locator(self):
        r = self.ground("source", "add", "--kind", "web", "--locator", SOURCE, "--text",
                        "Add the deploy key under Settings, then Keys.", "--tier", "T2")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.ground("claim", "add", "Keys live under Settings", "--source", "S1",
                        "--quote", "Add the deploy key under Settings")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.ans("write", "how do I add the deploy key", "--no-sources",
                     "--body", "Open Settings, then Keys [verified: S1].")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Kept the ledger for S1", r.stdout)
        key = recall.key_for("how do I add the deploy key")
        ledger = json.loads((self.root / "answers" / f"{key}.ledger.json").read_text(encoding="utf-8"))
        canonical = "https://docs.example.com/setup"            # the fragment is not part of the page
        self.assertEqual(ledger["map"], {"S1": canonical})
        self.assertEqual(ledger["claims"][0]["sources"], ["S1"])
        text = (self.root / "answers" / f"{key}.md").read_text(encoding="utf-8")
        self.assertIn(canonical, text)                            # the locator joins the sources
        self.assertIn(f"ledger: {key}.ledger.json", text)
        h = ledger["sources"][0]["hash"]
        self.assertTrue(list((self.root / "evidence").glob(f"{h}*")))   # the snapshot is kept too

    def test_an_id_the_session_does_not_hold_is_refused(self):
        r = self.ans("write", "how do I add the deploy key", "--source", SOURCE,
                     "--body", "Open Settings [verified: S4].")
        self.assertEqual(r.returncode, 1)
        self.assertIn("S4", r.stderr)
        self.assertFalse(list((self.root / "answers").glob("*.md")))

    def test_ledger_ids_are_read_from_every_label_that_cites_sources(self):
        body = "[verified: S3+S7] a [weak: S9] b [conflict: S2 vs S5] [inference from S2, S3] [your input]"
        self.assertEqual(answers.ledger_ids(body), ["S3", "S7", "S9", "S2", "S5"])


class TestPinnedSourcesTriggerARecheck(_Base):
    def setUp(self):
        super().setUp()
        (self.root / "sources.tsv").write_text(
            "type\tkey\tvalue\texpect\tnote\npin\tdeploy-key\t" + SOURCE + "\tAdd the deploy key\t\n",
            encoding="utf-8")
        self.ans("write", "how do I add the deploy key", "--source", SOURCE, "--body", "Open Settings.")
        self.ans("approve", "how do I add the deploy key")

    def verdict(self):
        return recall.lookup(self.root, "how do I add the deploy key")

    def stamp(self, days_ago, status="ok"):
        from datetime import date, timedelta
        state = self.root / ".index" / "state.json"
        data = json.loads(state.read_text(encoding="utf-8")) if state.is_file() else {}
        data["pins"] = {"deploy-key": {"status": status, "hash": "x",
                                       "checked_on": (date.today() - timedelta(days=days_ago)).isoformat()}}
        state.write_text(json.dumps(data), encoding="utf-8")

    def test_never_checked_pin_means_recheck(self):
        got = self.verdict()
        self.assertEqual(got["verdict"], "recheck")
        self.assertIn("deploy-key (never checked)", got["why"])

    def test_a_recent_ok_check_replays(self):
        self.stamp(3)
        self.assertEqual(self.verdict()["verdict"], "replay")

    def test_an_old_or_drifted_check_means_recheck(self):
        self.stamp(31)
        self.assertEqual(self.verdict()["verdict"], "recheck")
        self.stamp(1, "drift")
        self.assertIn("found it drift", self.verdict()["why"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
