#!/usr/bin/env python3
"""check.py - every check on a draft, in one command, with one short answer.

The pipeline's step 8 used to be four commands, and a busy agent skipped some of them.
This runs them all and prints either PASS or FIX: with a numbered list, one line per fix,
each with where it is. Fix the list and run it again until it says PASS.

  python3 scripts/check.py draft.md
  python3 scripts/check.py - --contract wf-03            (the draft on standard input)
  python3 scripts/check.py reply.md --outbound --seen-url https://example.com/page

What it runs, in this process:
  ground.py verify   every claim in this session's ledger, when there is one
  ground.py lint     labels resolve to passing claims, every specific is labelled
  ground.py urls     every URL was seen: in the ledger, or passed with --seen-url. Offline
  check_output.py    style (--profile), citations, and --contract or --template when given
  redact.py          with --outbound: what should not leave the machine. Report only

It works with no knowledge base and no ledger. Then lint lists the specifics with no label,
and every URL needs --seen-url.

Exit codes: 0 PASS, 1 FIX, 2 usage or file error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_output  # noqa: E402
import ground  # noqa: E402
from evidence import staging_dir  # noqa: E402
from kb import resolve_root  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent
LINE_MAX = 170
MAX_FIXES = 25


def _short(text: str) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= LINE_MAX else text[:LINE_MAX - 3] + "..."


def _where(line) -> str:
    return f"line {line}: " if line else ""


def run_checks(text: str, root: Path, contract: str | None = None, template: str | None = None,
               profile: str = "plain", outbound: bool = False, seen_urls: list[str] = (),
               repo_root: Path | None = None) -> dict:
    """{"fixes": [...], "notes": [...], "checked": {...}}. Nothing is written anywhere."""
    fixes: list[dict] = []
    notes: list[str] = []
    checked: dict = {}

    def fix(line, msg, by):
        fixes.append({"line": line or 0, "message": _short(msg), "check": by})

    has_ledger = any((staging_dir(root) / n).is_file() for n in (ground.SOURCES_FILE, ground.CLAIMS_FILE))

    # 1. the claim ledger
    if has_ledger:
        results = ground.verify_all(root)
        checked["claims"] = len(results)
        for r in results:
            if r["ok"]:
                continue
            why = r["reasons"][0] if r["reasons"] else "it has not earned that label"
            fix(0, f"{r['id']} wants {r['stated']}, earned {r['computed']}: {why}", "verify")

    # 2. labels and coverage
    linted = ground.lint(root, text)
    cov = linted["coverage"]
    checked["specific_sentences"] = cov["specific"]
    checked["labelled"] = cov["coverage"]
    warn_kinds: dict[str, int] = {}
    for f in linted["findings"]:
        if f["severity"] == "error":
            fix(f["line"], f"{f['message']} \"{_short(f['evidence'])[:70]}\"" if f["evidence"] else f["message"],
                "lint")
        else:
            warn_kinds[f["rule"]] = warn_kinds.get(f["rule"], 0) + 1

    # 3. every URL was seen. Offline: no request leaves the machine
    urls = ground.check_urls(root, text, seen_urls=list(seen_urls))
    checked["urls"] = len(urls)
    for u in urls:
        if u["verdict"] != "ok":
            fix(u["line"], f"{u['url']} was not seen in a tool result or the person's words. Remove it, fetch "
                           f"it with ground.py fetch, or pass --seen-url if you saw it", "urls")

    # 4. style, citations, contract and template
    try:
        rules = check_output.load_style_words(SKILL_DIR / "assets" / "style-words.tsv") if profile != "none" else []
        if profile == "google":
            rules += check_output.load_style_words(SKILL_DIR / "assets" / "style-words-google.tsv")
    except FileNotFoundError as e:
        notes.append(f"style word list missing: {e}")
        rules = []
    contracts = check_output.load_contracts(SKILL_DIR / "assets" / "contracts.tsv")
    if (root / "contracts.tsv").is_file():
        contracts = check_output.merge_contracts(contracts, check_output.load_contracts(root / "contracts.tsv"))
    args = SimpleNamespace(style=True, citations=True, contract=contract, template=template, profile=profile,
                           kb_root=root, repo_root=repo_root, ledger=None)
    try:
        found = check_output.run_file(Path.cwd() / "<draft>", args, rules, contracts, text)
    except OSError as e:
        raise SystemExit(f"error: cannot read {getattr(e, 'filename', '') or template}: {e.strerror or e}")
    checked["style"] = profile
    if contract:
        checked["contract"] = contract
    if template:
        checked["template"] = template
    for f in found:
        # S# ids are lint's job, with a better message. Do not say it twice.
        if f["rule"] == "citation-ledger":
            continue
        if f["severity"] == "error":
            fix(f["line"], f"{f['message']}", f["rule"])
        else:
            warn_kinds[f["rule"]] = warn_kinds.get(f["rule"], 0) + 1

    # 5. outbound: report only. The person decides what happens next
    if outbound:
        import redact
        patterns = redact.load_all(root if (root / "config.json").is_file() else None)
        hits = redact.scan(text, patterns, "low")
        checked["outbound"] = len(hits)
        for h in hits:
            if redact.ORDER.get(h["severity"], 0) >= redact.ORDER["medium"]:
                fix(h["line"], f"{h['means']} ({h['severity']}): \"{h['text']}\". Remove it, or ask the person. "
                               f"redact.py --apply writes a cleaned copy", "outbound")
            else:
                warn_kinds["outbound-low"] = warn_kinds.get("outbound-low", 0) + 1

    if warn_kinds:
        notes.append("worth a look: " + ", ".join(f"{n} {k}" for k, n in sorted(warn_kinds.items())))
    fixes.sort(key=lambda x: (x["line"] == 0, x["line"]))
    return {"pass": not fixes, "fixes": fixes, "notes": notes, "checked": checked}


def render(result: dict) -> str:
    c = result["checked"]
    parts = []
    if "claims" in c:
        parts.append(f"{c['claims']} claim(s)")
    parts.append(f"{c['specific_sentences']} specific sentence(s), {c['labelled']}% labelled")
    parts.append(f"{c['urls']} URL(s)")
    parts.append(f"style {c['style']}")
    if c.get("contract"):
        parts.append(f"contract {c['contract']}")
    if c.get("template"):
        parts.append("template")
    if "outbound" in c:
        parts.append(f"outbound {c['outbound']} hit(s)")
    lines = []
    if result["pass"]:
        lines.append("PASS")
    else:
        lines.append("FIX:")
        shown = result["fixes"][:MAX_FIXES]
        for i, f in enumerate(shown, start=1):
            lines.append(f"{i}. {_where(f['line'])}{f['message']}")
        if len(result["fixes"]) > MAX_FIXES:
            lines.append(f"... and {len(result['fixes']) - MAX_FIXES} more. Fix these, then run it again.")
    lines.append("Checked: " + "; ".join(parts) + ".")
    for n in result["notes"]:
        lines.append(n[0].upper() + n[1:] + ". --json lists them.")
    return "\n".join(lines)


def saved_profile(root) -> str:
    """The person's saved voice profile, or plain when there is none."""
    try:
        from kb import read_prefs  # noqa: E402
        prefs = read_prefs(root)
    except Exception:
        return "plain"
    value = prefs.get("voice") or prefs.get("style") or "plain"
    value = {"natural": "plain"}.get(value, value)
    return value if value in ("plain", "google", "none") else "plain"


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
    p = argparse.ArgumentParser(prog="check.py", description="Every check on a draft, in one command: PASS or FIX.")
    p.add_argument("file", help="the draft, or - for standard input")
    p.add_argument("--contract", metavar="ID", help="required sections for a workflow, such as wf-03")
    p.add_argument("--template", metavar="PATH", help="the template the draft follows")
    p.add_argument("--profile", choices=("plain", "google", "none"), default=None,
                   help="writing style to check. Default: your saved voice, else plain")
    p.add_argument("--outbound", action="store_true", help="it will leave the machine: run the redaction scan too")
    p.add_argument("--seen-url", action="append", default=[], metavar="URL",
                   help="a URL you saw in a tool result or the person's words (repeatable)")
    p.add_argument("--root", help="knowledge base folder (default: ~/.flareware/flarehand). It need not exist")
    p.add_argument("--repo-root", metavar="DIR", help="where cited repository paths live")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    if args.file == "-":
        text = sys.stdin.read()
    else:
        try:
            text = Path(args.file).read_text(encoding="utf-8-sig")
        except OSError as e:
            print(f"error: cannot read {args.file}: {e.strerror or e}", file=sys.stderr)
            return 2
    if args.template and not Path(args.template).is_file():
        print(f"error: no template at {args.template}", file=sys.stderr)
        return 2
    root = resolve_root(args.root)
    profile = args.profile or saved_profile(root)
    result = run_checks(text, root, args.contract, args.template, profile, args.outbound, args.seen_url,
                        Path(args.repo_root).expanduser() if args.repo_root else None)
    print(json.dumps(result, indent=2) if args.json else render(result))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
