#!/usr/bin/env python3
"""review.py - grade a review the same way every time.

A review has lenses, such as correctness or regressions. Each lens produces findings,
and each finding is checked against the code before anyone reports it. This script
does the parts that should never be a judgment call: the brief each reviewer gets,
the rule that turns findings into a grade, and the order the report lists them in.
The same findings always give the same grades and the same report.

Usage
  python3 scripts/review.py lenses                    # the lenses, and what each checks
  python3 scripts/review.py brief regressions         # the brief for one reviewer
  python3 scripts/review.py brief --verify            # the brief for whoever checks the findings
  python3 scripts/review.py rules                     # the house rules every review checks against
  python3 scripts/review.py configs                   # the linters and style configs this repo ships
  python3 scripts/review.py grade findings.jsonl      # grades and the ranked report
  python3 scripts/review.py grade findings.jsonl --most-likely "<one sentence>"
  python3 scripts/review.py grade findings.jsonl --only correctness,regressions
  python3 scripts/review.py grade findings.jsonl --reviewed "PR 42 against main" --ticket "TOOL-1 ..." --tested yes

The report follows assets/templates/code-review.md, section for section. Rows you did not
pass on the command line say [your input], so fill them in before the template check.

Findings file: one JSON object per line. checked must be a JSON boolean: true or false, not a string.
  {"lens": "regressions", "checked": true}
  {"lens": "regressions", "checked": false, "reason": "no tests on the base branch"}
  {"lens": "regressions", "severity": "blocking", "verdict": "confirmed", "where": "src/a.py:40",
   "finding": "...", "evidence": "...", "fix": "..."}
  Add "outside_change": true for a problem in code the change did not touch.

The grading rule
  fail          any confirmed blocking finding
  concerns      any confirmed should-fix finding, or any plausible blocking finding
  pass          everything else, including minor findings
  not checked   the lens says checked false, or it has no record and no findings
Rejected findings are counted and never graded. The overall grade is the worst lens grade.

House rules
  Every lens brief carries the house rules from house-rules.md in every layer: your knowledge
  base, then each team playbook (layers.py). Rules add up, so a rule in any layer applies.
  A house-rules.md has one rule per "- " line under "## <area>" headings. The brief also names
  the linter and style configs found at the root of the repo under review, because the
  project's own config is its first standard.

Exit codes: 0 pass or concerns, 1 fail, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kb import _utf8_console, resolve_root  # noqa: E402
from _text import REPO_PATH, is_citable_source  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
SEVERITIES = ["blocking", "should-fix", "minor"]
SEVERITY_TITLES = {"blocking": "Blocking", "should-fix": "Should fix", "minor": "Minor"}
VERDICTS = ["confirmed", "plausible", "rejected"]
GRADE_ORDER = ["pass", "concerns", "fail"]
LENS_COLUMNS = ["lens", "name", "question", "look_for", "standard"]
LENS_KEY_RE = re.compile(r"^[a-z0-9-]+$")
HOUSE_RULES = "house-rules.md"
HEADING_RE = re.compile(r"^##\s+(.+?)\s*#*\s*$")
RULE_RE = re.compile(r"^\s*[-*]\s+(.+?)\s*$")
# Linter, formatter and style configs a project keeps at its root. Their rules are the project's
# own standard, so a reviewer applies them and skips what the tool already enforces.
CONFIG_FILES = [
    (".editorconfig", "EditorConfig"),
    ("pyproject.toml", "Python project config (ruff, black, mypy, pytest sections)"),
    ("ruff.toml", "Ruff"), (".ruff.toml", "Ruff"), (".flake8", "Flake8"), ("setup.cfg", "Python tool config"),
    (".pylintrc", "Pylint"), ("pylintrc", "Pylint"), ("mypy.ini", "mypy"), ("tox.ini", "tox and Python tools"),
    (".eslintrc", "ESLint"), (".eslintrc.js", "ESLint"), (".eslintrc.cjs", "ESLint"), (".eslintrc.json", "ESLint"),
    (".eslintrc.yml", "ESLint"), (".eslintrc.yaml", "ESLint"), ("eslint.config.js", "ESLint"),
    ("eslint.config.mjs", "ESLint"), ("eslint.config.cjs", "ESLint"), ("eslint.config.ts", "ESLint"),
    (".prettierrc", "Prettier"), (".prettierrc.json", "Prettier"), (".prettierrc.yml", "Prettier"),
    (".prettierrc.yaml", "Prettier"), (".prettierrc.js", "Prettier"), ("prettier.config.js", "Prettier"),
    ("biome.json", "Biome"), ("tsconfig.json", "TypeScript compiler options"),
    (".stylelintrc", "Stylelint"), (".stylelintrc.json", "Stylelint"),
    (".golangci.yml", "golangci-lint"), (".golangci.yaml", "golangci-lint"), (".golangci.toml", "golangci-lint"),
    ("rustfmt.toml", "rustfmt"), (".rustfmt.toml", "rustfmt"), ("clippy.toml", "Clippy"),
    (".rubocop.yml", "RuboCop"), (".clang-format", "clang-format"), (".clang-tidy", "clang-tidy"),
    ("checkstyle.xml", "Checkstyle"), ("detekt.yml", "detekt"), (".swiftlint.yml", "SwiftLint"),
    ("analysis_options.yaml", "Dart analyzer"), (".sqlfluff", "SQLFluff"), (".markdownlint.json", "markdownlint"),
    (".markdownlint.yaml", "markdownlint"), (".pre-commit-config.yaml", "pre-commit hooks"),
    ("sonar-project.properties", "SonarQube"),
]
PLACEHOLDER = "[your input]"
PR_COMMENT_NOTE = ("<!-- Only if they will post it, and only after they have read the code themselves. "
                   "Three parts: what you liked, what to keep an eye on (non-blocking), and the decision. "
                   "Run redact.py first. Never post without a yes. -->")


def load_lenses(root: Path | None = None) -> list[dict]:
    """The shipped lenses, then any the person added. A personal list adds lenses and never
    hides one, because a review that quietly skips a lens reads as a review that passed it."""
    shipped = _lens_rows(SKILL / "assets" / "review-lenses.tsv")
    mine = root / "templates" / "review-lenses.tsv" if root is not None else None
    if mine is None or not mine.is_file():
        return shipped
    keys = {r["lens"] for r in shipped}
    added = []
    for row in _lens_rows(mine):
        if row["lens"] in keys:
            print(f"warning: {mine}: '{row['lens']}' is a shipped lens, so yours was skipped. "
                  f"Give it a key of its own to add it alongside.", file=sys.stderr)
            continue
        keys.add(row["lens"])
        added.append(row)
    return shipped + added


def _lens_rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    lines = [l for l in path.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    head = [h.strip() for h in lines[0].split("\t")] if lines else []
    missing = [c for c in LENS_COLUMNS if c not in head]
    if missing:
        print(f"warning: {path} is not a lens list. Its header lacks: {', '.join(missing)}. "
              f"Expected columns: {', '.join(LENS_COLUMNS)}. Skipping it.", file=sys.stderr)
        return []
    rows = []
    for n, line in enumerate(lines[1:], start=2):
        cells = [c.strip() for c in line.split("\t")]
        row = dict(zip(head, cells))
        if len(cells) < len(head) or not LENS_KEY_RE.match(row.get("lens", "")):
            print(f"warning: {path} line {n}: skipped. A lens row needs {len(head)} columns and a "
                  f"lens key of lowercase letters, digits and hyphens.", file=sys.stderr)
            continue
        rows.append(dict(row, file=str(path)))
    if not rows:
        print(f"warning: {path} has no usable lens rows. Skipping it.", file=sys.stderr)
    return rows


def house_rule_files(root: Optional[Path] = None, cwd: Optional[Path] = None) -> list:
    """Every house-rules.md that applies, highest precedence first, as (layer, path).

    layers.py finds your knowledge base and each team playbook. Without it, only the
    knowledge base is read, so a missing module costs the team rules, never the check."""
    try:
        import layers  # noqa: E402
        found = layers.layered(HOUSE_RULES, cwd=cwd, root=root)
        return [(str(layer), Path(path)) for layer, path in found if Path(path).is_file()]
    except Exception:
        pass
    base = root if root is not None else resolve_root(None)
    path = Path(base) / HOUSE_RULES
    return [("yours", path)] if path.is_file() else []


def parse_house_rules(text: str) -> list:
    """One rule per "- " line, under the "## <area>" heading above it."""
    rules, area, fenced = [], "", False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        h = HEADING_RE.match(line)
        if h:
            area = h.group(1).strip()
            continue
        m = RULE_RE.match(line)
        if m and area:
            rules.append({"area": area, "rule": m.group(1)})
    return rules


def house_rules(root: Optional[Path] = None, cwd: Optional[Path] = None) -> list:
    """The union of every layer's house rules, each tagged with its layer. Rules add up:
    a personal file can add a rule, never remove a team one. An exact repeat is kept once,
    under the nearest layer that says it."""
    out, seen = [], set()
    for layer, path in house_rule_files(root, cwd):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            continue
        for r in parse_house_rules(text):
            key = (r["area"].lower(), r["rule"].lower())
            if key in seen:
                continue
            seen.add(key)
            out.append(dict(r, layer=layer, file=str(path)))
    return out


def repo_root(start: Optional[Path] = None) -> Path:
    """The git root above start, or start itself when there is none."""
    here = Path(start or Path.cwd()).resolve()
    for p in (here, *here.parents):
        if (p / ".git").exists():
            return p
    return here


def repo_configs(repo: Optional[Path] = None) -> list:
    """Linter and style configs at the root of the repo, in a fixed order."""
    root = repo_root(repo)
    return [{"file": name, "tool": tool} for name, tool in CONFIG_FILES if (root / name).is_file()]


def norm(value) -> str:
    return re.sub(r"[\s_]+", "-", str(value or "").strip().lower())


def read_findings(path: str, lens_names: list[str],
                  known: list[str] | None = None) -> tuple[list[dict], dict, list[str]]:
    """Returns findings, coverage records by lens, and every problem with the input.

    lens_names are the lenses being graded. A line for a lens in `known` but not in lens_names
    is skipped, so one findings file can be graded a few lenses at a time with --only."""
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8-sig")
    findings, coverage, problems = [], {}, []
    known = list(known if known is not None else lens_names)
    for n, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as e:
            problems.append(f"line {n}: not JSON ({e.msg})")
            continue
        if not isinstance(item, dict):
            problems.append(f"line {n}: expected an object")
            continue
        lens = norm(item.get("lens"))
        if lens not in lens_names:
            if lens in known:
                continue  # another lens, graded in another run
            problems.append(f"line {n}: unknown lens '{item.get('lens')}'. Lenses: {', '.join(known)}")
            continue
        if "checked" in item and "finding" not in item:
            if not isinstance(item["checked"], bool):
                problems.append(f"line {n}: checked must be true or false as a JSON boolean, "
                                f"not {json.dumps(item['checked'])}")
                continue
            coverage[lens] = {"checked": item["checked"], "reason": str(item.get("reason", "")).strip()}
            continue
        f = {"line": n, "lens": lens, "severity": norm(item.get("severity")), "verdict": norm(item.get("verdict")),
             "where": str(item.get("where", "")).strip(), "finding": str(item.get("finding", "")).strip(),
             "evidence": str(item.get("evidence", "")).strip(), "to_confirm": str(item.get("to_confirm", "")).strip(),
             "fix": str(item.get("fix", "")).strip(), "outside_change": bool(item.get("outside_change")),
             # What the lens actually read. A sub agent does its own reading, and until this
             # field existed every source it read was lost the moment the agent finished.
             "sources": []}
        missing = []
        bad = read_sources(item.get("sources"), f["sources"])
        if bad:
            missing.append(bad)
        if f["severity"] not in SEVERITIES:
            missing.append(f"severity ({' / '.join(SEVERITIES)})")
        if f["verdict"] not in VERDICTS:
            missing.append(f"verdict ({' / '.join(VERDICTS)})")
        if not f["finding"]:
            missing.append("finding")
        if f["verdict"] == "confirmed" and not (f["where"] and f["evidence"]):
            missing.append("where and evidence, because confirmed means someone saw it in the code")
        if f["verdict"] == "plausible" and not f["to_confirm"]:
            missing.append("to_confirm, saying what would prove it")
        if f["verdict"] != "rejected" and not f["fix"]:
            missing.append("fix")
        if missing:
            problems.append(f"line {n}: missing or wrong: {'; '.join(missing)}")
            continue
        findings.append(f)
    return findings, coverage, problems


def grade(lenses: list[dict], findings: list[dict], coverage: dict) -> dict:
    rows = []
    for lens in lenses:
        name = lens["lens"]
        seen = [f for f in findings if f["lens"] == name]
        mine = [f for f in seen if not f["outside_change"]]
        live = [f for f in mine if f["verdict"] != "rejected"]
        record = coverage.get(name)
        counts = {v: sum(1 for f in mine if f["verdict"] == v) for v in VERDICTS}
        if (record and not record["checked"]) or (record is None and not seen):
            reason = record["reason"] if record and record["reason"] else "no record that this lens was checked"
            rows.append({"lens": name, "name": lens.get("name", name), "grade": "not checked", "reason": reason, **counts})
            continue
        if any(f["severity"] == "blocking" and f["verdict"] == "confirmed" for f in live):
            g = "fail"
        elif any((f["severity"] == "should-fix" and f["verdict"] == "confirmed")
                 or (f["severity"] == "blocking" and f["verdict"] == "plausible") for f in live):
            g = "concerns"
        else:
            g = "pass"
        rows.append({"lens": name, "name": lens.get("name", name), "grade": g, "reason": "", **counts})
    graded = [r["grade"] for r in rows if r["grade"] in GRADE_ORDER]
    overall = max(graded, key=GRADE_ORDER.index) if graded else "not checked"
    return {"overall": overall, "not_checked": [r["lens"] for r in rows if r["grade"] == "not checked"], "lenses": rows}


def where_key(where: str):
    m = re.match(r"(.*?)(?::(\d+))?$", where)
    return (m.group(1), int(m.group(2) or 0)) if m else (where, 0)


def ordered(findings: list[dict], lens_names: list[str]) -> list[dict]:
    return sorted(findings, key=lambda f: (SEVERITIES.index(f["severity"]), lens_names.index(f["lens"]),
                                           where_key(f["where"]), f["finding"]))


def read_sources(raw, into: list) -> str:
    """Fill `into` with the sources a finding lists, sorted so the same findings always give
    the same report. Returns what is wrong with them, or ""."""
    if raw is None:
        return ""
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return "sources (a list of ids)"
    for item in raw:
        text = item.strip() if isinstance(item, str) else ""
        if not text or "]" in text or "\n" in text or not (is_citable_source(text) or REPO_PATH.match(text)):
            return (f"sources ({json.dumps(item)} is not an id anyone can look up: use a URL, "
                    f"a ticket key, a repo path or the ref evidence.py add printed)")
        if text not in into:
            into.append(text)
    into.sort()
    return ""


def render_finding(f: dict, names: dict) -> str:
    parts = [f"- **{f['finding']}** Lens: {names[f['lens']]}. Severity: {SEVERITY_TITLES[f['severity']].lower()}."]
    if f["where"]:
        parts.append(f"Where: `{f['where']}`.")
    if f["verdict"] == "confirmed":
        parts.append(f"Verified: confirmed. {f['evidence']}")
    else:
        parts.append(f"Verified: plausible, not proven. To confirm: {f['to_confirm']}")
    parts.append(f"Fix: {f['fix']}")
    # Labelled, so the report is something check_output.py --citations can actually read and
    # kb.py rests-on can find when one of those pages changes.
    for src in f.get("sources") or []:
        parts.append(f"[verified: {src}]")
    return " ".join(p.rstrip() for p in parts)


def render(result: dict, findings: list[dict], lenses: list[dict], most_likely: str,
           reviewed: str = "", ticket: str = "", tested: str = "") -> str:
    """The report, in the shape of assets/templates/code-review.md, every section present."""
    names = {l["lens"]: l.get("name", l["lens"]) for l in lenses}
    order = [l["lens"] for l in lenses]
    live = ordered([f for f in findings if f["verdict"] != "rejected"], order)
    reviewed, ticket, tested = (v.strip() or PLACEHOLDER for v in (reviewed, ticket, tested))
    out = [f"# Code review: {reviewed}", "", "## Verdict", "", "| Field | Value |", "|---|---|",
           f"| Overall | {result['overall']} |", f"| Reviewed | {reviewed} |", f"| Ticket | {ticket} |",
           f"| Tested and analysed before review | {tested} |",
           f"| Not checked | {', '.join(names[n] for n in result['not_checked']) or 'none'} |"]
    out += ["", "## Most likely to fail", "",
            most_likely or f"{PLACEHOLDER} <!-- One sentence: the thing to fix if nothing else gets fixed. -->", "",
            "## Grades", "", "| Lens | Grade | Confirmed | Plausible | Rejected |", "|---|---|---|---|---|"]
    for r in result["lenses"]:
        out.append(f"| {r['name']} | {r['grade']} | {r['confirmed']} | {r['plausible']} | {r['rejected']} |")
    out += ["", "## Findings", "", "Each finding names its lens, severity, where it is, how it was verified, and the fix.", ""]
    for sev in SEVERITIES:
        out += [f"### {SEVERITY_TITLES[sev]}", ""]
        items = [render_finding(f, names) for f in live if f["severity"] == sev and not f["outside_change"]]
        out += (items or ["None."]) + [""]
    outside = [render_finding(f, names) for f in live if f["outside_change"]]
    out += ["## Outside this change", "",
            "Problems in code this change did not touch. Not graded. Each one is worth its own ticket.", ""]
    out += (outside or ["None."]) + [""]
    out += ["## What this review did not cover", ""]
    gaps = [f"- {r['name']}: {r['reason']}" for r in result["lenses"] if r["grade"] == "not checked"]
    out += gaps or ["Every lens was checked. A review can still miss things, so say what you did not read."]
    out += ["", "## PR comment", "", PR_COMMENT_NOTE]
    return "\n".join(out).rstrip() + "\n"


def render_rules(rules: list, configs: list) -> list:
    """The house rules and the repo's own configs, as lines for a brief."""
    out = []
    if rules:
        out += ["", "House rules (from house-rules.md, every layer; a rule in any layer applies):"]
        area = None
        for r in rules:
            if r["area"] != area:
                area = r["area"]
                out.append(f"  {area}:")
            out.append(f"  - {r['rule']} [{r['layer']}]")
    else:
        out += ["", "House rules: none saved. Judge against the public standard named above, and say so."]
    if configs:
        out += ["", "This repo's own configs. Apply their rules, and skip what the tool already enforces:"]
        out += [f"  - {c['file']} ({c['tool']})" for c in configs]
    return out


