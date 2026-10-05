#!/usr/bin/env python3
"""check_output.py - validate a file against the flarehand writing rules and
output contracts.

Three independent checks, each switched on by a flag. With no flag, --style runs.

  --style               plain-language rules: em dashes, long sentences, banned
                        words, passive voice, filler openers, long paragraphs,
                        numeric dates, optional plurals and double negatives
  --profile plain       the house voice, the default. `natural` is the older name
  --profile none        house style off. The rules that protect facts still run:
                        dates that read two ways, optional plurals, double negatives
  --profile google      with --style, the stricter document rules on top: tense,
                        directional words, heading case, dashes and quotes
  --contract <id>       required sections and markers for a workflow archetype,
                        read from assets/contracts.tsv. A section counts only as a
                        markdown heading of any level, numbered or not. Markers
                        may appear anywhere.
  --template <file>     the same check against a template's own "## " headings.
                        A heading followed by <!-- optional --> is not required.
                        Nor is an author-only section: one listed in frontmatter
                        author_only: [...], one followed by <!-- author-only -->,
                        or any after a <!-- reviewer-notes --> line.
                        A general-practice template accepts [your input] where
                        the workflow asks for [verified:.
  --citations           every [verified: ...] marker names a source in a known
                        shape: a URL, a ledger id (S3), a repository path with an
                        optional line range, git:<rev>:<path>, mcp:<server>:<id>,
                        a ticket key (ABC-123) or a snapshot. A ledger id must be
                        in this session's source ledger, and a cited file or
                        snapshot must exist. ground.py lint goes further.

Exit codes
  0  no errors (warnings may still be printed)
  1  at least one error
  2  bad usage, missing file, or unreadable data file

Output is plain text by default and bounded. Use --json for machine output.
Diagnostics go to stderr so stdout stays parseable.

Examples
  python3 scripts/check_output.py --style SKILL.md
  python3 scripts/check_output.py --style --strict references/*.md
  python3 scripts/check_output.py --contract wf-03 --citations packet.md
  python3 scripts/check_output.py --style --profile google runbook.md
  echo "$REPLY" | python3 scripts/check_output.py --style -
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _text import (GIT_REF, LEDGER_ID, REPO_PATH, SNAPSHOT, SNAPSHOT_HASH, SOURCE_SHAPES, VERIFIED,  # noqa: E402
                   is_self_source, strip_line_span)
DEFAULT_MAX = 60

# --------------------------------------------------------------------------
# masking: hide anything that is not prose so we never lint code or YAML
# --------------------------------------------------------------------------

FENCE = re.compile(r"^(\s*)(```|~~~)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
LINK_TARGET = re.compile(r"\]\([^)\s]+\)")
URL = re.compile(r"https?://\S+")
HTML_TAG = re.compile(r"<[^>\n]+>")


def mask(text: str, keep_links: bool = False) -> list[str]:
    """Return lines with non-prose spans replaced by spaces.

    Columns are preserved, so every reported position still points at the real
    character in the original file. With keep_links, URLs and link targets stay
    visible, which the citation check needs.
    """
    text = text.lstrip("\ufeff").replace("\r\n", "\n")
    lines = text.split("\n")
    out: list[str] = []
    in_fence = False
    fence_mark = ""
    in_frontmatter = False
    in_comment = False
    prev_blank = True
    prev_code = False

    for i, line in enumerate(lines):
        # an HTML comment spread over several lines is not prose
        if in_comment:
            end = line.find("-->")
            if end < 0:
                out.append(" " * len(line))
                continue
            line = " " * (end + 3) + line[end + 3:]
            in_comment = False
        start = line.find("<!--")
        if start >= 0 and line.find("-->", start) < 0:
            out.append(line[:start] + " " * (len(line) - start))
            in_comment = True
            continue
        # YAML frontmatter, only when it opens on line 1
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            out.append(" " * len(line))
            continue
        if in_frontmatter:
            out.append(" " * len(line))
            if line.strip() in ("---", "..."):
                in_frontmatter = False
            continue

        m = FENCE.match(line)
        if m:
            if not in_fence:
                in_fence, fence_mark = True, m.group(2)
            elif line.strip().startswith(fence_mark):
                in_fence, fence_mark = False, ""
            out.append(" " * len(line))
            continue
        if in_fence:
            out.append(" " * len(line))
            continue

        # Indented code needs a blank line (or more code) above it, as in real Markdown.
        # Otherwise an indented continuation line inside a paragraph would escape every check.
        indented = bool(re.match(r"^(\s{4,}|\t)\S", line)) and not re.match(r"^\s*([-*+]|\d+[.)])\s", line)
        if indented and (prev_blank or prev_code):
            out.append(" " * len(line))
            prev_code, prev_blank = True, False
            continue
        prev_code = False
        prev_blank = not line.strip()

        masked = line
        pats = (INLINE_CODE, HTML_TAG) if keep_links else (INLINE_CODE, LINK_TARGET, URL, HTML_TAG)
        for pat in pats:
            masked = pat.sub(lambda mo: " " * len(mo.group(0)), masked)
        out.append(masked)
    return out


def is_table_row(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and s.count("|") >= 2


def is_heading(line: str) -> bool:
    return bool(re.match(r"^\s{0,3}#{1,6}\s", line))


# --------------------------------------------------------------------------
# style rules
# --------------------------------------------------------------------------

EM_DASH = "—"
EN_DASH = "–"
MAX_WORDS = 25

PASSIVE = re.compile(
    r"\b(?:is|are|was|were|be|been|being)\s+"
    r"(?:\w+ed|done|made|given|taken|seen|known|shown|written|held|kept|built|"
    r"sent|found|left|put|set|run|told|brought|caught|chosen|driven)\b",
    re.IGNORECASE,
)

WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’\-]*")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])[\)\"'”*_\]`]*\s+")
ABBREV = {"e.g.", "i.e.", "etc.", "vs.", "no.", "fig.", "approx.", "dr.", "mr.", "ms."}


def load_style_words(path: Path) -> list[tuple[re.Pattern, str, str, str]]:
    """Read a word list: term, replacement, severity, and an optional fourth column.

    A fourth column of `case` makes the match case-sensitive, so a list can enforce how a
    name is written (GitHub, JavaScript) without flagging the correct form.

    The edges are "not a word character" rather than `\\b`. With `\\b`, a term that starts
    or ends with punctuation, such as `e.g.` or `etc.`, could never match.
    """
    if not path.is_file():
        raise FileNotFoundError(f"style word list not found: {path}")
    rules = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.startswith("term\t") or raw.startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) < 3:
            continue
        term, repl, sev = parts[0].strip(), parts[1].strip(), parts[2].strip()
        flags = 0 if len(parts) > 3 and "case" in parts[3] else re.IGNORECASE
        # spaces in a phrase may be any whitespace
        body = r"\s+".join(re.escape(w) for w in term.split())
        rules.append((re.compile(rf"(?<!\w){body}(?!\w)", flags), term, repl, sev))
    return rules


# Rule 7. Openers and sign-offs that carry no content. Checked at the start of every
# paragraph, which is where a model reaches for them.
FILLER = re.compile(
    r"^\W*(?:great question|good question|excellent question|certainly[!,.]|absolutely[!,.]|of course[!,.]|"
    r"sure thing|happy to help|i'?d be (?:happy|glad) to|i would be (?:happy|glad) to|"
    r"i hope this (?:helps|finds you well)|hope this helps|let me know if you have any (?:other )?questions|"
    r"as an ai\b|in today'?s fast[- ]paced)",
    re.IGNORECASE,
)
# Rule 8, and Google's paragraph advice: more than this reads as a wall.
PARA_MAX_SENTENCES = 6
PARA_MAX_WORDS = 130
# CORE additions from the Google review. Each fixes a misreading, not a matter of taste.
SLASH_DATE = re.compile(r"(?<![\w/.])\d{1,2}/\d{1,2}/\d{2,4}(?![\w/])")
OPTIONAL_PLURAL = re.compile(r"\b[A-Za-z]+\((?:s|es|ren)\)", re.IGNORECASE)
DOUBLE_NEGATIVE = re.compile(r"\bnot\s+(?:un\w{3,}|in(?:significant|frequent|correct|valid)|impossible|without)\b"
                             r"|\bcannot\s+not\b|\bnever\s+not\b", re.IGNORECASE)

# ---- the google profile: stricter rules for documents, off unless asked for
FUTURE_BEHAVIOUR = re.compile(
    r"\bwill\s+(?:now\s+)?(?:be\s+)?(?:display|show|appear|return|open|close|run|create|send|list|save|load|start|stop|"
    r"update|change|prompt|ask|generate|contain|include|post|print|redirect|refresh)\w*\b", re.IGNORECASE)
DIRECTIONAL = re.compile(
    r"\b(?:see|shown|listed|described|mentioned|as)\s+(?:above|below)\b|\bthe\s+(?:above|below)\b|"
    r"\b(?:left|right)-hand\b|\b(?:top|bottom|upper|lower)[- ](?:left|right)\b", re.IGNORECASE)
SPACED_HYPHEN = re.compile(r"(?<=\w) - (?=\w)")
CURLY = re.compile(r"[“”‘’]")
SMALL_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into", "of", "on", "or", "the",
               "to", "vs", "via", "with"}


def title_case(heading: str, lowercase_words: set | None = None) -> bool:
    """True when a heading capitalises words the way a book title does.

    Product names are capitalised too (GitHub, Claude Code), so a capital alone proves nothing.
    A capitalised word counts against the heading when the same word appears in lower case in
    the document's prose, which a name never does. With no such evidence, the heading must
    capitalise every word that is not small, and have at least three of them.
    """
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'’\-]*", heading)][1:]
    words = [w for w in words if w.lower() not in SMALL_WORDS and not w.isupper() and not re.search(r"[a-z][A-Z]", w)]
    capitalised = [w for w in words if w[0].isupper()]
    if lowercase_words and any(w.lower() in lowercase_words for w in capitalised):
        return True
    return len(words) >= 3 and len(capitalised) == len(words)


def split_sentences(text: str) -> list[tuple[int, str]]:
    """Split into sentences, returning (offset_in_text, sentence).

    Abbreviations such as e.g. and i.e. are not sentence ends. Without this a long
    sentence could hide behind one and pass the length check. The swap keeps the
    same character count, so offsets still line up with the original text.
    """
    for abbr in sorted(ABBREV, key=len, reverse=True):
        # only a whole word: "ms." inside "teams." is a sentence end, not an abbreviation
        text = re.sub(r"(?<![A-Za-z])" + re.escape(abbr), lambda m: m.group(0).replace(".", "\u2024"),
                      text, flags=re.IGNORECASE)
    out, start = [], 0
    for part in SENTENCE_SPLIT.split(text):
        if part.strip():
            idx = text.find(part, start)
            if idx < 0:
                idx = start
            out.append((idx, part))
            start = idx + len(part)
    return out


# Rules that protect what a sentence means, so they hold under every profile, `none` included.
FACT_RULES = {"date", "optional-plural", "double-negative"}


def check_style(lines: list[str], raw_lines: list[str], rules, profile: str = "plain") -> list[dict]:
    """The house rules for every profile. `google` adds the document rules on top and never removes one.
    `none` keeps only the rules that protect facts."""
    if profile == "none":
        return [f for f in check_style(lines, raw_lines, [], "plain") if f["rule"] in FACT_RULES]
    findings: list[dict] = []
    google = profile == "google"
    # words the document writes in lower case, so a heading can be judged against its own prose
    lowercase_words = {w for ln in lines if not is_heading(ln) for w in re.findall(r"\b[a-z][a-z'\-]+\b", ln)}

    def add(sev, line_no, col, rule, message, evidence=""):
        findings.append(
            {
                "severity": sev,
                "line": line_no,
                "col": col,
                "rule": rule,
                "message": message,
                "evidence": evidence[:120],
            }
        )

    # paragraph accumulation for sentence length, so a wrapped sentence counts once
    para: list[tuple[int, str]] = []

    def flush_paragraph():
        if not para:
            return
        # Build a map from character offset back to source line, so a finding
        # points at the sentence and not at the top of the paragraph.
        joined_parts, offsets, cursor = [], [], 0
        for line_no, text in para:
            offsets.append((cursor, line_no))
            joined_parts.append(text)
            cursor += len(text) + 1
        joined = " ".join(joined_parts)

        def line_at(pos: int) -> int:
            found = para[0][0]
            for start, line_no in offsets:
                if start <= pos:
                    found = line_no
                else:
                    break
            return found

        sentences = split_sentences(joined)
        # Rule 7: the first words of a paragraph carry content, not a warm-up.
        if FILLER.search(joined):
            add("error", para[0][0], 1, "filler", "filler opener. Start with the answer.", joined.strip())
        # Rule 8: a wall of text. A list item is its own unit, so this is a real paragraph.
        n_words = len(WORD.findall(joined))
        if len(sentences) > PARA_MAX_SENTENCES or n_words > PARA_MAX_WORDS:
            add("warn", para[0][0], 1, "long-paragraph",
                f"paragraph runs {len(sentences)} sentences and {n_words} words. Break it up with a list or a heading.",
                joined.strip())
        for pos, sentence in sentences:
            words = WORD.findall(sentence)
            if len(words) > MAX_WORDS:
                add(
                    "error",
                    line_at(pos),
                    1,
                    "long-sentence",
                    f"sentence runs {len(words)} words, the limit is {MAX_WORDS}. Split it.",
                    sentence.strip(),
                )
        para.clear()

    for n, line in enumerate(lines, start=1):
        raw = raw_lines[n - 1]
        stripped = line.strip()

        # dashes
        for col, ch in enumerate(line, start=1):
            if ch == EM_DASH:
                add("error", n, col, "em-dash", "em dash found. Use a period, comma, colon or brackets.", raw.strip())
                break
        m = re.search(rf"\s{EN_DASH}\s", line)
        if m:
            add("error", n, m.start() + 1, "en-dash", "spaced en dash reads as an em dash. Rewrite it.", raw.strip())
        m = re.search(r"\s--\s", line)
        if m:
            add("warn", n, m.start() + 1, "double-hyphen", "double hyphen used as a dash. Rewrite it.", raw.strip())

        # banned terms, checked everywhere including headings and tables
        for pat, term, repl, sev in rules:
            for m in pat.finditer(line):
                add(sev, n, m.start() + 1, "word", f'"{term}" -> {repl}', raw.strip())
                break  # one hit per term per line keeps output bounded

        # dates, plurals and negatives that readers get wrong
        m = SLASH_DATE.search(line)
        if m:
            add("error", n, m.start() + 1, "date", f'"{m.group(0)}" reads as two different dates in Canada and the US. '
                "Write the month as a word, or use YYYY-MM-DD.", raw.strip())
        m = OPTIONAL_PLURAL.search(line)
        if m:
            add("warn", n, m.start() + 1, "optional-plural", f'"{m.group(0)}": pick one, or write "one or more".',
                raw.strip())
        m = DOUBLE_NEGATIVE.search(line)
        if m:
            add("warn", n, m.start() + 1, "double-negative", f'"{m.group(0)}": say what is true instead.', raw.strip())

        if google:
            for pat, rule, msg in (
                    (FUTURE_BEHAVIOUR, "future-tense", "describe what the product does now, in the present tense"),
                    (DIRECTIONAL, "directional", "name the section or the label instead of above, below, left or right"),
                    (SPACED_HYPHEN, "spaced-hyphen", "a spaced hyphen reads as a dash. Use a colon or a period"),
                    (CURLY, "curly-quote", "use straight quotes, so pasted text and commands still work")):
                m = pat.search(line)
                if m:
                    add("warn", n, m.start() + 1, rule, f'"{m.group(0)}": {msg}.', raw.strip())
            if is_heading(line):
                text = re.sub(r"^\s{0,3}#{1,6}\s+", "", line).strip()
                if title_case(text, lowercase_words):
                    add("warn", n, 1, "heading-case", "use sentence case: capitalise only the first word and names.",
                        raw.strip())
                if text.endswith("."):
                    add("warn", n, len(line.rstrip()), "heading-period", "a heading takes no end period.", raw.strip())
            elif "!" in re.sub(r"!\[", "", line) and not is_table_row(line):
                add("warn", n, line.find("!") + 1, "exclamation", "no exclamation marks in a document.", raw.strip())

        # passive voice
        for m in PASSIVE.finditer(line):
            add("warn", n, m.start() + 1, "passive", f'passive voice: "{m.group(0)}". Say who does it.', raw.strip())
            break

        # sentence length, prose lines only. A table cell is checked as its own unit.
        if is_table_row(line):
            flush_paragraph()
            if not re.match(r"^\s*\|?[\s:|\-]+\|?\s*$", line):
                for cell in [c for c in line.strip().strip("|").split("|") if c.strip()]:
                    for _, sentence in split_sentences(cell):
                        words = WORD.findall(sentence)
                        if len(words) > MAX_WORDS:
                            add("error", n, 1, "long-sentence",
                                f"table cell sentence runs {len(words)} words, the limit is {MAX_WORDS}. Split it.",
                                sentence.strip())
            continue
        if not stripped or is_heading(line):
            flush_paragraph()
            continue
        # A list item is its own unit. Without this, a bullet list with no full
        # stops joins into one giant "sentence" and every list looks too long.
        is_item = bool(re.match(r"^\s*([-*+]|\d+[.)])\s+", line))
        if is_item:
            flush_paragraph()
        body = re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", line)
        body = re.sub(r"^\s*>\s?", "", body)
        para.append((n, body))

    flush_paragraph()
    return findings


# --------------------------------------------------------------------------
# citation rule
# --------------------------------------------------------------------------

# `[verified: <source>]` or `[verified: evidence/<hash>.txt]` is the instruction in a
# template or a reference, not a claim. No real id holds an angle bracket.
PLACEHOLDER = re.compile(r"<[^>]*>")


# Other labels that name ledger ids. Each id must be a row in the session's source ledger.
LEDGER_LABEL = re.compile(r"\[(?:weak|stale|conflict):\s*([^\]]+)\]|\[inference from\s+([^\]]+)\]", re.IGNORECASE)
LEDGER_IDS = re.compile(r"\bS\d{1,4}\b")
ACCEPTED = ("a URL, a ledger id such as S3, a repository path such as src/x.py#L3-L8, git:<rev>:<path>, "
            "mcp:<server>:<id>, a ticket key such as ABC-123, or evidence/<hash>.txt")


def ledger_ids(root: Path | None, ledger: Path | None = None) -> set | None:
    """The S# ids in the source ledger, or None when there is no ledger to read."""
    path = None
    if ledger is not None:
        path = ledger / "sources.jsonl" if ledger.is_dir() else ledger
    elif root is not None:
        try:
            sys.path.insert(0, str(SKILL_DIR / "scripts"))
            from evidence import staging_dir  # noqa: E402
            path = staging_dir(root) / "sources.jsonl"
        except Exception:
            path = None
    if path is None or not path.is_file():
        return None
    ids = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("id"):
            ids.add(str(row["id"]))
    return ids


