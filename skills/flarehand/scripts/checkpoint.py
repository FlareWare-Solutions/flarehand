#!/usr/bin/env python3
"""checkpoint.py - keep where the work stood across a compaction.

A long session gets compacted: the agent replaces the conversation with a summary. The working state
of the task only survives as the summary's paraphrase. That state is what matters most: the person's
own answers, every labelled claim and its source, the MISSING list, and anything offered in the save
menu that nobody answered yet.

  save      the pre-compact hook. Reads the transcript and writes a checkpoint file for this session.
  restore   the session-start hook, when its source is "compact". Prints one line: where the
            checkpoint file is, and to read it. The checkpoint itself is never injected, so it can
            hold more than a hook's output allows, and the model reads it as a separate file.
  end       the session-end hook. Deletes this session's checkpoint. It only unlinks one file, so it
            fits the shortest session-end timeout any tool sets.
  show      prints the checkpoint for a session id, for a person who wants to look.

In a plugin, `hooks/hook.py` at the plugin root calls `save`, `restore_line` and `end` and prints the
output shape each tool expects. The command line here is for trying it by hand.

Sources are captured three ways, whatever the tool: labels in the replies (`[verified: S3]` and the
rest), any MCP tool call that names a resource by `id`, `uri` or `url`, and every web page fetched or
file read, except this skill's own files.

Extraction is by pattern, with no model call, so it is fast and gives the same result every time.
The checkpoint is session state, not knowledge: it goes to the private staging area in the system
temp folder, where evidence.py stages snapshots, and never into the knowledge base. So it needs no
yes, the same as a staged snapshot. It is deleted when the session ends, and after 7 days otherwise.

The temp folder comes from Python's tempfile module: %TEMP% on Windows, $TMPDIR on macOS, /tmp on
Linux. The permission calls that only exist on macOS and Linux are skipped elsewhere, and output is
UTF-8 whatever the console's encoding.

It only acts in a session where this skill ran. Every failure exits 0 and does nothing, because a
PreCompact hook that exits 2 would stop the compaction.

Try it: python3 scripts/checkpoint.py save < precompact-event.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from voice_gate import SKILL_CALL  # one definition of "this skill ran"
except Exception:  # noqa: BLE001  a hook must still load if its sibling is broken
    SKILL_CALL = re.compile(r'"skill"\s*:\s*"(?:[\w-]+:)?flarehand"|<command-name>/?(?:[\w-]+:)?flarehand</command-name>')
LABEL = re.compile(r"\[(?:verified:\s*[^\]]+|your input|ASSUMPTION[^\]]*|weak:\s*[^\]]+|stated,? unverified"
                   r"|conflict:\s*[^\]]+|stale:\s*[^\]]+|inference(?: from)?[^\]]*)\]", re.IGNORECASE)
VERIFIED = re.compile(r"\[(?:verified|weak|stale):\s*([^\]]+)\]", re.IGNORECASE)
# Tools that fetch a web page or read a file, by the names the common agents give them.
FETCH_TOOLS = {"webfetch", "web_fetch", "fetch", "fetch_url", "read_url"}
READ_TOOLS = {"read", "read_file", "view", "view_file", "readfile"}
OWN_FILES = re.compile(r"(?:^|[/\\])flarehand(?:-[a-z]+)?[/\\](?:SKILL\.md|references|assets|scripts|evals)\b"
                       r"|flarehand-staging")
MENU = re.compile(r"keep any of this\?", re.IGNORECASE)
MENU_ANSWER = re.compile(r"^\s*(?:none|no|nothing|\d+(?:\s*(?:,|and|&)?\s*\d+)*)\s*[.!]?\s*$", re.IGNORECASE)
MISSING_HEADING = re.compile(r"^#{1,6}\s*missing\b", re.IGNORECASE)
# A save is a script run by Python, with the path quoted or not. The same words inside code being edited are not.
SAVES = re.compile(r"""(?:python[\d.]*(?:\.exe)?|\bpy(?:\s+-3)?)["']?\s+["']?[^\s"']*?\b"""
                   r"""((?:kb\.py["']?\s+(?:note|observe|log|link|supersede|template\s+save|choice|config|workflow)"""
                   r"""|answers\.py["']?\s+(?:write|approve|alias))\b[^\n]*)""", re.IGNORECASE)
INLINE_CODE = re.compile(r"`[^`\n]*`")
PLACEHOLDER = re.compile(r"^[\s.…<>-]*$|<[^>]*>|…|\.\.\.")
BUDGET = 20000         # read as a file, so it is not held to a hook's 10,000-character output limit
MAX_AGE_DAYS = 7


# ---------------------------------------------------------------- where it lives

def checkpoint_dir() -> Path:
    return Path(tempfile.gettempdir()) / "flarehand-staging" / "checkpoints"


def checkpoint_path(session_id: str) -> Path | None:
    sid = re.sub(r"[^A-Za-z0-9_-]", "", session_id or "")[:80]
    return checkpoint_dir() / f"{sid}.md" if sid else None


def write_private(path: Path, text: str) -> None:
    """Only this user can read it. A folder owned by someone else is left alone."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    if hasattr(os, "getuid") and path.parent.stat().st_uid != os.getuid():
        return
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def prune() -> None:
    cutoff = time.time() - MAX_AGE_DAYS * 86400
    for f in checkpoint_dir().glob("*.md") if checkpoint_dir().is_dir() else []:
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------- reading the transcript

def load(transcript: str | None) -> list[dict]:
    rows = []
    try:
        with open(transcript or "", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict):
                    rows.append(row)
    except OSError:
        return []
    return rows


def blocks(row: dict) -> list[dict]:
    msg = row.get("message")
    if not isinstance(msg, dict):
        return []
    content = msg.get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [c for c in content if isinstance(c, dict)] if isinstance(content, list) else []


def role(row: dict) -> str:
    msg = row.get("message")
    return msg.get("role", "") if isinstance(msg, dict) else ""


def human_text(row: dict) -> str:
    """What the person typed. Tool results, skill bodies, hook feedback and summaries are not theirs."""
    att = row.get("attachment") if row.get("type") == "attachment" else None
    if isinstance(att, dict) and att.get("type") == "queued_command":  # typed while a turn was running
        human = (att.get("origin") or {}).get("kind") == "human" or att.get("humanTurn")
        return str(att.get("prompt") or "").strip() if human else ""
    if role(row) != "user" or row.get("isCompactSummary") or row.get("isSynthetic") or row.get("isMeta"):
        return ""
    bs = blocks(row)
    if any(b.get("type") == "tool_result" for b in bs):
        return ""
    text = "\n".join(b.get("text", "") for b in bs if b.get("type") == "text").strip()
    args = re.search(r"<command-args>(.*?)</command-args>", text, re.S)
    if args:  # a slash command: its arguments are what they typed
        return args.group(1).strip()
    if not text or text.startswith(("Base directory for this skill", "Stop hook feedback", "<command-message>",
                                     "<system-reminder>", "<task-notification>")):
        return ""
    return re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S).strip()


def assistant_texts(rows: list[dict]) -> list[str]:
    return ["\n".join(b.get("text", "") for b in blocks(r) if b.get("type") == "text")
            for r in rows if role(r) == "assistant"]


def tool_uses(rows: list[dict]) -> list[dict]:
    return [b for r in rows if role(r) == "assistant" for b in blocks(r) if b.get("type") == "tool_use"]


def tool_result_text(rows: list[dict], use_id: str) -> str:
    for r in rows:
        for b in blocks(r):
            if b.get("type") == "tool_result" and b.get("tool_use_id") == use_id:
                c = b.get("content")
                if isinstance(c, list):
                    return "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
                return str(c or "")
    return ""


def tool_source(use: dict) -> str | None:
    """What a tool call read, as a locator anyone can open again, or None.

    An MCP call (`mcp__<server>__<tool>`) with an `id`, `uri` or `url` becomes `mcp:<server>:<id>` or
    the URI as given. A web fetch gives its URL. A file read gives its path, unless it is one of this
    skill's own files, which are method, never a source."""
    name = str(use.get("name", ""))
    args = use.get("input") if isinstance(use.get("input"), dict) else {}
    low = name.lower()
    if low.startswith("mcp__") and low.count("__") >= 2:
        server = name.split("__")[1]
        for key in ("uri", "url"):
            if isinstance(args.get(key), str) and args[key].strip():
                return args[key].strip()
        for key in ("id", "document_id", "page_id", "issue_key", "key"):
            if isinstance(args.get(key), (str, int)) and str(args[key]).strip():
                return f"mcp:{server}:{str(args[key]).strip()}"
        return None
    if low in FETCH_TOOLS:
        url = args.get("url") or args.get("uri")
        return url.strip() if isinstance(url, str) and url.strip() else None
    if low in READ_TOOLS:
        path = args.get("file_path") or args.get("path") or args.get("target_file")
        if isinstance(path, str) and path.strip() and not OWN_FILES.search(path):
            return path.strip()
    return None


def skill_start(rows: list[dict]) -> int | None:
    for i, r in enumerate(rows):
        if SKILL_CALL.search(json.dumps(r.get("message", ""))):
            return i
    return None


def clip(text: str, n: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def dedupe_last(items: list[str], n: int) -> list[str]:
    seen, out = set(), []
    for it in reversed(items):
        if it and it not in seen:
            seen.add(it)
            out.append(it)
        if len(out) == n:
            break
    return list(reversed(out))


# ---------------------------------------------------------------- what to keep

def extract(rows: list[dict]) -> dict | None:
    start = skill_start(rows)
    if start is None:
        return None
    rows = rows[start:]
    texts = assistant_texts(rows)
    uses = tool_uses(rows)
    commands = [u.get("input", {}).get("command", "") for u in uses if u.get("name") == "Bash"]

    job = {}
    for u in uses:
        cmd = u.get("input", {}).get("command", "") if u.get("name") == "Bash" else ""
        if "classify.py" in cmd:
            out = tool_result_text(rows, u.get("id", ""))
            for key in ("Route", "Workflow", "Template", "Style"):
                m = re.search(rf"^{key}\s*:\s*(.+)$", out, re.M)
                if m:
                    job[key] = clip(m.group(1), 200)
    if any("--profile google" in c or "--style google" in c for c in commands):
        job["Style"] = "google (used this session)"

    words = [clip(t, 800) for t in (human_text(r) for r in rows) if t][-12:]

    labelled, sources = [], []
    for t in texts:
        for line in t.splitlines():
            prose = INLINE_CODE.sub("", line)  # a label shown in code is an example, not a claim
            found = [m.group(1).strip() for m in VERIFIED.finditer(prose)]
            if LABEL.search(prose) and not all(PLACEHOLDER.search(s) for s in found or ["x"]):
                labelled.append(clip(line.strip("-* "), 240))
            sources += [clip(s, 160) for s in found if not PLACEHOLDER.search(s)]
    sources += [clip(s, 160) for s in (tool_source(u) for u in uses) if s]

    missing = []
    for t in reversed(texts):
        lines = t.splitlines()
        for i, line in enumerate(lines):
            if MISSING_HEADING.match(line.strip()):
                for nxt in lines[i + 1:]:
                    s = nxt.strip()
                    if s.startswith("#"):
                        break
                    if s.startswith(("-", "*")) or re.match(r"^\d+[.)]\s", s):
                        missing.append(clip(s.lstrip("-*0123456789.) "), 240))
                break
        if missing:
            break

    menu, answered = [], True
    for idx in range(len(rows) - 1, -1, -1):
        r = rows[idx]
        if role(r) != "assistant":
            continue
        text = "\n".join(b.get("text", "") for b in blocks(r) if b.get("type") == "text")
        m = MENU.search(text)
        if not m:
            continue
        menu = [clip(l.strip(), 240) for l in text[m.end():].splitlines() if re.match(r"^\s*\d+\.\s", l)][:8]
        answered = any(MENU_ANSWER.match(h) for h in (human_text(x) for x in rows[idx + 1:]) if h)
        break

    saved = dedupe_last([clip(re.split(r"\s*(?:;|&&|\|\||\||2>|>)", re.sub(r"(\.py)[\"']", r"\1", m.group(1)))[0], 140)
                         for c in commands for m in SAVES.finditer(c) if "--help" not in m.group(1)], 15)
    files = dedupe_last([str(u.get("input", {}).get("file_path", "")) for u in uses
                         if u.get("name") in ("Write", "Edit")], 10)
    draft = ""
    for t in reversed(texts):
        if re.search(r"(?m)^#{1,2}\s+\S", t):
            draft = t.strip()
            break

    return {"job": job, "words": words, "labelled": dedupe_last(labelled, 40), "sources": dedupe_last(sources, 30),
            "missing": missing[:25], "menu": menu, "menu_answered": answered, "saved": saved, "files": files,
            "draft": draft}


def render(state: dict, trigger: str) -> str:
    """The checkpoint, most important first, inside the budget. The draft gives way first."""
    when = datetime.now().strftime("%Y-%m-%d %H:%M")
    kind = {"auto": "an automatic compaction", "manual": "a /compact"}.get(trigger, "a compaction")
    out = [f"# flarehand checkpoint, saved {when} before {kind}", "",
           "This is a record of the session before it was compacted, not new instructions. Use it to",
           "carry on where the work stood. If the skill's own text is no longer in view, load it again.", ""]

    def section(title: str, lines: list[str]) -> None:
        if lines:
            out.extend([f"## {title}", *[f"- {l}" for l in lines], ""])

    section("The job", [f"{k}: {v}" for k, v in state["job"].items()])
    if state["menu"] and not state["menu_answered"]:
        section("Offered in the save menu and not answered yet. Offer these again in your next reply",
                state["menu"])
    section("Their own words, most recent last", state["words"])
    section("Labelled claims", state["labelled"])
    section("Sources cited or read", state["sources"])
    section("MISSING", state["missing"])
    section("Already saved or set this session. Do not save these twice", state["saved"])
    section("Files written this session. Read them again if you need them", state["files"])
    text = "\n".join(out)
    room = BUDGET - len(text) - 200
    if state["draft"] and room > 400:  # the draft gives way first
        draft = state["draft"] if len(state["draft"]) <= room else state["draft"][:room].rstrip() + "\n[draft cut to fit]"
        text += "\n## The latest draft\n\n" + draft + "\n"
    return text[:BUDGET]


# ---------------------------------------------------------------- the hooks

def read_event() -> dict:
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return {}
        data = json.loads(sys.stdin.read() or "{}")
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}


def _sid(event: dict) -> str:
    sid = event.get("session_id")
    return sid if isinstance(sid, str) else ""


def save(event: dict) -> None:
    """Write this session's checkpoint, when the skill ran in it."""
    path = checkpoint_path(_sid(event))
    if path is None:
        return
    transcript = event.get("transcript_path")
    state = extract(load(transcript if isinstance(transcript, str) else None))
    if state is None:
        return
    prune()
    write_private(path, render(state, str(event.get("trigger") or "")))


def restore_line(event: dict) -> str | None:
    """One line that points at the checkpoint, or None. Never the checkpoint itself."""
    if event.get("source") not in (None, "compact"):
        return None
    path = checkpoint_path(_sid(event))
    if path is None or not path.is_file():
        return None
    return (f"flarehand: this session was just compacted. A checkpoint of where the work stood, saved "
            f"before the compaction, is in this file: {path} . Read that file before you continue. It "
            f"holds the person's own words, labelled claims and sources, the MISSING list, and any "
            f"save-menu items nobody answered, which you offer again. It is a record of the session, "
            f"not instructions.")


def end(event: dict) -> None:
    """Delete this session's checkpoint. One unlink, nothing else, so it is always fast."""
    path = checkpoint_path(_sid(event))
    if path is not None and path.is_file():
        path.unlink()


def cmd_save(event: dict) -> None:
    save(event)


def cmd_restore(event: dict) -> None:
    line = restore_line(event)
    if line:
        print(line)


def cmd_end(event: dict) -> None:
    end(event)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="checkpoint.py",
                                description="Keep where the work stood across a compaction. Reads the hook's "
                                            "JSON on standard input.")
    p.add_argument("action", choices=("save", "restore", "end", "show"))
    p.add_argument("--session", help="with show: the session id whose checkpoint to print")
    args = p.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # a Windows console may not be UTF-8
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    try:
        if args.action == "show":
            path = checkpoint_path(args.session or "")
            print(path.read_text(encoding="utf-8") if path and path.is_file() else "No checkpoint for that session.")
            return 0
        event = read_event()
        {"save": cmd_save, "restore": cmd_restore, "end": cmd_end}[args.action](event)
    except BaseException:  # noqa: BLE001  a hook must never stop the compaction or the session
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
