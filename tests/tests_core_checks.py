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

import kb  # noqa: E402
import check_output  # noqa: E402


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / script), *args],
        capture_output=True, text=True, timeout=60,
    )


# ---------------------------------------------------------------- normalising


class TestStyleChecker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = check_output.load_style_words(SKILL / "assets" / "style-words.tsv")

    def findings(self, text: str, rule: str) -> list:
        masked = check_output.mask(text)
        raw = text.split("\n")
        return [f for f in check_output.check_style(masked, raw, self.rules) if f["rule"] == rule]

    def test_em_dash_is_an_error(self):
        self.assertTrue(self.findings("A sentence with an em dash — here.", "em-dash"))

    def test_banned_word_is_caught(self):
        self.assertTrue(self.findings("We should utilize the tool.", "word"))

    def test_profiles_plain_none_and_the_old_name(self):
        text = "We should utilize it — on 3/4/2026, and not without care.\n"
        f = Path(tempfile.mktemp(suffix=".md"))
        f.write_text(text, encoding="utf-8")
        try:
            got = {}
            for profile in ("plain", "natural", "none", "google"):
                r = run("check_output.py", "--style", "--profile", profile, "--json", str(f))
                got[profile] = sorted({x["rule"] for x in json.loads(r.stdout)["findings"]})
        finally:
            f.unlink()
        self.assertEqual(got["plain"], got["natural"])
        self.assertIn("em-dash", got["plain"])
        self.assertEqual(got["none"], ["date", "double-negative"])
        self.assertTrue(set(got["plain"]) <= set(got["google"]))

    def test_long_sentence_is_caught(self):
        long = "This " + "word " * 30 + "ends."
        self.assertTrue(self.findings(long, "long-sentence"))

    def test_code_blocks_are_ignored(self):
        text = "```\nutilize — prior to\n```\n"
        self.assertFalse(self.findings(text, "word"))
        self.assertFalse(self.findings(text, "em-dash"))

    def test_frontmatter_is_ignored(self):
        text = "---\ndescription: utilize this — thing\n---\n\nClean body.\n"
        self.assertFalse(self.findings(text, "word"))

    def test_inline_code_is_ignored(self):
        self.assertFalse(self.findings("Say `use` not `utilize` here.", "word"))

    def test_list_items_count_separately(self):
        text = "- one two three\n- four five six\n- seven eight nine\n"
        self.assertFalse(self.findings(text, "long-sentence"))

    def test_the_skill_passes_its_own_rules(self):
        targets = [SKILL / "SKILL.md"] + sorted((SKILL / "references").glob("*.md"))
        r = run("check_output.py", "--style", *[str(p) for p in targets])
        self.assertEqual(r.returncode, 0, f"the skill breaks its own writing rules:\n{r.stdout}")


# ---------------------------------------------------------------- citations


class TestCitations(unittest.TestCase):
    def test_good_shapes_pass(self):
        good = ("A [verified: git:abc123:docs/x.md] and [verified: TOOL-9059] "
                "and [verified: https://example.com/x] and [verified: mcp:tracker:ABC-1].")
        self.assertFalse([f for f in check_output.check_citations(good.split("\n"), Path("."))
                          if f["severity"] == "error"])

    def test_nonsense_source_fails(self):
        self.assertTrue(check_output.check_citations(["[verified: not a real id]"], Path(".")))

    def test_missing_snapshot_fails(self):
        self.assertTrue(check_output.check_citations(["[verified: evidence/abcdef123456.txt]"], Path(".")))


# ---------------------------------------------------------------- redaction


