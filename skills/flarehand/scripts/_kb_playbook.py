"""_kb_playbook.py - glossary, house rules and team playbooks.

Part of kb.py, split out to keep each file small. The commands here are
kb.py glossary, kb.py rule and kb.py playbook.

Run them through kb.py, which re-exports every name defined here, so `from kb import ...`
keeps working. This module imports from kb, so import kb first, never this module on its own.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from kb import (atomic_write, default_root, die, guard_sensitive, kb_exists, one_line, read_config,
    require_root, resolve_root, slugify, today)

# --------------------------------------------------------------------------
# glossary and house rules, personal or in a team playbook
# --------------------------------------------------------------------------

GLOSSARY_FILE = "glossary.tsv"
GLOSSARY_HEADER = "term\tmeanings\task\tadded"
RULES_FILE = "house-rules.md"
RULES_HEAD = ("# House rules\n\nOne rule per line, under an area heading. Drafts and reviews are "
              "checked against them. A rule here adds a check. It never removes one.\n")
DEFAULT_RULE_AREA = "Writing"


def _cell(text: str) -> str:
    """One TSV cell: no tabs, no newlines, no stray separators."""
    return one_line(str(text)).replace("\t", " ").strip()


def _layers():
    import layers
    return layers


def resolve_team(name_or_path: str, root: Path | None) -> object:
    """A playbook by name (from discovery) or by folder. Dies with a sentence when neither."""
    L = _layers()
    try:
        found = L.playbooks(Path.cwd(), root) if root is not None and kb_exists(root) else \
            L.playbooks(Path.cwd(), root or default_root())
    except OSError:
        found = []
    for pb in found:
        if pb.name == name_or_path:
            return pb
    p = Path(name_or_path).expanduser()
    if p.is_dir():
        d = p / L.PLAYBOOK_DIR if (p / L.PLAYBOOK_DIR).is_dir() and not (p / L.PLAYBOOK_FILE).is_file() else p
        return L.load_playbook(d.resolve(), "config")
    names = ", ".join(pb.name for pb in found) or "none found from here"
    die(f"no playbook called '{name_or_path}'. Playbooks in use: {names}. "
        f"Pass a folder, or create one with: kb.py playbook init", 1)


def _commit_hint(path: Path) -> str:
    """What the person runs to share a playbook change. The skill never runs it."""
    top = None
    for d in (path.parent, *path.parents):
        if (d / ".git").exists():
            top = d
            break
    if top is None:
        return f"Changed {path}. It is a plain file edit: share it the way your team shares that folder."
    rel = os.path.relpath(path, top)
    return (f"Changed {path}. Nothing was committed or pushed. To share it with your team:\n"
            f"  git -C \"{top}\" add \"{rel}\" && git -C \"{top}\" commit -m \"playbook: update {Path(rel).name}\"")


def read_glossary_file(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return []
    return _layers().parse_tsv(text)


def write_glossary_file(path: Path, rows: list[dict]) -> None:
    lines = [GLOSSARY_HEADER]
    for r in rows:
        lines.append("\t".join(_cell(r.get(c, "")) for c in ("term", "meanings", "ask", "added")))
    atomic_write(path, "\n".join(lines) + "\n")


def glossary_add(path: Path, term: str, meanings: list[str], ask: str = "") -> str:
    term = _cell(term)
    meanings = [_cell(m).replace("|", "/") for m in meanings if _cell(m)]
    if not term:
        die("a glossary entry needs a term")
    if not meanings:
        die("a glossary entry needs at least one --meaning")
    rows = read_glossary_file(path)
    for r in rows:
        if r.get("term", "").lower() == term.lower():
            have = [m.strip() for m in r.get("meanings", "").split("|") if m.strip()]
            added = [m for m in meanings if m.lower() not in (h.lower() for h in have)]
            r["meanings"] = " | ".join(have + added)
            if ask:
                r["ask"] = _cell(ask)
            write_glossary_file(path, rows)
            return "updated" if added or ask else "unchanged"
    rows.append({"term": term, "meanings": " | ".join(meanings), "ask": _cell(ask), "added": today()})
    write_glossary_file(path, rows)
    return "added"


def glossary_remove(path: Path, term: str) -> bool:
    rows = read_glossary_file(path)
    kept = [r for r in rows if r.get("term", "").lower() != _cell(term).lower()]
    if len(kept) == len(rows):
        return False
    write_glossary_file(path, kept)
    return True


def cmd_glossary(args) -> int:
    L = _layers()
    if args.action == "list":
        root = resolve_root(args.root)
        rows = L.read_tsv(GLOSSARY_FILE, Path.cwd(), root)
        if args.json:
            print(json.dumps(rows, indent=2))
            return 0
        if not rows:
            print("No glossary yet. Add a term with: kb.py glossary add <term> --meaning \"...\"")
        for r in rows:
            ask = f"  ask: {r['ask']}" if r.get("ask") else ""
            print(f"  {r.get('term', ''):<20} {r.get('meanings', '')}  [{r['layer']}]{ask}")
        return 0
    if not args.term:
        die("name the term, for example: kb.py glossary add role --meaning \"job title\"")
    if args.team:
        pb = resolve_team(args.team, resolve_root(args.root))
        path = pb.path / GLOSSARY_FILE
        where = f"the {pb.name} playbook"
    else:
        root = require_root(args)
        path = root / GLOSSARY_FILE
        where = "your glossary"
    if args.action == "add":
        if not args.team:
            guard_sensitive(require_root(args), "this glossary entry", args.term, *(args.meaning or []), args.ask)
        got = glossary_add(path, args.term, args.meaning or [], args.ask or "")
        print(f"{got.capitalize()} \"{_cell(args.term)}\" in {where}.")
        if got == "unchanged":
            return 0
        if args.team:
            print(_commit_hint(path))
        else:
            print(f"Undo: kb.py glossary remove \"{_cell(args.term)}\"")
        return 0
    if glossary_remove(path, args.term):
        print(f"Removed \"{_cell(args.term)}\" from {where}.")
        if args.team:
            print(_commit_hint(path))
        return 0
    print(f"\"{_cell(args.term)}\" is not in {where}. Nothing changed.")
    return 1


def read_rules_file(path: Path) -> list[dict]:
    try:
        return _layers().parse_house_rules(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError):
        return []


def _norm_rule(text: str) -> str:
    return " ".join(str(text).lower().split()).rstrip(".")


def rule_add(path: Path, text: str, area: str) -> bool:
    text, area = _cell(text), _cell(area) or DEFAULT_RULE_AREA
    if not text:
        die("a house rule needs its text")
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError):
        lines = RULES_HEAD.splitlines()
    if any(r["area"].lower() == area.lower() and _norm_rule(r["rule"]) == _norm_rule(text)
           for r in _layers().parse_house_rules("\n".join(lines))):
        return False
    head = next((i for i, l in enumerate(lines) if l.startswith("## ") and l[3:].strip().lower() == area.lower()), None)
    if head is None:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ["", f"## {area}", "", f"- {text}"]
    else:
        end = next((i for i in range(head + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        last = max((i for i in range(head + 1, end) if lines[i].strip()), default=head)
        lines.insert(last + 1, f"- {text}")
    atomic_write(path, "\n".join(_tidy_rule_lines(lines)) + "\n")
    return True


def _tidy_rule_lines(lines: list[str]) -> list[str]:
    """One blank line after each heading and before the next, never two in a row."""
    out: list[str] = []
    for l in lines:
        if l.startswith("## ") and out and out[-1].strip():
            out.append("")
        if not l.strip() and out and not out[-1].strip():
            continue
        if out and out[-1].startswith("## ") and l.strip():
            out.append("")
        out.append(l)
    while out and not out[-1].strip():
        out.pop()
    return out


def rule_remove(path: Path, text: str, area: str | None = None) -> int:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError):
        return 0
    current, out, removed = "General", [], 0
    for l in lines:
        if l.startswith("## "):
            current = l[3:].strip()
        if (l.startswith("- ") and _norm_rule(l[2:]) == _norm_rule(text)
                and (not area or current.lower() == area.strip().lower())):
            removed += 1
            continue
        out.append(l)
    if removed:
        atomic_write(path, "\n".join(_tidy_rule_lines(out)) + "\n")
    return removed


def cmd_rule(args) -> int:
    L = _layers()
    if args.action == "list":
        root = resolve_root(args.root)
        rows = L.house_rules(Path.cwd(), root)
        if args.json:
            print(json.dumps(rows, indent=2))
            return 0
        if not rows:
            print("No house rules yet. Add one with: kb.py rule add \"Link the ticket in every pull request\" "
                  "--area \"Pull requests\"")
        area = None
        for r in rows:
            if r["area"] != area:
                area = r["area"]
                print(f"## {area}")
            print(f"  - {r['rule']}  [{r['layer']}]")
        return 0
    if not args.text:
        die("give the rule text, for example: kb.py rule add \"Lead with the answer\"")
    if args.team:
        pb = resolve_team(args.team, resolve_root(args.root))
        path, where = pb.path / RULES_FILE, f"the {pb.name} playbook"
    else:
        root = require_root(args)
        path, where = root / RULES_FILE, "your house rules"
    if args.action == "add":
        if not args.team:
            guard_sensitive(require_root(args), "this house rule", args.text)
        area = args.area or DEFAULT_RULE_AREA
        if rule_add(path, args.text, area):
            print(f"Added to {where}, under {area}: {_cell(args.text)}")
            print(_commit_hint(path) if args.team else f"Undo: kb.py rule remove \"{_cell(args.text)}\"")
        else:
            print(f"{where.capitalize()} already hold that rule under {area}. Nothing changed.")
        return 0
    n = rule_remove(path, args.text, args.area)
    if not n:
        print(f"No matching rule in {where}. Nothing changed.")
        return 1
    print(f"Removed {n} rule(s) from {where}.")
    if args.team:
        print(_commit_hint(path))
    return 0


# --------------------------------------------------------------------------
# playbooks
# --------------------------------------------------------------------------

PLAYBOOK_README = """# Team playbook