def git_ref_exists(ref: str, repo_root: Path | None) -> bool | None:
    """True or False when a repository is at hand to ask, None when there is none."""
    m = re.match(r"^git:([^\s:]+):(.+)$", ref)
    where = repo_root or Path.cwd()
    if not m or m.group(1).startswith("-"):
        return False
    try:
        import subprocess
        inside = subprocess.run(["git", "-C", str(where), "rev-parse", "--is-inside-work-tree"],
                                capture_output=True, text=True, timeout=5)
        if inside.returncode != 0:
            return None
        got = subprocess.run(["git", "-C", str(where), "cat-file", "-e", f"{m.group(1)}:{m.group(2).strip()}"],
                             capture_output=True, text=True, timeout=5)
        return got.returncode == 0
    except (OSError, ValueError):
        return None
    except Exception:
        return None


def repo_path_exists(ref: str, base: Path, repo_root: Path | None) -> bool:
    """A cited file, looked for next to the artifact, under --repo-root, and in the folder
    the check runs from. The line number is not checked: files move under you."""
    name = strip_line_span(ref)
    places = [base / name, Path.cwd() / name]
    if repo_root is not None:
        places.append(repo_root / name)
    return any(p.is_file() for p in places)


def snapshot_exists(ref: str, base: Path, root: Path | None) -> bool:
    """A snapshot may sit next to the artifact, in the knowledge base, or in session staging."""
    name = ref.split("/", 1)[-1] if ref.startswith("evidence/") else f"{ref}.txt"
    places = [base / ref, base / "evidence" / name]
    if root is not None:
        places.append(root / "evidence" / name)
        try:
            sys.path.insert(0, str(SKILL_DIR / "scripts"))
            from evidence import staging_dir  # noqa: E402
            places.append(staging_dir(root) / name)
        except Exception:
            pass
    return any(p.is_file() for p in places)


