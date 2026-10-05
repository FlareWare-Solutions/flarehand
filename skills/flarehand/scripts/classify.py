#!/usr/bin/env python3
"""classify.py - work out what kind of help a request needs.

It reads the request, matches it against assets/router-table.tsv, and returns
the route to take. This is a table lookup, not a judgment call, so the same
words always give the same result, in any tool, on any model.

Words are normalised before matching, so plurals, tense, contractions and a few
common typos do not change the result: "write user stories" matches the same
row as "write a user story", "deploy failed" matches "fail", and "payroll isn't
calculating" matches "not calculating".

Routes
  workflow   produce an artifact. Read the workflow file it names.
  lookup     a single fact or a definition. Find it, cite it, answer. No ceremony.
  setup      install, connect, or fix access to a tool, or set up this plugin.
  memory     save, log, or recall something from your knowledge base.
  outside    general coding or personal writing with no work deliverable. Answer normally.
  unclear    nothing matched. Offer the jobs that fit what you can tell.

What it reads, in order of strength
  nouns      the artifact asked for, such as a test plan. The strongest signal.
  verbs      the kind of help, such as review or summarize
  context    words that settle what an ambiguous word means
  systems    which tool is involved, such as Jira, GitHub or Claude Code
  audience   who reads the result
  risk       phrases that need a guardrail, such as a stated cause or legal advice

A longer phrase beats a shorter one inside it: "case study" is not a support
"case", and "cutover plan" does not also count as the verb "plan". That holds
for risk phrases too: "map 1:1 with" is not a manager's "1:1 with".

The table in assets/router-table.tsv is edited by hand. There is no generator.
After any edit, run evals/test_scripts.py: its routing table is the guard.

Words with two meanings come from glossaries, not from the shipped table. Each
term in the person's glossary.tsv, and in any team playbook's, becomes an
`ambiguous` row: when the term appears and none of its saved meanings does, the
saved question is asked first. Glossaries add up across layers.

Usage
  python3 scripts/classify.py "why is the nightly export failing for this customer"
  python3 scripts/classify.py --explain "summarize this for the board"
  echo "draft a knowledge base article" | python3 scripts/classify.py -

Exit codes: 0 a clear result, 1 unclear or a question must be asked first,
2 usage or file error.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _text import tokens, tsv_rows  # noqa: E402
from kb import _utf8_console  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent
TABLE = SKILL_DIR / "assets" / "router-table.tsv"
TEMPLATES = SKILL_DIR / "assets" / "templates"

WORKFLOWS_TABLE = SKILL_DIR / "assets" / "workflows.tsv"
STYLE_TABLE = SKILL_DIR / "assets" / "style-profiles.tsv"
GRAPH_TABLE = SKILL_DIR / "assets" / "workflow-graph.tsv"


_rows = tsv_rows


# id -> (name, slug). The reference file for wf-09 is references/wf-09-plan.md.
SHIPPED_ARCHETYPES = {r[0]: (r[1], r[2]) for r in _rows(WORKFLOWS_TABLE, 3) if r[0]}
ARCHETYPES = dict(SHIPPED_ARCHETYPES)
PERSONAL_ARCHETYPES: dict[str, tuple] = {}
PERSONAL_TEMPLATES: Path | None = None     # their templates folder, read before the shipped one


def load_personal_workflows(root) -> None:
    """Workflows someone wrote for their own team, read after the shipped ones.

    A workflow is three parts: a method, a shape and a set of checks. Registering the id
    here is what lets the router name it, so it stops being a note nobody can reach.
    """
    global ARCHETYPES, PERSONAL_TEMPLATES
    ARCHETYPES = dict(SHIPPED_ARCHETYPES)
    PERSONAL_ARCHETYPES.clear()
    PERSONAL_TEMPLATES = Path(root) / "templates" if root is not None else None
    if root is None:
        return
    for r in _rows(Path(root) / "workflows.tsv", 3):
        if r[0] and r[0] not in SHIPPED_ARCHETYPES:
            PERSONAL_ARCHETYPES[r[0]] = (r[1] or r[0], r[2] or r[0])
    ARCHETYPES.update(PERSONAL_ARCHETYPES)

# Optional writing profiles, and the templates that count as write-ups for each. A write-up
# offers the profile once; chat and customer replies never do. references/voice-google.md.
STYLE_PROFILES: dict[str, dict] = {}
for _r in _rows(STYLE_TABLE, 4):
    if _r[0]:
        STYLE_PROFILES[_r[0]] = {"templates": {x.strip() for x in _r[1].split(",") if x.strip()},
                                 "reference": _r[2], "words": _r[3]}

# Every edge the workflow files name under "## Chains to", strongest first. Holding all of
# them, rather than one per workflow, is what stops "offer next" walking a two-step loop
# forever: wf-09 points at wf-11 and wf-11 points back, and the second edge is the way out.
NEXT_STEPS: dict[str, list[tuple[str, str]]] = {}
for _r in sorted(_rows(GRAPH_TABLE, 4), key=lambda x: (x[0], x[3])):
    if _r[0] and _r[1]:
        NEXT_STEPS.setdefault(_r[0], []).append((_r[1], _r[2]))


def archetype_name(archetype: str) -> str:
    """The display name, or the bare id when a table names a workflow this build does not
    have. A typo in a data file must not take the classifier down."""
    known = ARCHETYPES.get(archetype)
    return known[0] if known else f"{archetype} (not a workflow this build knows)"


def reference_for(archetype: str) -> str:
    if archetype in PERSONAL_ARCHETYPES:
        # theirs lives in their knowledge base, not in the skill
        return f"workflows/{archetype}.md"
    known = SHIPPED_ARCHETYPES.get(archetype)
    return f"references/{archetype}-{known[1]}.md" if known else ""



# AI tools and this plugin. Naming one with a setup verb, or with a failure, is setup.
AI_TOOL_SYSTEMS = {"claude", "copilot", "codex", "cursor", "gemini", "mcp", "flarehand"}
SETUP_SYSTEMS = AI_TOOL_SYSTEMS | {"python", "obsidian"}
# Naming a language is about code, not about installing anything. So a language means
# setup only with a setup verb or a failure such as "python not found".
LANGUAGE_SYSTEMS = {"python"}
# The developer machine. A failure here is a machine problem, so it is setup too.
WORKSTATION_SYSTEMS = {"git", "node", "ssh", "homebrew", "wsl", "editor", "package-manager", "flutter", "java"}
# Work tools and infrastructure. Naming one is usually about the work ("the pod keeps
# crashing", "the Jira export is wrong"), so it means setup only with a setup verb.
WORK_TOOL_SYSTEMS = {"jira", "confluence", "github", "gitlab", "bitbucket", "notion", "slack", "m365",
                     "google-workspace", "salesforce", "hubspot", "zendesk", "servicenow", "linear", "sso"}
INFRA_SYSTEMS = {"docker", "kubernetes", "aws", "azure", "gcp", "database"}
VERB_SETUP_SYSTEMS = WORK_TOOL_SYSTEMS | INFRA_SYSTEMS
# Git hosts are set up on the machine (keys, sign in), so their setup answer is the workstation one.
GIT_HOSTS = {"github", "gitlab", "bitbucket"}
# Templates that are themselves a setup answer, so a setup request that names one stays setup.
SETUP_TEMPLATES = {"docs-page"}
# A noun whose answer is a method rather than a shape: the router sends these to the reference.
TEMPLATE_REFERENCES = {"code-review": "references/review-code.md",
                       "workflow-authoring": "references/wf-authoring.md"}
# A code review checklist written as a plan is still a plan. Only a review reads the review guide.
REFERENCE_ONLY_FOR = {"code-review": "wf-10"}
HIGH_STAKES_AUDIENCE = {"customer", "executive", "engineering", "auditor"}
HIGH_STAKES_RISK = {"outbound-gate", "legal-advice", "financial-figures", "people-matter", "security-claim",
                    "production-write", "stated-cause", "check-before-send"}
# "Check this before I send it" asks for grounding, not for a critique. The draft goes through
# the outbound check before any opinion, so its numbers and claims are tested, not admired.
CHECK_HINT = ("Run `python3 scripts/check.py - --outbound` on the draft first, with the draft on standard "
              "input. Ground every number, date and claim it lists before you say the draft is right.")
CLEAR_MARGIN = 3.0
WILDCARD_MAX = 3


def compile_pattern(pattern: str) -> list[str | None]:
    """A pattern becomes a token sequence. `*` stands for one to three words."""
    seq: list[str | None] = []
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


def find_span(hay: list[str], seq: list[str | None]) -> tuple[int, int] | None:
    """First occurrence of seq in hay, as (start, end). end is exclusive."""
    if not seq:
        return None

    def match_from(i: int, j: int) -> int | None:
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


def find_all_spans(hay: list[str], seq: list[str | None]) -> list[tuple[int, int]]:
    """Every start where seq matches, shortest match at each start."""
    out = []
    for start in range(len(hay)):
        span = find_span(hay[start:], seq)
        if span and span[0] == 0:
            out.append((start, start + span[1]))
    return out


def personal_table(root: Path | None) -> Path | None:
    """Router rows someone wrote for their own workflows, read after the shipped ones."""
    if root is None:
        return None
    path = Path(root) / "router-table.tsv"
    return path if path.is_file() else None


def load_table(path: Path, personal: Path | None = None, glossary: list[dict] | None = None) -> list[dict]:
    rows = _read_table(path, required=True)
    if personal is not None:
        rows += _read_table(personal, required=False, personal=True)
    if glossary:
        rows += glossary_rows(glossary)
    return rows


def read_glossary(root: Path | None = None, cwd: Path | None = None) -> list[dict]:
    """Every saved term from every layer: the person's knowledge base, then each playbook.

    The layers module finds the playbooks. When it is missing or fails, only the personal
    glossary is read, so a broken playbook never takes routing down with it."""
    try:
        import layers  # noqa: E402
        rows = layers.read_tsv("glossary.tsv", cwd=cwd, root=root)
        return [dict(r) for r in rows if (r.get("term") or "").strip()]
    except Exception:
        pass
    if root is None:
        try:
            from kb import resolve_root  # noqa: E402
            root = resolve_root(None)
        except Exception:
            return []
    path = Path(root) / "glossary.tsv"
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    lines = [ln for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines:
        return []
    head = [h.strip() for h in lines[0].split("\t")]
    out = []
    for raw in lines[1:]:
        cells = [c.strip() for c in raw.split("\t")]
        row = dict(zip(head, cells + [""] * (len(head) - len(cells))))
        if row.get("term"):
            row["layer"] = "yours"
            out.append(row)
    return out


def glossary_rows(entries: list[dict]) -> list[dict]:
    """Saved terms become `ambiguous` rows, and their meanings become `context` rows.

    Rules add up, so a term saved in several layers keeps every meaning from all of them,
    and the question from the nearest layer. A term with one meaning has nothing to ask."""
    terms: dict[str, dict] = {}
    for e in entries:
        term = " ".join(tokens(e.get("term", "")))
        if not term:
            continue
        t = terms.setdefault(term, {"pattern": e["term"].strip(), "meanings": [], "ask": "",
                                    "layer": e.get("layer") or "yours"})
        for meaning in (e.get("meanings") or "").split("|"):
            meaning = meaning.strip()
            if meaning and meaning.lower() not in (m.lower() for m in t["meanings"]):
                t["meanings"].append(meaning)
        if not t["ask"] and (e.get("ask") or "").strip():
            t["ask"] = e["ask"].strip()
    rows = []
    for t in terms.values():
        if len(t["meanings"]) < 2 and not t["ask"]:
            continue
        ask = t["ask"] or "Do you mean " + ", or ".join(t["meanings"]) + "?"
        seq = compile_pattern(t["pattern"])
        if not seq:
            continue
        rows.append({"kind": "ambiguous", "pattern": t["pattern"], "value": ask, "weight": 0.0, "extra": "",
                     "seq": seq, "length": sum(1 for x in seq if x is not None), "personal": False,
                     "glossary": t["layer"]})
        for meaning in t["meanings"]:
            mseq = compile_pattern(meaning)
            if mseq:
                rows.append({"kind": "context", "pattern": meaning, "value": t["pattern"], "weight": 0.0,
                             "extra": meaning, "seq": mseq, "length": sum(1 for x in mseq if x is not None),
                             "personal": False, "glossary": t["layer"]})
    return rows


def _read_table(path: Path, required: bool, personal: bool = False) -> list[dict]:
    if not path.is_file():
        if required:
            print(f"error: router table not found at {path}", file=sys.stderr)
            sys.exit(2)
        return []
    rows = []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip() or raw.startswith("kind\t"):
            continue
        parts = raw.split("\t")
        if len(parts) < 4:
            continue
        try:
            weight = float(parts[3] or 0)
        except ValueError:
            print(f"warning: router table line {n} has a bad weight '{parts[3]}', skipped", file=sys.stderr)
            continue
        seq = compile_pattern(parts[1])
        if not seq:
            continue
        rows.append({"kind": parts[0], "pattern": parts[1], "value": parts[2], "weight": weight,
                     "extra": parts[4] if len(parts) > 4 else "", "seq": seq,
                     "length": sum(1 for s in seq if s is not None), "personal": personal})
    return rows


def contains(outer: tuple[int, int], inner: tuple[int, int]) -> bool:
    return outer[0] <= inner[0] and inner[1] <= outer[1] and (outer[1] - outer[0]) > (inner[1] - inner[0])


def classify(text: str, rows: list[dict]) -> dict:
    hay = tokens(text)
    hits: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        span = find_span(hay, row["seq"])
        if span:
            hits[row["kind"]].append(dict(row, span=span))

    # a longer phrase wins over a shorter one it contains
    pool = hits["verb"] + hits["noun"]
    blockers = pool + hits["context"] + hits["route"]
    kept = [m for m in pool if not any(contains(o["span"], m["span"]) for o in pool)]
    routes = {}
    lookup_hits = []
    risky = bool(hits["risk"])
    for m in hits["route"]:
        # A personal row may add a way in. It may not turn a request that trips a shipped
        # guardrail into a light one, which is what routing it to memory or lookup would do.
        if m.get("personal") and risky:
            continue
        if not any(contains(o["span"], m["span"]) for o in pool):
            routes.setdefault(m["value"], []).append(m["pattern"])
            if m["value"] == "lookup":
                lookup_hits.append(m)

    scores: dict[str, float] = defaultdict(float)
    for m in kept:
        scores[m["value"]] += m["weight"] + 0.5 * (m["length"] - 1)
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    top = ranked[0] if ranked else (None, 0.0)
    second = ranked[1] if len(ranked) > 1 else (None, 0.0)

    # The template comes from the nouns that survived. A noun swallowed by a longer
    # verb of another kind does not count: "list the edge cases" is not a support case.
    all_nouns = hits["noun"]
    noun_pool = [m for m in all_nouns
                 if not any(contains(o["span"], m["span"]) and (o["kind"] == "noun" or o["value"] != m["value"])
                            for o in pool)]
    # Strongest noun first. On a tie, a noun that names a template beats one that does not,
    # then a noun of the winning workflow, then the earlier noun in the sentence.
    # A light noun (weight under 5) sets the template only for its own workflow.
    top_arch = ranked[0][0] if ranked else None
    nouns = sorted((m for m in noun_pool if m["weight"] >= 5 or m["value"] == top_arch),
                   key=lambda m: (-(m["weight"] + 0.5 * (m["length"] - 1)), not m["extra"],
                                  m["value"] != top_arch, m["span"][0], m["extra"]))
    template = nouns[0]["extra"] if nouns else ""
    nouns = [m for m in nouns if m["extra"]]

    systems = sorted({m["value"] for m in hits["system"]})
    audience = sorted({m["value"] for m in hits["audience"]})
    # A risk phrase inside a longer noun that names no template is that phrase, not a risk:
    # "map 1:1 with" is data, not a manager's 1:1. A noun with a template keeps its risks,
    # so "indemnity clause" still carries legal-advice.
    # A personal row never suppresses a risk either. Otherwise a long noun somebody added
    # could swallow "indemnity clause" and quietly take the legal guardrail with it.
    plain_nouns = [m for m in all_nouns if not m["extra"] and not m.get("personal")]
    risks = sorted({m["value"] for m in hits["risk"]
                    if not any(contains(o["span"], m["span"]) for o in plain_nouns)})
    # Code is reviewed, not sent. "Fact check the skill" is a code review, not an outbound draft.
    if template == "code-review" and "check-before-send" in risks:
        risks.remove("check-before-send")

    # Only report a settled sense for a word that is in the sentence. A personal row can add
    # a question but never answer a shipped one, because where intent is unclear the skill asks.
    # A glossary's own meanings may settle that glossary's own term, and nothing else.
    present = {m["pattern"] for m in hits["ambiguous"]}
    glossary_terms = {m["pattern"] for m in hits["ambiguous"] if m.get("glossary")}
    shipped_terms = {m["pattern"] for m in hits["ambiguous"] if not m.get("glossary") and not m.get("personal")}
    shipped_blockers = [o for o in blockers if not o.get("personal")]
    resolved = {}
    for m in hits["context"]:
        if m.get("personal"):
            continue
        if m.get("glossary") and (m["value"] not in glossary_terms or m["value"] in shipped_terms):
            continue
        if m["value"] in present:
            resolved.setdefault(m["value"], m["extra"])
    ask = []
    for m in hits["ambiguous"]:
        word = m["pattern"]
        if word in resolved:
            continue
        # Every place the word appears counts. "The release notes for the release" still
        # holds one bare "release" after the noun has swallowed the first.
        if all(any(contains(o["span"], span) for o in shipped_blockers)
               for span in find_all_spans(hay, m["seq"])):
            continue
        if not any(q["word"] == word for q in ask):
            q = {"word": word, "ask": m["value"]}
            if m.get("glossary"):
                q["source"] = m["glossary"]
            ask.append(q)

    # ---- choose the route
    archetype = top[0]
    # a lookup phrase that covers the artifact noun is a question about it, not a request for one
    lookup_covers_nouns = bool(nouns) and any(
        all(contains(m["span"], n["span"]) for n in nouns) for m in lookup_hits)
    # a language on its own is about code, so it forces setup only with a setup verb or a failure
    tool_systems = set(systems) & (SETUP_SYSTEMS | WORKSTATION_SYSTEMS)
    if tool_systems <= LANGUAGE_SYSTEMS and "setup-verb" not in routes and archetype != "wf-01":
        tool_systems = set()
    memory_kind = ""
    # "Draft the SOW and keep a copy of the pricing table" asks for a SOW. When a work verb and
    # an artifact are both present, a memory phrase is a side clause and the work wins.
    work_verbs = [m for m in kept if m["kind"] == "verb"]
    if "memory" in routes and work_verbs and nouns:
        routes.pop("memory")
    # Naming a tool is not work context on its own: "write a python script that reads the
    # Jira API" is general coding. What overrides an outside phrase is an artifact, a memory
    # request, or a request to set a tool up.
    setup_signal = "setup" in routes or ("setup-verb" in routes and bool(set(systems) - LANGUAGE_SYSTEMS))
    if "outside" in routes and not (nouns or setup_signal or "memory" in routes):
        route = "outside"
        archetype = None
        ask = []
    elif "memory" in routes:
        # Which store this belongs in, from the longest phrase that matched. The knowledge
        # base has seven, with different write commands and different freshness rules, and
        # picking the wrong one is why a chain saved as a note can never be promoted.
        route, archetype = "memory", None
        memory_kind = next((m["extra"] for m in sorted(
            hits["route"], key=lambda x: -x["length"]) if m["value"] == "memory" and m["extra"]), "")
    elif "definition" in routes:
        route, archetype = "lookup", "wf-06"
    elif "lookup" in routes and (not nouns or lookup_covers_nouns):
        # One fact with a citation. Whatever archetype happened to top the score is not
        # what they asked for, and carrying it invites the shape of an artifact nobody
        # wanted. SKILL.md gives a lookup steps 4, 5 and 7 only. A definition keeps wf-06
        # above, because explaining a term really is that workflow.
        route, archetype, template = "lookup", None, ""
    elif (("setup" in routes and (not nouns or template in SETUP_TEMPLATES))
          or (tool_systems
              and (archetype in (None, "wf-01", "wf-09") or "setup-verb" in routes)
              and (not nouns or template in SETUP_TEMPLATES))
          or (set(systems) & VERB_SETUP_SYSTEMS and "setup-verb" in routes and not nouns)):
        # A setup verb alone ("billing module setup") is configuring the work, not tool setup.
        # It only means tool setup when a tool is named.
        route = "setup"
        archetype = archetype if archetype in ("wf-01", "wf-09") else "wf-09"
    elif archetype:
        route = "workflow"
    else:
        route = "unclear"

    # A draft they want checked before it goes out is work to do, even with no verb or noun:
    # "is this accurate?" with a pasted reply. The fact check is the critique workflow.
    if "check-before-send" in risks and route in ("unclear", "lookup"):
        route, archetype, template = "workflow", "wf-10", ""
        top = ("wf-10", max(top[1], CLEAR_MARGIN))
    hints = [CHECK_HINT] if "check-before-send" in risks and route == "workflow" else []

    if route in ("lookup", "setup", "memory", "outside"):
        confidence = "clear"
    elif top[0] is None:
        confidence = "unclear"
    elif top[1] - second[1] >= CLEAR_MARGIN:
        confidence = "clear"
    else:
        confidence = "close"

    if route == "memory":
        reference = "references/memory.md"
    elif route == "lookup":
        reference = "references/grounding.md"
    elif route == "setup":
        if "python" in systems:
            reference = "references/setup-python.md"
        elif "obsidian" in systems:
            reference = "references/setup-visualize.md"
        elif set(systems) & AI_TOOL_SYSTEMS:
            # this plugin in an AI tool, or a server connected to one
            reference = "references/setup-ai-tools.md"
        elif set(systems) & (WORKSTATION_SYSTEMS | INFRA_SYSTEMS | GIT_HOSTS) or template in SETUP_TEMPLATES:
            reference = "references/setup-workstation.md"
        else:
            reference = "references/setup-ai-tools.md"
    elif route == "workflow" and template in TEMPLATE_REFERENCES and \
            REFERENCE_ONLY_FOR.get(template, archetype) == archetype:
        reference = TEMPLATE_REFERENCES[template]
    elif route == "workflow" and archetype:
        reference = reference_for(archetype)
    else:
        reference = ""

    if route in ("lookup", "memory", "outside"):
        ceremony = "light"
    elif set(risks) & HIGH_STAKES_RISK or set(audience) & HIGH_STAKES_AUDIENCE:
        ceremony = "full"
    elif route == "setup":
        ceremony = "light"
    else:
        ceremony = "standard"

    tpl_path = TEMPLATES / f"{template}.md" if template else None
    mine = PERSONAL_TEMPLATES / f"{template}.md" if template and PERSONAL_TEMPLATES else None
    chain = NEXT_STEPS.get(archetype or "", [])
    if route == "workflow" and "legal-advice" in risks:
        # a legal question ends with Legal, not with the next workflow in the chain
        next_steps = [{"archetype": "", "name": "Legal",
                       "why": "hand them the summary and the open questions, since only Legal concludes"}]
    elif route == "workflow" and chain:
        next_steps = [{"archetype": a, "name": archetype_name(a), "why": w} for a, w in chain]
    else:
        next_steps = []
    next_step = next_steps[0] if next_steps else None
    asked_style = sorted({m["value"] for m in hits["style"] if m["value"] in STYLE_PROFILES})
    offer_style = sorted(name for name, prof in STYLE_PROFILES.items()
                         if route == "workflow" and template in prof["templates"] and name not in asked_style)
    return {
        "route": route,
        "memory_kind": memory_kind,
        "archetype": archetype,
        "archetype_name": archetype_name(archetype) if archetype else "",
        "reference": reference,
        "template": template,
        "template_file": (str(mine) if mine and mine.is_file() else
                          f"assets/templates/{template}.md" if tpl_path and tpl_path.is_file() else ""),
        "ceremony": ceremony,
        "confidence": confidence,
        "score": round(top[1], 2),
        "runner_up": ({"archetype": second[0], "name": archetype_name(second[0]), "score": round(second[1], 2)}
                      if second[0] else None),
        "matched": {
            "nouns": sorted({m["pattern"] for m in kept if m["kind"] == "noun"}),
            "verbs": sorted({m["pattern"] for m in kept if m["kind"] == "verb"}),
            "routes": {k: sorted(set(v)) for k, v in sorted(routes.items())},
            "systems": systems,
            "audience": audience,
            "risk_flags": risks,
            "resolved": resolved,
        },
        "must_ask_first": ask,
        "hints": hints,
        "style": {"asked": asked_style, "offer": offer_style,
                  "reference": next((STYLE_PROFILES[n]["reference"] for n in asked_style + offer_style), "")},
        "next_step": next_step,
        "next_steps": next_steps,
    }


def render(r: dict) -> str:
    out = [f"Route    : {r['route']}  (ceremony: {r['ceremony']})"]
    if r["archetype"]:
        out.append(f"Workflow : {r['archetype']}  {r['archetype_name']}")
    if r["reference"]:
        out.append(f"Read     : {r['reference']}")
    if r["template"]:
        where = r["template_file"] or "no shipped file, use the workflow's own output block"
        out.append(f"Template : {r['template']}  ({where})")
    out.append(f"Certainty: {r['confidence']} (score {r['score']})")
    if r["confidence"] == "close" and r["runner_up"]:
        ru = r["runner_up"]
        out.append(f"           close to {ru['archetype']} {ru['name']} ({ru['score']}). Say which one you picked.")
    m = r["matched"]
    for label, key in (("Nouns", "nouns"), ("Verbs", "verbs"), ("Systems", "systems"),
                       ("Audience", "audience"), ("Risk", "risk_flags")):
        if m[key]:
            out.append(f"{label:9}: {', '.join(m[key])}")
    if m["resolved"]:
        out.append("Settled  : " + ", ".join(f"{w} is read as {v}" for w, v in m["resolved"].items())
                   + ". The sentence settles it, so do not ask.")
    if r["route"] == "outside":
        out.append("\nGeneral coding or personal writing, with no work deliverable. Answer it normally "
                   "without this skill's pipeline.")
    if r["route"] == "unclear":
        out.append("\nNo clear match. Offer the jobs that fit what you can tell about their work.")
    if "stated-cause" in m["risk_flags"]:
        out.append("\nThe request states a cause. Keep it labelled unverified in anything you write.")
    for hint in r.get("hints") or []:
        out.append(f"\nHint: {hint}")
    style = r.get("style") or {}
    if style.get("asked"):
        out.append(f"\nStyle    : they asked for {', '.join(style['asked'])}. Read {style['reference']}, and check "
                   f"with --profile {style['asked'][0]}.")
    elif style.get("offer"):
        out.append(f"\nStyle    : a write-up. Unless prefs.style is set, offer the {style['offer'][0]} style once, "
                   f"as an optional question in the same round. See {style['reference']}.")
    if r["must_ask_first"]:
        out.append("\nAsk this before anything else:")
        for q in r["must_ask_first"]:
            src = q.get("source", "")
            where = ("  (from your glossary)" if src == "yours" else
                     f"  (from the {src.split(':', 1)[-1]} playbook glossary)" if src else "")
            out.append(f"  - {q['ask']}{where}")
    if r.get("memory_kind"):
        out.append(f"Kind     : {r['memory_kind']}  (name it back to them before writing anything)")
    if r.get("next_steps"):
        out.append("")
        for i, step in enumerate(r["next_steps"]):
            who = " ".join(x for x in (step["archetype"], step["name"]) if x)
            label = "Offer next" if i == 0 else "         or"
            out.append(f"{label}: {who}, to {step['why']}.")
    return "\n".join(out)


def main(argv=None) -> int:
    _utf8_console()
    p = argparse.ArgumentParser(prog="classify.py", description="Work out which route a request needs.")
    p.add_argument("request", help="the user's words, or - to read standard input")
    p.add_argument("--explain", action="store_true", help="readable output instead of JSON")
    p.add_argument("--json", action="store_true", help="JSON output, which is also the default")
    p.add_argument("--table", help="use a different router table instead of the shipped one")
    p.add_argument("--root", help="knowledge base folder, for your own router rows and glossary "
                                  "(default: ~/.flareware/flarehand)")
    p.add_argument("--no-glossary", action="store_true",
                   help="ignore saved glossaries, yours and your team's, for this run")
    args = p.parse_args(argv)

    text = sys.stdin.read() if args.request == "-" else args.request
    if not text.strip():
        print("error: empty request", file=sys.stderr)
        return 2
    if args.table:
        rows = load_table(Path(args.table))
    else:
        mine, root = None, None
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from kb import resolve_root  # noqa: E402
            root = resolve_root(args.root)
            load_personal_workflows(root)
            mine = personal_table(root)
        except Exception:
            mine = None
        glossary = [] if args.no_glossary else read_glossary(root)
        rows = load_table(TABLE, mine, glossary)
    result = classify(text, rows)
    print(render(result) if args.explain else json.dumps(result, indent=2))
    return 1 if (result["must_ask_first"] or result["route"] == "unclear") else 0


if __name__ == "__main__":
    sys.exit(main())
