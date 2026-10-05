# setup-ai-tools - setting up flarehand in each AI tool

**Scope.** Getting flarehand running in the AI tool someone uses, and connecting their work tools to
it. This page is the overview. The exact install steps for each tool live in `cross-tool.md`. For
Python, read `setup-python.md`. For the rest of a developer machine, read `setup-workstation.md`.

## Contents

- Check the machine first
- When a step could not be confirmed
- What every tool needs
- Tool by tool
- Connecting work tools through MCP
- When something does not connect

## Check the machine first

```bash
python3 scripts/doctor.py --capabilities
```

It reports the operating system, Python and which agent is running. It also says whether there is a
shell, web access, git, MCP servers and a knowledge base. Read it before giving
any steps. Do not give instructions for something already set up.

**Never state a command or a version from memory.** Install syntax for these tools changes often.
Take the command from `cross-tool.md` or from the tool's own documentation, confirm it matches the
machine in front of you, then give the steps.

## When a step could not be confirmed

When you could not check a step against the tool's own documentation this session, open your answer
with this sentence, then give the steps:

```text
I could not check these steps against the tool's own documentation this session, so treat them as
general guidance and confirm each one as you go.
```

Then label each step you could not confirm `[ASSUMPTION, verify]`.

## What every tool needs

flarehand is one set of skills with a few scripts beside them. Every tool needs the same three things.

1. **The skills folder**, installed through that tool's plugin or extension system, or copied by hand.
2. **Python 3**, to run the scripts. Read `setup-python.md` if `doctor.py` did not find it.
3. **A way to start**, which is hooks where the tool has them, and a short bootstrap file where it
   does not. `AGENTS.md` and `GEMINI.md` carry that bootstrap.

Where a tool has no shell, every script step has a written way to do it by hand. `cross-tool.md` has
those under "Without a shell".

## Tool by tool

| Tool | How flarehand gets in | Scripts run? | Check it worked |
|---|---|---|---|
| Claude Code, terminal or desktop Code tab | Add the `flareware` plugin marketplace, then install the `flarehand` plugin | Yes | The flarehand skills appear in the skills list |
| Codex, CLI and IDE | The Codex plugin manifest in the repository, or the skills copied by hand | Yes, inside its sandbox | Ask it to list its skills |
| GitHub Copilot, CLI and VS Code | The plugin manifest Copilot reads, or the skills copied by hand | Yes, where it has a terminal | Ask it to list its skills |
| Cursor | The Cursor plugin manifest, or the skills copied by hand | Yes, in agent mode | The skills appear in its rules or skills settings |
| Gemini CLI | The repository installed as a Gemini CLI extension | Yes | The extension appears in its extensions list |
| claude.ai in the browser | The skill uploaded in its settings, where the plan allows skills | Some, in its sandbox | The skill appears in the skills settings |

**Claude Code** gets the full behaviour: hooks, the knowledge base and every script.

**claude.ai** has no local files and no knowledge base. `classify.py`, `check_output.py`, `redact.py`
and `review.py` (`lenses`, `brief` and `grade`) still run in its sandbox. Say early what is missing there.

**Skills-only installers**, such as `npx skills add` or `gh skill install`, copy the skills without
hooks. Everything still works. The voice reminder and the compaction checkpoint do not run.

Read `cross-tool.md` for the commands and the differences in each tool.

## Connecting work tools through MCP

Most agent tools reach work systems through MCP servers. Jira, GitHub, Slack, Notion, Confluence,
Linear, Salesforce and many others publish one, either run by the vendor or by the community.

What every tool asks for is the same three things: a name, a transport (a local command or a URL),
and the sign-in. Get them from the service's own MCP documentation, never from memory.

| Tool | Where you add MCP servers | How to list them |
|---|---|---|
| Claude Code | `claude mcp add`, or the plugin that ships the server | `claude mcp list` |
| Codex | `codex mcp add`, kept in its own config, separate from Claude's | `codex mcp list` |
| GitHub Copilot CLI | `/mcp` inside the CLI | `/mcp` |
| VS Code and Cursor | Each editor's MCP settings | The tools list in agent mode |
| Gemini CLI | Its settings file | Its MCP list command |

Three things go wrong most often.

- **Sign-in is per tool.** Connecting Jira in one tool does not connect it in another.
- **Company single sign-on.** A work account may need the organisation's sign-on approved first, and
  the error rarely says so.
- **Write access.** An MCP server that can create or change records is a production write. Use it
  only when the person asked for that change in plain words this session.

After connecting, run `doctor.py --capabilities` again so the source order knows the server is there.

## When something does not connect

Work down in this order. The most common cause comes first.

1. **Run `doctor.py --capabilities` again.** It tells you what the machine actually sees now.
2. **Is it a fresh terminal or a restarted tool?** Configuration changes often need one.
3. **Is the sign-in done, and approved for the organisation?** The failure message rarely says so.
4. **Is the network reachable?** A corporate proxy or firewall can block a server silently.
5. **Look up the current procedure.** The one you have may be out of date.

If it is still stuck and their workplace manages the machine, that is a request for their IT
team rather than more guessing. Help them write it: what `doctor.py` reported, what was tried, and
the error word for word.
