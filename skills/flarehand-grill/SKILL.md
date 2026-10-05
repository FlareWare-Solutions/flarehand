---
name: flarehand-grill
description: "Stress-test a plan, a design or a vague ask with sharp questions before any work starts. Use when someone says grill me, poke holes in this, stress-test this plan, help me think this through, what am I missing, ask me questions first, or interview me about this. Asks every open question in one round, each with a recommended answer so 'just go' always works, looks facts up instead of asking for them, and ends with a short brief of decisions, assumptions and open questions. Part of flarehand. Not for a question that is already clear."
license: MIT
compatibility: "Needs the flarehand skill installed beside it. Works in any agent. A local shell and Python 3 add the request classifier and the person's saved templates."
metadata:
  flarehand.owner: "Flareware"
  flarehand.version: "0.1.0"
---

# flarehand-grill

An entry point. The `flarehand` skill does the work, with the interview as the route. This file
fixes the route so the questions come first.

1. **Load the `flarehand` skill** and keep its standing rules for the whole session. Installed as
   files, it sits beside this one at `../flarehand/SKILL.md`. Every path below is relative to this
   skill's folder.
2. **Read the method.** `../flarehand/references/interview.md` says how to build the decision tree,
   how to write a question, and when to stop.
3. **Name what they are deciding.** Run
   `python3 ../flarehand/scripts/classify.py "<their words>" --explain`. It names the artifact or
   plan, the ceremony level, and any question to ask before anything else.
4. **Look before you ask.** Finding facts is your job, never theirs. Search their notes with
   `python3 ../flarehand/scripts/kb.py search "<their words>"`, and read the repository, the files
   and the sources you can reach. Ask only what no tool can answer.
5. **Ask in rounds.** Put every question that is ready into one message, each with your
   recommended answer and the reason in one clause. Accept "just go" at any point, and write down
   each default you took.
6. **Poke holes in a plan.** When they brought a plan, also follow
   `../flarehand/references/wf-10-critique.md`.
7. **Close with a brief.** The decisions made, the assumptions taken, the questions still open and
   who can answer each. Then offer the save menu from `../flarehand/SKILL.md`.

The interview style follows `grill-me` by Matt Pocock, MIT licensed, at
https://github.com/mattpocock/skills. On Windows, use `py -3` in place of `python3`.