class TestCheckerRegressions(unittest.TestCase):
    def style(self, text):
        f = Path(tempfile.mktemp(suffix=".md"))
        f.write_text(text, encoding="utf-8")
        try:
            return json.loads(run("check_output.py", "--style", "--json", str(f)).stdout)["findings"]
        finally:
            f.unlink()

    def citations(self, text, root=None):
        f = Path(tempfile.mktemp(suffix=".md"))
        f.write_text(text, encoding="utf-8")
        try:
            args = ["check_output.py", "--citations", "--json", str(f)]
            if root:
                args += ["--root", str(root)]
            return json.loads(run(*args).stdout)["findings"]
        finally:
            f.unlink()

    LONG = " ".join(["word"] * 14)

    def long_hits(self, text):
        return [x for x in self.style(text) if x["rule"] == "long-sentence"]

    def test_long_sentence_cannot_hide_behind_an_abbreviation(self):
        self.assertTrue(self.long_hits(f"This {self.LONG} e.g. {self.LONG} ends.\n"))

    def test_a_word_ending_in_an_abbreviation_still_ends_a_sentence(self):
        """"ms." inside "teams." once swallowed a real sentence end."""
        self.assertFalse(self.long_hits("The docs hold little for many teams. " + " ".join(["word"] * 20) + ".\n"))

    def test_indented_continuation_line_is_still_checked(self):
        self.assertTrue(self.long_hits(f"This {self.LONG}\n    {self.LONG} ends.\n"))

    def test_table_cell_sentences_are_checked(self):
        self.assertTrue(self.long_hits(f"| a | b |\n|---|---|\n| x | This {self.LONG} {self.LONG} ends. |\n"))

    def test_multi_line_html_comment_is_not_prose(self):
        self.assertFalse(self.style("<!-- spans\nlines and would utilize — words -->\n\nShort.\n"))

    def test_a_repository_path_with_a_github_line_range_is_accepted(self):
        self.assertFalse([f for f in self.citations("Claim [verified: README.md#L1-L5].\n")
                          if f["severity"] == "error"])

    def test_url_and_jira_key_on_one_line_both_parse(self):
        self.assertFalse(self.citations("A [verified: https://example.com/p] and [verified: TOOL-9059].\n"))

    def test_citing_the_skill_itself_is_an_error(self):
        rules = [x["rule"] for x in self.citations("A [verified: flarehand references/evidence.md].\n")]
        self.assertIn("citation-self", rules)

    def test_another_repositorys_references_folder_is_not_self_citation(self):
        """Many repositories have a references/ folder. A URL or a git: revision names a page in
        some other place, so its path alone proves nothing."""
        for src in ("https://github.com/acme/tools/blob/main/skills/sql/references/18-check.md",
                    "git:4f2a9c1:references/house-style.md", "https://example.com/flarehand-notes/SKILL.md"):
            with self.subTest(src=src):
                self.assertNotIn("citation-self", [x["rule"] for x in self.citations(f"A claim [verified: {src}].\n")])

    def test_this_skills_own_folder_is_self_citation_even_as_a_url(self):
        src = "https://github.com/acme/flarehand/blob/main/skills/flarehand/references/voice.md"
        self.assertIn("citation-self", [x["rule"] for x in self.citations(f"A [verified: {src}].\n")])

    def test_every_shipped_template_source_is_citable(self):
        """A team source the skill ships must pass its own citation check."""
        for path in sorted((SKILL / "assets" / "templates").glob("*.md")):
            meta, _ = kb.parse_frontmatter(path.read_text(encoding="utf-8"))
            for src in meta.get("team_sources") or []:
                with self.subTest(template=path.name, src=src):
                    self.assertFalse(self.citations(f"A claim [verified: {src}].\n"), src)

    def test_a_snapshot_in_the_knowledge_base_is_found(self):
        tmp = Path(tempfile.mkdtemp(prefix="hww-cite-"))
        try:
            root = tmp / "memory"
            run("kb.py", "init", "--root", str(root))
            h = json.loads(run("evidence.py", "--root", str(root), "add", "--text", "kept text",
                               "--source", "s", "--keep", "--json").stdout)["hash"]
            self.assertFalse(self.citations(f"A [verified: evidence/{h}.txt].\n", root))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- knowledge base safety


if __name__ == "__main__":
    unittest.main(verbosity=2)
