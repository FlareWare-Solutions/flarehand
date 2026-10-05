---
name: flarehand-review
description: "Review code, a pull request, a diff, a document or a plan, and say what is wrong with it. Use when someone says review this, look over my PR, review my pull request, check this diff before I merge, what's wrong with this plan, what's wrong with this doc, critique this, is this ready to ship, or do a security review. Checks it lens by lens, such as correctness, regressions, completeness, code quality and house rules, has a second pass confirm each finding, and grades each lens pass, concerns or fail, with the location, severity and fix for every finding. Part of flarehand. Not for writing new code, or for fact-checking a reply before it is sent."
license: MIT
compatibility: "Needs the flarehand skill installed beside it, and Python 3 for the grading script. Subagents make the finder and checker separate; without them the checker is a fresh prompt."
metadata:
  flarehand.owner: "FlareWare Solutions"
  flarehand.version: "1.0.0"
---

# flarehand-review

An entry point. The `flarehand` skill does the work, with the review as the route. This file fixes
the route so the review starts at once.

1. **Load the `flarehand` skill** and keep its standing rules for the whole session. Installed as
   files, it sits beside this one at `../flarehand/SKILL.md`. Every path below is relative to this
   skill's folder.
2. **Read the method.** `../flarehand/references/review-code.md` covers code, a PR, a branch, or a
   whole repository. For a document or a plan, also read `../flarehand/references/wf-10-critique.md`.
3. **List the lenses.** Run `python3 ../flarehand/scripts/review.py lenses`. Use every lens the
   person named, and the ones that fit when they named none.
4. **Load the rules.** `python3 ../flarehand/scripts/review.py rules` prints the house rules from
   every layer. Every review checks against them.
5. **Brief each finder.** `python3 ../flarehand/scripts/review.py brief <lens>` gives one reviewer
   its brief. Walk the history where it helps: `git log -S`, `git log -L` and `git blame`.
6. **Check every finding.** A different agent, or a fresh prompt, confirms each one against the code
   or the text. The checker gets the finding, not the reasoning behind it. Anything nobody checked
   is reported as unchecked.
7. **Grade it.** Put the findings through `python3 ../flarehand/scripts/review.py grade`. Show its
   table, one row per lens, and give each finding its location, its severity, the fix, and whether
   it is confirmed or only plausible.

On Windows, use `py -3` in place of `python3`. With no shell, the grade rule is under "Without a
shell" in `../flarehand/references/cross-tool.md`.
