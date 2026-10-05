# flarehand

These lines are for the agent working with the person. They make flarehand work in tools that do
not run its hooks.

- For a work request, load the matching flarehand skill first and follow it:
  - `flarehand-ground` to check a draft, its facts or numbers before it goes out.
  - `flarehand-review` to review code, a PR, a document or a plan.
  - `flarehand-remember` to save, recall or forget.
  - `flarehand-grill` to stress-test a plan or a vague ask.
  - Otherwise `flarehand`, for any other work: a deliverable, a reply, a plan, a diagnosis, or a question about a customer, contract, policy or process.

  For anything else, answer normally.
- If your tool has no skill loader, read `skills/flarehand/SKILL.md` in this folder and follow it.
  Paths in it are relative to `skills/flarehand/`.
- Your tool may not run the session-start hook, so do its job by hand. Re-read the "Standing
  rules" section of `skills/flarehand/SKILL.md` at the start of a session. Read it again after your
  tool compacts or summarises the conversation.
- The four entry points hand over to `flarehand` with a fixed route, so all five share one set of
  rules.
- Run scripts with Python 3, as `python3 scripts/<name>.py` from the skill folder. On Windows try
  `py -3`, then `python`. Never rely on a script being executable.
