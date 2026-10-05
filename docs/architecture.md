# Architecture

This page describes how the flarehand repository is put together, where state lives, and the design principles every change has to keep.

## Repository layout

One repository is the plugin, the Claude marketplace and the install source for every other tool.

```text
.claude-plugin/
  plugin.json             the plugin manifest: Claude Code, Cowork; also read by Copilot, Codex and others
  marketplace.json        the "flareware" marketplace, with one plugin, flarehand
.codex-plugin/plugin.json Codex: skills, hooks and its plugin browser listing
.agents/plugins/          the Codex marketplace
.cursor-plugin/plugin.json Cursor: skills and hooks-cursor.json
gemini-extension.json     Gemini CLI, which loads GEMINI.md as context
AGENTS.md                 the bootstrap for tools with no hooks
GEMINI.md                 the bootstrap for Gemini CLI
hooks/
  hooks.json              Claude-format hooks, also read by Codex and Copilot
  hooks-cursor.json       Cursor-format hooks, the same five actions
  run-hook.cmd            one launcher that runs under both cmd.exe and a POSIX shell
  hook.py                 one dispatcher for every tool
skills/
  flarehand/              the router skill
  flarehand-ground/       entry point: check a draft before it goes out
  flarehand-review/       entry point: graded review
  flarehand-remember/     entry point: save, recall, forget
  flarehand-grill/        entry point: questions before any work
docs/                     these pages, and template-catalog.tsv
tools/
  bump_version.py         keeps every manifest version in step
  release_check.py        checks tracked files before a release
CHANGELOG.md, CONTRIBUTING.md, LICENSE, README.md
```

Inside the router skill:

```text
skills/flarehand/
  SKILL.md        the router: four rules, the standing rules, the nine-step pipeline, first run
  references/     one file per workflow, plus grounding, sources, memory, privacy, setup and more
  scripts/        Python 3, standard library only
  assets/         the lookup tables and the 72 templates (60 artifacts plus 12 workflow shapes)
  evals/          the unit tests and the live eval cases
```

## The five skills

| Skill | Role |
|---|---|
| `flarehand` | The router and pipeline. Any work request. |
| `flarehand-ground` | Fixes the route to the grounding protocol: lint the draft, gather snapshots, quote, check, independent checker, render. |
| `flarehand-review` | Fixes the route to the review: lenses, house rules, a finder per lens, a separate checker, `review.py grade`. |
| `flarehand-remember` | Fixes the route to memory: recall first, then search notes, save only on a yes. |
| `flarehand-grill` | Fixes the route to the interview: every open question in one round, each with a recommended answer, then a brief. |

**One brain.** Each entry point is a short file that loads `flarehand` and keeps its standing rules for the whole session. All five share one set of rules, one set of scripts and one knowledge base. The names carry a prefix because skills-only installers have no namespace, and `remember` or `review` would collide with other skills.

`SKILL.md` is a router, not a manual. It decides what kind of help someone needs and sends the agent to the one reference file that covers it. A long session may be compacted, and an agent may keep only the start of `SKILL.md` afterwards. So the standing rules sit near the top, within the first 15,000 characters, and a test checks that.

## Scripts

| Script | Job |
|---|---|
| `doctor.py` | What this machine and tool can do. Read only. |
| `classify.py` | The route, workflow, template, ceremony and risk flags for a request |
| `sources.py` | Which kinds of source to try first, for this person and question |
| `ground.py` | The grounding protocol: raw fetch, the claim ledger, checks, checker briefs, pins |
| `check.py` | Every check on a draft in one command: `PASS` or a fix list |
| `check_output.py` | Style, citations and required sections |
| `evidence.py` | Snapshots: stage, keep, compare, verify |
| `recall.py` | Whether a question was already answered, and whether it can be replayed |
| `answers.py` | Save, alias, approve and re-check saved answers |
| `kb.py` | The knowledge base: notes, log, templates, glossary, rules, playbooks, learning, freshness |
| `layers.py` | Finds playbooks and reads a file through every layer. Read only. |
| `redact.py` | Finds what you may not want to send outside |
| `review.py` | Lens briefs, house rules, repo configs, and the grade |
| `voice_gate.py`, `checkpoint.py` | Hook logic: the voice reminder and gate, and the compaction checkpoint |
| `validate_skill.py`, `package.py` | Will it load everywhere, and build the archives |