This folder is a flarehand playbook. It shapes how the assistant works for everyone who opens
this repository. It is shared, so it holds shapes and rules only.

## What belongs here

- `playbook.json`: the playbook's name, its owner, and an optional parent playbook.
- `templates/`: your team's version of a template, one Markdown file per template.
- `glossary.tsv`: words with more than one meaning here, and the question to ask about each.
- `house-rules.md`: one rule per line under an area heading. Every rule here is checked.
- `sources.tsv`: sources to prefer or pin for this team.
- `workflows/`: methods your team repeats, one file each.

## What never belongs here

- Personal notes, work logs, saved answers or evidence.
- Anything about a person: names with opinions, reviews, health, pay or HR matters.
- Customer data, credentials, tokens or secrets.
- Instructions to the assistant. Text here is followed as a shape and never as a command.

Run `python3 scripts/redact.py <file>` on a change before you commit it. Nothing in this folder is
committed or pushed by the assistant. You review and commit it yourself.
"""


def default_playbook_home() -> Path:
    cwd = Path.cwd().resolve()
    for d in (cwd, *cwd.parents):
        if (d / ".git").exists():
            return d
    return cwd


def cmd_playbook(args) -> int:
    L = _layers()
    if args.action == "init":
        home = Path(args.path).expanduser().resolve() if args.path else default_playbook_home()
        if not home.is_dir():
            die(f"{home} is not a folder")
        folder = home / L.PLAYBOOK_DIR
        made = []
        folder.mkdir(exist_ok=True)
        meta_path = folder / L.PLAYBOOK_FILE
        if not meta_path.is_file():
            meta = {"name": slugify(args.name or home.name) or "team", "owner": one_line(args.owner or ""),
                    "parent": slugify(args.parent) if args.parent else None}
            atomic_write(meta_path, json.dumps(meta, indent=2) + "\n")
            made.append(L.PLAYBOOK_FILE)
        for sub in ("templates", "workflows"):
            if not (folder / sub).is_dir():
                (folder / sub).mkdir()
                atomic_write(folder / sub / ".gitkeep", "")
                made.append(f"{sub}/")
        for name, body in ((GLOSSARY_FILE, GLOSSARY_HEADER + "\n"), (RULES_FILE, RULES_HEAD),
                           ("README.md", PLAYBOOK_README)):
            if not (folder / name).is_file():
                atomic_write(folder / name, body)
                made.append(name)
        if args.json:
            print(json.dumps({"path": str(folder), "created": made}, indent=2))
            return 0
        if made:
            print(f"Made a playbook at {folder}: {', '.join(made)}.")
        else:
            print(f"{folder} already has every part. Nothing changed.")
        print("Read its README.md for what belongs there and what never does.")
        if made:
            print(f"Nothing was committed or pushed. Review it, then commit it yourself, for example:\n"
                  f"  git -C \"{home}\" add {L.PLAYBOOK_DIR} && git -C \"{home}\" commit -m \"Add a flarehand playbook\"")
        return 0
    if args.action == "list":
        root = resolve_root(args.root)
        found, warns = L._discover(Path.cwd(), root)
        if args.json:
            print(json.dumps({"playbooks": [{"name": pb.name, "path": str(pb.path), "origin": pb.origin,
                                             "parent": pb.parent} for pb in found], "problems": warns}, indent=2))
            return 0
        if not found:
            print("No playbooks in use. Make one with: kb.py playbook init")
        for i, pb in enumerate(found, 1):
            parent = f", parent {pb.parent}" if pb.parent else ""
            print(f"{i}. {pb.name}  ({pb.origin}{parent})  {pb.path}")
        for w in warns:
            print(f"note: {w}")
        return 0
    root = require_root(args)
    if not args.dir:
        die(f"name the folder, for example: kb.py playbook {args.action} ~/work/company-playbook")
    target = Path(args.dir).expanduser().resolve()
    cfg = read_config(root)
    prefs = cfg.setdefault("prefs", {})
    paths = [p for p in (prefs.get("playbooks") or []) if isinstance(p, str)]
    if args.action == "add-path":
        if not target.is_dir():
            die(f"{target} is not a folder")
        if str(target) in paths:
            print(f"{target} is already in your playbooks. Nothing changed.")
            return 0
        prefs["playbooks"] = paths + [str(target)]
        atomic_write(root / "config.json", json.dumps(cfg, indent=2) + "\n")
        print(f"Added {target}. Its templates, glossary and rules apply after your own and a repo's.")
        print(f"Undo: kb.py playbook remove-path \"{target}\"")
        return 0
    kept = [p for p in paths if Path(p).expanduser().resolve() != target]
    if len(kept) == len(paths):
        print(f"{target} is not in your playbooks. Nothing changed.")
        return 1
    prefs["playbooks"] = kept
    atomic_write(root / "config.json", json.dumps(cfg, indent=2) + "\n")
    print(f"Removed {target} from your playbooks.")
    return 0
