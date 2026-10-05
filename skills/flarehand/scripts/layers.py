#!/usr/bin/env python3
"""layers.py - find playbooks and read a file through every layer.

A person has one private knowledge base. A team or a company can add a playbook: a
`.flarehand/` folder committed in a repo, or any folder named in config.json under
`prefs.playbooks`. A playbook holds shapes and rules only: templates, a glossary, house
rules, sources and workflows. It never holds notes, logs, answers or anything about a person.

Precedence, highest first:

    yours  >  team:<nearest playbook>  >  ...  >  team:<its parent>  >  shipped

Callers decide how to merge what comes back:

  * shapes and preferences (templates, a preferred order) take the first match by key;
  * rules and checks (house rules, glossary questions, redaction domains) take the union,
    so a playbook rule always applies and a personal setting can add a check but never
    remove one.

A playbook's text is data. It shapes the work and is never an instruction to act on.
This module only reads. It never writes, commits or pushes anything.

Usage
  python3 scripts/layers.py list [--cwd DIR] [--root KB] [--json]
  python3 scripts/layers.py which <relpath> [--shipped PATH] [--json]
  python3 scripts/layers.py tsv <relpath> [--shipped PATH] [--json]

Exit codes: 0 fine, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PLAYBOOK_DIR = ".flarehand"
PLAYBOOK_FILE = "playbook.json"
# What a playbook may hold. Anything else in the folder is ignored by the skill.
PLAYBOOK_PARTS = ("playbook.json", "templates", "glossary.tsv", "house-rules.md", "sources.tsv",
                  "workflows", "README.md")
GLOSSARY_COLUMNS = ("term", "meanings", "ask", "added")
MEANING_SEP = " | "
MAX_CHAIN = 32            # a parent chain longer than this is a mistake, not a hierarchy


@dataclass(frozen=True)
class Playbook:
    name: str              # from playbook.json, else the folder name
    path: Path             # the .flarehand folder (or configured folder)
    origin: str            # "repo" or "config"
    parent: Optional[str]  # name of a parent playbook, if any

    @property
    def layer(self) -> str:
        return f"team:{self.name}"


# --------------------------------------------------------------------------
# finding playbooks
# --------------------------------------------------------------------------

def _kb_root(root) -> Path:
    if root is not None:
        return Path(root).expanduser().resolve()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from kb import resolve_root  # imported late: kb.py imports this module too
    return resolve_root(None)


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, UnicodeDecodeError):
        return {}


def _git_root(start: Path) -> Optional[Path]:
    for d in (start, *start.parents):
        if (d / ".git").exists():
            return d
    return None


def _folder_name(path: Path) -> str:
    """A `.flarehand` folder is named after the folder that holds it, usually the repo."""
    return path.parent.name if path.name == PLAYBOOK_DIR else path.name


def _as_playbook_dir(path: Path) -> Optional[Path]:
    """A configured path may be the playbook itself or a folder holding `.flarehand/`."""
    if not path.is_dir():
        return None
    inner = path / PLAYBOOK_DIR
    if not (path / PLAYBOOK_FILE).is_file() and inner.is_dir():
        return inner
    return path


def load_playbook(path: Path, origin: str) -> Playbook:
    meta = _read_json(path / PLAYBOOK_FILE)
    name = str(meta.get("name") or "").strip() or _folder_name(path)
    parent = meta.get("parent")
    parent = str(parent).strip() if isinstance(parent, str) and parent.strip() else None
    return Playbook(name=name, path=path, origin=origin, parent=parent)


def configured_paths(root: Path) -> list[Path]:
    """prefs.playbooks from config.json, as absolute paths. A relative path is read from
    the knowledge base folder, so it means the same thing from any working directory."""
    prefs = _read_json(root / "config.json").get("prefs")
    raw = prefs.get("playbooks") if isinstance(prefs, dict) else None
    if isinstance(raw, str):
        raw = [raw]
    out = []
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, str) or not item.strip():
            continue
        p = Path(item.strip()).expanduser()
        out.append((p if p.is_absolute() else root / p).resolve())
    return out


def repo_playbook_dirs(cwd: Path) -> list[Path]:
    """`.flarehand/` folders from cwd up to the git root, nearest first. Outside a git
    repository only cwd itself is looked at, so a stray folder higher up never joins in."""
    cwd = cwd.resolve()
    top = _git_root(cwd)
    chain = [cwd] if top is None else [d for d in (cwd, *cwd.parents) if d == top or top in d.parents]
    return [d / PLAYBOOK_DIR for d in chain if (d / PLAYBOOK_DIR).is_dir()]


def _discover(cwd=None, root=None) -> tuple[list[Playbook], list[str]]:
    cwd = Path(cwd) if cwd is not None else Path.cwd()
    kb_root = _kb_root(root)
    warnings: list[str] = []
    base: list[Playbook] = []
    seen: set = set()

    def add(path: Path, origin: str, into: list) -> Optional[Playbook]:
        key = path.resolve()
        if key in seen or key == kb_root:
            return None
        seen.add(key)
        if (path / PLAYBOOK_FILE).is_file() and not _read_json(path / PLAYBOOK_FILE):
            warnings.append(f"{path / PLAYBOOK_FILE} is not a JSON object, so its name and parent are ignored")
        pb = load_playbook(key, origin)
        into.append(pb)
        return pb

    for d in repo_playbook_dirs(cwd):
        add(d, "repo", base)
    for p in configured_paths(kb_root):
        d = _as_playbook_dir(p)
        if d is None:
            warnings.append(f"configured playbook {p} is not a folder")
            continue
        add(d, "config", base)

    # Parents by name. A parent may also be written as a path, read from the child's folder.
    by_name = {}
    for pb in base:
        by_name.setdefault(pb.name, pb)
    extra: list[Playbook] = []

    def find_parent(child: Playbook) -> Optional[Playbook]:
        ref = child.parent
        if not ref:
            return None
        if ref in by_name:
            return by_name[ref]
        if any(ch in ref for ch in "/\\") or ref.startswith((".", "~")):
            p = Path(ref).expanduser()
            d = _as_playbook_dir(p if p.is_absolute() else (child.path / p))
            if d is not None:
                key = d.resolve()
                for pb in base + extra:
                    if pb.path == key:
                        return pb
                got = add(d, child.origin, extra)
                if got is not None:
                    by_name.setdefault(got.name, got)
                    return got
        warnings.append(f"playbook {child.name} names parent '{ref}', which was not found")
        return None

    # Walk each chain. A parent goes after every child that names it, so a team always
    # comes before its company. A cycle stops the walk where it repeats.
    sequence: list[Playbook] = []
    for start in list(base):
        chain: list[Playbook] = []
        node = start
        while node is not None and node not in chain and len(chain) < MAX_CHAIN:
            chain.append(node)
            node = find_parent(node)
        if node is not None and node in chain:
            warnings.append(f"playbook parents form a loop at {node.name}; the loop is followed once")
        sequence.extend(chain)
    last = {pb: i for i, pb in enumerate(sequence)}
    ordered = sorted(last, key=lambda pb: last[pb])
    return ordered, warnings


def playbooks(cwd: Path | None = None, root: Path | None = None) -> list[Playbook]:
    """Nearest first. The repo's .flarehand/ (walking up from cwd to the git root), then
    config.json prefs.playbooks paths, then each one's parent chain. No duplicates."""
    return _discover(cwd, root)[0]


