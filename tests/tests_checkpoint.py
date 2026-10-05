#!/usr/bin/env python3
"""tests_checkpoint.py - the compaction checkpoint, and the rules that must survive a compaction.
Loaded by tests/test_scripts.py.

A compaction replaces the conversation with a summary, and the working state of the task survives
only as the summary's paraphrase. So checkpoint.py saves that state to a file in the system temp
folder before a compaction, and after it hooks/hook.py prints one line that points at the file.
These tests pin what it keeps, including sources from any MCP server, web fetch or file read, that it
only ever points and never injects, that it cleans up, and that no failure can stop a compaction.
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
SCRIPT = SKILL / "scripts" / "checkpoint.py"
REPO = ROOT if (ROOT / ".claude-plugin" / "plugin.json").is_file() else None
sys.path.insert(0, str(SKILL / "scripts"))
import checkpoint  # noqa: E402
SID = "3f2c9a1e-test-session"


def user(text: str, **extra) -> dict:
    return {"type": "user", "message": {"role": "user", "content": text}, **extra}


def said(text: str) -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


def tool(name: str, use_id: str, **inputs) -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": use_id, "name": name, "input": inputs}]}}


def result(use_id: str, text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": use_id, "content": [{"type": "text", "text": text}]}]}}


DRAFT = """# Reply to Acme Logistics

The AP batch is locked by an open posting run [verified: https://docs.example.com/ap/batch-locks#posting].
Their version is 13.0 [your input]. The unlock takes a restart [ASSUMPTION, verify].

## MISSING
- The batch number
- Who started the posting run

Keep any of this?
1. Log this work: kb.py log workflow --workflow wf-05
2. Save a note: the batch lock clears after the posting run
3. Save the answer for next time
"""

SESSION = [
    user("an earlier question from before the skill ran"),
    user('<command-message>flarehand:flarehand</command-message>\n'
         '<command-name>/flarehand:flarehand</command-name>\n'
         '<command-args>draft a reply to Acme about the locked AP batch</command-args>'),
    user("Base directory for this skill: /somewhere/flarehand\n\n# flarehand", isMeta=True),
    tool("Bash", "t1", command='python3 scripts/classify.py "draft a reply to Acme about the locked AP batch" --explain'),
    result("t1", "Route: workflow\nWorkflow: wf-05 draft\nTemplate: support-reply\nCeremony: standard\n"),
    said("Labels look like `[verified: <source>]` and `[your input]` in what I write."),
    tool("mcp__docs__read", "t2", id="ap/posting-runs"),
    result("t2", "the posting run text"),
    tool("mcp__tickets__get_issue", "t8", uri="tickets://AP-1234"),
    tool("WebFetch", "t9", url="https://status.example.com/incidents/42", prompt="summarise"),
    tool("Read", "t10", file_path="/work/repo/src/posting.py"),
    tool("Read", "t11", file_path="/home/zoe/.claude/plugins/flarehand/skills/flarehand/references/memory.md"),
    tool("mcp__docs__search", "t12", query="posting run"),
    {"type": "attachment", "attachment": {"type": "queued_command", "prompt": "also say it is urgent for month end",
                                          "origin": {"kind": "human"}}},
    user("Stop hook feedback: not theirs", isSynthetic=True),
    tool("Bash", "t3", command='python3 scripts/kb.py log workflow --workflow wf-05 --why "month end" 2>/dev/null; echo ok'),
    result("t3", "Logged run 2."),
    tool("Bash", "t4", command="python3 scripts/kb.py log --help"),
    tool("Bash", "t6", command='py -3 "C:\\Users\\Zoë\\flarehand\\scripts\\kb.py" note "AP batch locks clear after the run" --type fact'),
    tool("Bash", "t7", command="sed -i 's/kb.py config --style natural/kb.py config --style google/' README.md"),
    tool("Write", "t5", file_path="/work/replies/acme-reply.md", content="..."),
    said(DRAFT),
]


class Checkpoint(unittest.TestCase):
    """Each test gets its own temp folder, set the way Windows, macOS and Linux each look for one."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hww-ckpt-"))
        self.temp = self.tmp / "temp Zoë 日本"  # a space and non-ASCII, like many Windows user folders
        self.temp.mkdir()
        self.env = dict(os.environ, TMPDIR=str(self.temp), TEMP=str(self.temp), TMP=str(self.temp),
                        PYTHONIOENCODING="utf-8")
        self.transcript = self.tmp / "session.jsonl"
        self.write(SESSION)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rows: list) -> None:
        self.transcript.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    def run_hook(self, action: str, event, env=None) -> subprocess.CompletedProcess:
        data = event if isinstance(event, str) else json.dumps(event)
        return subprocess.run([sys.executable, str(SCRIPT), action], input=data.encode("utf-8"),
                              capture_output=True, timeout=60, env=env or self.env)

    def save(self, sid: str = SID, trigger: str = "auto") -> subprocess.CompletedProcess:
        r = self.run_hook("save", {"hook_event_name": "PreCompact", "session_id": sid, "trigger": trigger,
                                   "transcript_path": str(self.transcript)})
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def restore(self, sid: str = SID, source: str = "compact") -> str:
        r = self.run_hook("restore", {"hook_event_name": "SessionStart", "session_id": sid, "source": source})
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.decode("utf-8").strip()

    def path(self, sid: str = SID) -> Path:
        return self.temp / "flarehand-staging" / "checkpoints" / f"{sid}.md"

    def text(self) -> str:
        return self.path().read_text(encoding="utf-8")