Every script runs as `python3 scripts/NAME.py`, takes `--help`, never asks a question, and exits 0 when fine, 1 when a check fails and 2 on a usage error. See [Commands](commands.md).

## Assets: the tables

| Table | Decides |
|---|---|
| `router-table.tsv` | Which words route to which workflow, template, risk flag and system. About 1,600 rows, edited by hand. |
| `workflows.tsv` | The twelve workflows |
| `workflow-graph.tsv` | Which workflow usually follows which. A test compares it with each workflow file's "Chains to" section. |
| `contracts.tsv` | The sections and markers each workflow's output must have |
| `source-tiers.tsv` | Source kinds, the order per role, question signals, project files and docs domains |
| `redact-patterns.tsv` | Every redaction rule, its severity and its replacement |
| `review-lenses.tsv` | The seven review lenses |
| `style-words.tsv`, `style-words-google.tsv`, `style-profiles.tsv` | The voice profiles and their word lists |
| `templates/` | 60 artifact templates and 12 workflow output shapes |

`docs/template-catalog.tsv` lists every artifact template with its group, workflow, roles, trigger words, audience and frequency. Tests check it against the templates and the router.

## The layers model

A request can draw on four layers, highest first:

```text
yours  >  team (nearest playbook)  >  company (its parent)  >  shipped
```

| Layer | Where |
|---|---|
| Yours | `~/.flareware/flarehand` |
| Team | A `.flarehand/` folder found by walking up to the git root, then folders in `prefs.playbooks` |
| Company | The `parent` named in a playbook's `playbook.json`, and its parent in turn |
| Shipped | `skills/flarehand/assets/` |

They combine two ways. **Shapes and preferences take the first match**: templates, workflows, voice, default answers, source preferences. **Rules and checks add up**: house rules, glossary questions, redaction domains, required sections and risk rows.

A personal row may add a route, a question or a guardrail. It may never remove, lower or answer one. `layers.py` does the reading for every caller and never writes. See [Teams and playbooks](teams-and-playbooks.md).

## Hooks: one dispatcher, one output per host

Five hooks, all through `hooks/run-hook.cmd` and `hooks/hook.py`:

| Action | Event | Logic |
|---|---|---|
| `session-start` | Start, resume, clear, compact | The nudge naming each skill. After a compaction, the line pointing at the checkpoint. |
| `prompt-submit` | Before each user message | `voice_gate.remind`: one line of house voice, once flarehand ran |
| `stop` | After each reply | `voice_gate.decide`: the em-dash gate, off unless turned on |
| `pre-compact` | Before a compaction | `checkpoint.save` |
| `session-end` | End of session | `checkpoint.end`: one file deleted, so it fits the shortest timeout |

**The launcher** is one file in two languages. `cmd.exe` runs its batch part. A POSIX shell skips that part through a heredoc and runs the rest. Either way it finds a working Python and starts `hook.py`, and exits 0 if Python or the dispatcher is missing. Every command in `hooks.json` first checks that the launcher exists under `CLAUDE_PLUGIN_ROOT`, so in a tool that does not set it, each hook does nothing.

**The dispatcher** reads the event JSON on standard input, normalises field names across hosts, and prints exactly one output shape for the host it detects:

| Host | Detected by | Output |
|---|---|---|
| Cursor | `CURSOR_PLUGIN_ROOT` | `{"additional_context": "..."}` |
| Copilot CLI | `COPILOT_CLI` | `{"additionalContext": "..."}` |
| Claude Code, Codex and everything else | Default | `{"hookSpecificOutput": {"hookEventName": ..., "additionalContext": ...}}` |

One shape per host, because Claude Code reads every context field it knows without de-duplicating. The stop gate runs only for Claude-format hosts. The dispatcher catches every error and always exits 0, because a pre-compact hook that fails can stop a compaction.

## Cross-tool manifests

