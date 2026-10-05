#!/usr/bin/env python3
"""Checks on the documentation files themselves. No model, no network, under a second.

Run: python3 evals/tests_docs.py
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
CROSS = (ROOT / "references" / "cross-tool.md").read_text(encoding="utf-8")
INTERVIEW = (ROOT / "references" / "interview.md").read_text(encoding="utf-8")
DISCOVERY = (ROOT / "references" / "skill-discovery.md").read_text(encoding="utf-8")
VOICE = (ROOT / "references" / "voice.md").read_text(encoding="utf-8")

failures: list[str] = []


def check(cond: bool, what: str) -> None:
    if not cond:
        failures.append(what)


def test_skill_md_defines_jargon_before_use() -> None:
    check("*artifact*" in SKILL, "the glossary defines artifact")
    if "## Where things live" in SKILL and "*artifact*" in SKILL:
        check(SKILL.index("*artifact*") < SKILL.index("## Where things live"),
              "the glossary sits before the routing table")


def test_skill_md_source_status_values() -> None:
    for value in ("sourced", "mixed", "general-practice"):
        check(f"`{value}`" in SKILL, f"SKILL.md defines source_status {value}")
    shipped = {p.read_text(encoding="utf-8") for p in (ROOT / "assets" / "templates").glob("*.md")}
    seen = set()
    for text in shipped:
        m = re.search(r"^source_status:\s*(\S+)", text, re.MULTILINE)
        if m:
            seen.add(m.group(1))
    check(seen <= {"sourced", "mixed", "general-practice"}, f"templates use only the three documented values, saw {seen}")


def test_template_docs_agree_with_the_templates() -> None:
    """wf-05-draft.md and docs/template-catalog.tsv describe the shipped templates. A
    template neither of them names is one nobody finds."""
    names = {p.stem for p in (ROOT / "assets" / "templates").glob("*.md")
             if not re.match(r"wf-\d\d-", p.stem)}
    wf05 = (ROOT / "references" / "wf-05-draft.md").read_text(encoding="utf-8")
    check("## Your team's specifics" in wf05, "wf-05-draft.md explains team specifics")
    for name in sorted(names):
        check(name in wf05, f"wf-05-draft.md names the {name} template")
    catalog = ROOT.parents[1] / "docs" / "template-catalog.tsv"
    if catalog.is_file():   # the catalog lives in the repo's docs folder, not in a packaged skill
        listed = {l.split("\t")[0] for l in catalog.read_text(encoding="utf-8").splitlines()[1:] if l.strip()}
        check(listed == names, f"template-catalog.tsv lists every template, differs by {sorted(listed ^ names)}")
    for text in (p.read_text(encoding="utf-8") for p in (ROOT / "assets" / "templates").glob("*.md")):
        m = re.search(r"^team_sources:\s*(.*)$", text, re.MULTILINE)
        check(bool(m) and m.group(1).strip() == "[]", "shipped templates list no team sources")


def test_learn_questions_have_one_rule() -> None:
    flat = " ".join(SKILL.split())   # a rewrap must not read as a removed rule
    check("This is the one rule for `learn` questions" in flat, "SKILL.md step 6 owns the learn rule")
    check("`SKILL.md` step 6" in INTERVIEW, "interview.md points at SKILL.md step 6")
    check("Then ask its `learn`" not in SKILL, "step 7 no longer repeats the learn rule")


def test_first_run_documents_init_flags() -> None:
    for flag in ("--tools", "--output", "--started <YYYY-MM-DD>"):
        check(flag in SKILL, f"first run mentions kb.py init {flag}")
    check("py -3" in SKILL and "py -3" in README, "Windows interpreter fallback is in SKILL.md and README")


def test_claude_ai_script_list_agrees() -> None:
    for name in ("classify.py", "check_output.py", "redact.py", "review.py"):
        check(name in SKILL.split("## Gotchas")[1], f"gotcha lists {name} as runnable in the sandbox")
        check(name in CROSS.split("## claude.ai")[1].split("## Without a shell")[0], f"cross-tool lists {name}")
    check("no scripts" not in SKILL.lower(), "SKILL.md no longer says claude.ai has no scripts")


def test_without_a_shell_covers_every_pipeline_script() -> None:
    section = CROSS.split("## Without a shell")[1].split("## The archives")[0]
    for name in ("doctor.py", "classify.py", "recall.py", "sources.py order", "evidence.py add",
                 "kb.py freshness", "kb.py template get", "check_output.py", "redact.py",
                 "review.py grade", "answers.py write", "kb.py choice", "kb.py about-me",
                 "kb.py rests-on", "kb.py themes", "sources.py"):
        check(f"**`{name}" in section, f"Without a shell has a manual entry for {name}")
    for title in ("Which kind of save", "Sources from a sub agent"):
        check(f"**{title}" in section, f"Without a shell covers {title.lower()}")


def test_cross_tool_rows_and_copilot_folders() -> None:
    check("| Claude Desktop, Code tab |" in CROSS, "cross-tool table has a Code tab row")
    check("| Copilot in VS Code |" in CROSS, "cross-tool table has a VS Code row")
    check("| Codex CLI and IDE |" in CROSS, "cross-tool table has a Codex row")
    check("## Codex, in the CLI and the IDE" in CROSS, "cross-tool has a Codex section")
    check("writable_roots" in CROSS and ".git" in CROSS.split("## Codex")[1].split("## claude.ai")[0],
          "the Codex section explains the sandbox and the read-only .git")
    check("Codex" in README and "Codex" in SKILL.split("---")[1], "README and the description name Codex")
    check("`.github/skills`" in CROSS, "Copilot folder list includes .github/skills")
    check("plugin folder" in CROSS, "package.py plugin folder is documented")
    check("observed, not documented" in CROSS, "Desktop .skill behaviour is labelled as observed")


def test_readme_install_prerequisites() -> None:
    install = README.split("## Install")[1].split("## First run")[0]
    check("Needs Python 3" in install, "README install states the Python 3 prerequisite")
    check("Save the attachment first" in install, "README says to save the email attachment first")
    check("send both `flarehand.skill` and `flarehand.zip`" in install, "README sends both files")
    check("Check it landed" in install, "README has a verify step")
    check("skips" not in README.split("## For maintainers")[1], "README no longer says the importer skips")


def test_discovery_spec_rules_and_chain() -> None:
    check("`anthropic` or `claude`" in DISCOVERY, "name rule about reserved words")
    check("one level below `SKILL.md`" in DISCOVERY, "references depth rule")
    check("`kb.py search` finds it" in DISCOVERY, "chain is a saved note found by search")


def test_voice_is_english_only() -> None:
    check("written for English" in VOICE, "voice.md says the rules are English-only")


def test_terminology() -> None:
    for text, name in ((SKILL, "SKILL.md"), (README, "README.md"), (CROSS, "cross-tool.md")):
        check("cached answer" not in text.lower() and "answer cache" not in text.lower(), f"{name} says saved answer")
        check("work memory" not in text.lower(), f"{name} says knowledge base")


class TestDocs(unittest.TestCase):
    """The same checks, as a TestCase, so evals/test_scripts.py picks them up. Its loader
    hoists unittest classes, so a suite written any other way is silently skipped: this
    file ran clean by hand for months and contributed nothing to the documented command."""

    def test_documentation_rules(self):
        for name, fn in sorted(globals().items()):
            if name.startswith("test_") and callable(fn) and name != "test_documentation_rules":
                before = len(failures)
                fn()
                with self.subTest(check=name):
                    self.assertEqual(failures[before:], [], failures[before:])


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
    for f in failures:
        print(f"FAIL  {f}")
    print(f"{len(tests)} test(s), {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