def check_citations(lines: list[str], base: Path, root: Path | None = None,
                    repo_root: Path | None = None, raw: list[str] | None = None,
                    ledger: Path | None = None) -> list[dict]:
    findings = []
    known_ids = ledger_ids(root, ledger)

    def add(sev, n, col, rule, message, line):
        findings.append({"severity": sev, "line": n, "col": col, "rule": rule, "message": message,
                         "evidence": line.strip()[:120]})

    def check_ids(ids: list[str], n: int, col: int, line: str):
        for sid in ids:
            if known_ids is None:
                add("error", n, col, "citation-ledger",
                    f"{sid} is a ledger id, and there is no source ledger for this session. Stage the source with "
                    f"ground.py fetch or ground.py source add, or pass --ledger.", line)
                return
            if sid not in known_ids:
                add("error", n, col, "citation-ledger", f"{sid} is not in the session's source ledger.", line)

    for n, line in enumerate(lines, start=1):
        original = raw[n - 1] if raw and n <= len(raw) else line
        for m in VERIFIED.finditer(line):
            src = m.group(1).strip()
            # Masking blanks `<source>` to spaces, so the placeholder is only visible in
            # the line as written. A template's footer is an instruction, not a claim.
            # Anchored at the same offset, because mask() keeps positions. No fallback to
            # "the first marker on the line": with two markers that would read the wrong
            # one, and skipping a real source is a false pass. If it does not match here,
            # check it.
            here = VERIFIED.match(original, m.start())
            if here and PLACEHOLDER.search(here.group(1)):
                continue
            if is_self_source(src):
                add("error", n, m.start() + 1, "citation-self",
                    "this cites the skill's own files. They are guidance, not evidence. Cite the source they "
                    "point to.", line)
                continue
            parts = [x.strip() for x in src.split("+")]
            if len(parts) > 1 and all(LEDGER_ID.match(x) for x in parts):
                check_ids(parts, n, m.start() + 1, line)
                continue
            if LEDGER_ID.match(src):
                check_ids([src], n, m.start() + 1, line)
                continue
            if not any(s.match(src) for s in SOURCE_SHAPES):
                add("error", n, m.start() + 1, "citation-shape",
                    f'source "{src}" is not a recognised id. Use {ACCEPTED}.', line)
                continue
            if GIT_REF.match(src):
                exists = git_ref_exists(src, repo_root)
                if exists is False:
                    add("warn", n, m.start() + 1, "citation-unreadable",
                        f'"{src}" does not exist in the repository here. Check the revision and the path, or '
                        f"pass --repo-root.", line)
                continue
            if REPO_PATH.match(src) and not src.startswith("evidence/"):
                if not repo_path_exists(src, base, repo_root):
                    add("warn", n, m.start() + 1, "citation-unreadable",
                        f'"{src}" is not a file here. Check it from the repository, or pass --repo-root, or '
                        f"snapshot it with ground.py fetch.", line)
                continue
            if SNAPSHOT.match(src) or SNAPSHOT_HASH.match(src):
                if not snapshot_exists(src, base, root):
                    add("error", n, m.start() + 1, "citation-missing",
                        f"snapshot {src} is not in the knowledge base, session staging, or next to this file.", line)
        for m in LEDGER_LABEL.finditer(line):
            here = LEDGER_LABEL.match(original, m.start())
            body = (here.group(1) or here.group(2)) if here else (m.group(1) or m.group(2))
            if PLACEHOLDER.search(body or ""):
                continue
            check_ids(LEDGER_IDS.findall(m.group(1) or m.group(2) or ""), n, m.start() + 1, line)
    return findings


