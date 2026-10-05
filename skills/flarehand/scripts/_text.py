"""_text.py - one definition of how this skill reads words.

The router and the answer cache both compare what someone typed against stored
text. If they each normalised words their own way, the same sentence could
route one way and cache another. So both import this.

This is a library module, not a command. Nothing here prints or writes.

Two levels, used for two different jobs:

  exact_form   Changes only what cannot change meaning: case, punctuation,
               apostrophes, and spelling variants such as set-up and setup.
               Every word stays, including single letters and product names.
               The answer cache replays word for word ONLY on an exact match.

  tokens       Also stems words (stories -> story, failing -> fail), fixes a
               few common typos, expands contractions (isn't -> is not) and
               maps irregular verbs. Used to FIND candidates: routing, and
               near-match suggestions that a person must confirm before
               anything is replayed.

Letters from any script count as words, so a question typed in Japanese or
Cyrillic keeps its own exact form instead of collapsing to an empty one. For
plain ASCII text the exact form is unchanged from earlier versions, so saved
answer keys still match.
"""

from __future__ import annotations

import re
from pathlib import Path
import unicodedata

# letters and digits in any script; underscore and punctuation split words
WORD = re.compile(r"[^\W_]+")

# Spelling variants only. Never a synonym: "install" and "set up" can mean
# different things, so they are NOT here.
SPELLING = {
    "setup": "set up",
    "signin": "sign in",
    "login": "log in",
    "logon": "log on",
    "e-mail": "email",
    "okay": "ok",
    "summarise": "summarize",
    "summarised": "summarized",
    "organise": "organize",
    "prioritise": "prioritize",
    "colour": "color",
    "behaviour": "behavior",
    "cancelled": "canceled",
    "utilisation": "utilization",
    "analyse": "analyze",
    "catalogue": "catalog",
}

TYPOS = {
    "wroking": "working", "workign": "working", "recieve": "receive", "teh": "the",
    "pls": "please", "plz": "please", "thx": "thanks", "u": "you", "ur": "your",
    "definately": "definitely", "seperate": "separate", "enviroment": "environment",
    "envirnoment": "environment", "reciept": "receipt", "acess": "access", "adress": "address",
    "occured": "occurred", "untill": "until", "wierd": "weird",
}

# Contractions lose their apostrophe in fold(), so "isn't" arrives as "isnt". For routing
# they expand to two words, so "payroll isn't calculating" matches the row "not calculating".
# exact_form never expands them: a saved answer replays only on the wording as typed.
CONTRACTIONS = {
    "isnt": "is not", "arent": "are not", "wasnt": "was not", "werent": "were not",
    "doesnt": "does not", "dont": "do not", "didnt": "did not",
    "cant": "can not", "cannot": "can not", "couldnt": "could not",
    "wont": "will not", "wouldnt": "would not", "shouldnt": "should not",
    "hasnt": "has not", "havent": "have not", "hadnt": "had not",
}

IRREGULAR = {
    "broke": "break", "broken": "break", "threw": "throw", "thrown": "throw",
    "ran": "run", "went": "go", "gone": "go", "did": "do", "done": "do", "does": "do",
    "wrote": "write", "written": "write", "saw": "see", "seen": "see", "got": "get",
    "gotten": "get", "made": "make", "took": "take", "taken": "take", "gave": "give",
    "given": "give", "sent": "send", "found": "find", "hung": "hang",
    "built": "build", "lost": "lose", "paid": "pay", "sold": "sell", "told": "tell",
    "children": "child", "people": "person", "analyses": "analysis", "statuses": "status",
    "indices": "index", "criteria": "criterion",
}

# Words that stems would mangle into something else.
KEEP_AS_IS = {
    "status", "analysis", "news", "always", "this", "its", "yes", "less", "us", "bus",
    "has", "was", "is", "as", "ops", "dns", "sms", "aws", "ios", "vs", "access", "process",
    "business", "address", "success", "class", "pass", "express", "series", "species",
    "during", "thing", "nothing", "something", "anything", "everything", "morning",
    "evening", "string", "bring", "spring", "ceiling", "wedding", "king", "ring", "sing",
    "need", "speed", "feed", "seed", "red", "bed", "shed", "embed", "used", "sled",
    "hundred", "united", "limited", "detailed", "advanced", "tss", "sso", "cors", "sql",
    "https", "http", "jenkins", "wiki", "api", "apis", "sdk", "sdks", "kpis", "okrs",
    # "theme" would lose its final e and become the pronoun "them"
    "theme",
    # contractions lose their apostrophe first, so "what's" arrives as "whats". Stemming it
    # to "what" would make a pattern for "what's" match every sentence containing "what".
    "whats", "thats", "hows", "wheres", "whos", "whens", "whys", "theres", "heres", "lets",
    "ive", "youre", "were", "theyre", "shes", "hes", "im", "ill", "id", "youve",
}


