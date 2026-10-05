#!/usr/bin/env python3
"""answers.py - your saved answers.

Write an answer down once, and when you ask the same question again you get
the same answer back, in any session or AI tool on this machine. It lives in
your own knowledge base and is not shared.

Commands
  write        save an answer for a question (only after the user says yes)
  alias        record that a new wording asks the same question as a saved one
  get          print a saved answer, exactly as stored
  approve      mark an answer good enough to replay
  invalidate   mark an answer out of date, with a reason
  verified     record that its sources were re-checked and still hold
  verify       re-hash every answer and report hand edits
  list         list saved answers, newest first

An answer stays a draft until it is approved. Only an approved answer replays.
A new wording only replays after you confirm it asks the same thing, which is
what `alias` records.

Writing the same question again replaces the old answer and makes it a draft.
Writing a question that is only an alias of a saved one is a collision, and is
refused unless you pass --replace.

Only write and approve record the answer's hash. If the file was edited by hand
since, alias, invalidate and verified refuse until you approve it again.

Saving an answer keeps the evidence it cites. Snapshots staged during the
session move into the knowledge base together with the answer. Text that holds
a credential is refused, so clean it with `redact.py --apply` first.

Exit codes: 0 fine, 1 a check failed or something was refused, 2 usage or file error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _text import EVIDENCE_REF, VERIFIED, exact_form, is_local_path, is_self_source  # noqa: E402
from evidence import keep, keep_refusal, locate, normalize_newlines, staging_dir  # noqa: E402
from kb import (_pref_days, _utf8_console, atomic_write, dump_frontmatter, kb_lock,  # noqa: E402
                require_root, sensitive_choice, today)
from recall import body_hash, key_for, load_answers  # noqa: E402

REVIEW_DAYS = 180
MAX_PRINT = 20000


def find(root: Path, question: str) -> dict | None:
    """Find a saved answer by exact wording, alias, or its file key."""
    exact = exact_form(question)
    q = question.strip()
    for e in load_answers(root):
        if (exact and exact in e["aliases"]) or e["path"].stem == q:
            return e
    return None


def _refuse_empty_wording(question: str) -> int | None:
    """A question with no words in it cannot be matched later. Exit 2, like any other usage error."""
    if not exact_form(question):
        print("error: that wording has no words in it, so it can never be matched. Give the question in words.",
              file=sys.stderr)
        return 2
    return None


def _intact(entry: dict) -> bool:
    """True when the body still matches the hash write or approve recorded. Answers saved before hashes
    existed have no hash and count as intact."""
    recorded = str(entry["meta"].get("content_sha256", ""))
    return not recorded or recorded == body_hash(entry["body"])


def _refuse_hand_edit(entry: dict) -> int | None:
    if _intact(entry):
        return None
    print(f"Refused: {entry['path'].name} was edited by hand since it was written. Read it, then approve it "
          f"again first. Only write and approve record its hash.", file=sys.stderr)
    return 1


def save(entry_path: Path, meta: dict, body: str, rehash: bool = False) -> None:
    """Write the file. Only write and approve pass rehash=True; every other command keeps the recorded hash."""
    body = normalize_newlines(body).strip()
    if rehash or "content_sha256" not in meta:
        meta["content_sha256"] = body_hash(body)
    atomic_write(entry_path, dump_frontmatter(meta) + "\n\n" + body + "\n")


# A ledger id inside any label that cites sources: [verified: S3], [verified: S3+S7], [weak: S9],
# [conflict: S2 vs S5], [stale: S6], [inference from S2, S3].
LEDGER_LABEL = re.compile(r"\[(?:verified|weak|conflict|stale|inference from)[:\s]([^\]]*)\]", re.I)
LEDGER_REF = re.compile(r"\bS\d{1,4}\b")
LEDGER_SUFFIX = ".ledger.json"


def _jsonl(path: Path) -> list[dict]:
    rows = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return rows
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def ledger_ids(body: str) -> list[str]:
    """The session ledger ids the answer's labels cite, in order of first use."""
    found = []
    for m in LEDGER_LABEL.finditer(body):
        for sid in LEDGER_REF.findall(m.group(1)):
            if sid not in found:
                found.append(sid)
    return found


