#!/usr/bin/env python3
"""tests_site.py - the landing page in site/index.html says only what the repository backs up.
No model, no network, a couple of seconds. Loaded by tests/test_scripts.py, and run on its own
by the Pages workflow before every deploy.

The page repeats facts that move with each release: the counts of templates and workflows, the
eval scores, the install commands. Each one is checked against the file it comes from, so a
release that changes a number fails here until the page changes with it. The page also holds
itself to the house style, loads nothing from other sites, and gives every AI tool the same card.

Run: python3 tests/tests_site.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "flarehand"
PAGE_PATH = ROOT / "site" / "index.html"
PAGE = PAGE_PATH.read_text(encoding="utf-8")
PRIVACY_PATH = ROOT / "site" / "privacy" / "index.html"
PRIVACY = PRIVACY_PATH.read_text(encoding="utf-8")
# Every page on the site, so the hygiene checks cover each one.
PAGES = {PAGE_PATH: PAGE, PRIVACY_PATH: PRIVACY}
README = (ROOT / "README.md").read_text(encoding="utf-8")
EVALS = (ROOT / "docs" / "evals.md").read_text(encoding="utf-8")
INSTALL = (ROOT / "docs" / "install.md").read_text(encoding="utf-8")
REPO_URL = "https://github.com/FlareWare-Solutions/flarehand"

# The chart's plain-language labels, and the eval case each one reports.
CHART_CASES = {
    "Keeping a legal question to the facts": "legal-question-no-conclusion",
    "Doing the work first on a first run": "first-run-does-the-work-first",
    "Stress-testing a plan": "grill-entry-point-fires",
    "Not inventing documentation links": "no-fabricated-doc-links",
}

INLINE = {"a", "b", "strong", "em", "q", "i", "mark", "wbr", "br", "abbr", "code"}
INLINE_SPAN_CLASSES = {"hl", "tag", "flare-text", "default"}
SKIP = {"head", "script", "style", "svg", "pre", "code"}


class _Page(HTMLParser):
    """Reads the page into prose paragraphs, commands, links and tool cards."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool, bool]] = []  # (tag, is_skipped, is_block)
        self.paragraphs: list[str] = []
        self.buffer: list[str] = []
        self.commands: list[str] = []
        self.code: list[str] | None = None
        self.links: list[str] = []
        self.loads: list[str] = []
        self.cards: list[dict] = []
        self.card_depth = 0
        self.heading: list[str] | None = None
        self.bars: list[tuple[str, str, str]] = []

    def _skipping(self) -> bool:
        return any(skip for _, skip, _ in self.stack)

    def _flush(self) -> None:
        text = " ".join("".join(self.buffer).split())
        if text:
            self.paragraphs.append(text)
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set((a.get("class") or "").split())
        if tag in ("img", "script", "iframe", "source", "video", "audio") and a.get("src"):
            self.loads.append(a["src"])
        if tag == "link" and "stylesheet" in (a.get("rel") or ""):
            self.loads.append(a.get("href", ""))
        if tag == "link" and "icon" in (a.get("rel") or "") and not a.get("href", "").startswith("data:"):
            self.loads.append(a.get("href", ""))
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag == "article" and "tool" in classes:
            self.cards.append({"name": "", "commands": [], "then": 0, "more": 0})
            self.card_depth = len(self.stack) + 1
        if self.cards and self.card_depth and len(self.stack) >= self.card_depth:
            card = self.cards[-1]
            card["then"] += "then" in classes
            card["more"] += tag == "a" and "more" in classes
        if tag == "h3" and self.card_depth and len(self.stack) == self.card_depth:
            self.heading = []
        if tag == "span" and "bar" in classes:
            self.bars.append((a.get("style", ""), a.get("title", ""), " ".join(classes)))
        if tag == "code" and not self._skipping():
            self.code = []
        if tag in ("wbr", "br", "meta", "link", "img", "input", "use", "path", "stop"):
            return
        skip = tag in SKIP or "note-ref" in classes
        inline = tag in INLINE or (tag == "span" and not a.get("role") and (not classes or classes & INLINE_SPAN_CLASSES))
        if not inline and not self._skipping():
            self._flush()
        self.stack.append((tag, skip, not inline))

    def handle_endtag(self, tag):
        if tag in ("wbr", "br"):
            return
        if tag == "code" and self.code is not None:
            command = "".join(self.code).strip()
            self.commands.append(command)
            if self.card_depth and len(self.stack) > self.card_depth:
                self.cards[-1]["commands"].append(command)
            self.code = None
        if tag == "h3" and self.heading is not None:
            self.cards[-1]["name"] = "".join(self.heading).strip()
            self.heading = None
        block = False
        while self.stack:
            open_tag, _, block = self.stack.pop()
            if open_tag == tag:
                break
        if tag == "article" and self.card_depth and len(self.stack) < self.card_depth:
            self.card_depth = 0
        if block and not self._skipping():
            self._flush()

    def handle_data(self, data):
        if self.code is not None:
            self.code.append(data)
        if self.heading is not None:
            self.heading.append(data)
        if not self._skipping():
            self.buffer.append(data)