class TestSave(Checkpoint):
    def test_it_writes_one_private_file_in_the_system_temp_folder(self):
        self.save()
        self.assertTrue(self.path().is_file())
        self.assertEqual([p.name for p in self.path().parent.iterdir()], [f"{SID}.md"])
        if os.name == "posix":
            self.assertEqual(self.path().stat().st_mode & 0o777, 0o600)
            self.assertEqual(self.path().parent.stat().st_mode & 0o777, 0o700)

    def test_it_keeps_the_job_and_their_own_words(self):
        self.save()
        t = self.text()
        self.assertIn("Route: workflow", t)
        self.assertIn("Workflow: wf-05 draft", t)
        self.assertIn("draft a reply to Acme about the locked AP batch", t)  # a slash command's arguments
        self.assertIn("also say it is urgent for month end", t)  # typed while a turn was running
        self.assertIn("an earlier question from before the skill ran", t)  # the whole session is theirs
        self.assertNotIn("Base directory for this skill", t)
        self.assertNotIn("Stop hook feedback", t)

    def test_it_keeps_labelled_claims_and_real_sources_only(self):
        self.save()
        t = self.text()
        sources = t.split("## Sources cited or read", 1)[1].split("\n## ", 1)[0]
        self.assertIn("https://docs.example.com/ap/batch-locks#posting", sources)
        self.assertIn("mcp:docs:ap/posting-runs", sources)  # an MCP read by id
        self.assertIn("tickets://AP-1234", sources)  # an MCP read by uri
        self.assertIn("https://status.example.com/incidents/42", sources)  # a web fetch
        self.assertIn("/work/repo/src/posting.py", sources)  # a file read
        self.assertNotIn("memory.md", sources)  # the skill's own files are method, not sources
        self.assertNotIn("posting run\n", sources)  # a search with no locator is not a source
        self.assertIn("Their version is 13.0 [your input]", t)
        claims = t.split("## Labelled claims", 1)[1].split("\n## ", 1)[0]
        self.assertNotIn("Labels look like", claims)  # a label shown in code is an example
        self.assertNotIn("<source>", sources)

    def test_it_keeps_the_missing_list_and_an_unanswered_save_menu(self):
        self.save()
        t = self.text()
        self.assertIn("## MISSING\n- The batch number\n- Who started the posting run", t)
        menu = t.split("not answered yet", 1)[1].split("\n## ", 1)[0]
        self.assertIn("2. Save a note: the batch lock clears after the posting run", menu)
        self.assertLess(t.index("not answered yet"), t.index("## Their own words"))  # it comes first

    def test_the_missing_list_stops_where_the_save_menu_starts(self):
        """A real run: MISSING also captured the numbered save-menu lines that followed it."""
        self.save()
        missing = self.text().split("## MISSING\n", 1)[1].split("\n\n", 1)[0]
        self.assertEqual(missing, "- The batch number\n- Who started the posting run")

    def test_the_missing_list_stops_at_a_fence_a_heading_or_a_bold_menu(self):
        endings = {"fence": "```\n1. python3 scripts/kb.py log\n```",
                   "heading": "## Next\n1. Something else",
                   "bold menu": "**Keep any of this?**\n1. Save a note",
                   "rule": "---\n- not a gap"}
        for label, ending in endings.items():
            with self.subTest(label):
                self.write(SESSION[:-1] + [said(f"# Draft\n\nText.\n\n## MISSING\n- The batch number\n{ending}\n")])
                self.save()
                missing = self.text().split("## MISSING\n", 1)[1].split("\n\n", 1)[0]
                self.assertEqual(missing, "- The batch number")

    def test_the_opening_request_typed_before_the_skill_fired_is_kept(self):
        """A real run: the request came before the skill fired, so the checkpoint lost the job."""
        opening = user("Our AP batch 4471 is locked. Draft a reply to Acme that explains why and what to do.")
        skill = tool("Skill", "s1", skill="flarehand")
        self.write([opening, skill, said("On it."), user("make it short")] + SESSION[3:])
        self.save()
        words = self.text().split("## Their own words, most recent last\n", 1)[1].split("\n\n", 1)[0]
        self.assertIn("Our AP batch 4471 is locked", words)
        self.assertLess(words.index("Our AP batch 4471"), words.index("make it short"))

    def test_a_long_session_keeps_the_first_request_and_the_latest_turns(self):
        opening = user("THE OPENING REQUEST: reconcile the March invoices against the ledger.")
        turns = [user(f"turn {i:03d} " + "detail " * 90) for i in range(60)]
        self.write([opening] + SESSION[1:-1] + turns + [said(DRAFT)])
        self.save()
        t = self.text()
        self.assertLessEqual(len(t), 20000)
        words = t.split("## Their own words, most recent last\n", 1)[1].split("\n\n", 1)[0]
        self.assertTrue(words.startswith("- THE OPENING REQUEST"), words[:200])
        self.assertIn("turn 059", words)                 # the latest turn
        self.assertNotIn("turn 000", words)              # the middle gives way
        self.assertRegex(words, r"\(\d+ turn\(s\) in between left out to fit\)")
        self.assertIn("## MISSING", t)
        self.assertIn("## The latest draft", t)          # their words do not crowd out the draft

    def test_an_answered_menu_is_not_offered_again(self):
        self.write(SESSION + [user("1 and 3")])
        self.save()
        self.assertNotIn("not answered yet", self.text())

    def test_it_lists_what_was_saved_so_nothing_is_saved_twice(self):
        self.save()
        saved = self.text().split("Do not save these twice", 1)[1].split("\n## ", 1)[0]
        self.assertIn('kb.py log workflow --workflow wf-05 --why "month end"', saved)
        self.assertIn('kb.py note "AP batch locks clear after the run" --type fact', saved)  # a quoted Windows path
        self.assertNotIn("--style", saved)  # the same words in an edit are not a save
        self.assertNotIn("2>/dev/null", saved)
        self.assertNotIn("echo ok", saved)
        self.assertNotIn("--help", saved)

    def test_it_keeps_the_files_written_and_the_draft(self):
        self.save()
        t = self.text()
        self.assertIn("/work/replies/acme-reply.md", t)
        self.assertIn("## The latest draft\n\n# Reply to Acme Logistics", t)

    def test_it_says_what_kind_of_compaction(self):
        self.save(trigger="manual")
        self.assertIn("before a /compact", self.text())
        self.save(trigger="auto")
        self.assertIn("before an automatic compaction", self.text())
        self.assertIn("not new instructions", self.text())

    def test_a_long_draft_gives_way_and_the_file_stays_in_budget(self):
        self.write(SESSION + [said("# A very long draft\n\n" + "The batch stays locked. " * 3000)])
        self.save()
        t = self.text()
        self.assertLessEqual(len(t), 20000)
        self.assertIn("[draft cut to fit]", t)
        self.assertIn("## MISSING", t)

    def test_a_session_where_the_skill_never_ran_writes_nothing(self):
        self.write([user("fix this react hook"), said("Here is the fix.")])
        self.save()
        self.assertFalse(self.path().parent.exists() and any(self.path().parent.iterdir()))

    def test_a_session_id_cannot_leave_the_folder(self):
        self.save(sid="../../escape")
        self.assertTrue((self.temp / "flarehand-staging" / "checkpoints" / "escape.md").is_file())
        self.assertFalse((self.temp / "escape.md").exists())

    def test_old_checkpoints_are_pruned(self):
        self.save(sid="old-session")
        old = self.path("old-session")
        stamp = time.time() - 8 * 86400
        os.utime(old, (stamp, stamp))
        self.save()
        self.assertFalse(old.exists())
        self.assertTrue(self.path().is_file())