def ledger_for(root: Path, ids: list[str]) -> tuple[dict | None, list[str]]:
    """The slice of this session's ground.py ledger an answer needs to outlive the session:
    each cited S# with its canonical locator and snapshot, and the claims that use them.
    Returns (ledger, ids missing from the session)."""
    if not ids:
        return None, []
    folder = staging_dir(root)
    rows = {r.get("id"): r for r in _jsonl(folder / "sources.jsonl") if r.get("id")}
    missing = [i for i in ids if i not in rows]
    sources = [rows[i] for i in ids if i in rows]
    wanted = set(ids)
    claims = []
    for c in _jsonl(folder / "claims.jsonl"):
        used = set(LEDGER_REF.findall(json.dumps(c.get("evidence", c.get("support", "")))))
        used |= {str(x) for x in (c.get("sources") or []) if isinstance(x, str)}
        if used & wanted:
            claims.append(c)
    ledger = {"saved_on": today(),
              "map": {r["id"]: r.get("canonical") or r.get("locator", "") for r in sources},
              "sources": sources, "claims": claims}
    return ledger, missing


def cmd_write(args) -> int:
    root = require_root(args)
    rc = _refuse_empty_wording(args.question)
    if rc:
        return rc
    if args.body_file:
        try:
            body = Path(args.body_file).expanduser().read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as e:
            print(f"error: cannot read {args.body_file}: {e}", file=sys.stderr)
            return 2
    elif args.body is not None:
        body = args.body
    elif sys.stdin is None or sys.stdin.isatty():
        print("error: the answer is empty. Pass --body, --body-file, or pipe it in.", file=sys.stderr)
        return 2
    else:
        body = sys.stdin.read()
    body = normalize_newlines(body)
    if not body.strip():
        print("error: the answer is empty. Pass --body, --body-file, or pipe it in.", file=sys.stderr)
        return 2

    sources = [s.strip() for s in (args.source or "").split(",") if s.strip()]
    if not sources and not args.no_sources:
        print("error: an answer with no sources cannot be re-checked later, so it cannot be replayed.", file=sys.stderr)
        print("       Pass --source with the ids you used, or --no-sources if it genuinely has none.", file=sys.stderr)
        return 2
    cited_in_body = [m.group(1) for m in VERIFIED.finditer(body)]
    local = [s for s in cited_in_body + sources if is_local_path(s)]
    if local:
        # A saved answer replays word for word, so every source has to be checkable later.
        # A path is only true for this checkout on this machine. See references/determinism.md.
        print(f"error: {local[0]} is a file on this machine, so nobody can re-check this "
              f"answer later.", file=sys.stderr)
        print(f"       Snapshot it first: evidence.py add --file {local[0].split(':')[0]} "
              f"--kind code --source \"<where it came from>\", then cite the snapshot.", file=sys.stderr)
        return 1
    if any(is_self_source(s) for s in cited_in_body + sources):
        print("Refused: this answer cites the skill's own reference files as evidence.", file=sys.stderr)
        print("Those are guidance, not sources. Cite the page, ticket or document they point to.", file=sys.stderr)
        return 1

    # The same once-asked choice as a note. A saved answer replays word for word, so whatever it
    # holds is read back into every session that asks that question.
    reason = sensitive_choice(root, "this answer", body)
    if reason:
        print(f"error: {reason}", file=sys.stderr)
        return 1

    # Ledger ids only mean something inside one session. Keep the slice of the ledger the
    # answer cites, so replay and recheck still know what S3 was after the session ends.
    ledger, missing_ids = ledger_for(root, ledger_ids(body))
    if missing_ids:
        print(f"error: the answer cites {', '.join(missing_ids)}, which this session's ground.py ledger does "
              f"not hold, so nobody could re-check it later.", file=sys.stderr)
        print("       Add the source with ground.py fetch or source add, or cite it by its locator.", file=sys.stderr)
        return 1
    if ledger:
        for locator in ledger["map"].values():
            if locator and locator not in sources:
                sources.append(locator)

    # every snapshot the answer cites must exist and be fit to keep, before anything is written
    cited = sorted(set(EVIDENCE_REF.findall(body)) |
                   {str(r.get("hash")) for r in (ledger or {}).get("sources", []) if r.get("hash")})
    missing = [h for h in cited if locate(root, h)[0] is None]
    if missing:
        print(f"error: the answer cites snapshots that do not exist: {', '.join(missing)}", file=sys.stderr)
        return 2
    for h in cited:
        if locate(root, h)[1] == "staged":
            why = keep_refusal(root, h)
            if why:
                print(f"Refused: the cited snapshot evidence/{h}.txt cannot be kept: {why}.", file=sys.stderr)
                return 1

    existing = find(root, args.question)
    if existing and exact_form(existing["asked"]) != exact_form(args.question) and not args.replace:
        print(f"Refused: \"{args.question}\" is a confirmed wording of a different saved question, "
              f"\"{existing['asked']}\" ({existing['path'].name}).", file=sys.stderr)
        print("Writing it would overwrite that answer. Pass --replace if that is what you want, or write the "
              "answer under its own question.", file=sys.stderr)
        return 1
    path = existing["path"] if existing else root / "answers" / f"{key_for(args.question)}.md"
    old = existing["meta"] if existing else {}
    aliases = list(existing["aliases"]) if existing else []
    if exact_form(args.question) not in aliases:
        aliases.insert(0, exact_form(args.question))

    meta = {
        "question_as_asked": " ".join(args.question.split()),
        "answer_id": path.stem,
        "aliases": aliases,
        "archetype": args.archetype or old.get("archetype", ""),
        "sources": sources,
        "first_written": str(old.get("first_written", today())),
        "generated_at": today(),
        "generated_by": args.model or "unrecorded",
        "tool": args.tool or "unrecorded",
        "status": "draft",
        "review_by": (date.today() + timedelta(days=_pref_days(root, "review_days", REVIEW_DAYS))).isoformat(),
    }
    if ledger:
        meta["ledger"] = path.stem + LEDGER_SUFFIX
    save(path, meta, body, rehash=True)
    ledger_path = path.with_name(path.stem + LEDGER_SUFFIX)
    if ledger:
        atomic_write(ledger_path, json.dumps(ledger, indent=2, ensure_ascii=False) + "\n")
    elif ledger_path.is_file():
        ledger_path.unlink()          # a rewrite without ledger ids leaves no stale map behind
    # the answer is on disk, so now the snapshots it cites can move in beside it
    kept, _, refused = keep(root, cited)

    if args.json:
        print(json.dumps({"key": path.stem, "path": str(path), "replaced": bool(existing),
                          "evidence_kept": kept, "evidence_refused": refused}, indent=2))
    else:
        print(f"{'Replaced' if existing else 'Saved'} answers/{path.name}")
        if kept:
            print(f"Kept {len(kept)} snapshot(s) it cites.")
        if ledger:
            print(f"Kept the ledger for {', '.join(ledger['map'])}, so they still resolve after this session.")
        for r in refused:
            print(f"Not kept: evidence/{r['hash']}.txt, {r['why']}.", file=sys.stderr)
        print("It is a draft. Once you have checked it, approve it so asking again gives you this same answer:")
        print(f"  {Path(sys.executable).name} scripts/answers.py approve {path.stem}")
        print("The file key above stands for the question, so it is safe to paste whatever the question holds.")
    return 1 if refused else 0


