#!/usr/bin/env python3
"""evidence.py - keep word-for-word copies of anything you rely on.

A cited answer is only repeatable if the thing it cites cannot move. This
script copies the exact text, names it after a hash of its content, and records
where it came from.

Nothing lands in your knowledge base on its own. A new snapshot goes to a
staging area for this session. It moves into the knowledge base only when you
keep it, which normally happens when you say yes to saving the work that cites
it. Discard what you do not need. Same text in means the same reference out,
so a citation never changes when a snapshot moves from staging to kept.

The staging area is private to your user account. Staged snapshots older than
seven days are dropped the next time you stage one. Keeping a snapshot re-hashes
it first, so a staged file that was changed on disk is refused.

Staging text that holds a password, key, token, connection string, government id
or card number prints a warning. Keeping it follows the person's answer to
`kb.py choice`: asked the first time, then said out loud each time it is used.

Commands
  add       stage a snapshot from a file, an argument or standard input
  keep      move staged snapshots into the knowledge base
  discard   throw staged snapshots away
  get       print a snapshot, staged or kept
  list      list snapshots, with where each one is
  verify    re-hash every kept snapshot and report anything edited
  compare   check whether a source still says what the snapshot says

It refuses to snapshot this skill's own reference files. Those are guidance,
not evidence, and citing them would make an answer look grounded when it is not.

`ground.py fetch` and `ground.py source add` stage through the same code, then
record where the text came from in the session's source ledger.

Exit codes: 0 fine, 1 a check failed or something was refused, 2 usage or file error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from redact import credential_hits  # noqa: E402  one guard, shared with every writer
from kb import (_utf8_console, atomic_write, kb_lock, require_root, sensitive_choice,  # noqa: E402
                session_only_refusal, today)

SKILL_DIR = Path(__file__).resolve().parent.parent
HASH_LEN = 12
HASH_RE = re.compile(rf"^[0-9a-f]{{{HASH_LEN}}}$")
LEDGER = "index.jsonl"
STAGING_MAX_AGE_DAYS = 7
from _text import is_self_source  # noqa: E402  one definition, shared with the checkers


def normalize_newlines(text: str) -> str:
    """CRLF and CR become LF, so the hash matches what read_text() gives back on every platform."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def digest(text: str) -> str:
    return hashlib.sha256(normalize_newlines(text).encode("utf-8")).hexdigest()[:HASH_LEN]


def staging_dir(root: Path) -> Path:
    """One staging area per knowledge base, outside it, in the system temp folder."""
    key = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:10]
    return Path(tempfile.gettempdir()) / "flarehand-staging" / key


def kept_dir(root: Path) -> Path:
    return root / "evidence"


def clean_hash(value: str) -> str | None:
    """Accept `abc123...`, `abc123....txt` or `evidence/abc123....txt`. Anything else is refused,
    so a crafted value such as ../../somewhere can never become a path."""
    h = value.strip().replace("\\", "/").split("/")[-1]
    if h.endswith(".txt"):
        h = h[:-4]
    return h if HASH_RE.match(h) else None


# ---------------------------------------------------------------- credentials

# os.environ["API_KEY"] names a secret without holding one. Keeping that is fine.
ENV_REFERENCE = re.compile(r"""(?:os\.environ|getenv|process\.env|ENV\[|System\.getenv|\$\{?[A-Z_]+\}?)""")


def describe_hits(hits: list[dict]) -> str:
    return ", ".join(f"{h['means']} on line {h['line']}" for h in hits[:5]) + (
        f", and {len(hits) - 5} more" if len(hits) > 5 else "")


# ---------------------------------------------------------------- private staging

def _ensure_private_dir(folder: Path) -> None:
    """Create the staging folder readable by this user only. On a shared machine the temp folder is
    shared, so a folder owned by someone else is refused rather than written into."""
    folder.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(folder, 0o700)
    except OSError:
        pass
    if hasattr(os, "getuid"):
        try:
            owner = folder.stat().st_uid
        except OSError:
            owner = os.getuid()
        if owner != os.getuid():
            print(f"error: the staging folder {folder} belongs to another user. Remove it or pick another "
                  f"temp folder, then try again.", file=sys.stderr)
            sys.exit(2)


