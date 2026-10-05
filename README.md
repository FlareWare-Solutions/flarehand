# flarehand

Turns a vague ask into the right deliverable, grounded in real sources, and remembers only what you
approve.

flarehand is an open-source agent plugin from Flareware. Type one vague line, such as "customer says
the export is broken" or "turn these notes into an update for my manager". flarehand names the
deliverable you need and asks only the questions that matter. It finds the facts itself, labels
every specific with its source, checks the draft, and offers to keep what was worth keeping. Nothing is
saved without your yes.

It works in Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot and any agent that reads Agent
Skills.

## What you get

| Skill | Use it to |
|---|---|
| `flarehand` | Do any work request: a deliverable, a reply, a plan, a diagnosis, a review. |
| `flarehand-remember` | Save, recall and search your notes. "What did we decide about X?" |
| `flarehand-ground` | Check a draft or a claim against real sources before it goes out. |
| `flarehand-grill` | Sharpen a vague ask or a plan with a short round of questions. |
| `flarehand-review` | Review code, a PR, a document or a plan with graded lenses. |

## Install

Python 3.9 or later makes everything work. Without it you still get the method, with no scripts.

**Claude Code**, inside a session:

```text
/plugin marketplace add FlareWare-Solutions/flarehand
/plugin install flarehand@flareware
```

**Codex:**

```bash
codex plugin marketplace add FlareWare-Solutions/flarehand
```

Then install `flarehand` from the Codex plugin browser, and approve its hooks when Codex asks.

**Gemini CLI:**

```bash
gemini extensions install https://github.com/FlareWare-Solutions/flarehand
```

**Cursor, Copilot, Devin, Factory and others** read the same repository. The commands for each are
in [the cross-tool guide](skills/flarehand/references/cross-tool.md).

**Skills only, for any agent** (no hooks):

```bash
npx skills add FlareWare-Solutions/flarehand
```

Where hooks do not run, paste the snippet from the cross-tool guide into your `AGENTS.md`.

## What it stores, and what it sends

- **Your knowledge base** is a folder of plain Markdown files at `~/.flareware/flarehand`
  (`%USERPROFILE%\.flareware\flarehand` on Windows). It is written only after you say yes, kept
  in a local git history so any change can be undone, and never pushed anywhere. To keep it
  elsewhere, run `kb.py init --root <folder> --set-default`.
- **Session files** go to your system temp folder. They are snapshots of sources you cite, a
  checkpoint saved before your agent compacts the conversation, and a marker that says whether the
  skill ran.
  The checkpoint is deleted when the session ends, and anything left is pruned after 7 days.
- **Team playbooks** are read from a `.flarehand/` folder in your repository, or a folder you name.
  They hold templates and rules only, never anything about a person.
- **Network.** flarehand sends no telemetry. When it checks a claim it fetches only pages that
  already appeared in your session, and `doctor.py` checks whether the web is reachable. Your agent
  sends your conversation to its own model provider, as it always does.
- **Hooks** run on your machine, in Python, and print a line or two of context for your agent.
  They never block, and they never write inside the plugin folder.

## Uninstall

- Claude Code: `/plugin uninstall flarehand`, then `/plugin marketplace remove flareware`.
- Gemini CLI: `gemini extensions uninstall flarehand`.
- Codex, Cursor and Copilot: remove it from the tool's plugin manager.
- Skills only: delete the `flarehand` and `flarehand-*` folders from your skills folder.
- To delete everything it learned, delete `~/.flareware/flarehand`.

## Help and contributing

Report a problem or ask a question in
[GitHub issues](https://github.com/FlareWare-Solutions/flarehand/issues). To change flarehand,
read [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE). The interview style credits `grill-me` by Matt Pocock (MIT).
