# Install

This page gives the install, update and removal steps for every tool flarehand supports, and what works in each.

One repository, `FlareWare-Solutions/flarehand`, is the plugin, the Claude marketplace and the install source for every other tool. Each tool reads the manifest it knows and ignores the rest.

**Where a step says "check your tool's docs", the repository has not confirmed the exact command.** Install syntax changes between releases, so take the current form from that tool's own documentation.

## What works where

"Scripts" means the Python scripts run on your machine. "Knowledge base" means the private folder at `~/.flareware/flarehand`.

| Where | How it gets there | Skills | Scripts | Hooks | Knowledge base |
|---|---|---|---|---|---|
| Claude Code | Plugin marketplace | Yes | Yes | Yes | Yes |
| Claude Desktop, Code tab | Same plugin as Claude Code | Yes | Yes | Yes | Yes |
| Cowork | Plugin marketplace, or skill upload | Yes | In its sandbox | Yes | No |
| claude.ai and Desktop chat | Skill upload | Yes | Four, in its sandbox | No | No |
| Codex CLI and IDE | Codex marketplace | Yes | What the sandbox allows | After you review them | With `writable_roots` |
| Copilot CLI | Plugin marketplace | Yes | Yes | Yes, check the docs | Yes |
| Copilot in VS Code | Reads the Claude plugin | Yes | Through the terminal tool | Partly | Yes |
| Cursor | Cursor plugin | Yes | Yes | Yes | Yes |
| Gemini CLI | Gemini extension | Through `GEMINI.md` | Yes | No, by design | Yes |
| Devin, Factory, Augment, Junie | Read the Claude plugin | Yes | Yes | Varies | Yes |
| OpenCode, Amp, Cline | Skills folder | Yes | Yes | No | Yes |
| Goose, Zed, Kiro | Skills folder | Yes | Yes | No | Yes |
| `npx skills`, `gh skill` | Skills only | Yes | Yes | No | Yes |