def _write_private(path: Path, text: str, append: bool = False) -> None:
    """Write a file only this user can read. Newlines are written as LF on every platform."""
    _ensure_private_dir(path.parent)
    flags = os.O_WRONLY | os.O_CREAT | (os.O_APPEND if append else os.O_TRUNC)
    fd = os.open(str(path), flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _expire_staged(root: Path) -> int:
    """Drop staged files older than STAGING_MAX_AGE_DAYS. Returns how many were dropped."""
    folder = staging_dir(root)
    if not folder.is_dir():
        return 0
    cutoff = time.time() - STAGING_MAX_AGE_DAYS * 86400
    dropped = 0
    for path in folder.glob("*.txt"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
                dropped += 1
        except OSError:
            continue
    if dropped:
        rows = [r for r in read_ledger(folder) if (folder / f"{r['hash']}.txt").is_file()]
        _write_ledger(folder, rows)
    return dropped


# ---------------------------------------------------------------- ledger

def read_ledger(folder: Path) -> list[dict]:
    path = folder / LEDGER
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and clean_hash(str(row.get("hash", ""))):
            rows.append(row)
    return rows


def _is_staging(folder: Path) -> bool:
    return folder.parent.name == "flarehand-staging"


def _remember_source_anywhere(root: Path, h: str, source: str) -> None:
    """The row may be in staging or already kept, and `add` without `--keep` only knew
    about staging. So a snapshot promoted earlier never gained its second source."""
    for folder in (kept_dir(root), staging_dir(root)):
        if any(r.get("hash") == h for r in read_ledger(folder)):
            _remember_source(folder, h, source)
            return


def _remember_source(folder: Path, h: str, source: str) -> None:
    """A snapshot's filename is a hash of its text, so the same paragraph from two pages is
    one file. Keeping only the first source loses the second one for good, and provenance
    is the whole point of a snapshot. Keep both."""
    source = " ".join((source or "").split())
    if not source or source == "unstated":
        return
    rows = read_ledger(folder)
    for row in rows:
        if row.get("hash") != h:
            continue
        have = row.get("sources") or ([row["source"]] if row.get("source") else [])
        if source in have:
            return
        row["sources"] = have + [source]
        row["source"] = have[0] if have else source
        _write_ledger(folder, rows)
        return


def append_ledger(folder: Path, row: dict) -> None:
    if _is_staging(folder):
        _write_private(folder / LEDGER, json.dumps(row) + "\n", append=True)
        return
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / LEDGER).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def _write_ledger(folder: Path, rows: list[dict]) -> None:
    if rows:
        text = "".join(json.dumps(r) + "\n" for r in rows)
        if _is_staging(folder):
            _write_private(folder / LEDGER, text)
        else:
            atomic_write(folder / LEDGER, text)
    else:
        (folder / LEDGER).unlink(missing_ok=True)


def locate(root: Path, h: str) -> tuple[Path | None, str]:
    """Find a snapshot. Returns (path, 'kept'|'staged') or (None, '')."""
    for folder, where in ((kept_dir(root), "kept"), (staging_dir(root), "staged")):
        path = folder / f"{h}.txt"
        if path.is_file():
            return path, where
    return None, ""


def is_self_citation(text: str, source: str) -> str | None:
    """Return a reason if this text is the skill's own guidance rather than evidence."""
    if source and is_self_source(source):
        return f'the source "{source}" names this skill\'s own files'
    snippet = [l.strip() for l in text.splitlines() if len(l.strip()) > 40][:40]
    if not snippet:
        return None
    for path in SKILL_DIR.rglob("*"):
        if path.suffix.lower() not in {".md", ".tsv", ".py"} or not path.is_file():
            continue
        # The eval cases quote sample pages on purpose. They are test data, not guidance.
        if "evals" in path.relative_to(SKILL_DIR).parts[:1]:
            continue
        try:
            body = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        shared = sum(1 for l in snippet if l in body)
        if shared >= max(3, int(len(snippet) * 0.6)):
            return f"it matches {path.relative_to(SKILL_DIR).as_posix()}, which is part of this skill"
    return None


def _read_stdin(flags: str) -> str | None:
    """Standard input, unless it is a terminal. A script must never sit waiting for someone to type."""
    if sys.stdin is None or sys.stdin.isatty():
        print(f"error: nothing to read. Pass {flags}, or pipe the text in.", file=sys.stderr)
        return None
    return sys.stdin.read()


def stage(root: Path, text: str, source: str = "", kind: str = "text", note: str = "",
          sensitivity: str = "internal", keep: bool = False, extra: dict | None = None) -> dict:
    """Stage (or, after a yes, keep) one snapshot. The one path every writer uses, so
    `evidence.py add` and `ground.py fetch` can never disagree about what a snapshot is.

    Returns {"hash", "ref", "status", "hits"} on success, or {"refused": reason, "code": n}.
    `extra` adds fields to the ledger row, such as where a fetch landed. Nothing here prints.
    """
    text = normalize_newlines(text)
    if not text.strip():
        return {"refused": "nothing to save. Pass --file, --text, or pipe text in.", "code": 2}
    reason = is_self_citation(text, source or "")
    if reason:
        return {"refused": f"{reason}. This skill's references are guidance, not evidence. Cite the page, "
                           f"ticket, file or document they point you at, and snapshot that instead.", "code": 1}
    hits = credential_hits(text)
    if keep:
        # Staging is temporary and private. Keeping is the moment it enters the knowledge base,
        # so that is where the once-asked choice applies.
        why = sensitive_choice(root, "this snapshot", text)
        if why:
            return {"refused": why, "code": 1}

    _expire_staged(root)
    h = digest(text)
    kept_path, where = locate(root, h)
    target_folder = kept_dir(root) if keep else staging_dir(root)
    row = {
        "hash": h,
        "file": f"evidence/{h}.txt",
        "source": " ".join((source or "unstated").split()),
        "kind": kind,
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "captured_on": today(),
        "bytes": len(text.encode("utf-8")),
        "lines": text.count("\n") + 1,
        "note": note or "",
        "sensitivity": sensitivity,
    }
    if extra:
        row.update({k: v for k, v in extra.items() if k not in row})

    if kept_path and where == "kept":
        status = "already kept"
        _remember_source_anywhere(root, h, row.get("source", ""))
    elif kept_path and where == "staged" and not keep:
        status = "already staged"
        _remember_source_anywhere(root, h, row.get("source", ""))
    else:
        if keep:
            atomic_write(target_folder / f"{h}.txt", text)
        else:
            _write_private(target_folder / f"{h}.txt", text)
        if not any(r["hash"] == h for r in read_ledger(target_folder)):
            append_ledger(target_folder, row)
        if kept_path and where == "staged" and keep:
            _remove_staged(root, h)
        status = "kept" if keep else "staged"
    return {"hash": h, "ref": f"evidence/{h}.txt", "status": status, "hits": hits}


def cmd_add(args) -> int:
    root = require_root(args)
    if args.file:
        try:
            text = Path(args.file).expanduser().read_text(encoding="utf-8-sig", errors="replace")
        except OSError as e:
            print(f"error: cannot read {args.file}: {e}", file=sys.stderr)
            return 2
    elif args.text is not None:
        text = args.text
    else:
        text = _read_stdin("--file or --text")
        if text is None:
            return 2

    got = stage(root, text, args.source or "", args.kind, args.note or "", args.sensitivity, args.keep)
    if "refused" in got:
        word = "Refused" if got["code"] == 1 else "error"
        print(f"{word}: {got['refused']}", file=sys.stderr)
        return got["code"]
    h, status, hits, ref = got["hash"], got["status"], got["hits"], got["ref"]
    if hits:
        print(f"WARNING: this text holds {describe_hits(hits)}. If it is live, treat it as exposed "
              f"and rotate it.", file=sys.stderr)
        if status == "staged":
            print("Keeping it asks first, or follows the answer they gave to kb.py choice.",
                  file=sys.stderr)
    if args.json:
        print(json.dumps({"hash": h, "ref": ref, "status": status,
                          "credentials": [{"rule": x["name"], "line": x["line"]} for x in hits]}, indent=2))
    else:
        print(f"{status.capitalize()}: {ref}")
        print(f"Cite it as: [verified: {ref}]")
        if status == "staged":
            print("It is not in your knowledge base yet. It is kept when you save the work that cites it.")
    return 0


def _remove_staged(root: Path, h: str) -> None:
    folder = staging_dir(root)
    (folder / f"{h}.txt").unlink(missing_ok=True)
    rows = [r for r in read_ledger(folder) if r["hash"] != h]
    _write_ledger(folder, rows)


def keep_refusal(root: Path, h: str) -> str | None:
    """Why a staged snapshot cannot be kept right now, or None when it can."""
    src = staging_dir(root) / f"{h}.txt"
    try:
        text = src.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"cannot read the staged file: {e}"
    if digest(text) != h:
        return "the staged file no longer matches its hash. It was changed on disk. Discard it and stage it again"
    return sensitive_choice(root, "this snapshot", text)


def keep(root: Path, hashes: list[str]) -> tuple[list[str], list[str], list[dict]]:
    """Move staged snapshots into the knowledge base. Returns (kept, missing, refused).
    Each refused entry is {"hash": h, "why": reason}. A snapshot is re-hashed before it moves."""
    staged = {r["hash"]: r for r in read_ledger(staging_dir(root))}
    kept, missing, refused = [], [], []
    for h in hashes:
        src = staging_dir(root) / f"{h}.txt"
        if (kept_dir(root) / f"{h}.txt").is_file():
            kept.append(h)
            continue
        if not src.is_file():
            missing.append(h)
            continue
        why = keep_refusal(root, h)
        if why:
            refused.append({"hash": h, "why": why})
            continue
        kept_dir(root).mkdir(parents=True, exist_ok=True)
        text = normalize_newlines(src.read_text(encoding="utf-8", errors="replace"))
        if digest(text) != h:
            # it changed between the fitness check and here, so it is not what was approved
            refused.append({"hash": h, "why": "the staged file changed while it was being kept"})
            continue
        _write_private(kept_dir(root) / f"{h}.txt", text)
        row = staged.get(h, {"hash": h, "file": f"evidence/{h}.txt", "source": "unstated",
                             "captured_on": today()})
        row["kept_on"] = today()
        if not any(r["hash"] == h for r in read_ledger(kept_dir(root))):
            append_ledger(kept_dir(root), row)
        _remove_staged(root, h)
        kept.append(h)
    return kept, missing, refused


def cmd_keep(args) -> int:
    root = require_root(args)
    reason = session_only_refusal(root)
    if reason:
        print(reason, file=sys.stderr)
        return 1
    if args.all:
        hashes = [r["hash"] for r in read_ledger(staging_dir(root))]
    else:
        hashes = []
        for v in args.hashes:
            h = clean_hash(v)
            if not h:
                print(f"error: '{v}' is not a snapshot reference", file=sys.stderr)
                return 2
            hashes.append(h)
    if not hashes:
        print("Nothing staged to keep.")
        return 0
    kept, missing, refused = keep(root, hashes)
    if args.json:
        print(json.dumps({"kept": kept, "missing": missing, "refused": refused}, indent=2))
    else:
        for h in kept:
            print(f"Kept evidence/{h}.txt")
        for h in missing:
            print(f"Not found in staging: {h}", file=sys.stderr)
        for r in refused:
            print(f"Refused {r['hash']}: {r['why']}.", file=sys.stderr)
    return 1 if (missing or refused) else 0


def cmd_discard(args) -> int:
    root = require_root(args)
    folder = staging_dir(root)
    if args.all:
        count = len(read_ledger(folder))
        shutil.rmtree(folder, ignore_errors=True)
        print(f"Discarded {count} staged snapshot(s).")
        return 0
    done = 0
    for v in args.hashes:
        h = clean_hash(v)
        if h and (folder / f"{h}.txt").is_file():
            _remove_staged(root, h)
            done += 1
    print(f"Discarded {done} staged snapshot(s).")
    return 0


def cmd_get(args) -> int:
    root = require_root(args)
    h = clean_hash(args.hash)
    if not h:
        print(f"error: '{args.hash}' is not a snapshot reference", file=sys.stderr)
        return 2
    path, _ = locate(root, h)
    if not path:
        print(f"error: no snapshot {h}.txt, kept or staged", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > args.max_chars:
        print(text[: args.max_chars])
        print(f"\n... truncated at {args.max_chars} characters of {len(text)}. Raise --max-chars to see more.")
    else:
        print(text, end="")
    return 0


def cmd_compare(args) -> int:
    """Compare a snapshot with the source's current text. A comparison, not a judgment.

    Re-read the source (fetch the same URL, read the same file or revision, or ask the same
    MCP server for the same item), save what it says now, and pass that here. Identical means the citation still holds. Anything else prints the diff.
    """
    import difflib
    root = require_root(args)
    h = clean_hash(args.hash)
    if not h:
        print(f"error: '{args.hash}' is not a snapshot reference", file=sys.stderr)
        return 2
    path, _ = locate(root, h)
    if not path:
        print(f"error: no snapshot {h}.txt, kept or staged", file=sys.stderr)
        return 2
    if args.file:
        try:
            current = Path(args.file).expanduser().read_text(encoding="utf-8-sig", errors="replace")
        except OSError as e:
            print(f"error: cannot read {args.file}: {e}", file=sys.stderr)
            return 2
    else:
        current = _read_stdin("--file")
        if current is None:
            return 2
    current = normalize_newlines(current)
    old = normalize_newlines(path.read_text(encoding="utf-8", errors="replace"))

    def squash(s: str) -> str:
        return " ".join(s.split())

    if old == current:
        verdict = "identical"
    elif squash(old) == squash(current):
        verdict = "whitespace-only"
    else:
        verdict = "changed"
    record_compare(root, h, verdict)
    diff = []
    if verdict == "changed":
        diff = list(difflib.unified_diff(old.splitlines(), current.splitlines(),
                                         fromfile=f"snapshot {h}", tofile="source now", lineterm="", n=1))
    if args.json:
        print(json.dumps({"hash": h, "verdict": verdict, "diff": diff[:200]}, indent=2))
    else:
        if verdict == "identical":
            print("Identical. The source still says exactly what the snapshot says.")
        elif verdict == "whitespace-only":
            print("Same words, different spacing. The citation still holds.")
        else:
            print("Changed. The source no longer matches the snapshot:\n")
            print("\n".join(diff[:80]))
            if len(diff) > 80:
                print(f"... {len(diff) - 80} more diff lines")
            # Knowing a page moved is only half of it. This says what moved with it.
            print(f"\nWhat rests on it:  python3 scripts/kb.py rests-on evidence/{h}.txt")
    return 0 if verdict != "changed" else 1


def compare_log(root: Path) -> Path:
    return root / ".index" / "compare-log.jsonl"


def record_compare(root: Path, h: str, verdict: str) -> None:
    """Keep what a comparison found. It used to print and vanish, so "which of my snapshots
    is known to have changed" had no answer the next day."""
    path = compare_log(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"hash": h, "verdict": verdict, "on": today()}) + "\n")