def read_page(text: str = PAGE) -> _Page:
    parser = _Page()
    parser.feed(text)
    parser.close()
    return parser


def github_slug(heading: str) -> str:
    """The anchor GitHub gives a Markdown heading."""
    text = re.sub(r"[`*_]", "", heading.strip().lower())
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


class SiteFacts(unittest.TestCase):
    """Every number on the page comes from the repository, and still matches it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.page = read_page()
        cls.text = "\n".join(cls.page.paragraphs)

    def test_template_and_workflow_counts(self) -> None:
        templates = [p for p in (SKILL / "assets" / "templates").glob("*.md") if not p.name.startswith("wf-")]
        workflows = [ln for ln in (SKILL / "assets" / "workflows.tsv").read_text(encoding="utf-8").splitlines()
                     if ln.startswith("wf-")]
        self.assertIn(f"{len(templates)} templates", self.text, "the page's template count matches assets/templates")
        self.assertIn(f"{len(workflows)} workflows", self.text, "the page's workflow count matches workflows.tsv")
        self.assertIn(f"{len(templates)} templates", README)
        self.assertIn(f"{len(workflows)} workflows", README)

    def test_eval_headline_numbers(self) -> None:
        cases = re.search(r"There are (\d+) cases", EVALS).group(1)
        row = re.search(r"Mean score, all \d+ cases \| ([\d.]+) \| ([\d.]+) \|", EVALS)
        near_miss = re.search(r"Fired on a near-miss request \| 0 of (\d+) runs", EVALS).group(1)
        self.assertIn(f"We ran {cases} realistic work cases", self.text)
        self.assertIn(f"{row.group(1)}\nAverage score with flarehand", self.text)
        self.assertIn(f"{row.group(2)}\nAverage score without it", self.text)
        self.assertIn(f"{near_miss} of {near_miss}\nRuns where it stayed out of the way", self.text)

    def test_chart_matches_the_eval_results(self) -> None:
        labels = [p for p in self.page.paragraphs if p in CHART_CASES]
        self.assertEqual(sorted(labels), sorted(CHART_CASES), "the chart shows exactly the mapped cases")
        bars = self.page.bars
        self.assertEqual(len(bars), 2 * len(CHART_CASES))
        for i, label in enumerate(labels):
            (with_style, with_title, _), (without_style, without_title, _) = bars[2 * i], bars[2 * i + 1]
            with_v = re.search(r"--v:\s*([\d.]+)", with_style).group(1)
            without_v = re.search(r"--v:\s*([\d.]+)", without_style).group(1)
            self.assertTrue(with_title.endswith(with_v) and without_title.endswith(without_v),
                            f"{label}: the bar length and its label agree")
            self.assertIn(f"`{CHART_CASES[label]}` {with_v} against {without_v}", EVALS,
                          f"{label}: docs/evals.md reports the same scores")

    def test_unit_test_count_still_holds(self) -> None:
        count = sum(len(re.findall(r"^\s*def test_", p.read_text(encoding="utf-8"), re.MULTILINE))
                    for p in (ROOT / "tests").glob("*.py"))
        self.assertIn("over 800 unit tests", self.text)
        self.assertGreater(count, 800, "the page says over 800 unit tests")

    def test_python_requirement_matches_the_readme(self) -> None:
        version = re.search(r"Python (3\.\d+) or later", README).group(1)
        self.assertIn(f"You need Python {version} or later", self.text)


class SiteInstall(unittest.TestCase):
    """Install commands are the documented ones, and no tool is favoured."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.page = read_page()

    def test_every_command_is_in_the_install_guide(self) -> None:
        self.assertTrue(self.page.commands)
        for command in self.page.commands:
            if command.startswith(".flarehand"):
                continue
            self.assertIn(command, INSTALL, f"docs/install.md documents `{command}`")

    def test_every_tool_gets_the_same_card(self) -> None:
        cards = self.page.cards
        names = [c["name"] for c in cards]
        self.assertEqual(names[-1], "Other agents")
        self.assertEqual(names[:-1], sorted(names[:-1], key=str.lower), "named tools are in A to Z order")
        for card in cards:
            self.assertGreaterEqual(len(card["commands"]), 1, f"{card['name']} has a command")
            self.assertEqual((card["then"], card["more"]), (1, 1), f"{card['name']} has one next step and one link")

    def test_works_with_line_names_the_same_tools(self) -> None:
        line = next(p for p in self.page.paragraphs if p.startswith("Works with"))
        named = [c["name"] for c in self.page.cards[:-1]]
        positions = [line.find(name) for name in named]
        self.assertTrue(all(p >= 0 for p in positions), f"the hero names every tool: {named}")
        self.assertEqual(positions, sorted(positions), "in the same order as the cards")


