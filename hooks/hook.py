#!/usr/bin/env python3
"""hook.py - the one hook dispatcher for the flarehand plugin.

Every hook in hooks/hooks.json (Claude format, also read by Codex, Copilot and others) and
hooks/hooks-cursor.json (Cursor) runs `run-hook.cmd <action>`, which starts this file with Python.

  session-start   the nudge to use the skill for work requests. After a compaction, also one line
                  that points at the checkpoint saved before it.
  prompt-submit   the house-voice reminder, only once the skill ran this session.
  stop            the em-dash gate. Off unless the person ran `kb.py config --voice-gate on`.
  pre-compact     saves the checkpoint to the system temp folder.
  session-end     deletes this session's checkpoint. One unlink, so it fits a short timeout.

It reads the event JSON on standard input, works out which tool is running it, and prints exactly
one output shape for that tool, because Claude Code reads every shape it knows without
de-duplicating:

  Cursor (CURSOR_PLUGIN_ROOT set)   {"additional_context": "..."}
  Copilot CLI (COPILOT_CLI set)     {"additionalContext": "..."}
  everything else                   {"hookSpecificOutput": {"hookEventName": ..., "additionalContext": ...}}

The logic lives in skills/flarehand/scripts/checkpoint.py and voice_gate.py. This file only does the
input and output for each tool. It never writes under the plugin folder, never blocks, never asks,
and always exits 0, whatever it is given.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# No __pycache__ under the plugin folder: it may be read-only, and it holds no state of ours.
sys.dont_write_bytecode = True

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PLUGIN_ROOT / "skills" / "flarehand" / "scripts"

ACTIONS = ("session-start", "prompt-submit", "stop", "pre-compact", "session-end")
# The Claude-format event name each action answers, for hookSpecificOutput.hookEventName.
EVENT_NAMES = {"session-start": "SessionStart", "prompt-submit": "UserPromptSubmit", "stop": "Stop",
               "pre-compact": "PreCompact", "session-end": "SessionEnd"}

# Paid in every session, so it stays short. It names the entry point that fits, because a bare
# "use flarehand" sends a fact-check or a review to the router instead.
ROUTES = (("flarehand-ground", "to check a draft, its facts or numbers before it goes out"),
          ("flarehand-review", "to review code, a PR, a document or a plan"),
          ("flarehand-remember", "to save, recall or forget"),
          ("flarehand-grill", "to stress-test a plan or a vague ask"))
NUDGE = ("flarehand is installed. For a work request, invoke the matching skill: "
         + "; ".join(f"{name} {job}" for name, job in ROUTES)
         + "; otherwise flarehand for any other work: a deliverable, a reply, a plan, a diagnosis, or a question about a customer, contract, policy or process. "
         "For anything else, answer normally.")


def detect_host(env=None) -> str:
    """Which output shape to print. One per host, never two."""
    env = os.environ if env is None else env
    if env.get("CURSOR_PLUGIN_ROOT"):
        return "cursor"
    if env.get("COPILOT_CLI"):
        return "copilot"
    if env.get("CODEX_HOME") or env.get("CODEX_PLUGIN_ROOT") or env.get("CODEX_SANDBOX"):
        return "codex"
    return "claude"


def normalise(data) -> dict:
    """The fields the scripts read, whichever spelling the host used."""
    if not isinstance(data, dict):
        return {}
    out = dict(data)
    for key, alts in (("session_id", ("sessionId", "conversation_id", "conversationId")),
                      ("transcript_path", ("transcriptPath",)),
                      ("source", ("trigger_source",)),
                      ("stop_hook_active", ("stopHookActive",))):
        if out.get(key) in (None, ""):
            for alt in alts:
                if out.get(alt) not in (None, ""):
                    out[key] = out[alt]
                    break
    for key in ("session_id", "transcript_path"):
        if out.get(key) is not None and not isinstance(out.get(key), str):
            out[key] = str(out[key]) if isinstance(out[key], (int, float)) else None
    return out


def context(host: str, action: str, text: str) -> dict:
    if host == "cursor":
        return {"additional_context": text}
    if host == "copilot":
        return {"additionalContext": text}
    return {"hookSpecificOutput": {"hookEventName": EVENT_NAMES[action], "additionalContext": text}}


def _scripts():
    if not SCRIPTS.is_dir():
        return None, None
    sys.path.insert(0, str(SCRIPTS))
    import checkpoint  # noqa: E402
    import voice_gate  # noqa: E402
    return checkpoint, voice_gate


def dispatch(action: str, data: dict, host: str) -> dict | None:
    """The JSON to print, or None for nothing."""
    checkpoint, voice_gate = _scripts()
    if action == "session-start":
        lines = [NUDGE]
        if checkpoint is not None:
            line = checkpoint.restore_line(data)
            if line:
                lines.append(line)
        return context(host, action, "\n".join(lines))
    if checkpoint is None:
        return None
    if action == "prompt-submit":
        line = voice_gate.remind(data)
        return context(host, action, line) if line else None
    if action == "stop":
        if host in ("cursor", "copilot"):
            return None  # the gate uses the Claude-format block decision only
        return voice_gate.decide(data)
    if action == "pre-compact":
        checkpoint.save(data)
        return None
    if action == "session-end":
        checkpoint.end(data)
        return None
    return None


def read_stdin() -> dict:
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return {}
        raw = sys.stdin.buffer.read() if hasattr(sys.stdin, "buffer") else sys.stdin.read().encode("utf-8")
        data = json.loads(raw.decode("utf-8", "replace") or "{}")
    except (ValueError, OSError, AttributeError):
        return {}
    return data if isinstance(data, dict) else {}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        if not argv or argv[0] in ("-h", "--help"):
            print(f"usage: hook.py <{'|'.join(ACTIONS)}>  (reads the hook event JSON on standard input)")
            return 0
        action = argv[0]
        if action not in ACTIONS:
            return 0
        host = detect_host()
        data = normalise(read_stdin())
        out = dispatch(action, data, host)
        if out:
            payload = json.dumps(out, ensure_ascii=False)
            stream = getattr(sys.stdout, "buffer", None)
            if stream is not None:
                stream.write(payload.encode("utf-8") + b"\n")
                stream.flush()
            else:
                print(payload)
    except BaseException:  # noqa: BLE001  a hook must never stop the agent, a compaction or a session
        return 0
    return 0


if __name__ == "__main__":
    code = main()
    try:
        sys.stdout.flush()
    except BaseException:  # noqa: BLE001
        pass
    sys.exit(code)