| File | Read by | Points at |
|---|---|---|
| `.claude-plugin/plugin.json` | Claude Code, Cowork, Copilot, Devin, Factory, Augment, Junie | The skills and `hooks/hooks.json` by convention |
| `.claude-plugin/marketplace.json` | Claude Code, Copilot CLI and others | The `flareware` marketplace, source `./` |
| `.codex-plugin/plugin.json` | Codex | `./skills/`, `./hooks/hooks.json`, and its listing |
| `.agents/plugins/marketplace.json` | Codex | The local plugin |
| `.cursor-plugin/plugin.json` | Cursor | `./skills/`, `./hooks/hooks-cursor.json` |
| `gemini-extension.json` | Gemini CLI | `GEMINI.md` as context. No hooks. |

`tools/bump_version.py` keeps the version the same in every manifest and in each skill's `flarehand.version` metadata. `.version-bump.json` lists them all.

Skill front matter uses only the portable keys: `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools`. claude.ai refuses an upload with any other key.

## Where state lives

| State | Location | Written when |
|---|---|---|
| Knowledge base | `~/.flareware/flarehand`, or a folder named with `--set-default` | After a yes |
| Its history | `.git/` inside it, no remote | After each write |
| Staged snapshots and the claim ledger | `<temp>/flarehand-staging/<id>/` | During a session |
| Compaction checkpoint | `<temp>/flarehand-staging/checkpoints/` | Before a compaction. Deleted at session end. |
| Hook state | `<temp>/flarehand-staging/hooks/` | On each hook call |
| Session files | `<temp>/flarehand-sessions/` | Session-only mode, and counters with learning off |
| Team playbook | `.flarehand/` in a repository | Only by a `--team` command or `playbook init`. Never committed by flarehand. |

**No state under the plugin folder.** Installers replace it on every update. Full detail, including what each file holds and how long it stays, is in [Privacy and data](privacy-and-data.md#what-is-stored-and-where).

## Packaging

`package.py` builds three archives for each of the five skills, plus a plugin folder, into `dist/`:

| File | For |
|---|---|
| `flarehand.skill` | Claude Desktop chat: double-click, then **Save skill** |
| `flarehand.zip` | Windows, macOS and the claude.ai upload |
| `flarehand.tar.gz` | Linux, where `unzip` may be missing |

The build is reproducible: file order is sorted and timestamps are fixed, so the same source always gives the same checksum. Each archive has exactly one top-level folder holding `SKILL.md`, and stays under 30 MB.

Several packaging rules exist for reasons that are not obvious:

- **Scripts run through Python, never by their executable bit.** Packagers and upload paths strip it. The one exception is `hooks/run-hook.cmd`, which Cursor runs directly.
- **No PowerShell script files.** Windows blocks downloaded `.ps1` files under the default policy.
- **No binaries or launchable files.** macOS gates those after a download.
- **No top-level `bin/` folder.** It blocks the plugin install in claude.ai and Cowork.
- **No `.claude-plugin`, `agents`, `hooks` or `workflows` folder inside a skill.** Any of them makes Claude Code load the skill as a plugin. Plugin parts live at the repository root.

## Design principles

These hold across every change.

**Determinism by tables.** Anything that should never vary lives in a table or a script, not in the model's memory. Routing, source order, style, redaction and grading are lookups and rules. "Good enough" is a check a machine runs. A saved answer replays as a file read. A near match is shown to a person, never replayed on a guess.

**Consent first.** Nothing goes into the knowledge base without a yes, and nothing leaves the machine without the person's word. The few writes that need no separate yes record what the person already agreed to, or rebuild what is already there. Every write prints its undo, and every write is a git commit.

**The finder is not the checker.** Agents reading the same source agree with each other, and agreement is not verification. A claim's checker gets the claim, the quote and the source, never the reasoning. A review's checker is never the agent that found the issue. Anything nobody checked is reported as unchecked, never as passed.

**Files shape the work, never the checks.** Templates, workflows, glossaries, house rules and sources in a knowledge base or a playbook are read into real decisions. Everything in them is text, comments included. They may widen what gets searched. They may never narrow what gets checked. A fetched page is data too.

**A script is never the only path.** Every script-backed step has a written way to do it by hand, for tools with no shell or no terminal permission. That is why the method lives in the reference files and the scripts only do what should never vary.

**Hooks never block.** Every hook exits 0, prints one output shape, and writes only to the temp folder. A tool with no hooks loses a convenience, not a feature.

**Plain voice everywhere.** Every file a person reads passes `check_output.py --style`, including these pages.

Next: [Documentation home](README.md)