Every tool needs three things: the skills folder, Python 3 for the scripts, and a way to start. Hooks are the way to start where a tool runs them. Where it does not, `AGENTS.md` or `GEMINI.md` does the same job. See [Tools with no hooks](#tools-with-no-hooks-the-agentsmd-snippet).

## Claude Code, and the Desktop Code tab

Everything works here: the scripts, the knowledge base, saved answers, the file checks and all five hooks.

Inside Claude Code:

```text
/plugin marketplace add FlareWare-Solutions/flarehand
/plugin install flarehand@flareware
```

Or from a terminal:

```bash
claude plugin marketplace add FlareWare-Solutions/flarehand
claude plugin install flarehand@flareware
```

You get five skills: `flarehand` and four entry points. Type `/flarehand-remember`, `/flarehand-ground`, `/flarehand-grill` or `/flarehand-review` to call one by name. Claude Code may show them with a `flarehand:` prefix.

The Code tab in the Claude Desktop app is Claude Code in a window. It reads the same plugins and runs the same scripts. If you are not an engineer, use the Code tab rather than Desktop chat, because chat cannot reach your files.

**Check it landed.** Start a new session, type `/skills` and look for `flarehand`. You can also ask "check that flarehand is set up". That is a setup request, so it runs `doctor.py --capabilities`, which only reads, from wherever the plugin was installed.

## Codex, in the CLI and the IDE

Codex reads `.codex-plugin/plugin.json` and the Claude-format hooks. Add the marketplace:

```bash
codex plugin marketplace add FlareWare-Solutions/flarehand
```

Then install `flarehand` from the Codex plugin browser. How the browser install works can change between releases, so check your tool's docs. Type `$flarehand` to call the skill by name.

As skills only, copy the five folders under `skills/` into `~/.agents/skills`, or into a repository's `.agents/skills`.

### Codex hooks need your review

Codex shows a plugin's hooks for review before they run, and asks again when they change. They are the five commands in `hooks/hooks.json`. Each one calls `hooks/run-hook.cmd`. See [Privacy and data](privacy-and-data.md#what-the-hooks-do) for what each does.

### The Codex sandbox

In its usual mode, Codex writes only inside the folder it started in and the temp folder, and the network is off. Four things follow.

- **Saves ask for approval.** The knowledge base is outside the workspace. To stop the prompts, add it to `~/.codex/config.toml`:

  ```toml
  [sandbox_workspace_write]
  writable_roots = ["~/.flareware"]
  ```

- **The git history can miss saves.** Codex keeps `.git` read-only, even inside a writable folder. Notes still save, but the history skips them until a write made outside the sandbox. flarehand says so once a day.
- **No raw fetch.** With the network off, `ground.py fetch` cannot reach a page. `doctor.py --capabilities` reports that, and grounding falls back to your files, git, MCP servers and what you paste.
- **MCP servers still work.** They run outside the sandbox. Codex keeps its own list in `~/.codex/config.toml`, and `codex mcp list` shows it.

Codex tends to act without asking. flarehand's two gates still hold there: nothing is written to your knowledge base without a yes, and nothing leaves the machine without your word.

## GitHub Copilot, in the CLI and in VS Code

The Copilot CLI reads `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and the Claude-format hooks. Its marketplace commands follow Claude Code's form, under `copilot plugin`. Check your tool's docs for the current form.

As skills only, Copilot reads these folders:

| Scope | Folders |
|---|---|
| Project | `.github/skills`, `.claude/skills` and `.agents/skills` in the repository |
| Personal | `~/.copilot/skills` and `~/.agents/skills` |

It has not been confirmed that Copilot sets `CLAUDE_PLUGIN_ROOT` for a Claude-format plugin. Every hook command does nothing when that variable is empty, so the worst case is a plugin with no hooks, never a broken one. If the session-start line does not appear, check your tool's docs and add the [AGENTS.md snippet](#tools-with-no-hooks-the-agentsmd-snippet).

**Copilot in VS Code** reads `.claude-plugin`, and chat and agent mode load the skills. Two things differ:

- VS Code has no session-end event, so a compaction checkpoint stays in the temp folder until it is pruned after 7 days.
- Scripts run through the terminal tool, which VS Code asks you to allow the first time. Allow it. Otherwise every script step falls back to the by-hand version.

## Cursor

Cursor reads `.cursor-plugin/plugin.json`, which points at `skills/` and at `hooks/hooks-cursor.json`. Install it from the Cursor marketplace once it is listed there. Until then, check your tool's docs for installing a plugin from a GitHub repository.

Cursor runs `./hooks/run-hook.cmd` directly from the plugin folder. The em-dash gate does not run in Cursor, because its stop hook has no way to hold a reply once.

## Gemini CLI

Gemini reads `gemini-extension.json`, which loads `GEMINI.md` into every session. `GEMINI.md` is a short bootstrap that says which flarehand skill to use for each kind of work request.

```bash
gemini extensions install https://github.com/FlareWare-Solutions/flarehand
```

**Gemini runs no flarehand hooks, by design.** Gemini reads `hooks/hooks.json` with its own event names and environment, and it does not set `CLAUDE_PLUGIN_ROOT`. So each hook command finds nothing and exits quietly. `GEMINI.md` asks the agent to re-read the standing rules at the start of a session and after Gemini compresses the conversation.

## claude.ai and Claude Desktop chat

No terminal is needed. Upload the skill:

1. In claude.ai, open **Customize**, then **Skills**.
2. Select the plus button, then **Upload a skill**.
3. Pick `flarehand.zip`. Upload any entry point you want after it, such as `flarehand-review.zip`.

Code execution must be on in your settings. On Claude Desktop chat, you can also double-click `flarehand.skill` and press **Save skill** in the preview that opens.

Chat has real limits. Skills run in a sandbox in Anthropic's cloud, not on your computer:

- **No knowledge base.** Nothing is remembered between chats. flarehand says so once and offers a paste-ready "about me" block instead.
- **Four scripts still run** in the sandbox: `classify.py`, `check_output.py`, `redact.py` and `review.py`.
- **No hooks.** The skill fires on its description alone.
- **Per person, no sync.** Each person uploads the skills. Skills there and in Claude Code are separate.

Cowork installs plugins from a marketplace or takes a skill upload, and hooks run there. Its scripts run in its own sandbox, so a knowledge base kept there does not follow you to Claude Code.

## Skills-only installers

Two installers copy the skills into the right folder for many tools at once. Neither installs hooks.

```bash
npx skills add FlareWare-Solutions/flarehand
gh skill install FlareWare-Solutions/flarehand
```

The `npx skills` form is from skills.sh. Check the `gh` docs for the current `gh skill` form. Both copy all five skills. The four entry points need `flarehand` beside them, so keep the five together.

## Installing by hand

Use this when you cannot reach GitHub, or your tool only reads a skills folder. You need the archive, `flarehand.zip` or `flarehand.tar.gz`, from whoever shares it with you. Save it to your Downloads folder first.

**macOS and Linux**, pasted into Terminal:

```bash
mkdir -p ~/.claude/skills && unzip -o ~/Downloads/flarehand.zip -d ~/.claude/skills && ls ~/.claude/skills
```

**Windows**, pasted into PowerShell:

```powershell
$d="$env:USERPROFILE\.claude\skills"; New-Item -ItemType Directory -Force $d | Out-Null; Expand-Archive -Force "$env:USERPROFILE\Downloads\flarehand.zip" $d; dir $d
```

**Linux without `unzip`**, using the tarball:

```bash
mkdir -p ~/.claude/skills && tar -xzf ~/Downloads/flarehand.tar.gz -C ~/.claude/skills && ls ~/.claude/skills
```

For any other agent, swap `~/.claude/skills` for the folder it reads. Nearly every agent reads `~/.agents/skills`. OpenCode, Amp, Cline, Goose, Zed and Kiro load skills from a folder. Check your tool's docs for the exact one.

**For a whole team**, commit the skill folders to `.agents/skills/` in the repository, which Codex, Copilot, Cursor and Gemini read. Claude Code reads `.claude/skills/`. Share your team's templates and rules in a `.flarehand/` playbook beside it. See [Teams and playbooks](teams-and-playbooks.md).

Installed by hand, there are no hooks. Add the snippet below.

**Check it landed.** Run the doctor against the folder you unzipped into:

```bash
python3 ~/.claude/skills/flarehand/scripts/doctor.py --capabilities
```

## Tools with no hooks: the AGENTS.md snippet

Where hooks do not run, nothing reminds the agent to use flarehand at the start of a session. Paste this into the project's `AGENTS.md`, or your tool's own rules file:

```markdown
## flarehand
- For a work request, load the matching flarehand skill first and follow it.
  `flarehand-ground` checks a draft, its facts or numbers before it goes out.
  `flarehand-review` reviews code, a PR, a document or a plan. `flarehand-remember` saves,
  recalls or forgets. `flarehand-grill` stress-tests a plan or a vague ask. Otherwise use
  `flarehand`, for any other work: a deliverable, a reply, a plan, a diagnosis, or a question about a customer, contract, policy or process. For anything else, answer normally.
- At the start of a session, and after the conversation is compacted, re-read the "Standing rules"
  section of the flarehand SKILL.md before you answer.
```

Devin injects the plugin's own `AGENTS.md` as an always-on rule, so it gets this without the snippet.

## Windows and Python

- Python is not always `python3` on Windows. In a terminal, try `py -3` first, then `python`. `doctor.py` reports which one it found, and flarehand uses that one for the rest of the session.
- If Python is missing, download the Python install manager from `https://www.python.org/downloads/` and run it. It installs for you only, with no admin rights. Say yes when it offers to add Python to PATH.
- The hook launcher tries `python3`, then `python`, then `py -3`. It skips the Microsoft Store stub that only prints a hint.
- Claude Code runs hooks through Git Bash, or PowerShell when Git Bash is missing. The hook commands are written for a POSIX shell, so install Git for Windows if the session-start line never appears.
- The knowledge base is at `%USERPROFILE%\.flareware\flarehand`. The checkpoint goes to `%TEMP%`.
- Nothing in the plugin is a PowerShell script file, because Windows blocks downloaded `.ps1` files.

flarehand needs Python 3.9 or later. Every script uses the standard library only, so there is nothing else to install.

## Update

| Tool | How |
|---|---|
| Claude Code | `claude plugin marketplace update flareware`, then `claude plugin update flarehand@flareware`. Restart Claude Code to apply it. |
| Codex, Copilot, Cursor, Gemini CLI | Through the tool's plugin or extension manager. Check your tool's docs. |
| `npx skills`, `gh skill` | Run the install command again. Check the installer's docs. |
| By hand | Unzip the new archive over the old folder, with the same command as the install. |

Updating never touches your knowledge base. flarehand keeps no state under the plugin folder, because installers replace that folder on every update.

## Uninstall

| Tool | How |
|---|---|
| Claude Code | `claude plugin uninstall flarehand` |
| Gemini CLI | `gemini extensions uninstall flarehand` |
| Codex, Copilot, Cursor | Through the tool's plugin manager. Check your tool's docs. |
| claude.ai | Remove the skill under **Customize**, then **Skills**. |
| By hand | Delete the `flarehand` and `flarehand-*` folders from the skills folder you used. |

Removing the plugin leaves your knowledge base in place. To delete that too, see [Privacy and data](privacy-and-data.md#deleting-everything).

Next: [How it works](how-it-works.md)