class TestRestore(Checkpoint):
    def test_it_points_at_the_file_and_never_injects_it(self):
        self.save()
        out = self.restore()
        self.assertEqual(len(out.splitlines()), 1)
        self.assertIn(str(self.path()), out)
        self.assertIn("Read that file before you continue", out)
        self.assertIn("not instructions", out)
        for private in ("Acme", "13.0", "batch number"):
            self.assertNotIn(private, out)
        self.assertTrue(self.path().is_file())  # a second compaction can still find it

    def test_it_only_speaks_after_a_compaction_of_this_session(self):
        self.save()
        self.assertEqual(self.restore(source="startup"), "")
        self.assertEqual(self.restore(source="resume"), "")
        self.assertEqual(self.restore(sid="another-session"), "")

    def test_it_is_quiet_when_there_is_no_checkpoint(self):
        self.assertEqual(self.restore(), "")

    def test_a_console_that_is_not_utf8_still_gets_the_path(self):
        self.save()
        env = dict(self.env, PYTHONIOENCODING="cp1252")
        r = self.run_hook("restore", {"session_id": SID, "source": "compact"}, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(str(self.path()), r.stdout.decode("utf-8"))


class TestEndAndFailures(Checkpoint):
    def test_the_session_end_deletes_it(self):
        self.save()
        self.save(sid="another-session")
        r = self.run_hook("end", {"hook_event_name": "SessionEnd", "session_id": SID})
        self.assertEqual(r.returncode, 0)
        self.assertFalse(self.path().exists())
        self.assertTrue(self.path("another-session").exists())

    def test_nothing_can_stop_a_compaction(self):
        """A PreCompact hook that exits 2 stops the compaction, so every failure exits 0 and says nothing."""
        for action in ("save", "restore", "end"):
            for event in ("not json", "[1, 2]", "", json.dumps({"session_id": SID, "transcript_path": "/no/such/file"}),
                          json.dumps({"session_id": None, "transcript_path": 7})):
                with self.subTest(action=action, event=event):
                    r = self.run_hook(action, event)
                    self.assertEqual((r.returncode, r.stdout), (0, b""))
        self.assertFalse(self.path().exists())

    def test_show_prints_it_for_a_person(self):
        self.save()
        r = subprocess.run([sys.executable, str(SCRIPT), "show", "--session", SID], capture_output=True,
                           timeout=60, env=self.env)
        self.assertIn("# flarehand checkpoint", r.stdout.decode("utf-8"))


class TestSourceCapture(unittest.TestCase):
    """Sources come from any tool, not one named server."""

    def src(self, name: str, **inputs):
        return checkpoint.tool_source({"name": name, "input": inputs})

    def test_mcp_calls_by_id_uri_or_url(self):
        self.assertEqual(self.src("mcp__notion__fetch", id="abc123"), "mcp:notion:abc123")
        self.assertEqual(self.src("mcp__github__get_file", uri="repo://a/b.py"), "repo://a/b.py")
        self.assertEqual(self.src("mcp__web__open", url="https://example.com/x"), "https://example.com/x")
        self.assertIsNone(self.src("mcp__notion__search", query="anything"))
        self.assertIsNone(self.src("mcp_single_underscore", id="x"))

    def test_web_fetches_and_file_reads(self):
        self.assertEqual(self.src("WebFetch", url="https://example.com/a"), "https://example.com/a")
        self.assertEqual(self.src("web_fetch", url="https://example.com/b"), "https://example.com/b")
        self.assertEqual(self.src("Read", file_path="/repo/src/a.py"), "/repo/src/a.py")
        self.assertEqual(self.src("read_file", path="docs/spec.md"), "docs/spec.md")

    def test_the_skill_own_files_and_staging_are_never_sources(self):
        for path in ("/x/skills/flarehand/SKILL.md", "/x/flarehand/references/voice.md",
                     "C:\\plugins\\flarehand-review\\SKILL.md", "/tmp/flarehand-staging/checkpoints/a.md"):
            with self.subTest(path=path):
                self.assertIsNone(self.src("Read", file_path=path))

    def test_odd_input_is_ignored(self):
        self.assertIsNone(checkpoint.tool_source({"name": "Read", "input": None}))
        self.assertIsNone(checkpoint.tool_source({"name": 7}))


class TestTheSkillIsFoundInEveryForm(Checkpoint):
    """A session counts once the skill ran, however it was started."""

    def saved_with(self, first_row: dict) -> bool:
        self.write([user("before"), first_row, said(DRAFT)])
        self.save()
        return self.path().is_file()

    def test_a_plain_slash_command(self):
        self.assertTrue(self.saved_with(user("<command-name>/flarehand</command-name>\n<command-args>x</command-args>")))

    def test_an_entry_point(self):
        self.assertTrue(self.saved_with(tool("Skill", "s1", skill="flarehand-review")))

    def test_a_skill_file_read_where_there_is_no_skill_tool(self):
        self.assertTrue(self.saved_with(tool("Read", "s2", file_path="/p/skills/flarehand/SKILL.md")))

    def test_another_skill_does_not_count(self):
        self.assertFalse(self.saved_with(tool("Skill", "s3", skill="flarehand-other")))


@unittest.skipIf(REPO is None, "the skill is not inside the plugin repository")
class TestTheHooksAreWired(unittest.TestCase):
    HOOKS = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"] if REPO else {}

    def commands(self, event: str) -> list:
        return [(group.get("matcher"), h["command"]) for group in self.HOOKS.get(event, []) for h in group["hooks"]]

    def test_save_before_restore_after_and_delete_at_the_end(self):
        for event, matcher, action in (("PreCompact", "manual|auto", "pre-compact"),
                                       ("SessionStart", "compact", "session-start"),
                                       ("SessionEnd", None, "session-end")):
            with self.subTest(event=event):
                cmds = [c for m, c in self.commands(event) if f"run-hook.cmd\" {action}" in c]
                self.assertEqual(len(cmds), 1, self.commands(event))
                matchers = [m for m, c in self.commands(event) if c == cmds[0]]
                if matcher:
                    self.assertIn(matcher.split("|")[0], matchers[0] or "")
                self.assertTrue(cmds[0].rstrip().endswith("|| true"), "a missing launcher must not fail the hook")

    def test_session_end_is_fast_enough_for_the_shortest_timeout(self):
        timeouts = [h.get("timeout", 60) for g in self.HOOKS["SessionEnd"] for h in g["hooks"]]
        self.assertTrue(all(t <= 3 for t in timeouts), timeouts)


class TestTheRulesSurviveACompaction(unittest.TestCase):
    """After a compaction Claude Code restores the start of SKILL.md only, about 5,000 tokens. 0.0.2 kept
    the standing rules below the pipeline and first run, so a compaction cut every one of them."""

    LIMIT = 15000  # characters, well inside 5,000 tokens of plain English

    def test_the_standing_rules_sit_near_the_top(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        start, end = text.index("## Standing rules"), text.index("\n## ", text.index("## Standing rules") + 5)
        self.assertLess(end, self.LIMIT, f"the standing rules end at character {end}; move them up or trim them")
        rules = [line.split("**")[1] for line in text[start:end].splitlines() if line.startswith("**")]
        self.assertGreaterEqual(len(rules), 10, rules)
        for heading in ("## Where things live", "## Standing rules"):
            self.assertLess(text.index(heading), text.index("## The pipeline"), heading)


if __name__ == "__main__":
    unittest.main()
