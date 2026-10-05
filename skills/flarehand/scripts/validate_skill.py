#!/usr/bin/env python3
"""validate_skill.py - check every skill, and the plugin around them, will load everywhere.

Every rule here guards a silent failure. None of them raise an error at load time. The skill
just quietly does not work, and nobody finds out for weeks.

What it checks, for each skill
  frontmatter   only the portable keys (claude.ai refuses an upload with any other), string
                metadata values, a name that matches the folder, a quoted description inside
                the 1024 character limit
  size          SKILL.md body under 500 lines
  routing       every reference SKILL.md names exists, every reference that exists is named,
                and every path into a sibling skill (../flarehand/...) exists
  references    a Scope line at the top, and a table of contents once long
  packaging     no folder that makes a client load the skill as a plugin, no PowerShell, no
                binaries, and no file so big it bloats every install

And, inside the repository (this skill at <root>/skills/<name>/, with .claude-plugin/plugin.json
at the root), the plugin itself
  manifests     the required keys of each tool's manifest, one name, one version everywhere
  hooks         hooks.json and hooks-cursor.json run the same dispatcher actions, through the
                launcher, and the launcher and dispatcher exist
  repository    no top-level bin/, no .DS_Store, no binaries, a LICENSE, a README of 40 words
                or more, and AGENTS.md

Usage
  python3 scripts/validate_skill.py
  python3 scripts/validate_skill.py --json
  python3 scripts/validate_skill.py --strict

Exit codes: 0 clean, 1 problems found, 2 the skill could not be read.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from package import is_stray  # noqa: E402  one definition of operating system litter
except Exception as _import_error:  # a broken or missing package.py must not hide every other finding
    print(f"warning: scripts/package.py could not be imported ({type(_import_error).__name__}: {_import_error}). "
          f"Litter filtering is off for this run.", file=sys.stderr)

    def is_stray(rel_posix: str) -> bool:
        name = rel_posix.rsplit("/", 1)[-1]
        return name == ".DS_Store" or name.startswith("._") or "__pycache__" in rel_posix

PORTABLE_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
DESC_LIMIT = 1020          # 1024 is the hard cap, 4 spare for folding artefacts
BODY_LINE_LIMIT = 500
TOC_AFTER_LINES = 100
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED_WORDS = ("claude", "anthropic")
# Claude Code loads a skill folder as a plugin when it holds any of these. The skill then
# loads as a plugin, not as a skill, and its eval and marketplace shape change with it.
PLUGIN_TRIGGERS = {"agents", "hooks", "workflows", ".claude-plugin"}
# House rule: these are plugin component folders. Keep them out of a skill too, so nobody
# mistakes the folder for a plugin. Claude Code does not treat them as a trigger.
PLUGIN_COMPONENTS = {"monitors", "themes", "output-styles"}
PLUGIN_ADOPTING = PLUGIN_TRIGGERS | PLUGIN_COMPONENTS
BAD_SUFFIXES = {".ps1", ".psm1", ".psd1", ".app", ".pkg", ".command", ".exe", ".dll", ".dylib", ".so",
                ".bin", ".jar", ".class", ".wasm"}
# Files that are binary by nature and fine to ship. Everything else gets sniffed for NUL bytes.
BINARY_OK_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".woff", ".woff2", ".ttf"}
SNIFF_BYTES = 8192
BIG_FILE_BYTES = 3 * 1024 * 1024
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".idea", ".vscode", "dist", "results"}
SIBLING_PATH = re.compile(r"\.\./([a-z0-9-]+)/([A-Za-z0-9._/\-]*[A-Za-z0-9_\-])")

# The plugin around the skills.
HOOK_ACTIONS = {"session-start", "prompt-submit", "stop", "pre-compact", "session-end"}
CLAUDE_HOOK_EVENTS = {"SessionStart", "UserPromptSubmit", "Stop", "PreCompact", "SessionEnd", "PreToolUse",
                      "PostToolUse", "Notification", "SubagentStop", "SubagentStart", "PostCompact"}
CURSOR_HOOK_EVENTS = {"sessionStart", "beforeSubmitPrompt", "stop", "preCompact", "sessionEnd",
                      "beforeShellExecution", "afterFileEdit", "beforeReadFile", "beforeMCPExecution",
                      "afterAgentResponse", "afterAgentThought", "subagentStop"}
# key path -> type. A path is dotted; "[]" means every item of a list.
MANIFESTS = {
    ".claude-plugin/plugin.json": {"name": str, "version": str, "description": str, "author.name": str,
                                   "license": str},
    ".claude-plugin/marketplace.json": {"name": str, "owner.name": str, "plugins": list,
                                        "plugins[].name": str, "plugins[].source": (str, dict),
                                        "plugins[].description": str},
    ".codex-plugin/plugin.json": {"name": str, "version": str, "description": str, "skills": str,
                                  "interface.displayName": str, "interface.shortDescription": str,
                                  "interface.developerName": str, "interface.category": str,
                                  "interface.capabilities": list},
    ".agents/plugins/marketplace.json": {"name": str, "interface.displayName": str, "plugins": list,
                                         "plugins[].name": str, "plugins[].source.source": str,
                                         "plugins[].policy.installation": str,
                                         "plugins[].policy.authentication": str, "plugins[].category": str},
    ".cursor-plugin/plugin.json": {"name": str, "displayName": str, "version": str, "description": str,
                                   "author.name": str, "license": str, "keywords": list, "skills": str,
                                   "hooks": str},
    "gemini-extension.json": {"name": str, "version": str, "description": str, "contextFileName": str},
}
VERSIONED = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json",
             "gemini-extension.json")
# Claude Code keeps these marketplace names for Anthropic. Anything naming Claude or Anthropic is refused too.
RESERVED_MARKETPLACES = {"claude-code-marketplace", "claude-code-plugins", "claude-plugins-official",
                         "anthropic-marketplace", "anthropic-plugins", "agent-skills", "life-sciences"}


def find_repo_root(skill_dir: Path = SKILL_DIR) -> Path | None:
    root = skill_dir.parent.parent
    if skill_dir.parent.name == "skills" and (root / ".claude-plugin" / "plugin.json").is_file():
        return root
    return None


def read_frontmatter(text: str) -> tuple[dict, str, list[str]]:
    """Read the frontmatter block. Handles multi-line double-quoted scalars and
    folded blocks, which the real YAML parsers accept and a naive reader does not."""
    problems: list[str] = []
    if not text.startswith("---"):
        return {}, text, ["SKILL.md does not start with a frontmatter block at byte 0"]
    lines = text.split("\n")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            end = i
            break
    if end is None:
        return {}, text, ["frontmatter block is never closed with ---"]

    meta: dict = {}
    styles: dict = {}
    i = 1
    while i < end:
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        if raw.startswith((" ", "\t")):  # part of a nested map, handled by its parent
            i += 1
            continue
        if ":" not in raw:
            problems.append(f"frontmatter line {i + 1} is not a key: {raw.strip()[:50]}")
            i += 1
            continue
        key, _, rest = raw.partition(":")
        key, rest = key.strip(), rest.strip()

        if rest in (">", ">-", "|", "|-"):
            styles[key] = "folded"
            parts = []
            i += 1
            while i < end and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                parts.append(lines[i].strip())
                i += 1
            meta[key] = " ".join(p for p in parts if p)
            continue
        if rest.startswith('"') and not (len(rest) > 1 and rest.rstrip().endswith('"')):
            styles[key] = "quoted"
            parts = [rest[1:]]
            i += 1
            while i < end:
                chunk = lines[i].strip()
                if chunk.endswith('"'):
                    parts.append(chunk[:-1])
                    i += 1
                    break
                parts.append(chunk)
                i += 1
            meta[key] = " ".join(p for p in parts if p)
            continue
        if rest == "":
            styles[key] = "map"
            block = []
            i += 1
            while i < end and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                block.append(lines[i])
                i += 1
            meta[key] = block
            continue

        styles[key] = "quoted" if rest.startswith('"') else "plain"
        meta[key] = rest[1:-1] if (rest.startswith('"') and rest.endswith('"') and len(rest) > 1) else rest
        i += 1

    meta["__styles__"] = styles
    return meta, "\n".join(lines[end + 1:]), problems


def _looks_binary(path: Path) -> bool:
    """A NUL byte in the first few KB is the same test `grep` and git use for binary."""
    try:
        with path.open("rb") as fh:
            return b"\x00" in fh.read(SNIFF_BYTES)
    except OSError:
        return False


def _looks_binary(path: Path) -> bool:
    """A NUL byte in the first few KB is the same test `grep` and git use for binary."""
    try:
        with path.open("rb") as fh:
            return b"\x00" in fh.read(SNIFF_BYTES)
    except OSError:
        return False


def _file_checks(base: Path, label: str, errors: list, warnings: list, skip_top: set = frozenset()) -> None:
    """PowerShell, launchable files, binaries and big files, anywhere under base."""
    for path in base.rglob("*"):
        rel = path.relative_to(base)
        if is_stray(rel.as_posix()) or rel.parts[0] in SKIP_DIRS or rel.parts[0] in skip_top:
            continue
        if any(part in SKIP_DIRS for part in rel.parts) or not path.is_file():
            continue
        shown = f"{label}{rel.as_posix()}"
        suffix = path.suffix.lower()
        if suffix in BAD_SUFFIXES:
            errors.append(f"{shown} cannot ship. Windows blocks downloaded PowerShell, macOS gates launchable "
                          f"files, and a skill has no use for compiled code.")
        elif suffix not in BINARY_OK_SUFFIXES and _looks_binary(path):
            errors.append(f"{shown} is a binary file: its first {SNIFF_BYTES // 1024} KB holds a NUL byte. "
                          f"A skill ships text, images and PDFs only. Remove it.")
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        if size > BIG_FILE_BYTES:
            warnings.append(f"{shown} is {size / 1024 / 1024:.1f} MB. Every install carries it, and Claude "
                            f"Desktop caps an archive at 30 MB. Shrink it or leave it out.")


def _metadata_problems(block) -> list[str]:
    """The spec says metadata maps strings to strings. A nested map or a list fails other parsers."""
    problems = []
    if not isinstance(block, list):
        return ["`metadata` must be a map of keys to string values"]
    indent = None
    for line in block:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        lead = len(line) - len(line.lstrip())
        indent = lead if indent is None else indent
        key, sep, value = line.strip().partition(":")
        if lead != indent or not sep or line.strip().startswith("-"):
            problems.append(f"metadata line `{line.strip()[:40]}` is not a flat `key: value` pair")
        elif not value.strip() or value.strip() in ("|", ">", "|-", ">-"):
            problems.append(f"metadata `{key}` has no value on its line. Use a quoted string.")
    return problems


def check_skill(skill_dir: Path, repo_root: Path | None = None, sibling_prose: str = "") -> dict:
    """Errors, warnings and facts for one skill folder."""
    errors: list[str] = []
    warnings: list[str] = []
    facts: dict = {}

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {"errors": [f"no SKILL.md at {skill_md}"], "warnings": [], "facts": {}}

    text = skill_md.read_text(encoding="utf-8")
    meta, body, fm_problems = read_frontmatter(text)
    errors += fm_problems
    styles = meta.pop("__styles__", {})

    # ---- frontmatter keys
    for k in sorted(set(meta) - PORTABLE_KEYS):
        errors.append(f"frontmatter key `{k}` is not one of the portable keys ({', '.join(sorted(PORTABLE_KEYS))}). "
                      f"claude.ai refuses an upload that has it, and other tools ignore it.")
    if "metadata" in meta:
        errors += _metadata_problems(meta["metadata"])

    # ---- name
    name = str(meta.get("name", ""))
    facts["name"] = name
    if not name:
        errors.append("frontmatter has no `name`")
    else:
        if not NAME_RE.match(name):
            errors.append(f"name `{name}` must be lowercase letters, numbers and single hyphens")
        if len(name) > 64:
            errors.append(f"name is {len(name)} characters, the limit is 64")
        if name != skill_dir.name:
            errors.append(f"name `{name}` does not match the folder name `{skill_dir.name}`. "
                          f"Both standards need these to match.")
        for word in RESERVED_WORDS:
            if word in name.lower():
                errors.append(f"name cannot contain `{word}`")

    # ---- description
    desc = str(meta.get("description", ""))
    facts["description_chars"] = len(desc)
    facts["description_style"] = styles.get("description", "none")
    if not desc:
        errors.append("frontmatter has no `description`. A skill with no description is skipped, not warned about.")
    else:
        if len(desc) > DESC_LIMIT:
            errors.append(f"description is {len(desc)} characters. Keep it at or under {DESC_LIMIT} "
                          f"so the 1024-character limit in the Agent Skills spec is never hit.")
        if styles.get("description") != "quoted":
            warnings.append("description is not a quoted string. An unquoted colon is the most common "
                            "reason a skill is silently skipped by a non-Claude parser.")
        if re.match(r"^\s*(I |I'|My |We |Let me)", desc):
            errors.append("description must be written in the third person, describing the skill.")
        if "—" in desc or "–" in desc:
            errors.append("description contains a long dash. Keep the frontmatter to plain ASCII punctuation.")

    # ---- body size
    body_lines = body.strip().split("\n")
    facts["body_lines"] = len(body_lines)
    if len(body_lines) > BODY_LINE_LIMIT:
        errors.append(f"SKILL.md body is {len(body_lines)} lines, the limit is {BODY_LINE_LIMIT}. "
                      f"Move detail into references/.")
    facts["skill_md_bytes"] = len(text.encode("utf-8"))
    if facts["skill_md_bytes"] > 1_000_000:
        errors.append("SKILL.md is over 1 MB, which Claude Code documents as likely to hit context limits.")

    # ---- references, both directions. A path into a sibling skill is checked separately.
    local_text = SIBLING_PATH.sub("", text)
    ref_dir = skill_dir / "references"
    on_disk = {p.name for p in ref_dir.glob("*.md") if not is_stray(p.name)} if ref_dir.is_dir() else set()
    named = set(re.findall(r"references/([A-Za-z0-9._\-]+\.md)", local_text))
    facts["references_on_disk"] = len(on_disk)
    facts["references_named"] = len(named)
    for missing in sorted(named - on_disk):
        errors.append(f"SKILL.md points at references/{missing}, which does not exist")
    for orphan in sorted(on_disk - named):
        warnings.append(f"references/{orphan} exists but SKILL.md never points at it, so it never gets read")

    # ---- paths into a sibling skill, such as ../flarehand/scripts/recall.py
    for sibling, rest in sorted(set(SIBLING_PATH.findall(text))):
        target = skill_dir.parent / sibling
        if not target.is_dir():
            warnings.append(f"SKILL.md points into ../{sibling}/, which is not installed beside this skill. "
                            f"Install the two together.")
        elif not (target / rest).exists():
            errors.append(f"SKILL.md points at ../{sibling}/{rest}, which does not exist")

    # ---- each reference file
    for path in (sorted(p for p in ref_dir.glob("*.md") if not is_stray(p.name)) if ref_dir.is_dir() else []):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"references/{path.name} is not text. A skill ships no binaries.")
            continue
        head = "\n".join(content.split("\n")[:12]).lower()
        if "**scope.**" not in head and "## scope" not in head:
            warnings.append(f"references/{path.name} has no Scope line, so a reader landing mid-file "
                            f"cannot tell what it covers")
        n = len(content.split("\n"))
        if n > TOC_AFTER_LINES and not re.search(r"(?i)^\s*(##+\s*)?(contents|on this page|in this file)",
                                                 content, re.M):
            warnings.append(f"references/{path.name} is {n} lines with no contents list. "
                            f"A partial read will miss half of it.")
        if re.search(r"\]\(references/", content):
            warnings.append(f"references/{path.name} links into references/ with a path that only works "
                            f"from the skill root. Use a bare filename.")

    if (skill_dir / "scripts" / "classify.py").is_file() and (skill_dir / "assets").is_dir():
        _workflow_checks(skill_dir, errors, warnings)

    # ---- packaging
    for child in skill_dir.iterdir():
        if child.is_dir() and child.name in PLUGIN_TRIGGERS:
            errors.append(f"folder `{child.name}/` makes Claude Code load this folder as a plugin, not a skill. "
                          f"Rename it. Plugin parts live at the repository root.")
        elif child.is_dir() and child.name in PLUGIN_COMPONENTS:
            errors.append(f"folder `{child.name}/` is a plugin component name. House rule: keep those out of a "
                          f"skill, so nobody mistakes it for a plugin. Rename it.")
    _file_checks(skill_dir, "", errors, warnings)

    # ---- every script must actually be invoked somewhere, not merely listed.
    # A script that appears only in a table is one the model never runs. That is
    # how the answer cache shipped read-only: recall.py read it, answers.py was
    # listed but never called, so it never filled.
    script_dir = skill_dir / "scripts"
    if script_dir.is_dir():
        prose = text + "\n" + sibling_prose
        for path in sorted(p for p in ref_dir.glob("*.md") if not is_stray(p.name)) if ref_dir.is_dir() else []:
            prose += "\n" + path.read_text(encoding="utf-8", errors="replace")
        for path in sorted(p for p in script_dir.glob("*.py") if not is_stray(p.name)):
            if path.name == "validate_skill.py" or path.name.startswith("_"):
                continue  # a maintainer tool, invoked from the README
            if f"scripts/{path.name}" not in prose.replace("`", ""):
                errors.append(f"scripts/{path.name} is never invoked in SKILL.md or any reference. "
                              f"A script nothing calls is dead weight.")
            elif not re.search(rf"(python3?|interpreter)\s+(?:\.\./{re.escape(skill_dir.name)}/)?scripts/"
                               rf"{re.escape(path.name)}", prose):
                warnings.append(f"scripts/{path.name} is mentioned but never shown as a runnable command")

        # ---- assets nothing reads
        scripts_text = "\n".join(f.read_text(encoding="utf-8", errors="replace")
                                 for f in sorted(script_dir.glob("*.py")))
        for asset in sorted((skill_dir / "assets").glob("*.tsv")) if (skill_dir / "assets").is_dir() else []:
            if asset.name not in scripts_text:
                warnings.append(f"assets/{asset.name} is not loaded by any script. It ships in every "
                                f"install and nothing reads it. Wire it up or delete it.")

        for path in sorted(p for p in script_dir.glob("*.py") if not is_stray(p.name)):
            try:
                src = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                errors.append(f"scripts/{path.name} is not text. A skill ships no binaries.")
                continue
            if re.search(r"^\s*\w*\s*=?\s*input\s*\(", src, re.M):
                errors.append(f"scripts/{path.name} calls input(). An agent shell has nobody to answer, "
                              f"so it hangs forever.")
            if not src.startswith('#!/usr/bin/env python3') and not src.startswith('"""'):
                warnings.append(f"scripts/{path.name} has no shebang or docstring at the top")
            if '"""' not in src[:400]:
                warnings.append(f"scripts/{path.name} has no docstring explaining what it does")

    meta_version = re.search(r"flarehand\.version:\s*[\"']?([^\"'\n]+)", text)
    if meta_version:
        facts["version"] = meta_version.group(1).strip()
    return {"errors": errors, "warnings": warnings, "facts": facts}