def brief(lens: dict | None, lenses: list[dict], rules: Optional[list] = None,
          configs: Optional[list] = None) -> str:
    shape = ('{"lens": "<lens>", "severity": "blocking|should-fix|minor", "verdict": "plausible", '
             '"where": "path:line", "finding": "...", "to_confirm": "...", "fix": "...", '
             '"sources": ["<a URL, a repo path, a ticket key, or the ref evidence.py add printed>"]}')
    if lens is None:
        return "\n".join([
            "You are checking review findings. You did not write them.",
            "",
            "For each finding, open the place it names and read the code around it. Then set its verdict:",
            "- confirmed: you saw it in the code. Add `where` and `evidence`, quoting the lines that show it.",
            "- plausible: likely, but not proven from the code alone. Keep `to_confirm`, saying what would prove it.",
            "- rejected: the code does not do what the finding says. Keep one line of `evidence` saying why.",
            "",
            "Change a severity only when the evidence shows it is wrong, and say so in `evidence`.",
            "Do not add new findings. Do not fix anything.",
            "Return the same JSON lines, one per finding, with the verdict set. Keep every coverage line as it is.",
            "Add to `sources` whatever you read to reach the verdict: a URL, a repo path, or the ref",
            "that `evidence.py add` printed. A confirmed finding with no source cannot be re-checked later.",
        ]) + "\n"
    return "\n".join([
        f"You are reviewing one lens only: {lens.get('name', lens['lens'])}.",
        "",
        f"The question: {lens.get('question', '')}",
        f"Look for: {lens.get('look_for', '')}",
        f"Judge it against: {lens.get('standard', '')}",
        *render_rules(rules or [], configs or []),
        "",
        "Rules:",
        "- Stay in this lens. Other reviewers cover the rest.",
        "- Review the change, not the whole codebase. For a problem in code the change did not touch, add"
        ' "outside_change": true.',
        "- Every finding needs a concrete fix. Do not make the change yourself.",
        "- Mark every finding plausible. Someone else confirms it against the code.",
        "- Blocking means it must not merge. Should-fix means fix it before long. Minor is a nit.",
        "",
        "- A finding that breaks a house rule quotes the rule in `evidence` and names its layer.",
        "",
        "Anything you read goes in `sources` as an id someone else can open: a URL, a repo path",
        "with its line, or a ticket key. Anything you quote, stage",
        "first with `python3 scripts/evidence.py add --root <the knowledge base> --source <id>`,",
        "and put the ref it prints in `sources`. Work you did that nobody can re-read is work",
        "nobody can check.",
        "Return JSON lines only, nothing else. First, one coverage line:",
        f'{{"lens": "{lens["lens"]}", "checked": true}}',
        f'or {{"lens": "{lens["lens"]}", "checked": false, "reason": "<why you could not check it>"}}',
        "Then one line per finding:",
        shape.replace("<lens>", lens["lens"]),
    ]) + "\n"