def fold(text: str) -> str:
    """Lowercase, strip accents, drop apostrophes so can't == cant."""
    norm = unicodedata.normalize("NFKD", str(text))
    norm = "".join(c for c in norm if not unicodedata.combining(c))
    norm = norm.lower().replace("’", "'").replace("‘", "'")
    return norm.replace("'", "")


def words(text: str) -> list[str]:
    return WORD.findall(fold(text))


def exact_form(text: str) -> str:
    """Case, punctuation and spelling variants only. Every word is kept."""
    out: list[str] = []
    for w in words(text):
        out.extend(SPELLING.get(w, w).split())
    return " ".join(out)


def stem(word: str) -> str:
    w = TYPOS.get(word, word)
    w = IRREGULAR.get(w, w)
    if w in KEEP_AS_IS or len(w) <= 3 or w.isdigit():
        return w
    if w.endswith("ies") and len(w) > 4:
        w = w[:-3] + "y"
    elif w.endswith("ied") and len(w) > 4:
        w = w[:-3] + "y"
    elif w.endswith("ying") and len(w) > 5:
        w = w[:-4] + "y"
    elif w.endswith("ing") and len(w) - 3 >= 3:
        w = _restore_e(w[:-3])
    elif w.endswith("ed") and len(w) - 2 >= 3:
        w = _restore_e(w[:-2])
    elif w.endswith("es") and len(w) - 2 >= 3:
        w = w[:-2] if re.search(r"(ss|x|z|ch|sh)$", w[:-2]) else w[:-1]
    elif w.endswith("s") and not w.endswith("ss") and len(w) - 1 >= 3:
        w = w[:-1]
    if w in KEEP_AS_IS:
        return w
    # drop a final silent e so create, created and creating agree
    if len(w) > 4 and w.endswith("e"):
        w = w[:-1]
    return w


def _restore_e(w: str) -> str:
    """After -ed or -ing comes off: undo a doubled consonant (logged -> log), or put back
    the silent e a short stem lost (fired -> fire, timed -> time), so it agrees with
    the base word. The e comes back only for a three-letter consonant-vowel-consonant
    stem, never after w, x or y (fixed -> fix, rowed -> row)."""
    if len(w) >= 4 and w[-1] == w[-2] and w[-1] not in "lsz":
        return w[:-1]
    if (len(w) == 3 and w[0] not in "aeiou" and w[1] in "aeiou"
            and w[2] not in "aeiouwxy"):
        return w + "e"
    return w


def tokens(text: str) -> list[str]:
    """Stemmed tokens, in order. Spelling variants and contractions expand first."""
    out: list[str] = []
    for w in exact_form(text).split():
        for part in CONTRACTIONS.get(w, w).split():
            out.append(stem(part))
    return out


# --------------------------------------------------------------------------
# what counts as citing this skill instead of a real source
# --------------------------------------------------------------------------

# A bare path to one of this skill's own guidance files.
_SKILL_FILE = re.compile(
    r"(^|[\s/])references/[a-z0-9-]+\.md"      # references/voice.md, anywhere in the string
    r"|(^|[\s/])SKILL\.md"
    r"|(^|[\s/])flarehand([\s/]|$)"           # the folder, not a page merely named after it
    r"|skill reference",
    re.IGNORECASE,
)
# A source with a scheme or a prefix names something outside this skill: a web page, a
# revision in some repository, an item an MCP server holds. Its path may well contain a
# `references/` folder of its own, so the path alone proves nothing.
_PREFIXED = re.compile(r"^(?:https?://|git:|mcp:)", re.IGNORECASE)


def is_self_source(source: str) -> bool:
    """True when a source names this skill's own guidance rather than evidence.

    One definition, because three scripts used to carry three regexes that disagreed.
    The reference files are guidance, so citing them makes an answer look grounded when
    it is not. A URL, a `git:` revision or an `mcp:` item is different: it names a page in
    some other place, and many repositories have a `references/` folder. Those count as
    the skill only when they also name this skill's own folder.
    """
    s = (source or "").strip()
    if not s:
        return False
    if _PREFIXED.match(s):
        return bool(re.search(r"(^|[/:])flarehand/", s, re.IGNORECASE)) and bool(_SKILL_FILE.search(s))
    return bool(_SKILL_FILE.search(s))


# A file this skill can point at on disk. Kept short on purpose: a source has to be
# something another person can open, and an unknown extension is more likely a typo.
CODE_SUFFIXES = (
    "py|js|jsx|mjs|cjs|ts|tsx|dart|java|kt|kts|scala|swift|m|mm|rs|go|rb|php|cs|fs|vb|c|h|cc|cpp|hpp"
    "|sql|pkb|pks|sh|bash|zsh|ps1|psm1|bat|cmd|lua|r|ex|exs|erl|clj|vue|svelte|tf|hcl|proto|graphql"
    "|md|rst|txt|json|jsonc|yaml|yml|toml|ini|cfg|conf|env|xml|html|css|scss|jsp|tsv|csv|lock|gradle"
    "|properties|csproj|sln|mod|sum"
)
# Files people cite by name that carry no extension.
BARE_FILES = "Makefile|Dockerfile|Gemfile|Rakefile|Procfile|Justfile|Jenkinsfile|LICENSE|CODEOWNERS"
# A line or a line range, in either of the two forms people paste: `:3-8` or `#L3-L8`.
LINE_SPAN = r"(?::\d+(?:-\d+)?|#L\d+(?:-L?\d+)?)"
# A relative path, optionally with a line or a line range: src/registry.rs:3-8, lib/a.py#L10-L20
REPO_PATH = re.compile(
    rf"^(?!/)(?:[\w.\-]+/)*(?:[\w.\-]+\.(?:{CODE_SUFFIXES})|(?:{BARE_FILES})){LINE_SPAN}?$", re.IGNORECASE
)