# --------------------------------------------------------------------------
# contract rule
# --------------------------------------------------------------------------

def load_contracts(path: Path) -> dict:
    if not path.is_file():
        return {}
    out = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.startswith("archetype\t"):
            continue
        parts = raw.split("\t")
        if len(parts) < 3:
            continue
        out[parts[0].strip()] = {
            "sections": [s.strip() for s in parts[1].split("|") if s.strip()],
            "markers": [s.strip() for s in parts[2].split("|") if s.strip()],
        }
    return out


def merge_contracts(shipped: dict, personal: dict) -> dict:
    """Shipped requirements are a floor. Personal rows add to them, never subtract."""
    out = dict(shipped)
    for archetype, spec in personal.items():
        base = shipped.get(archetype)
        if base is None:
            out[archetype] = spec
            continue
        out[archetype] = {
            "sections": base["sections"] + [s for s in spec["sections"] if s not in base["sections"]],
            "markers": base["markers"] + [m for m in spec["markers"] if m not in base["markers"]],
        }
    return out


HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
LEADING_NUMBER = re.compile(r"^\d+[.)]\s*")
OPTIONAL_MARK = re.compile(r"^<!--\s*optional\b")
# Sections only the author fills in, such as a draft's status or reviewer notes. The published
# artifact leaves them out, so the template check does not require them. Three ways to mark one:
# `author_only: [Heading, ...]` in the frontmatter, `<!-- author-only -->` on the line after the
# heading, or a `<!-- reviewer-notes -->` line, after which every section is author-only.
AUTHOR_MARK = re.compile(r"^<!--\s*author[- ]only\b", re.IGNORECASE)
REVIEWER_NOTES = re.compile(r"^\s*<!--\s*reviewer[- ]notes\b", re.IGNORECASE)