def last_compares(root: Path) -> dict:
    """{hash: {"verdict", "on"}}, the latest comparison of each snapshot."""
    out: dict = {}
    try:
        lines = compare_log(root).read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("hash"):
            out[str(row["hash"])] = {"verdict": str(row.get("verdict", "")), "on": str(row.get("on", ""))}
    return out


def cmd_list(args) -> int:
    _expire_staged(require_root(args))
    root = require_root(args)
    rows = [dict(r, where="kept") for r in read_ledger(kept_dir(root))]
    rows += [dict(r, where="staged") for r in read_ledger(staging_dir(root))]
    rows = sorted(rows, key=lambda r: str(r.get("captured_at", "")), reverse=True)[: args.limit]
    compared = last_compares(root)
    for r in rows:
        if r["hash"] in compared:
            r["last_compare"] = compared[r["hash"]]
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    if not rows:
        print("No snapshots yet.")
        return 0
    for r in rows:
        print(f"{r['hash']}  {r['where']:6}  {r.get('captured_on', '?')}  {str(r.get('kind', 'text')):8} "
              f"{int(r.get('bytes', 0)):>7}B  {str(r.get('source', ''))[:70]}")
        if r.get("last_compare", {}).get("verdict") == "changed":
            print(f"    CHANGED at the source, found on {r['last_compare']['on']}. "
                  f"See what rests on it: kb.py rests-on evidence/{r['hash']}.txt")
    return 0