def _workflow_checks(skill_dir: Path, errors: list, warnings: list) -> None:
    """The workflow set, which six files have to agree about. Only the router skill has one."""
    try:
        sys.path.insert(0, str(skill_dir / "scripts"))
        import classify  # noqa: E402
        sources = {
            "assets/workflows.tsv": set(classify.SHIPPED_ARCHETYPES),
            "assets/workflow-graph.tsv": {r[0] for r in classify._rows(
                skill_dir / "assets" / "workflow-graph.tsv", 4) if r[0]},
            "assets/contracts.tsv": {r.split("\t")[0] for r in
                                     (skill_dir / "assets" / "contracts.tsv").read_text(
                                         encoding="utf-8").splitlines()[1:] if r.strip()},
            # numbered only: wf-authoring.md is a guide to writing one, not one of them
            "references/wf-NN-*.md": {p.name[:5] for p in
                                      (skill_dir / "references").glob("wf-[0-9][0-9]-*.md")},
            "assets/templates/wf-NN-*.md": {p.name[:5] for p in
                                            (skill_dir / "assets" / "templates").glob("wf-[0-9][0-9]-*.md")},
        }
        shipped = sources["assets/workflows.tsv"]
        for where, found in sources.items():
            for extra in sorted(found - shipped):
                errors.append(f"{where} names workflow `{extra}`, which assets/workflows.tsv does "
                              f"not. An unknown workflow used to crash classify.py.")
            for missing in sorted(shipped - found):
                errors.append(f"{where} is missing workflow `{missing}`, which "
                              f"assets/workflows.tsv declares.")
        router = classify._rows(skill_dir / "assets" / "router-table.tsv", 5)
        worded = {r[2] for r in router if r[0] in ("noun", "verb")}
        for extra in sorted(worded - shipped):
            errors.append(f"assets/router-table.tsv routes to `{extra}`, which assets/workflows.tsv "
                          f"does not declare.")
        for missing in sorted(shipped - worded):
            errors.append(f"no row in assets/router-table.tsv reaches `{missing}`, so nothing can route to it.")

        # The prose and the table are the same graph, in the same order. Step 9 offers the first
        # edge, so an order that differs changes what the person is offered.
        graph: dict = {}
        for r in sorted(classify._rows(skill_dir / "assets" / "workflow-graph.tsv", 4),
                        key=lambda x: (x[0], int(x[3]) if x[3].isdigit() else 99)):
            graph.setdefault(r[0], []).append(r[1])
        for path in sorted((skill_dir / "references").glob("wf-[0-9][0-9]-*.md")):
            chains = path.read_text(encoding="utf-8").split("## Chains to")
            prose = list(dict.fromkeys(re.findall(r"wf-\d\d", chains[-1]))) if len(chains) > 1 else []
            if prose != graph.get(path.name[:5], []):
                errors.append(f"references/{path.name} chains to {prose or 'nothing'}, and "
                              f"assets/workflow-graph.tsv says {graph.get(path.name[:5], [])}, strongest "
                              f"first. Make them agree.")

        # Router to template, both ways. A named template that does not exist falls back in
        # silence. A template no words reach is only found by someone who knows its name.
        templates = {p.stem for p in (skill_dir / "assets" / "templates").glob("*.md")}
        named = {r[4] for r in router if r[0] == "noun" and r[4]}
        for name in sorted(named - templates - set(classify.TEMPLATE_REFERENCES)):
            errors.append(f"assets/router-table.tsv names template `{name}`, which is not in assets/templates.")
        for name in sorted(t for t in templates - named if not re.match(r"wf-\d\d-", t)):
            errors.append(f"assets/templates/{name}.md is not named by any noun row in "
                          f"assets/router-table.tsv, so no request reaches it.")
    except Exception as e:  # a broken table must not hide every other finding
        warnings.append(f"could not check the workflow tables ({type(e).__name__}: {e})")

    # ---- assets nothing reads
    scripts_text = "\n".join(
        f.read_text(encoding="utf-8", errors="replace")
        for f in sorted((skill_dir / "scripts").glob("*.py")))
    for asset in sorted((skill_dir / "assets").glob("*.tsv")):
        if asset.name not in scripts_text:
            warnings.append(f"assets/{asset.name} is not loaded by any script. It ships in every "
                            f"install and nothing reads it. Wire it up or delete it.")



