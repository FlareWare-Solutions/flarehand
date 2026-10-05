# Troubleshooting

This page lists the problems people hit most, what causes each, and how to fix it.

**Start here for any problem.** Ask flarehand "check that flarehand is set up", or run the doctor yourself from the `skills/flarehand/` folder:

```bash
python3 scripts/doctor.py --capabilities
```

It only reads. It reports the operating system, Python, which agent is running, git, MCP servers, the knowledge base and any playbooks. It ends with what to fix first.

## It does not fire

**Check it is installed.** In Claude Code, type `/skills` and look for `flarehand`. Start a new session after installing, because skills load at session start.

**Check the request is work.** flarehand stays out of general coding questions and personal writing on purpose. "My React effect runs in a loop", a SQL textbook query and a cover letter are all answered normally. A ticket key does not change that: "For TICKET-123, refactor this" is still general coding. Ask for an artifact, a review, a check, or to save or recall something.

**Call it by name.** Type `/flarehand` and your request on the same line, or an entry point such as `/flarehand-review`. In Codex, type `$flarehand`.

**Tools with no hooks need a nudge.** Gemini CLI, skills-only installs and tools such as OpenCode, Amp, Cline, Goose, Zed and Kiro run no session-start hook. Add the [AGENTS.md snippet](install.md#tools-with-no-hooks-the-agentsmd-snippet) to the project, or your tool's rules file.

**Install all five skills together.** An entry point such as `flarehand-review` hands over to `flarehand`. On its own it cannot work.

## It asks too many questions

- **Say "just go".** It takes every recommended answer and labels each `[ASSUMPTION, verify]`.
- **Give it the facts up front.** When your message holds the facts, such as notes to write up, it writes first and asks after.
- **Save your own template.** A shipped template asks `learn` questions about how your team works. Once you save your version, those stop.
- **Set a standing answer.** For a question it asks every time, run `kb.py config --default "QUESTION=ANSWER"`. Undo with `kb.py config --unset-default "QUESTION"`.
- **Set adaptation to `yours`.** `kb.py config --adaptation yours` lets a `standard` request skip one optional question.

Some requests always get more questions. Some work is always `full` ceremony. That is anything a customer, an executive, engineering or an auditor will act on. It is also anything that trips a risk flag, such as legal, money or a customer reply. That is up to four questions a round, and no setting lowers it.

## Python not found on Windows

1. Open PowerShell and run `py -3 --version`.
2. If that fails, try `python --version`. If it opens the Microsoft Store or prints a hint, that is the Store stub, not Python.
3. To install Python, download the Python install manager from `https://www.python.org/downloads/` and run it. It installs for you only, so it needs no admin rights. Say yes when it offers to add Python to PATH.
4. Close and reopen your terminal and your AI tool, then run `py -3 --version` again.

flarehand tries `py -3` first on Windows, then `python`. The hook launcher tries `python3`, then `python`, then `py -3`, and skips the Store stub. Python 3.9 or later is needed.

## Hooks are not running

The session-start line names the flarehand skills. If it never appears:

| Tool | Cause and fix |
|---|---|
| Claude Code on Windows | Hooks run through Git Bash, or PowerShell when Git Bash is missing. The hook commands are written for a POSIX shell. Install Git for Windows. |
| Codex | Codex shows a plugin's hooks for review before they run, and again when they change. Review and approve them. |
| Copilot CLI | It is not confirmed that Copilot sets `CLAUDE_PLUGIN_ROOT` for a Claude-format plugin. Without it, each hook quietly does nothing. Check your tool's docs, and add the AGENTS.md snippet meanwhile. |
| Gemini CLI | Runs no flarehand hooks, by design. `GEMINI.md` does the session-start job. |
| Cursor | Runs `./hooks/run-hook.cmd` directly, so the file must keep its executable bit. Reinstall if it was copied in a way that strips it. |
| Skills-only installs | `npx skills`, `gh skill` and hand installs copy no hooks. Add the AGENTS.md snippet. |

Without hooks, everything else still works. You lose the session-start nudge, the one-line voice reminder, and the checkpoint that keeps your place across a compaction. After a compaction in a tool with no hooks, tell the agent again what matters.

## Codex asks for approval on every save

The knowledge base is outside the Codex workspace, so the sandbox asks before each write. Add the folder to `~/.codex/config.toml`:

```toml
[sandbox_workspace_write]
writable_roots = ["~/.flareware"]
```

Two more sandbox effects:

- **The history misses some saves.** Codex keeps `.git` read-only, even inside a writable folder. Notes still save. The history catches up on the next write made outside the sandbox. flarehand says so once a day.
- **Pages cannot be fetched.** The network is off, so `ground.py fetch` fails. Grounding uses your files, git, MCP servers and what you paste, and labels the rest `[ASSUMPTION, verify]`. A web tool that Codex itself provides may still work.

## Copilot in VS Code skips the scripts

Scripts run through VS Code's terminal tool, which asks you to allow it the first time. Allow it. Otherwise every script step falls back to the by-hand version, which is slower and less exact.

## It does not remember anything

| Cause | Fix |
|---|---|
| You answered `b) just this session`, or "skip" | Ask it to set up your knowledge base. It runs `kb.py init` after your yes. |
| Session-only mode is still on | `python3 scripts/kb.py session end` |
| You are in claude.ai or Desktop chat | Chat has no local files. Use Claude Code or the Code tab in the Claude Desktop app. |
| You are in Cowork | Its scripts run in its own sandbox, so a knowledge base there does not follow you to Claude Code. |
| Nothing was picked in the save menu | Nothing is saved without a yes. Reply with the line numbers next time. |
| The knowledge base is somewhere else | See [Move the knowledge base](#move-the-knowledge-base). |

## A saved answer is not replayed

`recall.py` replays only when the question matches a wording you confirmed, ignoring case, punctuation and spelling variants. Run it to see why:

```bash
python3 scripts/recall.py "YOUR QUESTION" --explain
```

| Verdict | Why | Fix |
|---|---|---|
| `confirm` | A saved question looks similar but is worded differently | Say yes when it asks. It records the new wording and replays from then on. |
| `recheck` | Never approved, not checked for 30 days, edited by hand, or resting on a pin that drifted | Let it re-check the sources. If you never approved it, read it and run `python3 scripts/answers.py approve "QUESTION"` |
| `stale` | Someone marked it out of date | It answers again and offers to save the new one |
| `new` | No saved answer matches | Save it from the menu next time |

## The check keeps failing

`check.py` prints a numbered `FIX:` list. The common ones:

- **"a number, version or date with no label".** Every specific needs a label such as `[your input]` or `[ASSUMPTION, verify]`.
- **"was not seen in a tool result or the person's words".** A URL nobody saw. Remove it, fetch it with `ground.py fetch`, or pass `--seen-url` if you did see it.
- **A style error.** The plain voice bans em dashes and a list of wordy phrases. To change the voice, see the [FAQ](faq.md#how-do-i-turn-off-the-em-dash-rule).
- **A missing section.** The template or workflow requires it. A section you never need can be dropped from your own template, except the MISSING list.

## How to reset

Pick the smallest reset that solves it:

| To reset | Run |
|---|---|
| One learned preference, term, rule or template | `python3 scripts/kb.py about-me`, then `python3 scripts/kb.py forget ID` |
| Your version of one template | `python3 scripts/kb.py template reset NAME` |
| A remembered answer to "may I keep this?" | `python3 scripts/kb.py choice KEY --clear` |
| An offer you answered "never" | `python3 scripts/kb.py forget never:OFFER_ID` |
| The last thing written | `git -C ~/.flareware/flarehand revert --no-edit HEAD` |
| The newest work-log line | `python3 scripts/kb.py log undo` |
| Session-only mode | `python3 scripts/kb.py session end` |
| Everything, to see the first run again | Move the folder aside: `mv ~/.flareware/flarehand ~/flarehand-backup` |

After moving the folder aside, the next request is a first run. To delete everything for good, see [Privacy and data](privacy-and-data.md#deleting-everything).

## Move the knowledge base

To keep it somewhere other than `~/.flareware/flarehand`, such as a folder you back up:

1. Move the folder: `mv ~/.flareware/flarehand ~/Work/flarehand-kb`
2. Point flarehand at it:

   ```bash
   python3 scripts/kb.py init --root ~/Work/flarehand-kb --set-default
   ```

`--set-default` leaves a small pointer at `~/.flareware/flarehand/config.json`, so every session finds the new folder. It keeps your notes and settings. Without `--set-default`, you would need `--root` on every command.

Keep it out of folders that sync on their own, such as a OneDrive-redirected Documents folder. The knowledge base holds customer data and notes about people. A folder that moves without warning is worse than one that is slightly harder to find.

## Obsidian will not open the folder

The folder name starts with a dot, so file pickers hide it. Paste the path instead. On macOS, press Command, Shift and G, then paste `~/.flareware/flarehand`. On Windows, paste `%USERPROFILE%\.flareware\flarehand` into the address bar.

If a release refuses the folder, make a plain-named link and open that:

- macOS: `ln -s ~/.flareware/flarehand ~/flarehand-kb`
- Windows, in PowerShell: `cmd /c mklink /J "$env:USERPROFILE\flarehand-kb" "$env:USERPROFILE\.flareware\flarehand"`

## Still stuck

Open an issue at https://github.com/FlareWare-Solutions/flarehand/issues with what `doctor.py --capabilities` reported, what you tried, and the error word for word. Run `redact.py` on anything you paste first.

Next: [Evals](evals.md)
