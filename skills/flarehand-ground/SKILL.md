---
name: flarehand-ground
description: "Check a reply, draft or claim before it goes out: are the facts and numbers right. Use when someone says check this before I send it, are the numbers right, is this accurate, is this correct, fact-check this, does this add up, can I send this, verify these claims, check my sources, or where did that come from. Finds every specific (numbers, dates, names, versions, links), checks each against a real source or the person's own words, and marks it confirmed, weak, out of date, in conflict or unconfirmed, with the fix. Part of flarehand. Not for writing a first draft, or for reviewing code."
license: MIT
compatibility: "Needs the flarehand skill installed beside it. Best with a local shell and Python 3. Without web access it grounds in files, git, MCP servers and what the person pastes, and marks the rest as assumptions."
metadata:
  flarehand.owner: "FlareWare Solutions"
  flarehand.version: "1.0.0"
---

# flarehand-ground

An entry point. The `flarehand` skill does the work, with the grounding protocol as the route.
This file fixes the route so the check starts at once.

1. **Load the `flarehand` skill** and keep its standing rules for the whole session. Installed as
   files, it sits beside this one at `../flarehand/SKILL.md`. Every path below is relative to this
   skill's folder.
2. **Read the protocol.** `../flarehand/references/grounding.md` has the steps, the labels, the
   source tiers and the freshness classes.
3. **Lint the draft first.** Put the draft on standard input:
   `python3 ../flarehand/scripts/ground.py lint -`. It lists every specific with no label and every
   label with no ledger entry. That list is the work.
4. **Know your tools.** `python3 ../flarehand/scripts/doctor.py --capabilities` says whether this
   session has web search, a raw fetch, git and MCP servers.
5. **Gather evidence as raw snapshots.** Fetch only a URL that appeared in a tool result or in their
   words, with `python3 ../flarehand/scripts/ground.py fetch <url>`. Stage a file, a git show or a
   paste with `python3 ../flarehand/scripts/evidence.py add`. A summarising fetch tool never makes a
   claim `verified`.
6. **Quote, then check.** Copy word-for-word quotes into the claim ledger, one source at a time, and
   run `ground.py lint` again until it passes. A pinned source is re-checked with
   `python3 ../flarehand/scripts/ground.py pins check`.
7. **An independent checker.** A fresh subagent, or a fresh prompt where there are none, sees only
   the claim, the quote and the snapshot, and answers `SUPPORTED`, `PARTIAL`, `NOT_SUPPORTED` or
   `CONTRADICTED`. The checker is never the finder.
8. **Render.** Inline labels, a Sources list with tier and dates, and the open questions. Anything
   going outbound goes through `python3 ../flarehand/scripts/redact.py <file>` first.

"I could not confirm this" is a good answer. On Windows, use `py -3` in place of `python3`. With no
shell, follow "Without a shell" in `../flarehand/references/cross-tool.md`.