def strip_line_span(ref: str) -> str:
    """`src/a.py#L3-L8` and `src/a.py:3-8` both become `src/a.py`."""
    return re.sub(rf"{LINE_SPAN}$", "", (ref or "").strip())


def is_local_path(source: str) -> bool:
    """True when a source names a file on this machine rather than something anyone can
    look up. Good enough to cite in a review you are reading now, and not good enough to
    save: another machine, or this one next month, cannot check it."""
    s = (source or "").strip()
    return bool(s) and not s.startswith("evidence/") and bool(REPO_PATH.match(s))


# Every source shape the skill accepts, defined once. check_output, answers, kb, review and
# ground each used to keep a copy, and the copies drifted.
#
#   https://docs.python.org/3/library/re.html     a page anyone can open
#   S3                                            a row in this session's source ledger (ground.py)
#   src/registry.rs#L3-L8                         a file in the repository you are in
#   git:4f2a9c1:src/registry.rs                   a file as it was at one revision
#   mcp:jira:ABC-123                              an item an MCP server holds
#   ABC-123                                       a ticket key, in any tracker
#   evidence/48bb17d1ad08.txt or 48bb17d1ad08     a snapshot this skill kept
TICKET_KEY = re.compile(r"^[A-Z][A-Z0-9]{1,9}-\d{1,6}$")
JIRA_KEY = TICKET_KEY      # the older name, kept for callers that still use it
URL_ONLY = re.compile(r"^https?://\S+$")
LEDGER_ID = re.compile(r"^S\d{1,4}$")
SNAPSHOT = re.compile(r"^evidence/[0-9a-f]{8,64}\.txt$")
SNAPSHOT_HASH = re.compile(r"^[0-9a-f]{12}$")
# git:<revision>:<path>. A revision is a hash, a branch, a tag, or HEAD~2. No spaces.
GIT_REF = re.compile(r"^git:[^\s:]+:[^\s].*$")
# mcp:<server>:<id>. The id is whatever that server uses, and may hold slashes or spaces.
MCP_REF = re.compile(r"^mcp:[A-Za-z0-9][A-Za-z0-9_.\-]*:\S.*$")
SOURCE_SHAPES = (URL_ONLY, LEDGER_ID, SNAPSHOT, SNAPSHOT_HASH, TICKET_KEY, REPO_PATH, GIT_REF, MCP_REF)
VERIFIED = re.compile(r"\[verified:\s*([^\]]+)\]")
EVIDENCE_REF = re.compile(r"evidence/([0-9a-f]{12})\.txt")


def source_shape(source: str) -> str | None:
    """The name of the shape a source has, or None. Used to word messages and to pick a check."""
    s = (source or "").strip()
    for name, pat in (("url", URL_ONLY), ("ledger", LEDGER_ID), ("snapshot", SNAPSHOT),
                      ("snapshot", SNAPSHOT_HASH), ("ticket", TICKET_KEY), ("git", GIT_REF),
                      ("mcp", MCP_REF), ("path", REPO_PATH)):
        if pat.match(s):
            return name
    return None


def is_citable_source(source: str) -> bool:
    """True when a source is an id somebody else can look up again.

    A URL, `git:<rev>:<path>`, `mcp:<server>:<id>`, a ticket key and a snapshot all are.
    "said in session" and "4 sessions" are not: they are honest about where a fact came
    from, and there is nothing to re-read. A ledger id such as S3 is not either, because it
    only means something inside one session. Only a lookupable id belongs in a note's
    `sources:`, because that list is what the freshness check re-reads.
    """
    s = (source or "").strip()
    if not s or is_self_source(s):
        return False
    return bool(URL_ONLY.match(s) or SNAPSHOT.match(s) or TICKET_KEY.match(s)
                or GIT_REF.match(s) or MCP_REF.match(s))


def tsv_rows(path, columns: int) -> list[list[str]]:
    """Tab separated, header skipped, `#` lines skipped, short rows padded. A missing file
    means no rows, so a damaged table degrades into fewer options rather than a traceback.
    Every table loader uses this, so a personal table never reads two ways."""
    out = []
    try:
        lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError):
        return out
    for raw in lines[1:]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        cells = [c.strip() for c in raw.split("\t")]
        out.append(cells + [""] * (columns - len(cells)))
    return out
