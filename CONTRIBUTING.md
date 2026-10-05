# Contributing to flarehand

Thanks for helping. Open an issue before a large change, so we can agree on the shape first.

## Layout

```
.claude-plugin/                plugin.json and marketplace.json, read by Claude Code and most other tools
.codex-plugin/plugin.json      Codex
.agents/plugins/               the Codex marketplace
.cursor-plugin/plugin.json     Cursor
gemini-extension.json          Gemini CLI, with GEMINI.md as its context file
AGENTS.md                      the bootstrap for tools with no hooks. Users read it, so keep it short
hooks/                         hooks.json (Claude format), hooks-cursor.json, run-hook.cmd, hook.py
skills/flarehand/              the router skill: SKILL.md, references, scripts, assets
skills/flarehand-*/            entry points that hand over to the router with a fixed route
tests/                         the unit tests: test_scripts.py runs every tests_*.py beside it
evals/                         the live eval cases for `claude plugin eval`, and consistency.md
tools/bump_version.py          keeps every manifest version in lockstep
docs/                          user documentation
```

## Rules

- **Python 3.9 or later, standard library only.** Every script takes `--help`, never asks a
  question, and exits 0 when fine, 1 when a check fails, 2 on a usage error.
- **No state under the plugin folder.** The knowledge base lives at `~/.flareware/flarehand`. Session
  files go to the system temp folder.
- **Call scripts through Python**, as `python3 scripts/<name>.py`. Never rely on the executable bit.
  The one exception is `hooks/run-hook.cmd`, which Cursor runs directly, so keep it executable in
  git: `git update-index --chmod=+x hooks/run-hook.cmd`.
- **Hooks never block.** `hooks/hook.py` exits 0 whatever happens, and prints one output shape per
  tool. Keep `hooks.json` and `hooks-cursor.json` running the same actions.
- **Portable skill frontmatter only:** `name`, `description`, `license`, `compatibility`,
  `metadata` with string values, and `allowed-tools`. claude.ai refuses an upload with any other
  key. Keep each description under 1,024 characters with its trigger words first, and each
  `SKILL.md` under 500 lines.
- **No PowerShell files, no binaries, no top-level `bin/`, no `.DS_Store`.**
- **Plain voice in every file a person reads.** Short sentences, no em dashes. Check prose with
  `python3 skills/flarehand/scripts/check_output.py --style <file>`.
- **Nothing written without a yes.** A change that saves anything to the knowledge base must go
  through the save menu, or be one of the bookkeeping writes `SKILL.md` lists.

## Tests

Run all of these before you open a pull request:

```bash
python3 tests/test_scripts.py                          # every unit test, about four minutes
python3 skills/flarehand/scripts/validate_skill.py     # every skill, manifest and hook
claude plugin validate .                               # Claude Code's own check, if you have it
python3 skills/flarehand/scripts/package.py --check    # will it package
```

A new test file goes in `tests/` as `tests_<area>.py`. It must define
`unittest.TestCase` classes and end with an `if __name__ == "__main__":` block, or the suite skips it.

Live evals run the skill against a model with `claude plugin eval`. Each case is a folder in
`evals/`. Read `evals/consistency.md` first. Nothing under `tests/` or `evals/` ships in a skill
archive, and the plugin build copies only the eval cases.

## Versioning

Versions follow semantic versioning. The version lives in every tool's manifest and in each skill's
`flarehand.version` metadata, and `.version-bump.json` lists them all. Never edit one by hand:

```bash
python3 tools/bump_version.py check
python3 tools/bump_version.py bump minor
```

Then add the release to `CHANGELOG.md`, and tag it `v<version>`.