def cmd_verify(args) -> int:
    root = require_root(args)
    folder = kept_dir(root)
    rows = read_ledger(folder)
    edited, missing, orphan, circular = [], [], [], []
    known = set()
    for r in rows:
        h = r["hash"]
        known.add(h)
        path = folder / f"{h}.txt"
        if not path.is_file():
            missing.append(h)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if digest(text) != h:
            edited.append(h)
        # snapshots saved before the self-citation guard existed are checked here
        if is_self_citation(text, str(r.get("source", ""))):
            circular.append(h)
    if folder.is_dir():
        for path in sorted(folder.glob("*.txt")):
            if path.stem not in known:
                orphan.append(path.stem)

    if args.json:
        print(json.dumps({"checked": len(rows), "edited": edited, "missing": missing, "unrecorded": orphan,
                          "cites_the_skill": circular}, indent=2))
    else:
        print(f"Checked {len(rows)} kept snapshot(s).")
        for h in edited:
            print(f"  EDITED    {h}.txt no longer matches its hash. The citation is no longer trustworthy.")
        for h in missing:
            print(f"  MISSING   {h}.txt is in the ledger but not on disk.")
        for h in orphan:
            print(f"  UNTRACKED {h}.txt is on disk with no ledger entry.")
        for h in circular:
            print(f"  CIRCULAR  {h}.txt is a copy of this skill's own guidance, not evidence. Anything citing it "
                  f"only looks grounded. What rests on it: kb.py rests-on evidence/{h}.txt")
        if not (edited or missing or orphan or circular):
            print("Every snapshot matches its hash.")
    return 1 if (edited or missing or circular) else 0


