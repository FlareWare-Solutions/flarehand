"""Split from test_scripts.py. Loaded by tests/test_scripts.py, and runnable on its own."""

from __future__ import annotations

import json
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

import kb  # noqa: E402
import recall  # noqa: E402


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / script), *args],
        capture_output=True, text=True, timeout=60,
    )


# ---------------------------------------------------------------- normalising


class TestKnowledgeBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hww-test-"))
        self.root = self.tmp / "memory"
        r = run("kb.py", "init", "--root", str(self.root))
        self.assertEqual(r.returncode, 0, r.stderr)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def kb(self, *args):
        return run("kb.py", "--root", str(self.root), *args)

    def test_init_does_not_touch_the_real_home(self):
        """A test store must never hijack someone's real default."""
        cfg = json.loads((self.root / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(Path(cfg["root"]).resolve(), self.root.resolve())
        pointer = Path.home() / ".flareware" / "flarehand" / "config.json"
        if pointer.is_file():
            real = json.loads(pointer.read_text(encoding="utf-8")).get("root", "")
            self.assertNotEqual(Path(real).resolve(), self.root.resolve())

    def test_note_round_trip(self):
        self.assertEqual(self.kb("note", "Test Concept", "--type", "concept").returncode, 0)
        r = self.kb("get", "test-concept")
        self.assertEqual(r.returncode, 0)
        self.assertIn("permalink: test-concept", r.stdout)

    def test_duplicate_note_is_refused(self):
        self.kb("note", "Test Concept", "--type", "concept")
        self.assertNotEqual(self.kb("note", "Test Concept", "--type", "concept").returncode, 0)

    def test_observation_carries_provenance(self):
        self.kb("note", "Test Concept", "--type", "concept")
        self.kb("observe", "test-concept", "--text", "a fact", "--source", "somewhere")
        body = (self.kb("get", "test-concept")).stdout
        for part in ("[fact] a fact", "source: somewhere", "status: confirmed"):
            self.assertIn(part, body)

    def test_inferences_and_opinions_are_always_suspected(self):
        self.kb("note", "Priya", "--type", "person")
        for category, text in (("inference", "asks for repro steps first"), ("opinion", "not ready to lead the export yet")):
            with self.subTest(category=category):
                r = self.kb("observe", "priya", "--category", category, "--text", text, "--source", "4 sessions")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn(f"[{category}] {text} (source: 4 sessions, on: {kb.today()}, status: suspected)",
                              self.kb("get", "priya").stdout)
                r = self.kb("observe", "priya", "--category", category, "--text", "passed off as seen",
                            "--source", "2 sessions", "--status", "confirmed")
                self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("passed off as seen", self.kb("get", "priya").stdout)

    def test_a_person_note_starts_as_personal_data(self):
        self.kb("note", "Priya", "--type", "person")
        self.kb("note", "Test Concept", "--type", "concept")
        self.assertIn("sensitivity: personal-data", self.kb("get", "priya").stdout)
        self.assertIn("sensitivity: internal", self.kb("get", "test-concept").stdout)

    def test_observation_is_idempotent(self):
        self.kb("note", "Test Concept", "--type", "concept")
        for _ in range(3):
            self.kb("observe", "test-concept", "--text", "a fact", "--source", "somewhere")
        self.assertEqual((self.kb("get", "test-concept")).stdout.count("[fact] a fact"), 1)

    def test_supersede_keeps_the_old_fact(self):
        self.kb("note", "Test Concept", "--type", "concept")
        self.kb("observe", "test-concept", "--text", "old truth", "--source", "s")
        self.kb("supersede", "test-concept", "--match", "old truth")
        body = (self.kb("get", "test-concept")).stdout
        self.assertIn("old truth", body)
        self.assertIn("until:", body)

    def test_grouping_waits_for_three_then_files_everything(self):
        for i in range(2):
            self.kb("note", f"Concept {i}", "--type", "concept")
        self.assertTrue(list((self.root / "notes").glob("*.md")), "two notes should stay loose")
        self.kb("note", "Concept 3", "--type", "concept")
        self.assertEqual(self.kb("organize", "--apply").returncode, 0)
        self.assertFalse(list((self.root / "notes").glob("*.md")), "notes/ root should be empty now")
        self.assertEqual(len(list((self.root / "notes" / "concepts").glob("*.md"))), 3)

    def test_links_survive_a_move(self):
        self.kb("note", "Alpha", "--type", "concept")
        self.kb("note", "Beta", "--type", "concept")
        self.kb("link", "alpha", "relates_to", "beta")
        self.kb("note", "Gamma", "--type", "concept")
        self.kb("organize", "--apply")
        self.assertEqual(self.kb("lint").returncode, 0)
        self.assertIn("[[beta|Beta]]", (self.kb("get", "alpha")).stdout)

    def test_lint_is_clean_on_a_healthy_store(self):
        self.kb("note", "Alpha", "--type", "concept")
        r = self.kb("lint")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("No problems found", r.stdout)

    def test_flags_work_before_and_after_the_subcommand(self):
        self.kb("note", "Alpha", "--type", "concept")
        a = run("kb.py", "--root", str(self.root), "--json", "stats")
        b = run("kb.py", "stats", "--root", str(self.root), "--json")
        self.assertEqual(a.returncode, 0)
        self.assertEqual(b.returncode, 0)
        self.assertEqual(json.loads(a.stdout)["notes"], json.loads(b.stdout)["notes"])


# ---------------------------------------------------------------- the cache


class TestAnswerCache(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hww-ans-"))
        self.root = self.tmp / "memory"
        run("kb.py", "init", "--root", str(self.root))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ans(self, *args):
        return run("answers.py", "--root", str(self.root), *args)

    def test_an_answer_without_sources_is_refused(self):
        r = self.ans("write", "how do I set up the deploy key", "--body", "just wing it")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("sources", r.stderr)

    def recall(self, q):
        return json.loads(run("recall.py", q, "--root", str(self.root)).stdout)

    def test_exact_wording_replays_word_for_word(self):
        body = "Connect to the build server first.\n\nThen run the add command."
        self.ans("write", "how do I set up the deploy key", "--source", "https://docs.example.com/setup#keys", "--body", body)
        self.ans("approve", "how do I set up the deploy key")
        self.assertEqual(self.recall("How do I setup the deploy key?")["verdict"], "replay")
        self.assertEqual(self.ans("get", "HOW DO I SET UP THE DEPLOY KEY.").stdout.strip(), body.strip())

    def test_look_alike_never_replays_it_asks(self):
        self.ans("write", "set up the deploy key in claude code", "--source", "https://docs.example.com/setup#keys", "--body", "code steps")
        self.ans("approve", "set up the deploy key in claude code")
        out = self.recall("set up the deploy key in claude desktop")
        self.assertEqual(out["verdict"], "confirm")
        self.assertEqual(out["suggestions"][0]["words_only_in_yours"], ["desktop"])
        self.assertNotEqual(self.ans("get", "set up the deploy key in claude desktop").returncode, 0)

    def test_confirmed_alias_then_replays(self):
        self.ans("write", "how do I set up the deploy key", "--source", "https://docs.example.com/setup#keys", "--body", "steps")
        self.ans("approve", "how do I set up the deploy key")
        q = "what are the steps to configure the deploy key"
        self.assertNotEqual(self.recall(q)["verdict"], "replay")
        self.assertEqual(self.ans("alias", q, "--to", "how do I set up the deploy key").returncode, 0)
        self.assertEqual(self.recall(q)["verdict"], "replay")

    def test_alias_cannot_take_another_answers_wording(self):
        self.ans("write", "set up jira", "--source", "https://docs.example.com/jira#a", "--body", "jira")
        self.ans("write", "set up github", "--source", "https://docs.example.com/github#a", "--body", "github")
        r = self.ans("alias", "set up jira", "--to", "set up github")
        self.assertNotEqual(r.returncode, 0)

    def test_a_local_path_cannot_be_a_saved_source(self):
        """A saved answer replays word for word, so every source has to be checkable later.
        A path is only true for this checkout on this machine."""
        r = self.ans("write", "how does the registry work", "--source", "src/registry.rs:3-8",
                     "--body", "It maps names.")
        self.assertEqual(r.returncode, 1)
        self.assertIn("evidence.py add", r.stderr)

    def test_citing_the_skill_itself_is_refused(self):
        r = self.ans("write", "q", "--source", "flarehand references/memory.md", "--body", "x")
        self.assertNotEqual(r.returncode, 0)
        r = self.ans("write", "q2", "--source", "https://docs.example.com/setup",
                     "--body", "Claim [verified: flarehand references/memory.md].")
        self.assertNotEqual(r.returncode, 0)

    def test_recall_says_replay_only_after_approval(self):
        self.ans("write", "how do I set up the deploy key", "--source", "https://docs.example.com/setup#keys", "--body", "text")
        r = run("recall.py", "how do I set up the deploy key", "--root", str(self.root))
        self.assertEqual(json.loads(r.stdout)["verdict"], "recheck")
        self.ans("approve", "how do I set up the deploy key")
        r = run("recall.py", "how do I set up the deploy key", "--root", str(self.root))
        self.assertEqual(json.loads(r.stdout)["verdict"], "replay")

    def test_a_hand_edit_is_detected(self):
        self.ans("write", "how do I set up the deploy key", "--source", "https://docs.example.com/setup#keys", "--body", "text")
        self.ans("approve", "how do I set up the deploy key")
        path = self.root / "answers" / f"{recall.key_for('how do I set up the deploy key')}.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nsomeone edited this\n", encoding="utf-8")
        r = run("recall.py", "how do I set up the deploy key", "--root", str(self.root))
        self.assertEqual(json.loads(r.stdout)["verdict"], "recheck")
        self.assertNotEqual(self.ans("verify").returncode, 0)

    def test_invalidating_forces_a_fresh_answer(self):
        self.ans("write", "how do I set up the deploy key", "--source", "https://docs.example.com/setup#keys", "--body", "text")
        self.ans("approve", "how do I set up the deploy key")
        self.ans("invalidate", "how do I set up the deploy key", "--why", "the command changed in the new patch")
        r = run("recall.py", "how do I set up the deploy key", "--root", str(self.root))
        out = json.loads(r.stdout)
        self.assertEqual(out["verdict"], "stale")
        self.assertIn("command changed", out["why"])


# ---------------------------------------------------------------- evidence


class TestKnowledgeBaseSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hww-safe-"))
        self.root = self.tmp / "a" / "b" / "memory"
        run("kb.py", "init", "--root", str(self.root))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def kb(self, *args):
        return run("kb.py", "--root", str(self.root), *args)

    def outside(self):
        return [p for p in self.tmp.rglob("*.md") if self.root not in p.parents]

    def test_a_permalink_cannot_write_outside_the_store(self):
        self.kb("note", "Escape", "--type", "concept", "--permalink", "../../escaped")
        self.assertEqual(self.outside(), [])

    def test_a_crafted_permalink_in_frontmatter_cannot_move_a_file_out(self):
        for i in range(2):
            self.kb("note", f"Concept {i}", "--type", "concept")
        (self.root / "notes" / "planted.md").write_text(
            "---\ntitle: P\ntype: concept\npermalink: ../../../../planted\nstatus: active\n"
            "created: 2026-01-01\nupdated: 2026-01-01\n---\n\nx\n", encoding="utf-8")
        self.kb("organize", "--apply")
        self.assertEqual(self.outside(), [])

    def test_a_byte_order_mark_does_not_corrupt_a_note(self):
        self.kb("note", "Bom", "--type", "concept")
        path = next(self.root.rglob("bom.md"))
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        self.kb("observe", "bom", "--text", "fact", "--source", "s")
        self.assertEqual(path.read_text(encoding="utf-8").count("\n---\n") + 1, 2)

    def test_one_badly_encoded_note_does_not_break_every_command(self):
        self.kb("note", "Good", "--type", "concept")
        (self.root / "notes" / "bad.md").write_bytes(b"---\ntitle: caf\xe9\n---\n\nx\n")
        r = self.kb("stats")
        self.assertEqual(r.returncode, 0)
        self.assertIn("not saved as UTF-8", r.stderr)

    def test_a_damaged_config_is_repaired_by_init(self):
        (self.root / "config.json").write_text("{not json", encoding="utf-8")
        self.assertEqual(run("kb.py", "init", "--root", str(self.root)).returncode, 0)
        json.loads((self.root / "config.json").read_text(encoding="utf-8"))

    def test_code_blocks_inside_a_note_are_never_edited(self):
        self.kb("note", "Fence", "--type", "concept", "--body", "```\n# not a heading\nline\n```")
        self.kb("observe", "fence", "--text", "x", "--source", "s")
        self.assertIn("# not a heading\nline", next(self.root.rglob("fence.md")).read_text(encoding="utf-8"))

    def test_frontmatter_round_trip_keeps_lists_and_awkward_values(self):
        meta = {"title": "A: tricky, title", "tags": ["one", "two, three"], "empty": [], "quote": 'say "hi"'}
        back, _ = kb.parse_frontmatter(kb.dump_frontmatter(meta) + "\n\nbody")
        self.assertEqual(back["title"], "A: tricky, title")
        self.assertEqual(back["tags"], ["one", "two, three"])
        self.assertEqual(back["empty"], [])

    def test_grouping_threshold_is_exactly_three(self):
        self.assertEqual(kb.GROUP_THRESHOLD, 3)
        for i in range(2):
            self.kb("note", f"C{i}", "--type", "concept")
        self.kb("organize", "--apply")
        self.assertFalse((self.root / "notes" / "concepts").exists(), "two notes must not form a group")

    def test_link_goes_under_relations_not_observations(self):
        self.kb("note", "Alpha", "--type", "concept")
        self.kb("note", "Beta", "--type", "concept")
        self.kb("link", "alpha", "relates_to", "beta")
        body = next(self.root.rglob("alpha.md")).read_text(encoding="utf-8")
        self.assertGreater(body.index("[[beta|Beta]]"), body.index("## Relations"))

    def test_windows_device_names_and_non_latin_titles_get_safe_distinct_names(self):
        self.assertEqual(kb.slugify("CON"), "con-note")
        self.assertNotEqual(kb.slugify("日本語のノート"), kb.slugify("Русская заметка"))
        self.assertNotIn("/", kb.slugify("../../x"))


class TestKnowledgeBaseFreshness(unittest.TestCase):
    """The notes are the truth. The graph follows them, and old notes say they are old."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hww-fresh-"))
        self.root = self.tmp / "memory"
        self.assertEqual(run("kb.py", "init", "--root", str(self.root)).returncode, 0)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def kb(self, *args):
        return run("kb.py", "--root", str(self.root), *args)

    def note_path(self, permalink):
        return next(self.root.glob(f"notes/**/{permalink}.md"))

    def test_a_hand_added_link_reaches_the_graph_on_the_next_read(self):
        self.kb("note", "Alpha", "--permalink", "alpha", "--body", "first")
        self.kb("note", "Beta", "--permalink", "beta", "--body", "second")
        path = self.note_path("alpha")
        path.write_text(path.read_text(encoding="utf-8") + "\nSee [[beta|Beta]].\n", encoding="utf-8")
        r = self.kb("search", "alpha")
        self.assertIn("changed outside the skill", r.stderr)
        graph = json.loads((self.root / ".index" / "graph.json").read_text(encoding="utf-8"))
        edges = json.dumps(graph)
        self.assertIn("beta", edges[edges.find("alpha"):])

    def test_writes_through_the_skill_never_claim_an_outside_change(self):
        self.kb("note", "Alpha", "--permalink", "alpha", "--body", "first", "--source", "https://docs.example.com/approvals")
        self.kb("observe", "alpha", "--text", "It routes to a second approver", "--source", "https://docs.example.com/approvals")
        self.kb("verified", "alpha")
        for cmd in (("search", "alpha"), ("get", "alpha"), ("stats",)):
            self.assertNotIn("changed outside the skill", self.kb(*cmd).stderr, cmd)

    def test_a_knowledge_base_from_before_the_check_upgrades_quietly(self):
        self.kb("note", "Alpha", "--permalink", "alpha", "--body", "first")
        graph = self.root / ".index" / "graph.json"
        data = json.loads(graph.read_text(encoding="utf-8"))
        data.pop("fingerprint", None)
        graph.write_text(json.dumps(data), encoding="utf-8")
        r = self.kb("search", "alpha")
        self.assertNotIn("changed outside the skill", r.stderr)
        self.assertIn("fingerprint", json.loads(graph.read_text(encoding="utf-8")))

    def test_an_old_note_is_due_and_says_why(self):
        self.kb("note", "Alpha", "--permalink", "alpha", "--body", "first", "--source", "https://docs.example.com/approvals")
        path = self.note_path("alpha")
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"review_by: .*", "review_by: 2025-01-01", text)
        text = re.sub(r"verified_on: .*", "verified_on: 2025-01-01", text)
        text += "\n- [inference] Prefers short packets (source: 3 sessions, on: 2025-01-01, status: suspected)\n"
        path.write_text(text, encoding="utf-8")
        out = self.kb("freshness").stdout
        self.assertIn("past its review date", out)
        self.assertIn("sources should be re-checked", out)
        self.assertIn("unconfirmed inference", out)
        got = self.kb("get", "alpha").stdout
        self.assertTrue(got.startswith("<!-- freshness:"), got[:80])

    def test_verified_clears_the_source_and_review_items(self):
        self.kb("note", "Alpha", "--permalink", "alpha", "--body", "first", "--source", "https://docs.example.com/approvals")
        path = self.note_path("alpha")
        text = re.sub(r"review_by: .*", "review_by: 2025-01-01", path.read_text(encoding="utf-8"))
        path.write_text(re.sub(r"verified_on: .*", "verified_on: 2025-01-01", text), encoding="utf-8")
        self.assertEqual(self.kb("verified", "alpha").returncode, 0)
        meta, _ = kb.parse_frontmatter(path.read_text(encoding="utf-8"))
        self.assertEqual(str(meta["verified_on"]), kb.today())
        self.assertGreater(str(meta["review_by"]), kb.today())
        self.assertNotIn("alpha", self.kb("freshness").stdout.split("due", 1)[-1] if "due" in self.kb("freshness").stdout else "")

    def test_if_due_runs_once_then_stays_quiet_for_a_week(self):
        self.kb("note", "Alpha", "--permalink", "alpha", "--body", "first")
        first = self.kb("freshness", "--if-due")
        second = self.kb("freshness", "--if-due")
        self.assertEqual(first.returncode, 0)
        self.assertEqual(second.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