def cmd_alias(args) -> int:
    root = require_root(args)
    rc = _refuse_empty_wording(args.question)
    if rc:
        return rc
    target = find(root, args.to)
    if not target:
        print(f"error: no saved answer matches '{args.to}'", file=sys.stderr)
        return 1
    new = exact_form(args.question)
    other = find(root, args.question)
    if other and other["path"] != target["path"]:
        print(f"error: that wording already belongs to a different saved answer ({other['path'].name}).", file=sys.stderr)
        return 1
    rc = _refuse_hand_edit(target)
    if rc:
        return rc
    meta = target["meta"]
    aliases = list(target["aliases"])
    if new in aliases:
        print("Already recorded. Asking it that way already gives this answer.")
        return 0
    aliases.append(new)
    meta["aliases"] = aliases
    save(target["path"], meta, target["body"])
    print(f"Recorded. \"{args.question}\" now gives the same saved answer as \"{target['asked']}\".")
    return 0


def cmd_get(args) -> int:
    root = require_root(args)
    e = find(root, args.question)
    if not e:
        print(f"error: nothing saved for that exact wording. Try: recall.py \"{args.question}\"", file=sys.stderr)
        return 1
    text = e["path"].read_text(encoding="utf-8") if args.with_header else e["body"].strip()
    if len(text) > args.max_chars:
        print(text[: args.max_chars])
        print(f"\n... truncated at {args.max_chars} characters of {len(text)}.")
    else:
        print(text)
    return 0


