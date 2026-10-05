#!/usr/bin/env python3
"""bump_version.py - keep every manifest's version in lockstep.

The plugin carries its version in one manifest per tool (Claude, Codex, Cursor, Gemini) and in the
`flarehand.version` metadata of each skill. They must all agree. `.version-bump.json` at the
repository root lists where each one lives:

  {"files": [{"path": ".claude-plugin/plugin.json", "field": "version"}, ...],
   "skill_metadata": {"glob": "skills/*/SKILL.md", "key": "flarehand.version"}}

A `field` is a dotted path, and a number in it indexes a list (`plugins.0.version`). A skill
without the metadata key is left alone.

Usage
  python3 tools/bump_version.py                 # show every version, exit 1 if they differ
  python3 tools/bump_version.py check
  python3 tools/bump_version.py set 0.2.0
  python3 tools/bump_version.py bump patch      # or minor, or major
  python3 tools/bump_version.py bump minor --dry-run

Exit codes: 0 fine, 1 versions differ or a file is missing, 2 usage error.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")


def load_config(root: Path) -> dict:
    return json.loads((root / ".version-bump.json").read_text(encoding="utf-8"))


def _walk(data, field: str):
    """The container and key holding a dotted field, or (None, None)."""
    parts = field.split(".")
    node = data
    for part in parts[:-1]:
        if isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        elif isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None, None
    last = parts[-1]
    if isinstance(node, list) and last.isdigit() and int(last) < len(node):
        return node, int(last)
    if isinstance(node, dict) and last in node:
        return node, last
    return None, None


def _meta_pattern(key: str) -> re.Pattern:
    return re.compile(r"^(\s+" + re.escape(key) + r"\s*:\s*)([\"']?)([^\"'\n]*)([\"']?)\s*$", re.M)


def read_versions(root: Path, config: dict) -> dict[str, str | None]:
    """Every location and the version it holds. None means missing."""
    out: dict[str, str | None] = {}
    for item in config.get("files", []):
        path = root / item["path"]
        key = f"{item['path']}:{item['field']}"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            out[key] = None
            continue
        node, k = _walk(data, item["field"])
        out[key] = str(node[k]) if node is not None else None
    meta = config.get("skill_metadata")
    if meta:
        pattern = _meta_pattern(meta["key"])
        for path in sorted(root.glob(meta["glob"])):
            m = pattern.search(path.read_text(encoding="utf-8"))
            if m:
                out[f"{path.relative_to(root).as_posix()}:{meta['key']}"] = m.group(3).strip()
    return out


def write_version(root: Path, config: dict, version: str, dry_run: bool = False) -> list[str]:
    """Set every location to version. Returns what changed."""
    changed = []
    for item in config.get("files", []):
        path = root / item["path"]
        data = json.loads(path.read_text(encoding="utf-8"))
        node, k = _walk(data, item["field"])
        if node is None:
            raise KeyError(f"{item['path']} has no field {item['field']}")
        if node[k] != version:
            node[k] = version
            changed.append(item["path"])
            if not dry_run:
                path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    meta = config.get("skill_metadata")
    if meta:
        pattern = _meta_pattern(meta["key"])
        for path in sorted(root.glob(meta["glob"])):
            text = path.read_text(encoding="utf-8")
            m = pattern.search(text)
            if not m or m.group(3).strip() == version:
                continue
            quote = m.group(2) or '"'
            new = text[:m.start()] + f"{m.group(1)}{quote}{version}{quote}" + text[m.end():]
            changed.append(path.relative_to(root).as_posix())
            if not dry_run:
                path.write_text(new, encoding="utf-8")
    return changed


def bumped(version: str, part: str) -> str:
    m = SEMVER.match(version)
    if not m:
        raise ValueError(f"{version} is not a semantic version")
    major, minor, patch = (int(x) for x in m.groups())
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bump_version.py", description="Keep every manifest version in lockstep.")
    ap.add_argument("--root", default=str(ROOT), help="repository root (default: the parent of tools/)")
    ap.add_argument("--dry-run", action="store_true", help="say what would change, change nothing")
    ap.add_argument("--json", action="store_true")
    # The same options after the command, so `bump minor --dry-run` works as well as `--dry-run bump minor`.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=argparse.SUPPRESS)
    common.add_argument("--dry-run", action="store_true", default=argparse.SUPPRESS)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("check", parents=[common], help="show every version, exit 1 if they differ")
    s = sub.add_parser("set", parents=[common], help="set every version to this one")
    s.add_argument("version")
    b = sub.add_parser("bump", parents=[common], help="raise the version")
    b.add_argument("part", choices=("major", "minor", "patch"))
    args = ap.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    try:
        config = load_config(root)
    except (OSError, ValueError) as e:
        print(f"error: cannot read {root / '.version-bump.json'}: {e}", file=sys.stderr)
        return 2
    versions = read_versions(root, config)

    if args.cmd in (None, "check"):
        distinct = {v for v in versions.values()}
        ok = None not in distinct and len(distinct) == 1
        if args.json:
            print(json.dumps({"versions": versions, "in_step": ok}, indent=2))
        else:
            for where, v in versions.items():
                print(f"{v or 'MISSING':12} {where}")
            print("\nIn step." if ok else "\nNot in step. Run `bump_version.py set <version>`.")
        return 0 if ok else 1

    if args.cmd == "set":
        target = args.version
        if not SEMVER.match(target):
            print(f"error: {target} is not a semantic version such as 1.2.3", file=sys.stderr)
            return 2
    else:
        first = versions.get(f"{config['files'][0]['path']}:{config['files'][0]['field']}")
        if not first:
            print("error: the first file in .version-bump.json has no version", file=sys.stderr)
            return 1
        target = bumped(first, args.part)
    try:
        changed = write_version(root, config, target, dry_run=args.dry_run)
    except (OSError, ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"version": target, "changed": changed, "dry_run": args.dry_run}, indent=2))
    else:
        verb = "Would set" if args.dry_run else "Set"
        print(f"{verb} {target} in {len(changed)} file(s)" + (":" if changed else "."))
        for c in changed:
            print(f"  {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
