#!/usr/bin/env python3
"""sources.py - decide which kinds of source to look in first, for this person and question.

The same source matters differently to different people. The repository is
primary for a developer and secondary for support. A team playbook is primary
for a support analyst and rarely the answer to a version question. So the order
comes from five signals, combined the same way every time:

  1. the question   words like "what changed" put the git history first, "how do we"
                    puts the team playbook first
  2. your project   the files in the folder you work in name its technology, and that
                    names the official documentation to prefer
  3. your roles     a preferred order of source kinds for each kind of work you do,
                    merged so the strongest tier wins
  4. your pins      a kind or a domain you fixed at primary, secondary or never
  5. your usage     kinds and domains that keep helping you move up over time, after
                    several different days. That comes from work you saved and, if you
                    agreed once, from a list of source kinds, domains and dates recorded
                    after each answer. No content is ever recorded. Learning never
                    overrides a pin.

The source kinds are: user (what the person said), kb (their knowledge base),
repo (files), git (history), playbook (their team's written way of working),
mcp (MCP servers the harness has), official (official docs), secondary
(reputable secondary sources) and forum (forums and blogs).

This script cannot search anything. The agent does the searching, with the tools
its harness has, in the order this prints. The same inputs always give the same order.

Commands
  role      suggest or set your roles, or make one of your own
  kinds     what each source kind holds, and which ones your roles use
  project   which technologies the folder you work in uses, and their official docs
  order     the source order for a question, with a concrete hint for each kind
  pin       set a source kind or a domain to primary, secondary or never, or clear it
  learning  turn the usage list on or off, clear it, or show its state
  used      record which kinds and domains helped with an answer. Only when learning is on.

Lines that start with "Hint: " in the order output are actions for the agent to
take this session. The --json output lists them under "hints".

Pinned sources (a recurring question, its canonical locator and the quote it must
still contain) live in sources.tsv and are checked by `ground.py pins`.

Exit codes: 0 fine, 1 something needs attention, 2 usage or file error.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
import urllib.parse
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _text import tokens  # noqa: E402
from kb import (_utf8_console, atomic_write, read_config, read_prefs,  # noqa: E402
                require_root, today)

try:  # built by another part of the skill. Without it, only the knowledge base is read.
    import layers  # noqa: E402
except Exception:  # pragma: no cover - depends on what is installed next to this file
    layers = None

SKILL_DIR = Path(__file__).resolve().parent.parent
TIERS = SKILL_DIR / "assets" / "source-tiers.tsv"
PERSONAL_TIERS = "source-tiers.tsv"
SOURCES_TSV = "sources.tsv"
SOURCES_COLUMNS = ("type", "key", "value", "expect", "note")

KINDS = ("user", "kb", "repo", "git", "playbook", "mcp", "official", "secondary", "forum")
# user and kb lead every order: what the person said is the system of record for their own
# request, and their knowledge base costs one command to search.
ALWAYS_FIRST = ("user", "kb")
NEW_STARTER_DAYS = 30
# after the first month ends, say so for this long, so the change in order has a reason
NEW_STARTER_NOTE_DAYS = 7
# Several different days, so one busy afternoon never moves anything.
LEARN_MIN_CITES, LEARN_MIN_DAYS, LEARN_WINDOW = 3, 3, 60
# a role is only suggested for review after this long with none of its main kinds cited
ROLE_REVIEW_DAYS = 90
ROLE_SUGGEST_MIN_KINDS = 2
STRENGTH = {"first": -1, "signal": 0, "project": 1, "primary": 2, "secondary": 3}
WILDCARD_MAX = 3
USAGE_FILE = "usage.jsonl"
DOMAIN = re.compile(r"^[a-z0-9][a-z0-9.\-]*\.[a-z]{2,}(/[\w.\-/]*)?$")


# ---------------------------------------------------------------- matching

def compile_pattern(pattern: str) -> list:
    """A pattern becomes a token sequence. `*` stands for one to three words."""
    seq: list = []
    parts = pattern.split("*")
    for i, part in enumerate(parts):
        seq.extend(tokens(part))
        if i < len(parts) - 1:
            seq.append(None)
    while seq and seq[0] is None:
        seq.pop(0)
    while seq and seq[-1] is None:
        seq.pop()
    return seq


def find_span(hay: list, seq: list):
    """First occurrence of seq in hay, as (start, end), or None."""
    if not seq:
        return None

    def match_from(i: int, j: int):
        if j == len(seq):
            return i
        if seq[j] is None:
            for skip in range(1, WILDCARD_MAX + 1):
                if i + skip <= len(hay):
                    end = match_from(i + skip, j + 1)
                    if end is not None:
                        return end
            return None
        if i < len(hay) and hay[i] == seq[j]:
            return match_from(i + 1, j + 1)
        return None

    for start in range(len(hay)):
        end = match_from(start, 0)
        if end is not None:
            return start, end
    return None


# ---------------------------------------------------------------- data

def _empty_tiers() -> dict:
    return {"role": defaultdict(list), "signal": [], "source": {}, "roleword": [], "domain": defaultdict(list),
            "personal_roles": set(), "alias": {}, "serves": {}, "project": [], "host": {}}


def _read_tiers(path: Path, data: dict, personal: bool = False) -> dict:
    """Fold one tiers table into `data`. A personal row replaces the shipped rows for the
    same role, rather than adding to them, so someone editing their own copy gets what
    they wrote and not a merge they cannot see."""
    replaced: set = set()
    for raw in path.read_text(encoding="utf-8-sig").splitlines()[1:]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        f = (raw.split("\t") + ["", "", "", ""])[:5]
        kind, key, selector, tier, note = (x.strip() for x in f)
        if kind == "role" and selector.startswith("like:"):
            data["alias"][key] = selector[len("like:"):].strip()
            if personal:
                data["personal_roles"].add(key)
            continue
        if kind == "role":
            if selector not in KINDS:
                continue  # a typo in a hand-edited table degrades to one row fewer
            if personal and key not in replaced:
                replaced.add(key)
                data["role"][key] = []
                data["personal_roles"].add(key)
            data["role"][key].append({"kind": selector, "tier": tier or "secondary", "note": note})
        elif kind == "signal":
            if selector in KINDS:
                data["signal"].append({"patterns": [compile_pattern(p.strip()) for p in key.split("·") if p.strip()],
                                       "kind": selector, "note": note})
        elif kind == "source":
            if key in KINDS:
                data["source"][key] = {"tier": selector or "T3", "note": note}
        elif kind == "roleword":
            data["roleword"].append({"patterns": [compile_pattern(p.strip()) for p in key.split("·") if p.strip()],
                                     "role": selector})
        elif kind == "domain":
            data["domain"][key].append({"domain": selector.lower(), "tier": tier or "secondary", "note": note})
        elif kind == "serves":
            # A template's `serves:` list is job titles. A role is a source order. Two
            # vocabularies, and this row is the join, so neither drifts without a test noticing.
            data["serves"][key] = selector
        elif kind == "project":
            data["project"].append({"marker": key, "tech": selector,
                                    "domains": [d.strip().lower() for d in tier.split("·") if d.strip()],
                                    "note": note})
        elif kind == "host":
            data["host"][key.lower()] = {"kind": selector, "tier": tier, "note": note}
    return data


def personal_tiers(root: Path | None) -> Path | None:
    """Their own source tiers, read after the shipped ones. Yours wins, the shipped copy is the fallback."""
    if root is None:
        return None
    path = root / PERSONAL_TIERS
    return path if path.is_file() else None


def load_tiers(root: Path | None = None) -> dict:
    if not TIERS.is_file():
        print(f"error: {TIERS} is missing", file=sys.stderr)
        sys.exit(2)
    data = _empty_tiers()
    _read_tiers(TIERS, data)
    mine = personal_tiers(root)
    if mine is not None:
        try:
            _read_tiers(mine, data, personal=True)
        except OSError as e:
            print(f"warning: could not read {mine}: {e}. Using the shipped roles only.", file=sys.stderr)
    for name in data["alias"]:
        seen, like = {name}, data["alias"][name]
        while like in data["alias"] and like not in seen:   # an alias may point at an alias
            seen.add(like)
            like = data["alias"][like]
        if not data["role"].get(name):
            data["role"][name] = list(data["role"].get(like, []))
        if not data["domain"].get(name):
            data["domain"][name] = list(data["domain"].get(like, []))
    return data


def index_dir(root: Path) -> Path:
    d = root / ".index"
    d.mkdir(parents=True, exist_ok=True)
    return d


def days_old(stamp: str) -> int | None:
    try:
        return (date.today() - date.fromisoformat(str(stamp)[:10])).days
    except ValueError:
        return None


# ---------------------------------------------------------------- sources.tsv

def sources_rows(root: Path | None = None, cwd: Path | None = None) -> list[dict]:
    """Rows of sources.tsv from the knowledge base and every playbook, highest layer first.

    Columns: type, key, value, expect, note.
      pin     key = the question's intent, value = locator, expect = the quote it must still hold
      prefer  key = a source kind or a domain, value = primary, secondary or never
    Without layers.py, only the knowledge base copy is read.
    """
    if layers is not None:
        try:
            return layers.read_tsv(SOURCES_TSV, cwd=cwd, root=root)
        except Exception:
            pass
    if root is None:
        return []
    path = Path(root) / SOURCES_TSV
    if not path.is_file():
        return []
    out = []
    lines = [l for l in path.read_text(encoding="utf-8-sig").splitlines()
             if l.strip() and not l.lstrip().startswith("#")]
    if not lines:
        return out
    header = [c.strip().lower() for c in lines[0].split("\t")]
    for raw in lines[1:]:
        cells = [c.strip() for c in raw.split("\t")]
        cells += [""] * (len(header) - len(cells))
        row = dict(zip(header, cells))
        row["layer"] = "yours"
        out.append(row)
    return out


def team_preferences(root: Path | None, cwd: Path | None) -> dict:
    """{kind or domain: (tier, layer)} from `prefer` rows. Shapes, so the highest layer wins."""
    out: dict = {}
    for row in sources_rows(root, cwd):
        if str(row.get("type", "")).strip().lower() != "prefer":
            continue
        key = str(row.get("key", "")).strip().lower()
        tier = str(row.get("value", "")).strip().lower()
        if key and tier in ("primary", "secondary", "never") and key not in out:
            out[key] = (tier, str(row.get("layer", "")))
    return out


# ---------------------------------------------------------------- roles

def detect_roles(words: str, tiers: dict) -> list[str]:
    """Every role their own words point at, strongest first. People do more than one job."""
    hay = tokens(words)
    scores = Counter()
    for rw in tiers["roleword"]:
        for pat in rw["patterns"]:
            if find_span(hay, pat):
                scores[rw["role"]] += 1
    ranked = [r for r, _ in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))]
    return ranked or ["general"]


def current_roles(cfg: dict, tiers: dict) -> tuple[list[str], str]:
    """Roles the person confirmed, or the ones their words suggest."""
    prefs = cfg.get("prefs") or {}
    chosen = prefs.get("roles")
    if isinstance(chosen, str):
        chosen = [r.strip() for r in chosen.split(",")]
    elif chosen is not None and not isinstance(chosen, list):
        chosen = None  # a hand-edited config can hold anything. Fall back to what they said they do.
    if not chosen and prefs.get("role"):
        chosen = [prefs["role"]]
    if chosen:
        return [r for r in chosen if r in tiers["role"]] or ["general"], "set"
    return detect_roles(cfg.get("role_words", ""), tiers), "guessed from what you said you do"


def role_kinds(role: str, tiers: dict, tier: str | None = None) -> set[str]:
    return {e["kind"] for e in tiers["role"].get(role, []) if tier is None or e["tier"] == tier}


def role_suggestions(roles: list[str], usage: dict, tiers: dict) -> list[dict]:
    """Suggest a role their citations point at, or one they seem to have left. Never applied silently."""
    out = []
    learned = {k for k, r in usage.items() if k in KINDS and k not in ALWAYS_FIRST
               and r["cites"] >= LEARN_MIN_CITES and len(r["days"]) >= LEARN_MIN_DAYS}
    covered = set().union(*(role_kinds(r, tiers, "primary") for r in roles)) if roles else set()
    beyond = learned - covered
    for role in sorted(tiers["role"]):
        if role in roles or role == "general":
            continue
        overlap = sorted(beyond & role_kinds(role, tiers, "primary"))
        if len(overlap) >= ROLE_SUGGEST_MIN_KINDS:
            out.append({"action": "add", "role": role,
                        "why": f"you keep citing {', '.join(overlap)} sources, which that role looks in first"})
    total = sum(r["cites"] for k, r in usage.items() if k in KINDS)
    if len(roles) > 1 and total >= LEARN_MIN_CITES * 3:
        for role in roles:
            main = role_kinds(role, tiers, "primary") - set(ALWAYS_FIRST)
            if main and not any(usage.get(k, {}).get("cites") for k in main):
                out.append({"action": "review", "role": role,
                            "why": f"none of its main source kinds ({', '.join(sorted(main))}) were cited in "
                                   f"{ROLE_REVIEW_DAYS} days, while others were"})
    return out


# ---------------------------------------------------------------- the project

def repo_top(path: Path) -> Path | None:
    try:
        r = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    top = r.stdout.strip()
    return Path(top).resolve() if r.returncode == 0 and top else None


def repo_name_from_url(url: str) -> str | None:
    """'git@github.com:org/app.git', 'https://x/org/app', 'C:\\src\\app' all give 'app'."""
    url = url.strip().replace("\\", "/").rstrip("/")
    if not url:
        return None
    name = url.split("/")[-1].split(":")[-1]
    return name[:-4] if name.endswith(".git") else name


def detect_project(path: Path, tiers: dict) -> dict:
    """Which technologies the folder uses, from the files that name them.

    Looks in the folder and its parents, up to the repository's top (or three levels when
    it is not a repository), so a subfolder like src/ still finds its project. Each marker
    names a technology, and each technology names the official documentation to prefer.
    """
    path = Path(path).resolve()
    top = repo_top(path)
    folders = []
    for folder in [path, *path.parents]:
        folders.append(folder)
        if (top is not None and folder == top) or (top is None and len(folders) >= 3):
            break
    found: list[dict] = []
    seen_tech: set = set()
    for folder in folders:
        try:
            names = sorted(p.name for p in folder.iterdir() if p.is_file())
        except OSError:
            continue
        for row in tiers["project"]:
            hit = [n for n in names if fnmatch.fnmatchcase(n, row["marker"])]
            if hit and row["tech"] not in seen_tech:
                seen_tech.add(row["tech"])
                found.append({"technology": row["tech"], "marker": str(folder / hit[0]),
                              "docs": row["domains"], "about": row["note"]})
    domains: list[str] = []
    for f in found:
        for d in f["docs"]:
            if d not in domains:
                domains.append(d)
    return {"path": str(path), "repository": str(top) if top else None, "technologies": found, "docs": domains}


# ---------------------------------------------------------------- classifying a source

def host_of(locator: str) -> str:
    try:
        host = (urllib.parse.urlparse(locator).hostname or "").lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def _host_row(host: str, tiers: dict) -> dict | None:
    for known, row in tiers["host"].items():
        if host == known or host.endswith("." + known):
            return row
    return None


def official_domains(tiers: dict) -> list[str]:
    out = []
    for row in tiers["project"]:
        for d in row["domains"]:
            if d not in out:
                out.append(d)
    for rows in tiers["domain"].values():
        for r in rows:
            if r["domain"] not in out:
                out.append(r["domain"])
    return out


def _domain_match(url: str, domain: str) -> bool:
    """docs.python.org matches https://docs.python.org/3/x, and learn.microsoft.com/dotnet
    matches only paths under /dotnet."""
    host = host_of(url)
    want_host, _, want_path = domain.partition("/")
    if not (host == want_host or host.endswith("." + want_host)):
        return False
    if not want_path:
        return True
    path = urllib.parse.urlparse(url).path.lstrip("/")
    return path == want_path or path.startswith(want_path.rstrip("/") + "/")


def tier_for_url(url: str, tiers: dict | None = None) -> tuple[str, str]:
    """(source kind, tier) for a web page. A known forum is T4. Official docs for a known
    technology are T2. A primary text such as an RFC is T1. Anything else is T3, because a
    page nobody vouched for should not make a number verifiable on its own."""
    tiers = tiers or load_tiers()
    row = _host_row(host_of(url), tiers)
    if row:
        return row["kind"], row["tier"]
    if any(_domain_match(url, d) for d in official_domains(tiers)):
        return "official", "T2"
    return "secondary", "T3"


def kind_of(locator: str, tiers: dict, root: Path | None = None, tier: str = "") -> tuple[str, str]:
    """(source kind, domain) for a locator or a ground.py source row's kind. The domain is
    empty for anything that is not a web page."""
    s = (locator or "").strip()
    if not s:
        return "", ""
    if s.lower().startswith(("http://", "https://")):
        if tier in ("T0", "T1", "T2"):
            kind = "official"
        elif tier == "T3":
            kind = "secondary"
        elif tier == "T4":
            kind = "forum"
        else:
            kind = tier_for_url(s, tiers)[0]
        return kind, host_of(s)
    if s.startswith("git:"):
        return "git", ""
    if s.startswith("mcp:"):
        return "mcp", ""
    if s in KINDS:
        return s, ""
    if s.startswith("evidence/"):
        return "", ""
    p = Path(s).expanduser()
    if root is not None:
        try:
            p.resolve().relative_to(Path(root).resolve())
            return "kb", ""
        except (ValueError, OSError):
            pass
    if ".flarehand" in p.parts:
        return "playbook", ""
    if "/" in s or "." in s:
        return "repo", ""
    return "", ""


# ---------------------------------------------------------------- usage

def learning_state(cfg: dict) -> bool | None:
    """True or False once the person has chosen. None means nobody has asked them yet."""
    value = (cfg.get("prefs") or {}).get("usage_log")
    return value if isinstance(value, bool) else None


def _count(seen, key: str, day: str, window: int = LEARN_WINDOW):
    key = (key or "").strip().lower()
    if not key or not (key in KINDS or DOMAIN.match(key)):
        return
    age = days_old(day)
    if age is None or age > window:
        return
    rec = seen[key]
    rec["cites"] += 1
    rec["days"].add(day[:10])
    rec["last"] = max(rec["last"], day[:10])


def usage_counts(root: Path, window: int = LEARN_WINDOW) -> dict[str, dict]:
    """Uses per source kind and per domain, with distinct days. From saved work, and from the
    usage list if it is on. Keys are kind names (`official`) or domains (`docs.python.org`)."""
    seen: dict[str, dict] = defaultdict(lambda: {"cites": 0, "days": set(), "last": ""})
    try:
        enabled = learning_state(read_config(root)) is True
    except SystemExit:
        enabled = False
    tiers = None
    log = index_dir(root) / USAGE_FILE
    if enabled and log.is_file():
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                day = str(row.get("day", ""))
                _count(seen, str(row.get("kind", "")), day, window)
                if row.get("domain"):
                    _count(seen, str(row["domain"]), day, window)
    # Saved work counts whether or not the list is on: the person approved keeping it.
    sources: list[tuple[str, str]] = []
    ledger = root / "evidence" / "index.jsonl"
    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                sources.append((str(row.get("source", "")), str(row.get("kept_on") or row.get("captured_on") or "")))
    answers = root / "answers"
    if answers.is_dir():
        from kb import parse_frontmatter
        for p in answers.glob("*.md"):
            try:
                meta, _ = parse_frontmatter(p.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                continue
            for s in meta.get("sources") or []:
                sources.append((str(s), str(meta.get("generated_at", ""))))
    if sources:
        tiers = load_tiers(root)
    for src, day in sources:
        kind, domain = kind_of(src, tiers, root)
        if kind:
            _count(seen, kind, day, window)
        if domain:
            _count(seen, domain, day, window)
    return seen


def is_learned(rec: dict | None) -> bool:
    return bool(rec) and rec["cites"] >= LEARN_MIN_CITES and len(rec["days"]) >= LEARN_MIN_DAYS


# ---------------------------------------------------------------- order

def _merge(rows: dict, kind: str, tier: str, reason: str, only_if_weak: bool, cites: int) -> None:
    """Add a row, or raise an existing one. Two roles can rank the same kind differently.
    The stronger tier wins."""
    if kind in rows:
        row = rows[kind]
        if reason not in row["reasons"]:
            row["reasons"].append(reason)
        if STRENGTH.get(tier, 9) < STRENGTH.get(row["tier"], 9):
            row["tier"], row["only_if_weak"] = tier, only_if_weak
        return
    rows[kind] = {"kind": kind, "tier": tier, "reasons": [reason], "only_if_weak": only_if_weak, "cites": cites}


# A question about a link, a cause or a change is answered by walking the history, not by
# ranking pages. The first cue that matches names the move. See "Walk the history" in sources.md.
TRAVERSAL_CUES = (
    (re.compile(r"\b(who|what|which \w+) (calls|uses|references|depends on|imports)\b|\bcall(er|ers| sites)\b"),
     "what points at it", "git grep -n '<name>' for every caller in the working tree"),
    (re.compile(r"\b(renamed|moved|used to (be|live) (in|at|called))\b"),
     "where it came from", "git log --follow --oneline -- <path>"),
    (re.compile(r"\bwhy\b.*\b(written|this way|like this|chang\w*|added|removed)\b"),
     "why it is the way it is", "git log -S '<line>' --oneline, then git show <rev> to read the message"),
    (re.compile(r"\b(what|who|when)\b.*\b(changed|introduced|broke)\b|\bsince when\b|\bregress\w*"),
     "what changed", "git log -L <start>,<end>:<file> or git log --since=<date> -- <path>, then git blame -L"),
    (re.compile(r"\b(change[sd]?|move[sd]?) (together|alongside)\b|\bcoupled\b|\bco-?change"),
     "what moves with it", "git log --name-only --format= -- <path>, then count the other files"),
    (re.compile(r"\b(look|looked) like (in|on|at|before)\b|\bas of\b|\bback in\b"),
     "what it was then", "git rev-list -1 --before=<date> HEAD, then git show <rev>:<path>"),
    (re.compile(r"\b(every|all (the|of the)?)\s*(files?|tables?|endpoints?|routes?|screens?|procedures?|tests?)\b"),
     "all of one kind", "git ls-files or git grep -l '<pattern>', not a ranked search"),
)


def traversal_hint(question: str) -> str:
    q = " ".join(question.lower().split())
    for cue, what, move in TRAVERSAL_CUES:
        if cue.search(q):
            return (f"This asks {what}, which a search does not answer. Find the starting point, then walk: "
                    f"{move}. The moves are in references/sources.md, under Walk the history.")
    return ""


def _mcp_servers() -> list[str]:
    try:
        import doctor
        return doctor.mcp_server_names()
    except Exception:
        return []


def _playbook_list(root: Path | None, cwd: Path) -> list[dict]:
    if layers is None:
        return []
    try:
        return [{"name": p.name, "path": str(p.path)} for p in layers.playbooks(cwd, root)]
    except Exception:
        return []


def how_to(kind: str, ctx: dict) -> str:
    """A concrete next step for one source kind, for this harness and this folder."""
    q = ctx["question"].replace('"', "'")
    if kind == "user":
        return "Use what the person said or pasted this session. Label it [your input]."
    if kind == "kb":
        return f'python3 scripts/kb.py search "{q}", then kb.py neighbors on what it finds.'
    if kind == "repo":
        if ctx["repo"]:
            return f"Search the repository at {ctx['repo']} (rg or git grep for the terms), then read the files you cite."
        return "Search the folder they work in for the terms. It is not a git repository, so there is no history."
    if kind == "git":
        if ctx["repo"]:
            return (f"git -C {ctx['repo']} log -S '<term>' --oneline, git log -L, git blame. "
                    f"Cite a file at a revision as git:<rev>:<path>.")
        return "No git repository here. Skip this unless the person names one."
    if kind == "playbook":
        books = ctx["playbooks"]
        start = "Onboarding pages first, because you are new. " if ctx["new_starter"] else ""
        if books:
            names = ", ".join(f"{b['name']} ({b['path']})" for b in books)
            return f"{start}Read the team playbooks: {names}. Check house-rules.md in each."
        return f"{start}No playbook found here. Ask how their team does it, and offer to save their version."
    if kind == "mcp":
        servers = ctx["mcp"]
        if servers:
            return (f"MCP servers configured here: {', '.join(servers)}. Use one that holds this, and cite its "
                    f"item as mcp:<server>:<id>.")
        return "No MCP server is configured in the files doctor.py reads. Skip this kind."
    if kind == "official":
        docs = ctx["domains"]
        where = f"official docs at {', '.join(docs[:6])}" if docs else "the official docs for what this is about"
        return (f"Look in {where}. Fetch a page you have seen a link to with python3 scripts/ground.py fetch <url>. "
                f"Never write a URL you did not see in a tool result or the person's words.")
    if kind == "secondary":
        return "Reputable secondary sources are T3, so a number they give stays [weak] until a T0 to T2 source agrees."
    if kind == "forum":
        return "Forums and blogs are T4. Use them for leads, never as the only support for a specific."
    return ""


def build_order(root: Path, question: str, path: Path, tiers: dict, record: bool = True) -> dict:
    cfg = read_config(root)
    prefs = cfg.get("prefs", {}) or {}
    roles, role_source = current_roles(cfg, tiers)
    own_pins = {str(k).lower(): v for k, v in (prefs.get("source_pins", {}) or {}).items()}
    team = team_preferences(root, path)
    # Your own pin beats a team preference for the same kind or domain.
    pins = {k: t for k, (t, _) in team.items()}
    pins.update(own_pins)
    usage = usage_counts(root)
    project = detect_project(path, tiers)
    notes: list[str] = []
    hints: list[str] = []
    rows: dict[str, dict] = {}       # the order for this question
    standing: dict[str, dict] = {}   # the baseline from roles, pins and learning only

    excluded = {k for k, t in pins.items() if t == "never"}

    def put(kind: str, tier: str, reason: str, only_if_weak: bool = False, baseline: bool = False):
        if not kind or kind in excluded:
            return
        cites = usage.get(kind, {}).get("cites", 0)
        _merge(rows, kind, tier, reason, only_if_weak, cites)
        if baseline:
            _merge(standing, kind, tier, reason, only_if_weak, cites)

    # 1. question signals
    hay = tokens(question)
    for sig in tiers["signal"]:
        if any(find_span(hay, pat) for pat in sig["patterns"]):
            put(sig["kind"], "signal", sig["note"])

    # 2. what the person said, and their own notes, lead every order
    for kind in ALWAYS_FIRST:
        put(kind, "first", "always first: " + tiers["source"].get(kind, {}).get("note", kind), baseline=True)

    # 3. pins set the tier you chose, up or down. Only this question's own signals rank above a pin.
    pinned = {k: t for k, t in pins.items() if t in ("primary", "secondary") and k in KINDS}
    for kind, tier in sorted(pinned.items()):
        layer = "you pinned it" if kind in own_pins else f"your team prefers it ({team[kind][1]})"
        put(kind, tier, layer, only_if_weak=(tier == "secondary"), baseline=True)

    # 4. the project: the repository and its official docs move up when there is one
    if project["repository"] and "repo" not in pinned:
        put("repo", "project", f"you are working in {project['repository']}")
    if project["technologies"] and "official" not in pinned:
        techs = ", ".join(t["technology"] for t in project["technologies"])
        put("official", "project", f"this project uses {techs}")

    # 5. the role baseline, the first month, and learned promotions, for everything not pinned
    started = days_old(cfg.get("started_on", "")) if cfg.get("started_on") else None
    new_starter = started is not None and 0 <= started <= NEW_STARTER_DAYS
    if new_starter and "playbook" not in pinned:
        put("playbook", "primary", "you are new, so onboarding and team docs come early")
    for role in roles:
        for entry in tiers["role"].get(role, []):
            if entry["kind"] not in pinned:
                put(entry["kind"], entry["tier"], f"{entry['note']} ({role})",
                    only_if_weak=(entry["tier"] == "secondary"), baseline=True)
    for kind, rec in sorted(usage.items()):
        if kind not in KINDS or not is_learned(rec) or kind in excluded or kind in pinned:
            continue
        reason = f"you cited it {rec['cites']} times on {len(rec['days'])} days"
        for target in (rows, standing):
            if kind in target and target[kind]["tier"] == "secondary":
                target[kind]["tier"], target[kind]["only_if_weak"] = "primary", False
                target[kind]["reasons"].append(reason)
        if kind not in rows:
            put(kind, "primary", reason, baseline=True)
    if started is not None and NEW_STARTER_DAYS < started <= NEW_STARTER_DAYS + NEW_STARTER_NOTE_DAYS \
            and "playbook" in rows and rows["playbook"]["tier"] != "primary":
        notes.append("Your first month is over, so team docs are back to their role tier.")

    order_index = {k: i for i, k in enumerate(KINDS)}
    ordered = sorted(rows.values(), key=lambda r: (STRENGTH.get(r["tier"], 9), -r["cites"],
                                                     order_index.get(r["kind"], 99)))

    # Preferred domains: the project's official docs, your roles' domains, team and own
    # preferences, then what you keep citing. A domain pinned never is dropped everywhere.
    domains: list[dict] = []

    def add_domain(d: str, why: str, tier: str = "primary"):
        d = d.lower()
        if d in excluded or any(x["domain"] == d for x in domains):
            return
        domains.append({"domain": d, "tier": tier, "why": why})

    for d, t in sorted(pins.items()):
        if d not in KINDS and t in ("primary", "secondary"):
            add_domain(d, "you pinned it" if d in own_pins else "your team prefers it", t)
    for t in project["technologies"]:
        for d in t["docs"]:
            add_domain(d, f"official docs for {t['technology']}")
    for role in roles:
        for r in tiers["domain"].get(role, []):
            add_domain(r["domain"], f"{r['note']} ({role})", r["tier"])
    for d, rec in sorted(usage.items()):
        if d not in KINDS and is_learned(rec) and d not in pins:
            add_domain(d, f"you cited it {rec['cites']} times on {len(rec['days'])} days")

    ctx = {"question": question, "repo": project["repository"], "playbooks": _playbook_list(root, path),
           "mcp": _mcp_servers(), "domains": [d["domain"] for d in domains if d["tier"] == "primary"]
           or [d["domain"] for d in domains], "new_starter": new_starter}
    for row in ordered:
        row["how"] = how_to(row["kind"], ctx)

    if new_starter and not ctx["playbooks"]:
        hints.append("They are new and no playbook was found. Ask once where their team keeps onboarding notes.")
    walk = traversal_hint(question)
    if walk:
        hints.append(walk)
    if learning_state(cfg) is None:
        notes.append("Not asked yet: whether to keep a usage list of source kinds and domains. Ask once. "
                     "See sources.py learning.")

    review_usage = usage_counts(root, window=ROLE_REVIEW_DAYS)
    result = {
        "roles": roles, "role_source": role_source,
        "project": {"repository": project["repository"],
                    "technologies": [t["technology"] for t in project["technologies"]],
                    "markers": [t["marker"] for t in project["technologies"]]},
        "usage_log": learning_state(cfg),
        "role_suggestions": role_suggestions(roles, review_usage, tiers),
        "pin_suggestions": pin_suggestions(own_pins, prefs.get("source_pin_dates", {}) or {}, usage),
        "order": ordered,
        "domains": domains,
        "excluded": sorted(excluded),
        "rule": "Look in this order. Look at a row marked only_if_weak only when nothing so far gave a T0 to T2 "
                "source with a word-for-word quote. Stage what you cite with ground.py fetch or ground.py source add.",
        "hints": hints,
        "notes": sorted(set(notes)),
    }
    if record:
        # Only the standing baseline is compared: roles, pins and learning. The question and the
        # folder you are in change on purpose, so they are not "changes".
        _record_changes(root, ",".join(roles), [r["kind"] + ":" + r["tier"] for r in standing.values()
                                                if r["tier"] in ("primary", "secondary") and r["kind"] not in ALWAYS_FIRST],
                        result)
    return result


def pin_suggestions(pinned: dict, pin_dates: dict, usage: dict) -> list[dict]:
    """Learning never changes a pin. When your citations disagree with one, it says so, and you decide."""
    out = []
    for key, tier in sorted(pinned.items()):
        rec = usage.get(key)
        if tier == "secondary" and is_learned(rec):
            out.append({"action": "raise the pin on", "source": key,
                        "why": f"you pinned it secondary, and it still helped {rec['cites']} times "
                               f"on {len(rec['days'])} days"})
        pinned_for = days_old(pin_dates.get(key, ""))
        if tier != "never" and pinned_for is not None and pinned_for > LEARN_WINDOW and not (rec and rec["cites"]):
            out.append({"action": "review the pin on", "source": key,
                        "why": f"you pinned it {pinned_for} days ago, and it has not helped in {LEARN_WINDOW} days"})
    return out


def _record_changes(root: Path, role: str, baseline: list[str], result: dict):
    """Keep the last baseline so a change can be reported, not silently applied."""
    path = index_dir(root) / "source-map.json"
    old = []
    if path.is_file():
        try:
            prev = json.loads(path.read_text(encoding="utf-8"))
            old = prev.get("baseline", []) if prev.get("role") == role else []
        except (OSError, json.JSONDecodeError, AttributeError):
            old = []
    added = sorted(set(baseline) - set(old)) if old else []
    removed = sorted(set(old) - set(baseline)) if old else []
    if added or removed:
        result["changed_since_last_time"] = {"added": added, "removed": removed}
    atomic_write(path, json.dumps({"role": role, "baseline": sorted(baseline), "updated": today()}, indent=2) + "\n")


# ---------------------------------------------------------------- commands

def slugify_role(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")


def _new_role(root: Path, args, tiers: dict) -> int:
    """Write a role of their own into their knowledge base, seeded from one that exists.

    Their file is read after the shipped one, and a role they define replaces the shipped
    rows for that name rather than merging with them.
    """
    name = slugify_role(args.new)
    if not name:
        print("error: a role name needs a letter or a number in it", file=sys.stderr)
        return 2
    like = args.like or "general"
    if like not in tiers["role"]:
        print(f"error: no role called '{like}' to copy. Pick from: {', '.join(sorted(tiers['role']))}",
              file=sys.stderr)
        return 2
    path = root / PERSONAL_TIERS
    if not path.is_file():
        atomic_write(path, "kind\tkey\tselector\ttier\tnote\n"
                           "# Your own roles. Read after the shipped table, and a role here\n"
                           "# replaces the shipped rows for that name. Delete a block to go back.\n"
                           f"# Source kinds: {', '.join(KINDS)}. Tiers: primary, secondary.\n")
    existing = path.read_text(encoding="utf-8-sig")
    if any(l.split("\t")[:2] == ["role", name] for l in existing.splitlines()):
        print(f"You already have a role called {name}. Edit {path} to change it.")
        return 0
    rows = "".join(f"role\t{name}\t{e['kind']}\t{e['tier']}\t{e['note']}\n" for e in tiers["role"][like])
    rows += "".join(f"domain\t{name}\t{d['domain']}\t{d['tier']}\t{d['note']}\n" for d in tiers["domain"].get(like, []))
    atomic_write(path, existing.rstrip("\n") + "\n" + rows)
    print(f"Created the role '{name}' in {path}, with the source order {like} uses.")
    print(f"Edit that file to change which kinds it looks in first. Then add it to your roles with "
          f"sources.py role --add {name}, or make it your only role with --set {name}.")
    return 0


def cmd_role(args) -> int:
    root = require_root(args)
    tiers = load_tiers(root)
    cfg_path = root / "config.json"
    cfg = read_config(root)
    prefs = cfg.setdefault("prefs", {})
    roles, source = current_roles(cfg, tiers)

    if getattr(args, "new", None):
        return _new_role(root, args, tiers)

    changes = None
    if args.set:
        changes = [r.strip() for r in args.set.split(",") if r.strip()]
    elif args.add:
        changes = roles + [args.add] if args.add not in roles else roles
    elif args.remove:
        changes = [r for r in roles if r != args.remove]
    if changes is not None:
        unknown = [r for r in changes if r not in tiers["role"]]
        if unknown:
            near = [r for r in sorted(tiers["role"]) if r.lower() == unknown[0].lower()]
            print(f"error: unknown role {', '.join(unknown)}.", file=sys.stderr)
            if near:
                print(f"       Did you mean {near[0]}? Role names are lower case.", file=sys.stderr)
            print(f"       Pick from: {', '.join(sorted(tiers['role']))}", file=sys.stderr)
            print(f"       Or make your own: sources.py role --new {slugify_role(unknown[0])} "
                  f"--like general", file=sys.stderr)
            return 2
        prefs["roles"] = list(dict.fromkeys(changes)) or ["general"]
        prefs.pop("role", None)  # the single-role field is replaced, not left to disagree
        atomic_write(cfg_path, json.dumps(cfg, indent=2) + "\n")
        print(f"Roles are now: {', '.join(prefs['roles'])}. Their source orders merge, strongest tier first.")
        return 0

    suggested = detect_roles(cfg.get("role_words", ""), tiers)
    suggestions = role_suggestions(roles, usage_counts(root, window=ROLE_REVIEW_DAYS), tiers)
    out = {"current": roles, "current_source": source, "from_words": suggested,
           "words": cfg.get("role_words", ""), "suggestions": suggestions, "all_roles": sorted(tiers["role"])}
    if args.json:
        print(json.dumps(out, indent=2))
        return 0
    print(f"Current roles: {', '.join(roles)} ({source})")
    # Only when nobody has chosen yet. Someone who set their roles on purpose should not be
    # asked to undo it every time they run this, and order is not disagreement.
    if source != "set":
        print(f"Your words point at: {', '.join(suggested)}")
        if set(suggested) != set(roles):
            print(f"Confirm with the person, then run: sources.py role --set {','.join(suggested)}")
    elif set(suggested) - set(roles):
        extra = sorted(set(suggested) - set(roles))
        print(f"Your words also point at: {', '.join(extra)}. If that fits, add it: "
              f"sources.py role --add {extra[0]}")
    for s in suggestions:
        print(f"Suggestion: {s['action']} {s['role']}, because {s['why']}.")
    return 0


def cmd_kinds(args) -> int:
    """What each source kind holds, so someone can choose one instead of guessing a name."""
    root = require_root(args)
    tiers = load_tiers(root)
    prefs = read_prefs(root)
    pins = {str(k).lower(): v for k, v in (prefs.get("source_pins", {}) or {}).items()}
    team = team_preferences(root, Path(args.path).resolve())
    roles, _ = current_roles(read_config(root), tiers)
    mine = set().union(*(role_kinds(r, tiers) for r in roles)) if roles else set()
    rows = []
    for kind in KINDS:
        info = tiers["source"].get(kind, {})
        rows.append({"kind": kind, "holds": info.get("note", ""), "default_tier": info.get("tier", ""),
                     "in_your_roles": kind in mine or kind in ALWAYS_FIRST, "pinned": pins.get(kind, ""),
                     "team": team.get(kind, ("", ""))[0]})
    domain_pins = [{"domain": k, "pinned": v} for k, v in sorted(pins.items()) if k not in KINDS]
    if args.json:
        print(json.dumps({"kinds": rows, "domain_pins": domain_pins, "roles": roles}, indent=2))
        return 0
    print(f"Your roles: {', '.join(roles)}. A * marks a kind they look in.\n")
    for r in rows:
        mark = "*" if r["in_your_roles"] else " "
        pin = f"  [pinned {r['pinned']}]" if r["pinned"] else ""
        team_pin = f"  [team: {r['team']}]" if r["team"] else ""
        print(f"{mark} {r['kind']:<10} {r['default_tier']:<3} {r['holds'][:70]}{pin}{team_pin}")
    for d in domain_pins:
        print(f"  domain {d['domain']}  [pinned {d['pinned']}]")
    print("\nPin a kind or a domain with: sources.py pin <kind|domain> primary|secondary|never")
    print("Your order also moves on its own, as what you cite changes. `role` and `pin` show it.")
    return 0


def cmd_project(args) -> int:
    tiers = load_tiers()
    got = detect_project(Path(args.path), tiers)
    if args.json:
        print(json.dumps(got, indent=2))
    else:
        print(f"Folder      {got['path']}")
        print(f"Repository  {got['repository'] or 'not a git repository'}")
        for t in got["technologies"]:
            print(f"Uses        {t['technology']}, from {t['marker']}. Docs: {', '.join(t['docs'])}")
        if not got["technologies"]:
            print("Uses        nothing this table recognises")
    return 0 if got["technologies"] else 1


def cmd_order(args) -> int:
    root = require_root(args)
    result = build_order(root, args.question, Path(args.path).resolve(), load_tiers(root))
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"Roles: {', '.join(result['roles'])} ({result['role_source']})")
    if result["project"]["technologies"]:
        print(f"Project: {', '.join(result['project']['technologies'])}")
    for s in result.get("role_suggestions", []):
        print(f"Suggestion: {s['action']} {s['role']}, because {s['why']}. Ask before changing it.")
    for s in result.get("pin_suggestions", []):
        print(f"Suggestion: {s['action']} {s['source']}, because {s['why']}. Ask before changing it.")
    for r in result["order"]:
        cond = "  (only if nothing strong yet)" if r["only_if_weak"] else ""
        print(f"  {r['tier']:9} {r['kind']:10} {'; '.join(r['reasons'])}{cond}")
        print(f"            {r['how']}")
    if result["domains"]:
        print("Prefer: " + ", ".join(d["domain"] for d in result["domains"]))
    if result["excluded"]:
        print("Never: " + ", ".join(result["excluded"]))
    if result.get("changed_since_last_time"):
        c = result["changed_since_last_time"]
        print(f"Changed since last time: added {c['added'] or 'none'}, removed {c['removed'] or 'none'}")
    for h in result.get("hints", []):
        print(f"Hint: {h}")
    for n in result["notes"]:
        print(f"Note: {n}")
    return 0


def cmd_learning(args) -> int:
    root = require_root(args)
    cfg = read_config(root)
    prefs = cfg.setdefault("prefs", {})
    log = index_dir(root) / USAGE_FILE
    if args.on or args.off:
        prefs["usage_log"] = bool(args.on)
        prefs["usage_log_decided_on"] = today()
        atomic_write(root / "config.json", json.dumps(cfg, indent=2) + "\n")
        if args.on:
            print("On. After each answer, the kinds of source that helped, and their web domains, are "
                  "recorded with the date.")
            print("Nothing else is recorded: no questions, no answers, no addresses, no content.")
        else:
            print("Off. Nothing is recorded. It still learns from work you choose to save.")
        return 0
    if args.clear:
        removed = len(log.read_text(encoding="utf-8").splitlines()) if log.is_file() else 0
        log.unlink(missing_ok=True)
        print(f"Cleared {removed} recorded use(s).")
        return 0
    state = learning_state(cfg)
    rows = len(log.read_text(encoding="utf-8").splitlines()) if log.is_file() else 0
    out = {"usage_log": state, "asked": state is not None, "recorded_uses": rows, "file": str(log)}
    if args.json:
        print(json.dumps(out, indent=2))
    elif state is None:
        print("Not asked yet. Ask once: may I keep a list of which kinds of source help you, such as your "
              "repository or a docs site? Kinds, domains and dates only, no content. Then run: "
              "sources.py learning --on, or --off.")
    else:
        print(f"Usage list is {'on' if state else 'off'}. {rows} recorded use(s) in {log}.")
    return 0 if state is not None else 1


def _ledger_sources(root: Path) -> dict[str, dict]:
    """{S#: row} from this session's source ledger, written by ground.py."""
    try:
        from evidence import staging_dir
    except Exception:
        return {}
    path = staging_dir(root) / "sources.jsonl"
    out = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("id"):
            out[str(row["id"])] = row
    return out


GROUND_KIND = {"user": "user", "git": "git", "mcp": "mcp"}


def classify_used(items: list[str], root: Path, tiers: dict) -> list[tuple[str, str]]:
    """(kind, domain) for each S# id or locator, once each. Unknown items are skipped."""
    ledger = None
    out: list[tuple[str, str]] = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        if re.fullmatch(r"S\d+", item):
            if ledger is None:
                ledger = _ledger_sources(root)
            row = ledger.get(item)
            if not row:
                continue
            gk = str(row.get("kind", ""))
            if gk in GROUND_KIND:
                pair = (GROUND_KIND[gk], "")
            elif gk == "web":
                pair = kind_of(str(row.get("canonical") or row.get("locator", "")), tiers, root,
                               str(row.get("tier", "")))
            else:
                pair = kind_of(str(row.get("locator", "")), tiers, root)
        else:
            pair = kind_of(item, tiers, root)
        if pair[0] and pair not in out:
            out.append(pair)
    return out


def cmd_used(args) -> int:
    """Record the kinds and domains behind one answer. A no-op unless the person turned learning on."""
    root = require_root(args)
    state = learning_state(read_config(root))
    if state is not True:
        if state is None:
            print("Not recorded: the person has not been asked about the usage list yet.", file=sys.stderr)
        return 0
    pairs = classify_used(args.ids, root, load_tiers(root))
    if not pairs:
        return 0
    log = index_dir(root) / USAGE_FILE
    keep = []
    if log.is_file():
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            age = days_old(str(row.get("day", "")))
            if age is not None and age <= ROLE_REVIEW_DAYS:  # older uses no longer count, so drop them
                keep.append(json.dumps({"kind": row.get("kind", ""), "domain": row.get("domain", ""),
                                        "day": row.get("day")}))
    keep += [json.dumps({"kind": k, "domain": d, "day": today()}) for k, d in pairs]
    atomic_write(log, "\n".join(keep) + "\n")
    print(f"Recorded {len(pairs)} source kind(s): " + ", ".join(k + (f" ({d})" if d else "") for k, d in pairs))
    return 0


def cmd_pin(args) -> int:
    root = require_root(args)
    cfg = read_config(root)
    pins = cfg.setdefault("prefs", {}).setdefault("source_pins", {})
    dates = cfg["prefs"].setdefault("source_pin_dates", {})
    key = (args.source or "").strip().lower()
    if key.startswith(("http://", "https://")):
        key = host_of(key)
    if not key:
        print("error: give the source kind or the domain to pin", file=sys.stderr)
        return 2
    if args.clear:
        pins.pop(key, None)
        dates.pop(key, None)
        msg = f"Cleared the pin on {key}."
    else:
        if key not in KINDS and not DOMAIN.match(key):
            near = [k for k in KINDS if k.startswith(key[:3])]
            hint = f" Did you mean {near[0]}?" if near else ""
            print(f"error: {key} is not a source kind or a domain.{hint} Kinds: {', '.join(KINDS)}.", file=sys.stderr)
            return 2
        if args.tier not in ("primary", "secondary", "never"):
            print("error: tier must be primary, secondary or never", file=sys.stderr)
            return 2
        pins[key] = args.tier
        dates[key] = today()
        msg = (f"{key} is pinned to {args.tier}. Learning will not change that. If what you cite "
               f"disagrees with it, the order will suggest a change, and you decide.")
    atomic_write(root / "config.json", json.dumps(cfg, indent=2) + "\n")
    print(msg)
    return 0


def _common() -> argparse.ArgumentParser:
    """Flags accepted both before and after the subcommand, the same way kb.py does it."""
    c = argparse.ArgumentParser(add_help=False)
    c.add_argument("--root", default=argparse.SUPPRESS, help="knowledge base folder (default: ~/.flareware/flarehand)")
    c.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="machine readable output")
    return c