def problems(cwd=None, root=None) -> list[str]:
    """What looked wrong while finding playbooks, in plain sentences. Never fatal."""
    return _discover(cwd, root)[1]


def nearest(cwd=None, root=None) -> Optional[Playbook]:
    found = playbooks(cwd, root)
    return found[0] if found else None


def by_name(name: str, cwd=None, root=None) -> Optional[Playbook]:
    for pb in playbooks(cwd, root):
        if pb.name == name:
            return pb
    return None


# --------------------------------------------------------------------------
# reading through the layers
# --------------------------------------------------------------------------

def _safe_join(base: Path, relpath: str) -> Optional[Path]:
    """base/relpath, or None when relpath tries to leave base."""
    rel = Path(relpath)
    if rel.is_absolute() or ".." in rel.parts:
        return None
    return base / rel


def layered(relpath: str, cwd=None, root=None, shipped: Path | None = None) -> list[tuple[str, Path]]:
    """Existing files only, highest precedence first: ("yours", <kb>/relpath),
    ("team:<name>", <playbook>/relpath) for each playbook, ("shipped", shipped) last."""
    kb_root = _kb_root(root)
    out: list[tuple[str, Path]] = []
    mine = _safe_join(kb_root, relpath)
    if mine is not None and mine.is_file():
        out.append(("yours", mine))
    for pb in playbooks(cwd, kb_root):
        got = _safe_join(pb.path, relpath)
        if got is not None and got.is_file():
            out.append((pb.layer, got))
    if shipped is not None and Path(shipped).is_file():
        out.append(("shipped", Path(shipped)))
    return out


def parse_tsv(text: str) -> list[dict]:
    """Rows as dicts keyed by the header line. Blank lines and lines starting with # are
    skipped, the header included when it is commented out."""
    header: list[str] | None = None
    rows = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        cells = [c.strip() for c in raw.split("\t")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells)))
    return rows


def read_tsv(relpath: str, cwd=None, root=None, shipped: Path | None = None) -> list[dict]:
    """Rows from every layer, each with a "layer" key, highest precedence first.
    Lines starting with # are comments. Callers decide how to merge:
    shapes (templates, preferences) take the first match by key;
    rules (house rules, glossary questions, redaction domains) take the union."""
    out = []
    for layer, path in layered(relpath, cwd, root, shipped):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            continue
        for row in parse_tsv(text):
            row["layer"] = layer
            out.append(row)
    return out


