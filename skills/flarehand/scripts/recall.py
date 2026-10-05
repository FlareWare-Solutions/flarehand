#!/usr/bin/env python3
"""recall.py - decide whether you have already answered this question.

Your answers are saved in your own knowledge base, so this is about YOU asking
again: in a later session, or in a different AI tool on the same machine. It is
not shared with anyone else.

The rule that keeps it safe: a saved answer is replayed word for word ONLY when
the question matches a wording you already confirmed means the same thing.
Anything merely similar is shown to you as a suggestion, with the saved question
and the words that differ, and you decide. "Set up the deploy key in Claude Code"
and "set up the deploy key in Claude Desktop" look alike and have different
answers, so a guess is never good enough.

Usage
  python3 scripts/recall.py "how do I set up the deploy key"
  python3 scripts/recall.py --explain "how do I set up the deploy key"
  python3 scripts/recall.py --exact-only "How do I set up the deploy key?"

Verdicts
  replay    an exact, confirmed match that is approved and fresh. Print it word for word.
  recheck   an exact match, but unapproved, old, or edited by hand. Check its sources first.
  stale     an exact match somebody marked out of date. Answer again.
  confirm   similar to a saved question, not identical. Show the saved question and ask
            whether it is the same. Never replay without a yes.
  new       nothing saved. Answer it.

Exit codes: 0 replay, 1 anything else, 2 usage or file error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _text import exact_form, tokens  # noqa: E402
from evidence import normalize_newlines  # noqa: E402
from kb import _pref_days, _utf8_console, load_state, parse_frontmatter, resolve_root  # noqa: E402

KEY_LEN = 16
RECHECK_AFTER_DAYS = 30
PINS_CHECK_DAYS = 30      # the same horizon as ground.PINS_CHECK_DAYS
NEAR_MATCH = 0.5
MAX_SUGGESTIONS = 3

# Words that carry no meaning for similarity. Deliberately short. Negations,
# product names, letters and numbers are NOT here, because they change answers.
STOP = {
    "a", "an", "the", "please", "can", "could", "would", "you", "i", "me", "my", "we", "our",
    "to", "do", "how", "what", "is", "are", "for", "of", "in", "on", "with", "it", "this", "that",
    "just", "help", "hey", "hi", "hello", "thank", "thanks", "some", "any", "there", "way",
}


def key_for(text: str) -> str:
    """The file key for a question. Built from exact_form, so only case,
    punctuation and spelling variants collapse. Nothing else."""
    return hashlib.sha256(exact_form(text).encode("utf-8")).hexdigest()[:KEY_LEN]


def content(text: str) -> set[str]:
    return {t for t in tokens(text) if t not in STOP}


def similarity(a: str, b: str) -> tuple[float, list[str], list[str]]:
    ca, cb = content(a), content(b)
    if not ca or not cb:
        return 0.0, sorted(ca), sorted(cb)
    score = len(ca & cb) / len(ca | cb)
    return score, sorted(ca - cb), sorted(cb - ca)


def days_since(stamp: str) -> int | None:
    try:
        y, m, d = (int(x) for x in str(stamp).split("-")[:3])
        return (date.today() - date(y, m, d)).days
    except (ValueError, AttributeError):
        return None


def load_answers(root: Path) -> list[dict]:
    """Every saved answer with the exact wordings it is confirmed to answer."""
    out = []
    folder = root / "answers"
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("*.md")):
        try:
            meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        aliases = meta.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [aliases]
        aliases = [exact_form(a) for a in aliases if str(a).strip()]
        # answers saved before aliases existed still count their original wording
        asked = str(meta.get("question_as_asked", "")).strip()
        if asked and exact_form(asked) not in aliases:
            aliases.append(exact_form(asked))
        out.append({"path": path, "meta": meta, "body": body, "aliases": aliases,
                    "asked": asked or (aliases[0] if aliases else path.stem)})
    return out


def body_hash(body: str) -> str:
    """One hash for answers.py and recall.py. Newlines are normalised first, so CRLF text
    hashes the same before and after it is read back from disk."""
    return hashlib.sha256(normalize_newlines(body).strip().encode("utf-8")).hexdigest()


def judge(entry: dict, recheck_days: int = RECHECK_AFTER_DAYS) -> tuple[str, str]:
    meta, body = entry["meta"], entry["body"]
    status = str(meta.get("status", "draft"))
    recorded = str(meta.get("content_sha256", ""))
    intact = (recorded == body_hash(body)) if recorded else None
    # a re-check that found every source unchanged resets the clock, without rewriting the answer
    checked = max(str(meta.get("generated_at", "")), str(meta.get("last_verified", "")))
    age = days_since(checked)
    if status == "stale":
        return "stale", f"Marked out of date: {meta.get('stale_reason', 'no reason recorded')}. Answer it again."
    if intact is False:
        return "recheck", "The saved answer was edited by hand since it was written. Read it, then approve it again."
    if status != "approved":
        return "recheck", "Saved but never approved. Check it is still right, then run: answers.py approve"
    if age is not None and age > recheck_days:
        return "recheck", (f"Last checked {age} days ago. For each cited snapshot, re-read its source and run "
                           f"evidence.py compare. All identical: run answers.py verified, then replay it word for "
                           f"word. Anything changed: show the diff and write a new answer.")
    return "replay", "Print the saved answer word for word. Do not write a new one."


def pinned_due(root: Path, sources: list) -> list[str]:
    """Pinned sources this answer rests on that `ground.py pins check` has not passed lately:
    never checked, checked more than PINS_CHECK_DAYS ago, or last found drifted or gone."""
    try:
        import sources as sources_mod
        rows = sources_mod.sources_rows(root, Path.cwd())
    except Exception:
        return []
    try:
        import ground
        horizon = int(getattr(ground, "PINS_CHECK_DAYS", PINS_CHECK_DAYS))
    except Exception:
        horizon = PINS_CHECK_DAYS
    cited = {str(x).strip() for x in sources or [] if str(x).strip()}
    if not cited:
        return []
    stamps = load_state(root).get("pins") if (root / "config.json").is_file() else {}
    stamps = stamps if isinstance(stamps, dict) else {}
    due = []
    for r in rows:
        if str(r.get("type", "")).lower() != "pin" or str(r.get("value", "")).strip() not in cited:
            continue
        intent = str(r.get("key", "")).strip()
        stamp = stamps.get(intent) if isinstance(stamps.get(intent), dict) else {}
        age = days_since(str(stamp.get("checked_on", "")))
        if not stamp or age is None or age > horizon:
            due.append(f"{intent} (" + ("never checked" if age is None else f"checked {age} days ago") + ")")
        elif stamp.get("status") not in (None, "", "ok"):
            due.append(f"{intent} (last check found it {stamp.get('status')})")
    return due


def lookup(root: Path, text: str) -> dict:
    exact = exact_form(text)
    entries = load_answers(root)
    recheck = _pref_days(root, "answer_recheck_days", RECHECK_AFTER_DAYS)
    res = {
        "question": text, "exact_form": exact, "key": key_for(text),
        "verdict": "new", "why": "Nothing saved for this question. Answer it.",
        "path": None, "status": None, "sources": [], "generated_at": None,
        "suggestions": [],
    }
    for e in entries:
        if exact in e["aliases"]:
            verdict, why = judge(e, recheck)
            if verdict == "replay":
                due = pinned_due(root, e["meta"].get("sources") or [])
                if due:
                    verdict = "recheck"
                    why = (f"It rests on pinned sources due a check: {', '.join(due)}. Run ground.py pins check, "
                           f"then answers.py verified if they still hold, or write a new answer if one drifted.")
            res.update({
                "verdict": verdict, "why": why, "path": str(e["path"]),
                "status": str(e["meta"].get("status", "draft")),
                "sources": e["meta"].get("sources") or [],
                "generated_at": str(e["meta"].get("generated_at", "")),
                "saved_question": e["asked"],
            })
            return res

    scored = []
    for e in entries:
        best = None
        for alias in e["aliases"]:
            score, only_yours, only_saved = similarity(text, alias)
            if best is None or score > best[0]:
                best = (score, only_yours, only_saved)
        if best and best[0] >= NEAR_MATCH:
            scored.append({
                "saved_question": e["asked"], "path": str(e["path"]), "score": round(best[0], 2),
                "words_only_in_yours": best[1], "words_only_in_saved": best[2],
                "status": str(e["meta"].get("status", "draft")),
            })
    scored.sort(key=lambda s: (-s["score"], s["saved_question"]))
    if scored:
        res["verdict"] = "confirm"
        res["suggestions"] = scored[:MAX_SUGGESTIONS]
        top = scored[0]
        res["why"] = ("Similar to a saved question, but not the same wording. Show the saved question and the "
                      "words that differ, and ask whether it is the same question. Never replay without a yes. "
                      "On a yes, run: answers.py alias \"<their words>\" --to \"<saved question>\"")
        if top["words_only_in_yours"] or top["words_only_in_saved"]:
            res["why"] += " Differing words often mean a different answer, so read them first."
    return res


def render(res: dict) -> str:
    lines = [f"Question : {res['question']}", f"Verdict  : {res['verdict'].upper()}", f"Why      : {res['why']}"]
    if res.get("path"):
        lines += [f"Saved as : {res.get('saved_question')}", f"File     : {res['path']}",
                  f"Status   : {res['status']}, written {res['generated_at']}"]
        if res["sources"]:
            lines.append("Sources to re-check:")
            lines += [f"  - {s}" for s in res["sources"]]
    for s in res.get("suggestions", []):
        lines.append("")
        lines.append(f"Similar  : \"{s['saved_question']}\"  (score {s['score']}, {s['status']})")
        if s["words_only_in_yours"]:
            lines.append(f"  only in yours : {', '.join(s['words_only_in_yours'])}")
        if s["words_only_in_saved"]:
            lines.append(f"  only in saved : {', '.join(s['words_only_in_saved'])}")
    return "\n".join(lines)


def main(argv=None) -> int:
    _utf8_console()
    p = argparse.ArgumentParser(prog="recall.py", description="Check whether you already answered this question.")
    p.add_argument("question")
    p.add_argument("--root", help="knowledge base folder (default: ~/.flareware/flarehand)")
    p.add_argument("--explain", action="store_true", help="readable output instead of JSON")
    p.add_argument("--json", action="store_true", help="JSON output, which is also the default")
    p.add_argument("--exact-only", action="store_true", help="print just the exact form used for matching")
    p.add_argument("--key-only", action="store_true", help="print just the file key")
    args = p.parse_args(argv)

    if not args.question.strip():
        print("error: empty question", file=sys.stderr)
        return 2
    if not exact_form(args.question):
        print("error: that wording has no words in it, so it can never be matched. Give the question in words.",
              file=sys.stderr)
        return 2
    if args.exact_only:
        print(exact_form(args.question))
        return 0
    if args.key_only:
        print(key_for(args.question))
        return 0

    root = resolve_root(args.root)
    if not (root / "config.json").is_file():
        print(f"error: no knowledge base at {root}. Run: {Path(sys.executable).name} scripts/kb.py init",
              file=sys.stderr)
        return 2
    res = lookup(root, args.question)
    print(render(res) if args.explain else json.dumps(res, indent=2))
    return 0 if res["verdict"] == "replay" else 1


if __name__ == "__main__":
    sys.exit(main())
