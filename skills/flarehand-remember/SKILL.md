---
name: flarehand-remember
description: "Remember, save, recall or forget the person's own notes and answers. Use when someone says remember this, save this, note that, what did we decide about X, what do I know about X, find my notes on X, forget that, undo that save, log this, or what have you learned about me. Saves only after a yes, into a private knowledge base at ~/.flareware/flarehand with an undo for every write, and replays a saved answer word for word. Part of flarehand. Not for general questions with no saved context."
license: MIT
compatibility: "Needs the flarehand skill installed beside it, and Python 3 with a local shell for the knowledge base. Without a shell it gives the method and saves nothing."
metadata:
  flarehand.owner: "FlareWare Solutions"
  flarehand.version: "1.0.0"
---

# flarehand-remember

An entry point. The `flarehand` skill does the work, on its memory route. This file fixes the route
so nothing has to be classified first.

1. **Load the `flarehand` skill** and keep its standing rules for the whole session. Installed as
   files, it sits beside this one at `../flarehand/SKILL.md`. Every path below is relative to this
   skill's folder.
2. **No knowledge base yet?** If `~/.flareware/flarehand/config.json` does not exist, follow the
   First run section of `../flarehand/SKILL.md` before anything else.
3. **The route is memory.** Read `../flarehand/references/memory.md`. It says what is worth keeping
   and which kind of save fits.
4. **Recall before anything else.** Run
   `python3 ../flarehand/scripts/recall.py "<their words>" --explain`. On `replay`, print the saved
   answer word for word and stop. On `confirm`, show the saved question and ask. Never replay on a
   guess.
5. **Then search their notes.** Run `python3 ../flarehand/scripts/kb.py search "<their words>"`, and
   expand a hit with `python3 ../flarehand/scripts/kb.py neighbors <permalink>`. Say when each note
   was last checked.
6. **Save only on a yes.** Offer the save menu from step 9 of `../flarehand/SKILL.md`. On a yes, run
   the command for each line they chose, such as `python3 ../flarehand/scripts/kb.py note`, or
   `kb.py glossary add` for a term and `kb.py rule add` for a house rule. Pass on the undo line each
   command prints.
7. **What it has learned.** `python3 ../flarehand/scripts/kb.py about-me` lists every preference,
   its layer and the command that undoes it. `kb.py log undo` removes the newest work-log line.

On Windows, use `py -3` in place of `python3`. With no shell at all, follow "Without a shell" in
`../flarehand/references/cross-tool.md` and say plainly that nothing was saved.
