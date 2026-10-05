#!/usr/bin/env python3
"""release_check.py - scan every tracked file for terms that must not be published.

The terms live in `.release-guard` at the repository root, one regular expression per line. The
file is local and gitignored, so the list itself is never published. Without it, this check says
so and passes, so a fresh clone and CI still build.

Usage:
    python3 tools/release_check.py            # scan every tracked file
    python3 tools/release_check.py --json

Exit codes: 0 clean or no guard file, 1 a term was found, 2 usage or git error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUARD = ROOT / ".release-guard"


def guard_pattern(path: Path = GUARD) -> re.Pattern | None:
    """The guard terms as one pattern, or None when there is no guard file."""
    if not path.is_file():
        return None
    terms = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.lstrip().startswith("#")]
    return re.compile("|".join(f"(?:{t})" for t in terms), re.IGNORECASE) if terms else None


def tracked_files(root: Path = ROOT) -> list[Path]:
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True)
    return [root / p for p in out.stdout.decode("utf-8").split("\0") if p]


def scan(pattern: re.Pattern, files: list[Path]) -> list[dict]:
    hits = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            m = pattern.search(line)
            if m:
                hits.append({"file": str(path.relative_to(ROOT)), "line": n, "term": m.group(0)})
    return hits


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--json", action="store_true", help="print the hits as JSON")
    args = p.parse_args(argv)
    pattern = guard_pattern()
    if pattern is None:
        print("No .release-guard file, so there is nothing to check against.")
        return 0
    try:
        hits = scan(pattern, tracked_files())
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"error: cannot list tracked files: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(hits, indent=2))
    else:
        for h in hits:
            print(f"{h['file']}:{h['line']}: {h['term']}")
        print(f"{len(hits)} hit(s)." if hits else "Clean: no guarded term in any tracked file.")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
