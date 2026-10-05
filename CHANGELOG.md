# Changelog

All notable changes to flarehand are listed here. Versions follow semantic versioning.

## 0.1.0 (unreleased)

First public version.

- One router skill, `flarehand`, and four entry points: `flarehand-remember`, `flarehand-ground`,
  `flarehand-grill` and `flarehand-review`.
- A grounding protocol with a claim ledger, deterministic checks and an independent checker.
- A private knowledge base at `~/.flareware/flarehand`, with team playbooks in `.flarehand/`.
- One repository installs in Claude Code, Codex, Cursor, Gemini CLI, Copilot and any tool that
  reads Agent Skills.
- One hook dispatcher for every tool, which always exits 0 and keeps no state in the plugin folder.
- `check.py`: every check on a draft in one command, printing `PASS` or a numbered fix list.
- A learning loop that notices repeated changes and asks before keeping them, and a first run
  that does the work before asking anything.
- 60 templates in ten groups, and 12 workflows.
- 37 live eval cases for `claude plugin eval`, and over 800 unit tests.
- User documentation in `docs/`, and the flarehand mark in `assets/brand/`.