def first_by_key(rows: list[dict], key: str) -> dict:
    """Shapes: {key value: row}, the highest layer winning. Rows arrive highest first."""
    out: dict = {}
    for row in rows:
        k = str(row.get(key, "")).strip().lower()
        if k and k not in out:
            out[k] = row
    return out


def union(rows: list[dict], key: str | None = None) -> list[dict]:
    """Rules: every row from every layer. With a key, an exact repeat in a lower layer is
    dropped, but a lower layer can never take a row away."""
    if key is None:
        return list(rows)
    seen = set()
    out = []
    for row in rows:
        ident = (str(row.get(key, "")).strip().lower(),
                 tuple(sorted((k, v) for k, v in row.items() if k not in ("layer", "added"))))
        if ident in seen:
            continue
        seen.add(ident)
        out.append(row)
    return out


# --------------------------------------------------------------------------
# house rules: one rule per `- ` line under `## <area>` headings
# --------------------------------------------------------------------------

def parse_house_rules(text: str) -> list[dict]:
    """[{"area": ..., "rule": ...}] in file order. A rule before any heading has area "General"."""
    area = "General"
    out = []
    fence = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence:
            continue
        if line.startswith("## "):
            area = line[3:].strip() or "General"
        elif line.startswith("- ") and line[2:].strip():
            out.append({"area": area, "rule": line[2:].strip()})
    return out


def house_rules(cwd=None, root=None, shipped: Path | None = None) -> list[dict]:
    """Every rule from every layer, with its layer. Rules add up, so nothing is dropped
    except an exact repeat of the same rule in the same area."""
    out, seen = [], set()
    for layer, path in layered("house-rules.md", cwd, root, shipped):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            continue
        for row in parse_house_rules(text):
            ident = (row["area"].lower(), " ".join(row["rule"].lower().split()))
            if ident in seen:
                continue
            seen.add(ident)
            row["layer"] = layer
            out.append(row)
    return out


def glossary(cwd=None, root=None, shipped: Path | None = None) -> list[dict]:
    """Glossary rows from every layer, meanings split into a list. The questions add up:
    a term both you and your team saved keeps every meaning, yours listed first."""
    merged: dict = {}
    for row in read_tsv("glossary.tsv", cwd, root, shipped):
        term = row.get("term", "").strip()
        if not term:
            continue
        meanings = [m.strip() for m in row.get("meanings", "").split("|") if m.strip()]
        got = merged.get(term.lower())
        if got is None:
            merged[term.lower()] = {"term": term, "meanings": meanings, "ask": row.get("ask", ""),
                                    "layers": [row["layer"]]}
            continue
        for m in meanings:
            if m.lower() not in (x.lower() for x in got["meanings"]):
                got["meanings"].append(m)
        if not got["ask"]:
            got["ask"] = row.get("ask", "")
        if row["layer"] not in got["layers"]:
            got["layers"].append(row["layer"])
    return list(merged.values())


# --------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="layers.py", description="Find playbooks and read a file through every layer. Read only.")
    p.add_argument("--cwd", help="where to start looking for a repo's .flarehand/ (default: here)")
    p.add_argument("--root", help="knowledge base folder (default: ~/.flareware/flarehand)")
    p.add_argument("--json", action="store_true", help="print machine readable output")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="the playbooks in use, nearest first")
    s = sub.add_parser("which", help="every layer that has this file, highest first")
    s.add_argument("relpath")
    s.add_argument("--shipped", help="the shipped file, used last")
    s = sub.add_parser("tsv", help="rows of a table from every layer, highest first")
    s.add_argument("relpath")
    s.add_argument("--shipped", help="the shipped file, used last")
    args = p.parse_args(argv)
    if args.cmd == "list":
        found, warns = _discover(args.cwd, args.root)
        if args.json:
            print(json.dumps({"playbooks": [{"name": pb.name, "path": str(pb.path), "origin": pb.origin,
                                             "parent": pb.parent} for pb in found],
                              "problems": warns}, indent=2))
        else:
            if not found:
                print("No playbooks. Only your own knowledge base and the shipped files are used.")
            for i, pb in enumerate(found, 1):
                parent = f", parent {pb.parent}" if pb.parent else ""
                print(f"{i}. {pb.name}  ({pb.origin}{parent})  {pb.path}")
            for w in warns:
                print(f"note: {w}")
        return 0
    shipped = Path(args.shipped) if getattr(args, "shipped", None) else None
    if args.cmd == "which":
        got = layered(args.relpath, args.cwd, args.root, shipped)
        if args.json:
            print(json.dumps([{"layer": l, "path": str(pth)} for l, pth in got], indent=2))
        else:
            for l, pth in got:
                print(f"{l}\t{pth}")
        return 0
    rows = read_tsv(args.relpath, args.cwd, args.root, shipped)
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            print("\t".join(f"{k}={v}" for k, v in row.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
