# flarehand documentation

These pages explain how to install flarehand, use it day to day, share it with a team, and check what it does with your data.

flarehand is an open-source agent plugin by Flareware, under the MIT license. It turns a one-line work request into the deliverable it needs, grounds every specific in a real source, and remembers only what you approve.

## Suggested reading order

New to flarehand? Read these four, in this order:

1. [Getting started](getting-started.md): install it, make your first request, and learn the save menu.
2. [How it works](how-it-works.md): the nine steps every request runs through.
3. [Grounding](grounding.md): the labels on every claim, and why you can trust them.
4. [Memory and learning](memory-and-learning.md): what it keeps, where, and how to undo it.

Then read what fits your situation:

- Sharing shapes and rules with a team: [Teams and playbooks](teams-and-playbooks.md).
- Choosing or changing an output shape: [Templates](templates.md).
- A security or privacy review: [Privacy and data](privacy-and-data.md).
- Something does not work: [Troubleshooting](troubleshooting.md), then the [FAQ](faq.md).
- Contributing or auditing: [Architecture](architecture.md) and [Evals](evals.md).

## Every page

| Page | What it covers |
|---|---|
| [Getting started](getting-started.md) | Install, the first request, the consent question, the save menu, and five requests to try. |
| [Install](install.md) | Exact install steps for Claude Code, Codex, Copilot, Cursor, Gemini CLI, claude.ai and skills-only installers. Updates and removal. |
| [How it works](how-it-works.md) | The nine-step pipeline, the routes, how many questions it asks, the twelve workflows and the four entry points. |
| [Grounding](grounding.md) | Labels, source tiers, freshness, quotes and snapshots, the independent checker and `check.py`. |
| [Memory and learning](memory-and-learning.md) | The private knowledge base, saved answers, freshness, undo, and the learning loop. |
| [Teams and playbooks](teams-and-playbooks.md) | Personal, team and company layers, the `.flarehand/` folder, and which layer wins. |
| [Templates](templates.md) | All 60 templates by group, the frameworks they follow, modes, and how to save your own. |
| [Privacy and data](privacy-and-data.md) | Exactly what is stored where, what goes over the network, what hooks do, and how to delete everything. |
| [Commands](commands.md) | Every script and subcommand you might run, with its main flags. |
| [FAQ](faq.md) | Short answers to common questions. |
| [Troubleshooting](troubleshooting.md) | Fixes for when it does not fire, cannot find Python, or asks too much. |
| [Evals](evals.md) | How the plugin is tested, and the latest results. |
| [Architecture](architecture.md) | The repository layout, the five skills, the layers model, hooks and design principles. |

The file [template-catalog.tsv](template-catalog.tsv) lists every template with its group, workflow, roles and trigger words. The tests read it, so it stays in step with the templates.

## Words these pages use

| Word | Meaning |
|---|---|
| Artifact | The thing you ship: a postmortem, a customer reply, a plan. |
| Knowledge base | Your private folder at `~/.flareware/flarehand`. Plain Markdown, on your machine. |
| Playbook | A shared folder of shapes and rules, usually `.flarehand/` in a team repository. |
| Saved answer | An answer kept in your knowledge base and replayed word for word. |
| Ledger | The session's list of sources and claims, which the grounding checks read. |
| Save menu | The numbered "Keep any of this?" list at the end of a piece of work. |

Next: [Getting started](getting-started.md)