def main(argv=None) -> int:
    _utf8_console()
    p = argparse.ArgumentParser(prog="review.py", description="Grade a review the same way every time.")
    p.add_argument("--root", help="knowledge base folder, for a personal lens list (default: ~/.flareware/flarehand)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("lenses", help="list the lenses")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("brief", help="the brief for one reviewer, or for the verifier")
    s.add_argument("lens", nargs="?")
    s.add_argument("--verify", action="store_true")
    s.add_argument("--repo", help="the repo under review, for its linter configs (default: the current folder)")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("rules", help="the house rules from every layer, which every review checks against")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("configs", help="the linter and style configs at the root of the repo under review")
    s.add_argument("--repo", help="the repo under review (default: the current folder)")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("grade", help="grade a findings file and print the report")
    s.add_argument("findings", help="JSON lines file, or - for standard input")
    s.add_argument("--only", help="grade only these lenses, comma separated")
    s.add_argument("--most-likely", default="", help="the one sentence for 'Most likely to fail'")
    s.add_argument("--reviewed", default="", help="what was reviewed, against which base")
    s.add_argument("--ticket", default="", help="the ticket key or link, and the requirement it was checked against")
    s.add_argument("--jira", dest="ticket", help=argparse.SUPPRESS)  # the old name, kept working
    s.add_argument("--tested", default="", help="yes, no or unknown: tested and analysed before review")
    s.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    root = resolve_root(args.root)
    lenses = load_lenses(root if (root / "config.json").is_file() else None)

    if args.cmd == "rules":
        rules = house_rules(root)
        if args.json:
            print(json.dumps({"rules": rules, "files": [{"layer": l, "file": str(p)}
                                                         for l, p in house_rule_files(root)]}, indent=2))
        elif not rules:
            print("No house rules saved. Add one with: kb.py rule add, or write house-rules.md in a playbook.")
        else:
            area = None
            for r in rules:
                if r["area"] != area:
                    area = r["area"]
                    print(f"\n## {area}")
                print(f"- {r['rule']}  [{r['layer']}]")
        return 0

    if args.cmd == "configs":
        configs = repo_configs(Path(args.repo) if args.repo else None)
        if args.json:
            print(json.dumps(configs, indent=2))
        elif not configs:
            print("No linter or style config found at the repo root. Use the language's public style guide.")
        else:
            for c in configs:
                print(f"{c['file']:<26}{c['tool']}")
        return 0
    if not lenses:
        print("error: no lens list found in assets/review-lenses.tsv", file=sys.stderr)
        return 2

    if args.cmd == "lenses":
        if args.json:
            print(json.dumps(lenses, indent=2))
        else:
            print(f"Lenses from {lenses[0]['file']}\n")
            for l in lenses:
                print(f"{l['lens']:<14}{l.get('question', '')}")
        return 0

    if args.cmd == "brief":
        if args.verify:
            text = brief(None, lenses)
            print(json.dumps({"lens": None, "brief": text}, indent=2) if args.json else text, end="\n" if args.json else "")
            return 0
        match = next((l for l in lenses if norm(args.lens) in (l["lens"], norm(l.get("name")))), None)
        if not match:
            print(f"error: name a lens, or pass --verify. Lenses: {', '.join(l['lens'] for l in lenses)}",
                  file=sys.stderr)
            return 2
        rules = house_rules(root)
        configs = repo_configs(Path(args.repo) if args.repo else None)
        text = brief(match, lenses, rules, configs)
        if args.json:
            print(json.dumps({"lens": match["lens"], "brief": text, "house_rules": rules, "configs": configs},
                             indent=2))
        else:
            print(text, end="")
        return 0

    known = [l["lens"] for l in lenses]
    if args.only:
        wanted = [norm(x) for x in args.only.split(",") if x.strip()]
        unknown = [w for w in wanted if w not in set(known)]
        if unknown:
            print(f"error: unknown lens: {', '.join(unknown)}", file=sys.stderr)
            return 2
        lenses = [l for l in lenses if l["lens"] in wanted]
    names = [l["lens"] for l in lenses]
    try:
        findings, coverage, problems = read_findings(args.findings, names, known)
    except OSError as e:
        print(f"error: cannot read {args.findings}: {e}", file=sys.stderr)
        return 2
    if problems:
        print("The findings file has problems, so nothing was graded:", file=sys.stderr)
        for line in problems[:40]:
            print(f"  {line}", file=sys.stderr)
        return 2
    result = grade(lenses, findings, coverage)
    if args.json:
        shown = [{k: v for k, v in f.items() if k != "line"} for f in ordered(findings, names)]
        print(json.dumps({**result, "findings": shown}, indent=2))
    else:
        print(render(result, findings, lenses, args.most_likely.strip(),
                     args.reviewed, args.ticket or "", args.tested), end="")
    return 1 if result["overall"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