def author_only_headings(raw: str) -> set:
    """Lower-cased headings the frontmatter lists under author_only, inline or as a block list."""
    if not raw.lstrip("\ufeff").startswith("---"):
        return set()
    front = raw.lstrip("\ufeff").split("\n---", 1)[0]
    m = re.search(r"^author_only:\s*\[(.*?)\]\s*$", front, re.M)
    if m:
        items = m.group(1).split(",")
    else:
        m = re.search(r"^author_only:\s*\n((?:\s+-\s.*\n?)+)", front, re.M)
        items = re.findall(r"^\s+-\s+(.*)$", m.group(1), re.M) if m else []
    return {re.sub(r"[^a-z0-9]+", " ", i.strip().strip("'\"").lower()).strip() for i in items if i.strip()}
GENERAL_PRACTICE_MARKERS = {"[verified:": ["[your input]"]}


def heading_text(line: str) -> str | None:
    """The text of a markdown heading of any level, with a leading list number such as
    "6. " removed, or None when the line is not a heading."""
    m = HEADING.match(line)
    if not m:
        return None
    return LEADING_NUMBER.sub("", m.group(1)).strip()


def strip_frontmatter(text: str) -> str:
    text = text.lstrip("\ufeff")
    if text.startswith("---"):
        parts = text.split("\n---", 1)
        if len(parts) > 1:
            return parts[1]
    return text