def _set_status(root: Path, question: str, status: str, reason: str = "") -> int:
    e = find(root, question)
    if not e:
        print(f"error: nothing saved for that exact wording ('{question}')", file=sys.stderr)
        return 1
    meta = e["meta"]
    meta["status"] = status
    if status == "approved":
        meta["approved_on"] = today()
        meta.pop("stale_reason", None)
        # approve is the one review step, so it blesses the body as it stands now
        save(e["path"], meta, e["body"], rehash=True)
        return 0
    if status == "stale":
        rc = _refuse_hand_edit(e)
        if rc:
            return rc
        meta["stale_reason"] = " ".join(reason.split()) or "no reason recorded"
        meta["stale_on"] = today()
    save(e["path"], meta, e["body"])
    return 0


def cmd_approve(args) -> int:
    root = require_root(args)
    rc = _set_status(root, args.question, "approved")
    if rc == 0:
        print("Approved. When you ask this again, you get this same answer back.")
    return rc


def cmd_invalidate(args) -> int:
    root = require_root(args)
    rc = _set_status(root, args.question, "stale", args.why)
    if rc == 0:
        print("Marked out of date. Asking again will produce a fresh answer.")
        print(f"Reason kept on the file: {args.why}")
        print("Save the replacement with: answers.py write on the same question. That reuses the file and its "
              "confirmed wordings.")
    return rc


def cmd_verified(args) -> int:
    """After every cited source compares identical, record the check. The answer text is untouched."""
    root = require_root(args)
    e = find(root, args.question)
    if not e:
        print(f"error: nothing saved for that exact wording ('{args.question}')", file=sys.stderr)
        return 1
    meta = e["meta"]
    if str(meta.get("status")) == "stale":
        print("error: this answer is marked out of date. Write a new one instead of re-checking it.", file=sys.stderr)
        return 1
    rc = _refuse_hand_edit(e)
    if rc:
        return rc
    meta["last_verified"] = today()
    save(e["path"], meta, e["body"])
    print("Recorded. Its sources were checked today, so it replays without another check for 30 days.")
    return 0


def cmd_verify(args) -> int:
    root = require_root(args)
    edited, unapproved, overdue = [], [], []
    entries = load_answers(root)
    for e in entries:
        if not _intact(e):
            edited.append(e["path"].name)
        if str(e["meta"].get("status")) != "approved":
            unapproved.append(e["path"].name)
        rb = str(e["meta"].get("review_by", ""))
        if rb and rb < today():
            overdue.append(e["path"].name)
    if args.json:
        print(json.dumps({"checked": len(entries), "edited": edited, "not_approved": unapproved,
                          "past_review": overdue}, indent=2))
    else:
        print(f"Checked {len(entries)} saved answer(s).")
        for n in edited:
            print(f"  EDITED     {n} was changed by hand. Read it and approve it again.")
        for n in unapproved:
            print(f"  DRAFT      {n} has never been approved.")
        for n in overdue:
            print(f"  DUE        {n} is past its review date.")
        if not (edited or unapproved or overdue):
            print("Every answer matches its hash and is approved.")
    return 1 if edited else 0