# ---------------------------------------------------------------- the plugin around the skills

def _get(data, path: str) -> list:
    """Every value at a dotted path. `plugins[].name` fans out over a list."""
    values = [data]
    for part in path.split("."):
        nxt = []
        many = part.endswith("[]")
        key = part[:-2] if many else part
        for v in values:
            if isinstance(v, dict) and key in v:
                item = v[key]
                if many:
                    nxt += item if isinstance(item, list) else []
                else:
                    nxt.append(item)
            else:
                nxt.append(_MISSING)
        values = nxt
    return values


_MISSING = object()


def _load_json(path: Path, errors: list) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{path.name} is missing")
        return None
    except ValueError as e:
        errors.append(f"{path} is not valid JSON: {e}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{path} must hold a JSON object")
        return None
    return data


def _hook_actions(commands: list[str], where: str, errors: list) -> set:
    actions = set()
    for cmd in commands:
        if not isinstance(cmd, str) or "run-hook.cmd" not in cmd:
            errors.append(f"{where}: a hook command does not go through hooks/run-hook.cmd: {str(cmd)[:80]}")
            continue
        found = re.findall(r"run-hook\.cmd\"?\s+([a-z-]+)", cmd)
        if not found or found[-1] not in HOOK_ACTIONS:
            errors.append(f"{where}: a hook command names no known action ({', '.join(sorted(HOOK_ACTIONS))})")
            continue
        actions.add(found[-1])
    return actions