def template_contract(template_path: Path, contracts: dict) -> tuple[str, dict]:
    """A template's own '## ' headings become the required sections, minus any leading
    number. A heading whose next non-blank line is '<!-- optional -->' is not required.
    The workflow's non-negotiable markers, and its MISSING list, stay required whatever
    the shape. For a general-practice template, '[your input]' stands in for '[verified:'."""
    raw = template_path.read_text(encoding="utf-8")
    body = strip_frontmatter(raw)
    wf = ""
    m = re.search(r"^workflow:\s*(wf-\d{2})", raw, re.M)
    if m:
        wf = m.group(1)
    status = ""
    m = re.search(r"^source_status:\s*(\S+)", raw, re.M)
    if m:
        status = m.group(1).strip()
    base = contracts.get(wf, {"sections": [], "markers": []})
    lines = body.splitlines()
    sections: list[str] = []
    author_only = author_only_headings(raw)
    in_notes = False
    for i, line in enumerate(lines):
        if REVIEWER_NOTES.match(line):
            in_notes = True
        if not line.startswith("## ") or in_notes:
            continue
        name = heading_text(line)
        if not name:
            continue
        following = next((l.strip() for l in lines[i + 1:] if l.strip()), "")
        if OPTIONAL_MARK.match(following) or AUTHOR_MARK.match(following):
            continue
        if re.sub(r"[^a-z0-9]+", " ", name.lower()).strip() in author_only:
            continue
        sections.append(name)
    # Whatever shape a team uses, the workflow's place for unsourced facts stays required.
    # It is named differently per workflow: "MISSING - you must supply", "What is missing", "Gaps you must fill".
    for must in base["sections"]:
        low = must.lower()
        if ("missing" in low or "gaps" in low) and must not in sections:
            sections.append(must)
    spec = {"sections": sections, "markers": base["markers"]}
    if status == "general-practice":
        spec["marker_alternatives"] = GENERAL_PRACTICE_MARKERS
    return wf, spec