class SiteHygiene(unittest.TestCase):
    """Every page keeps the house style and the privacy promise it makes."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pages = {path: (text, read_page(text)) for path, text in PAGES.items()}

    def test_house_style(self) -> None:
        for path, (text, page) in self.pages.items():
            with self.subTest(page=path.relative_to(ROOT).as_posix()):
                self.assertNotIn("\u2014", text, "no em dashes anywhere in the page")
                with tempfile.TemporaryDirectory() as tmp:
                    prose = Path(tmp) / "site-text.md"
                    prose.write_text("\n\n".join(page.paragraphs) + "\n", encoding="utf-8")
                    r = subprocess.run([sys.executable, str(SKILL / "scripts" / "check_output.py"), "--style",
                                        "--json", "--max", "500", str(prose)], capture_output=True, text=True,
                                       timeout=60)
                findings = json.loads(r.stdout)
                errors = [f for f in findings.get("findings", findings.get("issues", []))
                          if f.get("severity") == "error"]
                self.assertEqual(errors, [], "the page text passes check_output.py --style")

    def test_nothing_loads_from_another_site(self) -> None:
        for path, (text, page) in self.pages.items():
            with self.subTest(page=path.relative_to(ROOT).as_posix()):
                self.assertEqual(page.loads, [], "no external scripts, styles, images or fonts")
                css = "".join(re.findall(r"<style>(.*?)</style>", text, re.DOTALL))
                self.assertNotIn("@import", css)
                for url in re.findall(r"url\(([^)]*)\)", css):
                    self.assertTrue(url.strip("'\" ").startswith(("#", "data:")), f"CSS url({url}) stays on the page")

    def test_repository_links_resolve(self) -> None:
        for path, (_, page) in self.pages.items():
            for href in page.links:
                m = re.match(re.escape(REPO_URL) + r"/(?:blob|tree)/main/([^#]+)(?:#(.+))?$", href)
                if not m:
                    continue
                target = ROOT / m.group(1)
                self.assertTrue(target.exists(), f"{path.name}: {href}: {m.group(1)} exists")
                if m.group(2):
                    headings = [ln.lstrip("#").strip() for ln in target.read_text(encoding="utf-8").splitlines()
                                if ln.startswith("#")]
                    self.assertIn(m.group(2), {github_slug(h) for h in headings}, f"{href}: the anchor exists")

    def test_links_between_pages_resolve(self) -> None:
        for path, (_, page) in self.pages.items():
            for href in page.links:
                if href.startswith(("http:", "https:", "#", "data:", "mailto:")):
                    continue
                target = (path.parent / href.split("#")[0]).resolve()
                if href.endswith("/") or target.is_dir():
                    target = target / "index.html"
                self.assertTrue(target.is_file(), f"{path.relative_to(ROOT).as_posix()}: {href} is a page on the site")

    def test_in_page_anchors_exist(self) -> None:
        for path, (text, page) in self.pages.items():
            ids = set(re.findall(r'\bid="([^"]+)"', text))
            for href in page.links:
                if href.startswith("#"):
                    self.assertIn(href[1:], ids, f"{path.name}: {href} points at an element on the page")


class SiteAddress(unittest.TestCase):
    """The page, the README and every manifest agree on where the website lives."""

    def test_one_address_everywhere(self) -> None:
        canonical = re.search(r'<link rel="canonical" href="([^"]+)">', PAGE).group(1)
        self.assertTrue(canonical.startswith("https://") and canonical.endswith("/"), canonical)
        self.assertIn(f'<meta property="og:url" content="{canonical}">', PAGE)
        site = canonical.rstrip("/")
        self.assertIn(f"({site})", README, "the README links to the website")
        manifests = {
            ".claude-plugin/plugin.json": lambda d: [d["homepage"]],
            ".claude-plugin/marketplace.json": lambda d: [p["homepage"] for p in d["plugins"]],
            ".codex-plugin/plugin.json": lambda d: [d["homepage"], d["interface"]["websiteURL"]],
            ".cursor-plugin/plugin.json": lambda d: [d["homepage"]],
        }
        for rel, read in manifests.items():
            data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
            for value in read(data):
                self.assertEqual(value, site, f"{rel} points at the website")

    def test_directory_listing_links(self) -> None:
        """The Claude plugin directory shows these four links on the listing."""
        site = re.search(r'<link rel="canonical" href="([^"]+)">', PAGE).group(1)
        privacy = re.search(r'<link rel="canonical" href="([^"]+)">', PRIVACY).group(1)
        self.assertEqual(privacy, site + "privacy/", "the privacy page lives at /privacy/")
        data = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(data["privacyPolicyUrl"], privacy)
        self.assertEqual(data["supportUrl"], REPO_URL + "/issues")
        self.assertEqual(data["termsOfServiceUrl"], REPO_URL + "/blob/main/LICENSE")
        self.assertTrue((ROOT / "LICENSE").is_file())
        self.assertEqual(data["documentationUrl"], REPO_URL + "/tree/main/docs")
        self.assertTrue((ROOT / "docs" / "README.md").is_file())
        self.assertIn('href="privacy/"', PAGE, "the home page links to the privacy page")
        self.assertIn(f"({privacy})", README, "the README links to the privacy page")


if __name__ == "__main__":
    unittest.main(verbosity=2)