def check_hooks(root: Path, errors: list, warnings: list) -> dict:
    hooks_dir = root / "hooks"
    for need in ("hook.py", "run-hook.cmd", "hooks.json", "hooks-cursor.json"):
        if not (hooks_dir / need).is_file():
            errors.append(f"hooks/{need} is missing")
    claude = _load_json(hooks_dir / "hooks.json", errors) or {}
    cursor = _load_json(hooks_dir / "hooks-cursor.json", errors) or {}

    claude_cmds = []
    for event, groups in (claude.get("hooks") or {}).items():
        if event not in CLAUDE_HOOK_EVENTS:
            errors.append(f"hooks/hooks.json: `{event}` is not a Claude Code hook event")
        for group in groups if isinstance(groups, list) else []:
            for h in group.get("hooks", []) if isinstance(group, dict) else []:
                cmd = h.get("command", "") if isinstance(h, dict) else ""
                claude_cmds.append(cmd)
                if "CLAUDE_PLUGIN_ROOT" in cmd and not re.search(r'\[ -f "\$\{CLAUDE_PLUGIN_ROOT\}', cmd):
                    warnings.append("hooks/hooks.json: a command does not check that ${CLAUDE_PLUGIN_ROOT} is set. "
                                    "Gemini CLI also reads this file, without that variable.")
                if not re.search(r"\bsh\s+\"\$\{CLAUDE_PLUGIN_ROOT\}", cmd):
                    warnings.append("hooks/hooks.json: a command runs the launcher without `sh`, so it depends on "
                                    "the executable bit, which installers strip.")
    cursor_cmds = []
    if cursor and cursor.get("version") != 1:
        errors.append("hooks/hooks-cursor.json must have \"version\": 1")
    for event, items in (cursor.get("hooks") or {}).items():
        if event not in CURSOR_HOOK_EVENTS:
            errors.append(f"hooks/hooks-cursor.json: `{event}` is not a Cursor hook event")
        for h in items if isinstance(items, list) else []:
            cursor_cmds.append(h.get("command", "") if isinstance(h, dict) else "")

    a = _hook_actions(claude_cmds, "hooks/hooks.json", errors)
    b = _hook_actions(cursor_cmds, "hooks/hooks-cursor.json", errors)
    if a != b:
        errors.append(f"hooks.json runs {sorted(a)} and hooks-cursor.json runs {sorted(b)}. Keep them the same.")
    launcher = hooks_dir / "run-hook.cmd"
    if os.name == "posix" and launcher.is_file() and not os.access(launcher, os.X_OK):
        warnings.append("hooks/run-hook.cmd is not executable. Cursor runs it directly: "
                        "`chmod +x hooks/run-hook.cmd` and `git update-index --chmod=+x hooks/run-hook.cmd`.")
    return {"actions": sorted(a)}