def main(argv=None) -> int:
    _utf8_console()
    p = argparse.ArgumentParser(prog="sources.py",
                                description="Decide which kinds of source to look in first, for this person and question.")
    p.add_argument("--root", help="knowledge base folder (default: ~/.flareware/flarehand)")
    p.add_argument("--json", action="store_true")
    common = _common()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("role", help="show, set, add or remove your roles", parents=[common])
    s.add_argument("--set", help="one or more roles, comma separated")
    s.add_argument("--add", help="add one role")
    s.add_argument("--remove", help="remove one role")
    s.add_argument("--new", metavar="NAME", help="create a role of your own, in your knowledge base")
    s.add_argument("--like", metavar="ROLE", help="with --new: the role to copy its source order from")
    s.set_defaults(func=cmd_role)

    s = sub.add_parser("kinds", help="what each source kind holds, and which ones you use", parents=[common])
    s.add_argument("--path", default=".", help="folder you are working in, for team preferences")
    s.set_defaults(func=cmd_kinds)

    s = sub.add_parser("project", help="which technologies this folder uses, and their docs", parents=[common])
    s.add_argument("--path", default=".")
    s.set_defaults(func=cmd_project)

    s = sub.add_parser("order", help="the source order for a question", parents=[common])
    s.add_argument("question")
    s.add_argument("--path", default=".", help="folder you are working in")
    s.set_defaults(func=cmd_order)

    s = sub.add_parser("pin", help="pin a source kind or a domain to a tier", parents=[common])
    s.add_argument("source", help=f"a kind ({', '.join(KINDS)}) or a domain such as docs.python.org")
    s.add_argument("tier", nargs="?", default="primary")
    s.add_argument("--clear", action="store_true")
    s.set_defaults(func=cmd_pin)

    s = sub.add_parser("learning", help="turn the usage list on or off, clear it, or show its state",
                       parents=[common])
    g = s.add_mutually_exclusive_group()
    g.add_argument("--on", action="store_true")
    g.add_argument("--off", action="store_true")
    g.add_argument("--clear", action="store_true")
    s.set_defaults(func=cmd_learning)

    s = sub.add_parser("used", help="record which kinds and domains helped (only when learning is on)",
                       parents=[common])
    s.add_argument("ids", nargs="+", help="S# ids from ground.py, or the locators you cited")
    s.set_defaults(func=cmd_used)

    args = p.parse_args(argv)
    if not hasattr(args, "root"):
        args.root = None
    if not hasattr(args, "json"):
        args.json = False
    return args.func(args)


if __name__ == "__main__":
    from kb import run_guarded
    sys.exit(run_guarded(main))
