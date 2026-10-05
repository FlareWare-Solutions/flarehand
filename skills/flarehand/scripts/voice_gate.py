#!/usr/bin/env python3
"""voice_gate.py - hooks that keep this skill's house voice in chat replies.

The house voice bans em dashes (references/voice.md). A model can follow that rule in a file and
forget it in chat, because nothing checks a reply that never becomes a file. These two hooks make
the rule hold in tools that run plugin hooks. `hooks/hook.py` at the plugin root calls the
functions here and prints the output shape each tool expects. This file holds the logic and a
small command line for trying it by hand.

Two modes, both inert until this skill has run in the session:

  --remind   a prompt-submit hook, on by default. Prints one line of context before each later
             turn: the house voice, no em dashes. It costs a few tokens and changes nothing the
             person sees.
  (default)  a stop hook, off by default. It holds a reply with an em dash in its prose and asks
             once for a rewrite. The person sees the reply twice, and the retry can hurt quality,
             so it runs only for someone who asked: `kb.py config --voice-gate on`.

"This skill ran" means the transcript shows the flarehand skill, or one of its entry points, called
as a skill, as a slash command, or read as a file. The transcript is scanned once: the byte offset
reached is cached in the system temp folder, so a later prompt reads only the new lines.

Both look at prose only, with code, inline code, URLs and HTML masked first. The stop hook lets the
retry through, so it can never loop. Any error, missing field or unreadable file means it does
nothing. Exit code is always 0.

Try it: python3 scripts/voice_gate.py --remind < prompt-event.json
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

SKILL_NAMES = r"flarehand(?:-(?:remember|ground|grill|review))?"
# Called as a skill, typed as a slash command (with or without a plugin prefix), or read as a file.
SKILL_CALL = re.compile(
    r'"skill"\s*:\s*"(?:[\w-]+:)?' + SKILL_NAMES + r'"'
    r"|<command-name>/?(?:[\w-]+:)?" + SKILL_NAMES + r"</command-name>"
    r'|"(?:file_path|path)"\s*:\s*"[^"]*' + SKILL_NAMES + r'[/\\]+SKILL\.md"')
EM_DASH = "—"
EN_DASH = "–"
SPACED_EN_DASH = re.compile(r"\s–\s")
TAIL_BYTES = 256 * 1024
STATE_MAX_AGE_DAYS = 7


# ---------------------------------------------------------------- did the skill run

def state_dir() -> Path:
    return Path(tempfile.gettempdir()) / "flarehand-staging" / "hooks"


def _state_path(transcript: str) -> Path:
    key = hashlib.sha256(os.path.abspath(transcript).encode("utf-8", "replace")).hexdigest()[:32]
    return state_dir() / f"{key}.json"


def _read_state(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_state(path: Path, state: dict) -> None:
    """Private to this user, and best effort: a failed write only means the next scan starts over."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(path.parent, 0o700)
        except OSError:
            pass
        tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        os.replace(tmp, path)
    except OSError:
        pass


def _prune_states() -> None:
    cutoff = time.time() - STATE_MAX_AGE_DAYS * 86400
    try:
        for f in state_dir().glob("*.json"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
    except OSError:
        pass


def skill_ran(transcript) -> bool:
    """True when the transcript shows this skill ran. Reads only what was added since the last call."""
    if not transcript or not isinstance(transcript, str):
        return False
    try:
        size = os.path.getsize(transcript)
    except OSError:
        return False
    path = _state_path(transcript)
    state = _read_state(path)
    if state.get("ran") is True:
        return True
    offset = state.get("offset", 0)
    if not isinstance(offset, int) or offset < 0 or offset > size:
        offset = 0  # a shorter file is a different file
    found = False
    reached = offset
    try:
        with open(transcript, "rb") as fh:
            fh.seek(offset)
            for raw in fh:
                if SKILL_CALL.search(raw.decode("utf-8", "replace")):
                    found = True
                    break
                if raw.endswith(b"\n"):  # a half-written last line is read again next time
                    reached += len(raw)
    except OSError:
        return False
    if offset == 0:
        _prune_states()
    _write_state(path, {"ran": found, "offset": reached, "transcript": os.path.abspath(transcript)})
    return found


# ---------------------------------------------------------------- the reply

def _tail_lines(path: str) -> list[str]:
    """The last whole lines of a file, never more than TAIL_BYTES of it."""
    with open(path, "rb") as fh:
        fh.seek(0, os.SEEK_END)
        size = fh.tell()
        start = max(0, size - TAIL_BYTES)
        fh.seek(start)
        data = fh.read()
    lines = data.decode("utf-8", "replace").splitlines()
    return lines[1:] if start > 0 else lines


def last_reply(data: dict) -> str:
    """The reply text. Newer hosts pass it directly; otherwise read the end of the transcript."""
    text = data.get("last_assistant_message")
    if isinstance(text, str) and text:
        return text
    path = data.get("transcript_path")
    if not path or not isinstance(path, str):
        return ""
    try:
        lines = _tail_lines(path)
    except OSError:
        return ""
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        msg = entry.get("message") if isinstance(entry, dict) else None
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
            if any(parts):
                return "\n".join(parts)
    return ""


def gate_is_on() -> bool:
    """Only for someone who turned it on. Everyone else gets the reminder instead."""
    try:
        from kb import read_prefs, resolve_root  # noqa: E402
        root = resolve_root(None)
        return root is not None and read_prefs(root).get("voice_gate") is True
    except Exception:
        return False


REMINDER = ("flarehand is active in this session. Write the reply in its house voice: plain words, short "
            "sentences, and no em dashes. Put the artifact itself in the reply, and end a workflow reply with "
            "the save menu.")


def remind(data: dict) -> str | None:
    """The context line for a prompt-submit hook, or None outside a session where the skill ran."""
    return REMINDER if skill_ran(data.get("transcript_path")) else None


def dashes_in_prose(text: str) -> int:
    try:
        from check_output import mask  # noqa: E402
        lines = mask(text)
    except Exception:
        lines = text.split("\n")
    return sum(ln.count(EM_DASH) + len(SPACED_EN_DASH.findall(ln)) for ln in lines)


def block_reason(n: int) -> str:
    return (f"flarehand house voice: your last reply has {n} em dash{'es' if n > 1 else ''} in its prose "
            "(references/voice.md). Send the same reply again with each one replaced by a period, a comma, "
            "a colon or brackets. Keep every fact, and do not mention this check.")


def decide(data: dict) -> dict | None:
    """The block decision, or None to let the reply through."""
    if data.get("stop_hook_active"):
        return None
    reply = last_reply(data)
    if EM_DASH not in reply and EN_DASH not in reply:
        return None
    if not skill_ran(data.get("transcript_path")):
        return None
    n = dashes_in_prose(reply)
    if not n or not gate_is_on():
        return None
    return {"decision": "block", "reason": block_reason(n)}


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(
        prog="voice_gate.py",
        description="House-voice hooks. Reads the hook's JSON on standard input. In a plugin, "
                    "hooks/hook.py calls this logic. Try it: python3 scripts/voice_gate.py < stop-event.json",
    )
    p.add_argument("--remind", action="store_true",
                   help="prompt-submit mode: print one line of house-voice context once this skill has run")
    args = p.parse_args(argv)
    try:
        data = {} if sys.stdin is None or sys.stdin.isatty() else json.loads(sys.stdin.read() or "{}")
        data = data if isinstance(data, dict) else {}
        if args.remind:
            line = remind(data)
            if line:
                print(line)
            return 0
        result = decide(data)
    except Exception:
        return 0
    if result:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