def check_repo(root: Path, errors: list, warnings: list) -> dict:
    facts: dict = {}
    # ---- manifests
    versions = {}
    names = {}
    for rel, spec in MANIFESTS.items():
        data = _load_json(root / rel, errors)
        if data is None:
            continue
        for key, kind in spec.items():
            values = _get(data, key)
            if not values or any(v is _MISSING for v in values):
                errors.append(f"{rel} has no `{key}`")
            elif any(not isinstance(v, kind) for v in values):
                errors.append(f"{rel}: `{key}` has the wrong type")
        if rel in VERSIONED and isinstance(data.get("version"), str):
            versions[rel] = data["version"]
        if isinstance(data.get("name"), str) and "marketplace" not in rel:
            names[rel] = data["name"]
        if rel == ".claude-plugin/marketplace.json":
            mname = str(data.get("name", ""))
            if mname in RESERVED_MARKETPLACES or "anthropic" in mname or "claude" in mname:
                errors.append(f"{rel}: marketplace name `{mname}` is reserved or names Anthropic")
            for p in data.get("plugins", []) if isinstance(data.get("plugins"), list) else []:
                if isinstance(p, dict) and "version" in p:
                    warnings.append(f"{rel}: plugin `{p.get('name')}` sets a version. Keep it only in plugin.json.")
                if isinstance(p, dict) and isinstance(p.get("source"), str) and not (root / p["source"]).is_dir():
                    errors.append(f"{rel}: plugin source `{p['source']}` does not exist")
        for key in ("skills", "hooks"):
            value = data.get(key)
            if rel.endswith("plugin.json") and isinstance(value, str) and not (root / value).exists():
                errors.append(f"{rel}: `{key}` points at {value}, which does not exist")
        if rel == "gemini-extension.json" and isinstance(data.get("contextFileName"), str) \
                and not (root / data["contextFileName"]).is_file():
            errors.append(f"{rel}: contextFileName {data['contextFileName']} does not exist")
    if len(set(names.values())) > 1:
        errors.append(f"the manifests disagree on the plugin name: {names}")
    if len(set(versions.values())) > 1:
        errors.append(f"the manifests disagree on the version: {versions}. Run tools/bump_version.py.")
    facts["version"] = next(iter(versions.values()), None)

    # ---- repository hygiene
    if (root / "bin").exists():
        errors.append("a top-level bin/ folder blocks the claude.ai and Cowork plugin install. Remove it.")
    ignored = (root / ".gitignore").is_file() and ".DS_Store" in (root / ".gitignore").read_text(encoding="utf-8")
    for path in root.rglob(".DS_Store"):
        rel = path.relative_to(root)
        if rel.parts[0] in SKIP_DIRS:
            continue
        (warnings if ignored else errors).append(
            f"{rel.as_posix()} is Finder litter. Delete it. The plugin directory rejects a repository that holds one.")
    for need in ("LICENSE", "README.md", "AGENTS.md"):
        if not (root / need).is_file():
            errors.append(f"{need} is missing at the repository root")
    readme = root / "README.md"
    if readme.is_file() and len(readme.read_text(encoding="utf-8").split()) < 40:
        errors.append("README.md has fewer than 40 words. The plugin directory needs a real description.")
    _file_checks(root, "", errors, warnings, skip_top={"skills", "docs"})
    facts["hooks"] = check_hooks(root, errors, warnings)
    return facts