def _common() -> argparse.ArgumentParser:
    c = argparse.ArgumentParser(add_help=False)
    c.add_argument("--root", default=argparse.SUPPRESS, help="knowledge base folder (default: ~/.flareware/flarehand)")
    c.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="print machine readable output")
    return c


def main(argv=None) -> int:
    _utf8_console()
    p = argparse.ArgumentParser(prog="evidence.py", description="Keep word-for-word copies of what you cite.")
    p.add_argument("--root", help="knowledge base folder (default: ~/.flareware/flarehand)")
    p.add_argument("--json", action="store_true")
    common = _common()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("add", help="stage a snapshot", parents=[common])
    s.add_argument("--file", help="read from this file")
    s.add_argument("--text", help="use this text")
    s.add_argument("--source", help="where it came from, such as a URL, a ticket key, git:<rev>:<path> or a person")
    s.add_argument("--kind", default="text", choices=["text", "log", "response", "screenshot-text", "sql", "email", "ticket", "code",
                                                "web", "doc"])
    s.add_argument("--note", help="permalink of a note this belongs to")
    s.add_argument("--sensitivity", default="internal",
                   choices=["public", "internal", "customer-data", "personal-data", "restricted"])
    s.add_argument("--keep", action="store_true", help="save straight into the knowledge base (only after a yes)")
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("keep", help="move staged snapshots into the knowledge base", parents=[common])
    s.add_argument("hashes", nargs="*")
    s.add_argument("--all", action="store_true")
    s.set_defaults(func=cmd_keep)

    s = sub.add_parser("discard", help="throw staged snapshots away", parents=[common])
    s.add_argument("hashes", nargs="*")
    s.add_argument("--all", action="store_true")
    s.set_defaults(func=cmd_discard)

    s = sub.add_parser("get", help="print a snapshot", parents=[common])
    s.add_argument("hash")
    s.add_argument("--max-chars", type=int, default=20000)
    s.set_defaults(func=cmd_get)

    s = sub.add_parser("compare", help="check a source still matches its snapshot", parents=[common])
    s.add_argument("hash")
    s.add_argument("--file", help="the source's current text (default: standard input)")
    s.set_defaults(func=cmd_compare)

    s = sub.add_parser("list", help="list snapshots", parents=[common])
    s.add_argument("--limit", type=int, default=25)
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("verify", help="re-hash every kept snapshot", parents=[common])
    s.set_defaults(func=cmd_verify)

    args = p.parse_args(argv)
    if not hasattr(args, "root"):
        args.root = None
    if not hasattr(args, "json"):
        args.json = False
    # add, keep and discard rewrite a ledger whole, so two sessions doing it at once used
    # to lose one side's rows. It is the same lock kb.py takes, and it nests.
    if args.cmd in ("add", "keep", "discard", "compare"):
        with kb_lock(require_root(args)):
            return args.func(args)
    return args.func(args)


if __name__ == "__main__":
    from kb import run_guarded
    sys.exit(run_guarded(main))
