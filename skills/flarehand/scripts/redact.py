#!/usr/bin/env python3
"""redact.py - find things you may not want to send outside.

Keeping raw customer data in your own knowledge base is fine. It is your machine.
This script exists for the moment that content is about to leave it: pasted
onto a case, sent in an email, posted to a service, attached to a ticket.

It tells you what it found and where. It does not decide for you. You either
send it as it is, redact it, or stop. That call is yours.

Usage
  python3 scripts/redact.py draft.md
  python3 scripts/redact.py --apply draft.md --out clean.md
  cat draft.md | python3 scripts/redact.py -
  python3 scripts/redact.py --min high draft.md
  python3 scripts/redact.py --domain acme.com --domain acme.io draft.md

Internal domains
  Host names on your organisation's own domains are flagged as internal. The list is the
  union of: prefs.internal_domains in the knowledge base config.json, every "- <domain>"
  line under "## Internal domains" in house-rules.md in any layer (your knowledge base and
  each team playbook), and each --domain. Always on, with no list: host names ending in
  .internal, .corp, .local, .lan or .intranet, intranet. sites, and private (RFC 1918)
  IP addresses.

Exit codes: 0 nothing found, 1 something found, 2 usage or file error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable, Optional

SKILL_DIR = Path(__file__).resolve().parent.parent
PATTERNS = SKILL_DIR / "assets" / "redact-patterns.tsv"
ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
# A rule whose replacement is KEEP is reported but never rewritten by --apply.
# Used where a script cannot make the line safe on its own, such as an [opinion] line
# that needs the author's name rather than a blank.
KEEP = "(keep)"
CREDENTIAL_RULES = frozenset({"password-assign", "password-prose", "aws-key", "private-key", "bearer-token",
                              "basic-auth", "jwt", "github-token", "key-prefix", "jdbc", "oracle-connect"})


def load_patterns(path: Path) -> list[dict]:
    if not path.is_file():
        print(f"error: pattern file not found at {path}", file=sys.stderr)
        sys.exit(2)
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.startswith("name\t"):
            continue
        parts = raw.split("\t")
        if len(parts) < 5:
            continue
        try:
            rows.append({"name": parts[0], "re": re.compile(parts[1]), "severity": parts[2],
                         "replacement": parts[3], "means": parts[4]})
        except re.error as e:
            print(f"warning: skipping pattern {parts[0]}: {e}", file=sys.stderr)
    return rows


DOMAIN_RE = re.compile(r"^(?=.{3,253}$)(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9\-]{0,62}$")
DOMAIN_HEADING = re.compile(r"^##\s+internal\s+domains?\b", re.I)


def clean_domain(raw) -> str:
    """`https://*.Acme.com/path` becomes `acme.com`. Anything that is not a domain becomes ""."""
    d = str(raw or "").strip().strip("`'\"").lower()
    d = re.sub(r"^[a-z][a-z0-9+.\-]*://", "", d)
    d = d.split("/", 1)[0].split(":", 1)[0]
    d = d.lstrip("*").lstrip(".").rstrip(".")
    return d if DOMAIN_RE.match(d) else ""


def domains_from_house_rules(text: str) -> list:
    """The `- <domain>` lines under a `## Internal domains` heading."""
    out, inside = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = bool(DOMAIN_HEADING.match(line))
            continue
        if inside:
            m = re.match(r"^\s*[-*]\s+(\S+)", line)
            if m:
                d = clean_domain(m.group(1))
                if d:
                    out.append(d)
    return out


def internal_domains(root: Optional[Path] = None, extra: Iterable[str] = (),
                     cwd: Optional[Path] = None) -> list:
    """The union of every configured internal domain, sorted. Rules add up: a domain any
    layer names is flagged, and nothing in a personal file can unflag a team one."""
    found = set()
    for d in extra or ():
        d = clean_domain(d)
        if d:
            found.add(d)
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import kb  # noqa: E402
        base = Path(root) if root is not None else kb.resolve_root(None)
        prefs = kb.read_prefs(base)
        raw = prefs.get("internal_domains") or []
        if isinstance(raw, str):
            raw = re.split(r"[,\s]+", raw)
        for d in raw if isinstance(raw, list) else []:
            d = clean_domain(d)
            if d:
                found.add(d)
        import review  # noqa: E402
        for _layer, path in review.house_rule_files(base, cwd):
            try:
                found.update(domains_from_house_rules(path.read_text(encoding="utf-8-sig")))
            except (OSError, UnicodeDecodeError):
                continue
    except Exception:
        pass
    return sorted(found)


def domain_rule(domains: Iterable[str]) -> list:
    """A pattern row for the configured internal domains, or [] when there are none."""
    names = sorted({d for d in (clean_domain(x) for x in domains) if d}, key=lambda d: (-len(d), d))
    if not names:
        return []
    alt = "|".join(re.escape(d) for d in names)
    rx = (rf"(?i)(?<![A-Za-z0-9.\-@])(?:https?://)?(?:[A-Za-z0-9\-]+\.)*(?:{alt})"
          rf"(?![A-Za-z0-9\-])(?!\.[A-Za-z0-9])(?::\d+)?(?:/(?:[^\s\"'<>]*[^\s\"'<>.,;:!?)])?)?")
    return [{"name": "internal-domain", "re": re.compile(rx), "severity": "medium",
             "replacement": "[INTERNAL-URL]",
             "means": "a host on one of your organisation's internal domains"}]


def load_all(root: Optional[Path] = None, extra: Iterable[str] = (), cwd: Optional[Path] = None,
             path: Path = None) -> list:
    """The shipped patterns plus the internal-domain rule built from config and house rules."""
    return load_patterns(path or PATTERNS) + domain_rule(internal_domains(root, extra, cwd))


PRIVATE_IP = re.compile(r"^(?:10\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.)")


def luhn_ok(digits: str) -> bool:
    nums = [int(c) for c in digits if c.isdigit()]
    if not 13 <= len(nums) <= 19:
        return False
    total, parity = 0, len(nums) % 2
    for i, n in enumerate(nums):
        if i % 2 == parity:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


# A release note full of version numbers looks exactly like a list of IP addresses. When a line
# talks about versions, treat its dotted numbers as versions and say so in the report instead.
VERSION_LINE = re.compile(r"\b(?:versions?|patch(?:es|ed)?|releases?d?|upgrad(?:e|ed|ing)|hotfix|"
                          r"build|rollback|semver|fixed in|sp\d|v\d)", re.I)


# Values reserved for documentation, which can never belong to a real person or customer.
# Flagging them trained people to ignore the check on templates and training material.
RESERVED_EMAIL = re.compile(r"@(?:[A-Za-z0-9\-]+\.)*(?:example\.(?:com|org|net)|[A-Za-z0-9\-]+\.(?:example|test|invalid))$",
                            re.I)
RESERVED_PHONE = re.compile(r"555[ \-.]?01\d\d$")
RESERVED_IP = re.compile(r"^(?:192\.0\.2|198\.51\.100|203\.0\.113)\.\d{1,3}$")
RESERVED_COMPANY = re.compile(r"^Example\s")


def reserved(rule: str, hit: str) -> bool:
    """True for example.com addresses, 555-0100 to 555-0199, the RFC 5737 blocks, and a
    company whose name starts with Example. references/privacy.md says to use these."""
    return bool((rule == "email" and RESERVED_EMAIL.search(hit))
                or (rule == "phone" and RESERVED_PHONE.search(hit))
                or (rule == "ipv4" and RESERVED_IP.match(hit))
                or (rule == "company-suffix" and RESERVED_COMPANY.match(hit)))


def scan(text: str, patterns: list[dict], min_sev: str) -> list[dict]:
    floor = ORDER.get(min_sev, 0)
    found = []
    lines = text.split("\n")
    for lineno, line in enumerate(lines, start=1):
        for p in patterns:
            if ORDER.get(p["severity"], 0) < floor:
                continue
            for m in p["re"].finditer(line):
                hit = m.group(0)
                # a long run of digits is only a card number if it passes the checksum
                if p["name"] == "card" and not luhn_ok(hit):
                    continue
                # dotted numbers on a version line are version numbers, not addresses
                if p["name"] in ("ipv4", "private-ip") and VERSION_LINE.search(line):
                    continue
                # a private address is reported once, by its own rule
                if p["name"] == "ipv4" and PRIVATE_IP.match(hit):
                    continue
                if reserved(p["name"], hit):
                    continue
                found.append({
                    "line": lineno,
                    "col": m.start() + 1,
                    "rule": p["name"],
                    "name": p["name"],
                    "severity": p["severity"],
                    "means": p["means"],
                    "text": hit if len(hit) <= 60 else hit[:57] + "...",
                    "replacement": p["replacement"],
                })
    found.sort(key=lambda f: (-ORDER.get(f["severity"], 0), f["line"], f["col"]))
    return found


def apply_redactions(text: str, patterns: list[dict], min_sev: str) -> tuple[str, int]:
    floor = ORDER.get(min_sev, 0)
    count = 0
    lines = text.split("\n")
    for p in sorted(patterns, key=lambda q: -ORDER.get(q["severity"], 0)):
        if ORDER.get(p["severity"], 0) < floor:
            continue

        if p["replacement"] == KEEP:
            continue

        def sub(m):
            nonlocal count
            if p["name"] == "card" and not luhn_ok(m.group(0)):
                return m.group(0)
            if reserved(p["name"], m.group(0)):
                return m.group(0)
            if p["name"] == "ipv4" and PRIVATE_IP.match(m.group(0)):
                return m.group(0)
            count += 1
            return p["replacement"]

        # line by line, so the same version-line rule the report uses applies here
        for i, line in enumerate(lines):
            if p["name"] in ("ipv4", "private-ip") and VERSION_LINE.search(line):
                continue
            lines[i] = p["re"].sub(sub, line)
    return "\n".join(lines), count


def main(argv=None) -> int:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
    ap = argparse.ArgumentParser(prog="redact.py", description="Find things you may not want to send outside.")
    ap.add_argument("file", help="file to check, or - for standard input")
    ap.add_argument("--apply", action="store_true", help="write a redacted copy")
    ap.add_argument("--out", help="where the redacted copy goes (default: alongside, with .redacted)")
    ap.add_argument("--min", default="low", choices=list(ORDER), help="lowest severity to report")
    ap.add_argument("--domain", action="append", default=[],
                    help="an internal domain to flag, added to the configured ones (repeatable)")
    ap.add_argument("--root", help="knowledge base folder, for prefs.internal_domains and house rules "
                                   "(default: ~/.flareware/flarehand)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    bad = [d for d in args.domain if not clean_domain(d)]
    if bad:
        print(f"error: not a domain: {', '.join(bad)}", file=sys.stderr)
        return 2

    if args.file == "-":
        text = sys.stdin.read()
        src = None
    else:
        src = Path(args.file)
        if not src.is_file():
            print(f"error: not a file: {src}", file=sys.stderr)
            return 2
        text = src.read_text(encoding="utf-8", errors="replace")

    patterns = load_all(Path(args.root).expanduser() if args.root else None, args.domain)
    found = scan(text, patterns, args.min)
    report = sys.stdout

    out_path = None
    written = 0
    if args.apply:
        cleaned, written = apply_redactions(text, patterns, args.min)
        if args.out:
            out_path = Path(args.out)
        elif src:
            out_path = src.with_suffix(src.suffix + ".redacted")
        if out_path:
            out_path.write_text(cleaned, encoding="utf-8")
        else:
            # stdout carries only the cleaned text, so it can be piped straight on.
            # The report goes to stderr instead.
            sys.stdout.write(cleaned)
            report = sys.stderr

    def say(*a):
        print(*a, file=report)

    if args.json:
        say(json.dumps({"findings": found, "count": len(found),
                        "redacted": written, "out": str(out_path) if out_path else None}, indent=2))
        return 1 if found else 0

    if not found:
        say("Nothing found that looks sensitive. Safe to send as far as this check goes.")
        say("It knows common English words for health and absence, not all of them. It cannot spot a bare customer")
        say("name, family or personal circumstances, or a protected characteristic. Read for those yourself.")
        return 0

    by_sev: dict[str, int] = {}
    for f in found:
        by_sev[f["severity"]] = by_sev.get(f["severity"], 0) + 1
    say(f"Found {len(found)} thing(s) worth a look before this leaves your machine:\n")
    for f in found[:40]:
        say(f"  {f['severity']:8} line {f['line']:>4}  {f['means']}: {f['text']}")
    if len(found) > 40:
        say(f"  ...and {len(found) - 40} more")
    say("\nCounts: " + ", ".join(f"{k} {v}" for k, v in sorted(by_sev.items(), key=lambda kv: -ORDER[kv[0]])))
    if any(f["rule"] in CREDENTIAL_RULES for f in found):
        say("\nA credential is in here. Removing it is not enough: whoever owns it needs to rotate it.")
    if any(f["rule"] == "company-suffix" for f in found):
        say("A company name is in here. If this goes to a different customer, that is a serious problem.")
    if any(f["rule"] in ("internal-domain", "internal-host", "private-ip") for f in found):
        say("An internal host or address is in here. Outside your organisation it maps your network, and")
        say("nobody else can open it anyway.")
    if any(f["rule"] == "health" for f in found):
        say("Health or a reason for absence is in here. Never keep it. --apply blanks the words it knows;")
        say("remove the whole sentence yourself before this goes anywhere.")
    kept = sum(1 for f in found if f["replacement"] == KEEP)
    if kept:
        say(f"{kept} [opinion] line(s) stay as they are, even with --apply. Outbound, an opinion must say whose")
        say("view it is. Add the name, or remove the line.")
    if out_path:
        say(f"\nRedacted copy written to {out_path} ({written} replacement(s)).")
    elif not args.apply:
        say("\nYour call. Three options:")
        say("  send it as it is       you know the audience and it is fine")
        say("  redact it              re-run with --apply and send the clean copy")
        say("  stop                   check with whoever owns the data first")
    return 1


if __name__ == "__main__":
    sys.exit(main())


# A reference to a variable is not the secret itself, so `os.environ["API_KEY"]` is fine.
ENV_REFERENCE = re.compile(r"os\.environ|getenv|process\.env|ENV\[|System\.getenv|\$\{[A-Z_]+\}")


# Rules about someone who is not in the room. The skill leaves these out of a note, and
# says that it did, because a silent omission is indistinguishable from not having noticed.
ABOUT_OTHERS = ("health",)


def other_people_hits(text: str) -> list[dict]:
    """Hits on the rules that protect somebody the note-taker is writing about."""
    out = []
    for h in scan(text, load_patterns(PATTERNS), "high"):
        if (h.get("rule") or h.get("name", "")) in ABOUT_OTHERS:
            out.append({"name": h.get("rule") or h.get("name", ""), "line": h.get("line", 0),
                        "means": h.get("means", "")})
    return out


def credential_hits(text: str) -> list[dict]:
    """Critical redaction hits: passwords, keys, tokens, connection strings, card and government ids.
    The matched text is never returned, so a caller cannot print the secret by accident."""
    lines = text.split("\n")
    hits = []
    for h in scan(text, load_patterns(PATTERNS), "critical"):
        line = lines[h.get("line", 1) - 1] if 0 < h.get("line", 0) <= len(lines) else ""
        if ENV_REFERENCE.search(line):
            continue
        hits.append({"name": h.get("rule") or h.get("name", ""), "severity": h.get("severity", ""),
                     "line": h.get("line", 0), "means": h.get("means", "")})
    return hits