def check(strict: bool) -> dict:
    """Every skill, and the plugin around them when this runs inside the repository."""
    root = find_repo_root()
    skills = sorted(p for p in (root / "skills").iterdir() if (p / "SKILL.md").is_file()) if root else [SKILL_DIR]
    if SKILL_DIR not in skills:
        skills.append(SKILL_DIR)
    # Entry-point skills run this skill's scripts, so their SKILL.md counts as prose that invokes them.
    prose = "\n".join((s / "SKILL.md").read_text(encoding="utf-8", errors="replace")
                      for s in skills if s != SKILL_DIR)
    errors: list[str] = []
    warnings: list[str] = []
    per_skill: dict = {}
    for skill in skills:
        r = check_skill(skill, root, prose if skill == SKILL_DIR else "")
        prefix = "" if len(skills) == 1 else f"{skill.name}: "
        errors += [prefix + e for e in r["errors"]]
        warnings += [prefix + w for w in r["warnings"]]
        per_skill[skill.name] = r["facts"]
    facts = dict(per_skill.get(SKILL_DIR.name, {}))
    facts["skills"] = per_skill
    if root is not None:
        repo = check_repo(root, errors, warnings)
        facts["plugin_version"] = repo.get("version")
        for name, f in per_skill.items():
            if f.get("version") and repo.get("version") and f["version"] != repo["version"]:
                warnings.append(f"{name}: SKILL.md metadata says version {f['version']}, the plugin says "
                                f"{repo['version']}. Run tools/bump_version.py.")
    if strict:
        errors += warnings
        warnings = []
    return {"errors": errors, "warnings": warnings, "facts": facts}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="validate_skill.py",
                                 description="Check every skill, and the plugin around them, will load everywhere.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args(argv)

    result = check(args.strict)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for name, f in result["facts"].get("skills", {}).items():
            print(f"{name:22} description {f.get('description_chars')} chars ({f.get('description_style')}), "
                  f"body {f.get('body_lines')} lines, references {f.get('references_on_disk')} on disk, "
                  f"{f.get('references_named')} named")
        if result["facts"].get("plugin_version"):
            print(f"{'plugin':22} version {result['facts']['plugin_version']}")
        for e in result["errors"]:
            print(f"\nERROR  {e}")
        for w in result["warnings"]:
            print(f"WARN   {w}")
        print(f"\n{len(result['errors'])} error(s), {len(result['warnings'])} warning(s)")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