def cmd_list(args) -> int:
    root = require_root(args)
    rows = [{
        "key": e["path"].stem, "question": e["asked"], "aliases": len(e["aliases"]),
        "status": str(e["meta"].get("status", "draft")), "generated_at": str(e["meta"].get("generated_at", "")),
        "sources": e["meta"].get("sources") or [],
    } for e in load_answers(root)]
    rows.sort(key=lambda r: r["generated_at"], reverse=True)
    rows = rows[: args.limit]
    if args.json:
        print(json.dumps(rows, indent=2))
    elif not rows:
        print("No answers saved yet.")
    else:
        for r in rows:
            print(f"{r['key']}  {r['generated_at']}  {r['status']:8}  {r['aliases']} wording(s)  {r['question']}")
    return 0


def _session_only_refusal(root: Path, session: str | None):
    """kb.py decides what a session-only session is, so both scripts refuse the same way."""
    try:
        from kb import session_only_refusal
    except ImportError:
        return None
    return session_only_refusal(root, session)


def _common() -> argparse.ArgumentParser:
    c = argparse.ArgumentParser(add_help=False)
    c.add_argument("--root", default=argparse.SUPPRESS, help="knowledge base folder")
    c.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="machine readable output")
    c.add_argument("--session", default=argparse.SUPPRESS,
                   help="the session id, for a session-only session (default: from the environment)")
    return c


def main(argv=None) -> int:
    _utf8_console()
    p = argparse.ArgumentParser(prog="answers.py", description="Your saved answers.")
    p.add_argument("--root")
    p.add_argument("--json", action="store_true")
    p.add_argument("--session", help="the session id, for a session-only session (default: from the environment)")
    common = _common()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("write", help="save an answer", parents=[common])
    s.add_argument("question")
    s.add_argument("--body")
    s.add_argument("--body-file")
    s.add_argument("--source", help="comma separated source ids you actually used")
    s.add_argument("--no-sources", action="store_true", help="this answer genuinely cites nothing")
    s.add_argument("--archetype", help="which workflow produced it, such as wf-09")
    s.add_argument("--model", help="model that wrote it")
    s.add_argument("--tool", help="tool it was written in")
    s.add_argument("--replace", action="store_true",
                   help="overwrite a saved answer even when this wording is only an alias of its question")
    s.set_defaults(func=cmd_write)

    s = sub.add_parser("alias", help="record that a new wording asks the same question", parents=[common])
    s.add_argument("question", help="the new wording, after the user confirmed it is the same question")
    s.add_argument("--to", required=True, help="the saved question, or its file key")
    s.set_defaults(func=cmd_alias)

    s = sub.add_parser("get", help="print a saved answer", parents=[common])
    s.add_argument("question")
    s.add_argument("--with-header", action="store_true", help="include the frontmatter")
    s.add_argument("--max-chars", type=int, default=MAX_PRINT)
    s.set_defaults(func=cmd_get)

    s = sub.add_parser("approve", help="mark an answer replayable", parents=[common])
    s.add_argument("question")
    s.set_defaults(func=cmd_approve)

    s = sub.add_parser("invalidate", help="mark an answer out of date", parents=[common])
    s.add_argument("question")
    s.add_argument("--why", required=True, help="what changed")
    s.set_defaults(func=cmd_invalidate)

    s = sub.add_parser("verified", help="record that an answer's sources still hold", parents=[common])
    s.add_argument("question")
    s.set_defaults(func=cmd_verified)

    s = sub.add_parser("verify", help="re-hash every answer", parents=[common])
    s.set_defaults(func=cmd_verify)

    s = sub.add_parser("list", help="list saved answers", parents=[common])
    s.add_argument("--limit", type=int, default=25)
    s.set_defaults(func=cmd_list)

    args = p.parse_args(argv)
    if not hasattr(args, "root"):
        args.root = None
    if not hasattr(args, "json"):
        args.json = False
    # writing commands take the same lock kb.py uses, so two tools never lose each other's work
    if args.func.__name__ in ("cmd_write", "cmd_alias", "cmd_approve", "cmd_invalidate", "cmd_verified"):
        root = require_root(args)
        with kb_lock(root):
            # "Just this session" means nothing is written to the knowledge base, answers included.
            reason = _session_only_refusal(root, getattr(args, "session", None))
            if reason:
                print(reason, file=sys.stderr)
                return 1
            return args.func(args)
    return args.func(args)


if __name__ == "__main__":
    from kb import run_guarded
    sys.exit(run_guarded(main))