def section_present(section: str, headings: list[str]) -> bool:
    """A required section is present when a heading of any level carries its name, or
    starts with its name followed by a non-word character, as "Evidence and findings"
    does for "Evidence". Prose that merely mentions the words does not count."""
    # Case and punctuation do not matter, so "Missing: you must supply" in sentence case satisfies
    # "MISSING - you must supply". The google profile needs that form.
    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    want = norm(section)
    for h in headings:
        got = norm(h)
        if got == want:
            return True
        if got.startswith(want) and not got[len(want)].isalnum():
            return True
    return False


def check_contract(text: str, archetype: str, contracts: dict) -> list[dict]:
    spec = contracts.get(archetype)
    if spec is None:
        return [
            {
                "severity": "error",
                "line": 0,
                "col": 0,
                "rule": "contract-unknown",
                "message": f'no contract defined for "{archetype}" in assets/contracts.tsv',
                "evidence": "",
            }
        ]
    text = strip_frontmatter(text)
    headings = [h for h in (heading_text(l) for l in text.split("\n")) if h]
    low = text.lower()
    findings = []
    for section in spec["sections"]:
        if not section_present(section, headings):
            findings.append(
                {
                    "severity": "error",
                    "line": 0,
                    "col": 0,
                    "rule": "contract-section",
                    "message": f'required section missing: "{section}" (a markdown heading)',
                    "evidence": "",
                }
            )
    alternatives = spec.get("marker_alternatives", {})
    for marker in spec["markers"]:
        accepted = [marker] + list(alternatives.get(marker, []))
        if not any(a.lower() in low for a in accepted):
            findings.append(
                {
                    "severity": "error",
                    "line": 0,
                    "col": 0,
                    "rule": "contract-marker",
                    "message": f'required element missing: "{marker}"'
                               + (f' (or {", ".join(accepted[1:])})' if len(accepted) > 1 else ""),
                    "evidence": "",
                }
            )
    return findings


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def run_file(path: Path, args, rules, contracts, text: str | None = None) -> list[dict]:
    if text is None:
        text = path.read_text(encoding="utf-8")
    raw_lines = text.split("\n")
    masked = mask(text)
    findings: list[dict] = []
    if args.style:
        findings += check_style(masked, raw_lines, rules, getattr(args, "profile", "plain"))
    if args.citations:
        findings += check_citations(mask(text, keep_links=True), path.parent, args.kb_root,
                                    getattr(args, "repo_root", None), raw_lines, getattr(args, "ledger", None))
    # Masked, like every other check. A heading inside an example block is not a section,
    # and a marker inside an instructional comment is not a claim.
    if args.template or args.contract:
        body = "\n".join(mask(text))
        # Both, when both are given. One silently winning is a trap: the workflow contract
        # is the floor and a personal template is the shape, and they answer different questions.
        if args.template:
            wf, spec = template_contract(Path(args.template), contracts)
            findings += check_contract(body, "__template__", {"__template__": spec})
        if args.contract:
            findings += check_contract(body, args.contract, contracts)
    for f in findings:
        f["file"] = str(path)
    return findings


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
    p = argparse.ArgumentParser(
        prog="check_output.py",
        description="Check a file against the flarehand writing rules and output contracts.",
    )
    p.add_argument("files", nargs="+", help="markdown or text files to check, or - to read a reply from standard input")
    p.add_argument("--style", action="store_true", help="run the plain-language checks")
    p.add_argument("--citations", action="store_true", help="check [verified: ...] markers")
    p.add_argument("--contract", metavar="ID", help="check required sections for an archetype, such as wf-03")
    p.add_argument("--template", metavar="FILE", help="check against a template's own sections, such as a personal one")
    p.add_argument("--strict", action="store_true", help="treat warnings as errors")
    p.add_argument("--profile", choices=("plain", "natural", "google", "none"), default="plain",
                   help="plain is the house voice (natural is its older name). google adds the document rules "
                        "from references/voice-google.md on top, and never removes a house rule. none turns "
                        "house style off and keeps the rules that protect facts")
    p.add_argument("--root", help="knowledge base folder, for finding snapshots (default: ~/.flareware/flarehand)")
    p.add_argument("--repo-root", metavar="DIR", help="where a cited code path such as src/x.rs:3-8 lives")
    p.add_argument("--ledger", metavar="PATH", help="a sources.jsonl, or the folder holding one, for S# ids "
                                                   "(default: this session's staging folder)")
    p.add_argument("--json", action="store_true", help="print JSON instead of text")
    p.add_argument("--max", type=int, default=DEFAULT_MAX, help=f"most findings to print (default {DEFAULT_MAX})")
    args = p.parse_args(argv)
    if args.profile == "natural":
        args.profile = "plain"

    if not (args.style or args.citations or args.contract or args.template):
        args.style = True
    args.repo_root = Path(args.repo_root).expanduser() if getattr(args, "repo_root", None) else None
    args.ledger = Path(args.ledger).expanduser() if getattr(args, "ledger", None) else None
    args.kb_root = None
    # Needed for snapshots and for a personal contract, so resolve it for both.
    if args.citations or args.contract or args.template:
        try:
            sys.path.insert(0, str(SKILL_DIR / "scripts"))
            from kb import resolve_root  # noqa: E402
            args.kb_root = resolve_root(args.root)
        except Exception:
            args.kb_root = Path(args.root).expanduser() if args.root else None

    try:
        rules = load_style_words(SKILL_DIR / "assets" / "style-words.tsv") if args.style else []
        if args.style and args.profile == "google":
            rules += load_style_words(SKILL_DIR / "assets" / "style-words-google.tsv")
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    contracts = load_contracts(SKILL_DIR / "assets" / "contracts.tsv")
    # A workflow someone wrote for their own team gets its sections checked the same way a
    # shipped one does. A new name is theirs outright. A name that already exists is a
    # floor, not a starting point: personal rows may ADD sections and markers and may never
    # remove one. Otherwise a one-line file turns off the checks the shipped contract makes,
    # which is the one thing references/adaptation.md says cannot happen.
    if args.kb_root is not None:
        contracts = merge_contracts(contracts, load_contracts(Path(args.kb_root) / "contracts.tsv"))

    all_findings: list[dict] = []
    checked = 0
    for name in args.files:
        # A chat reply never becomes a file, so it can be piped in. Citations in it resolve
        # against the folder the check runs from.
        stdin_text = sys.stdin.read() if name == "-" else None
        path = Path("<stdin>") if name == "-" else Path(name)
        if stdin_text is None and not path.is_file():
            print(f"error: not a file: {path}", file=sys.stderr)
            return 2
        try:
            if stdin_text is not None:
                path = Path.cwd() / "<stdin>"
            found = run_file(path, args, rules, contracts, stdin_text)
            if stdin_text is not None:
                for f in found:
                    f["file"] = "<stdin>"
            all_findings += found
            checked += 1
        except OSError as e:
            # name the file that could not be read, which may be the template rather than
            # the artifact the loop is on
            missing = getattr(e, "filename", None) or path
            print(f"error: cannot read {missing}: {e.strerror or e}", file=sys.stderr)
            return 2

    errors = [f for f in all_findings if f["severity"] == "error"]
    warns = [f for f in all_findings if f["severity"] == "warn"]
    if args.strict:
        errors, warns = errors + warns, []

    if args.json:
        print(json.dumps(
            {
                "files_checked": checked,
                "errors": len(errors),
                "warnings": len(warns),
                "findings": (errors + warns)[: args.max],
                "truncated": len(errors) + len(warns) > args.max,
            },
            indent=2,
        ))
    else:
        shown = (errors + warns)[: args.max]
        for f in shown:
            where = f"{f['file']}:{f['line']}:{f['col']}" if f["line"] else f["file"]
            print(f"{f['severity'].upper():5} {where}  [{f['rule']}] {f['message']}")
        hidden = (len(errors) + len(warns)) - len(shown)
        if hidden > 0:
            print(f"... and {hidden} more. Raise --max to see them.")
        print(f"\n{checked} file(s): {len(errors)} error(s), {len(warns)} warning(s)")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
