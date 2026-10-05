<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/mark-on-dark.svg">
    <img src="assets/brand/mark-on-light.svg" width="112" alt="flarehand: a hand holding a flame">
  </picture>
</p>

<h1 align="center">flarehand</h1>

<p align="center">
  <b>Turns a vague ask into the right deliverable, grounded in real sources.<br>Remembers only what you approve.</b>
</p>

<p align="center">
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-F64A68"></a>
  <a href="https://agentskills.io"><img alt="Agent Skills" src="https://img.shields.io/badge/Agent%20Skills-5%20skills-FC5338"></a>
  <img alt="Works in Claude Code, Codex, Cursor, Gemini CLI and Copilot" src="https://img.shields.io/badge/works%20in-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20Cursor%20%C2%B7%20Gemini%20%C2%B7%20Copilot-6B6577">
  <img alt="Python 3.9+, standard library only" src="https://img.shields.io/badge/python-3.9%2B%2C%20no%20dependencies-6B6577">
  <a href="docs/evals.md"><img alt="Eval score 0.99 with flarehand, 0.84 without" src="https://img.shields.io/badge/evals-0.99%20vs%200.84%20without-F0399A"></a>
</p>

---

Most work requests arrive as one vague line. "Customer says the export is broken." "Write up these
notes." "Is this ready to send?" A capable agent will happily answer. That is the problem. It guesses
what you meant, fills the gaps with plausible numbers, and forgets everything by tomorrow.

**flarehand** is an open-source plugin for your coding agent that does the thinking first. It names
the deliverable you actually need. It asks only the questions that change it, each with a
recommended answer. It finds the facts itself, labels every specific with where it came from, and
checks the draft before you see it. Then it offers to keep what was worth keeping, and keeps nothing
until you say yes.

It works for engineers, support, product, operations, sales, finance, HR, founders, freelancers
and students. It works alone, for a team, or across a company.

## See it work

**A vague one-liner** becomes a named job, three questions and a safe way forward:

```text
You:        customer says the invoice export is broken

flarehand:  I think you need a diagnosis: what is actually failing, and why. Then probably a
            reply to the customer. Say "just go" and I will write it from what we have, with
            the gaps listed.

            Reported cause: "the invoice export is broken" [stated, unverified]

            Possible causes, each with the evidence that confirms or rules it out:
            1. The export fails for everyone ...
            2. It fails only for their data or settings ...
            3. The export works, but the file is not what they expected ...

            Questions for the customer (my default in brackets):
            1. What exactly happens? The error text, or does the file look wrong? [file looks wrong]
            2. When did it last work? [recently]
            3. Every invoice, or only some? [only some]
```

**Notes become a postmortem**, with every fact traced back to you and nothing invented:

```text
| Failed checkouts            | About 2,300             | Grafana dashboard [your input] |
| Customers affected          | MISSING                 | ask the payments team          |
| Revenue effect              | MISSING                 | ask finance                    |

Root cause (most probable): the pool max dropped from 50 to 5. [your input]
Not yet verified: the rollback restored service, but no re-test with the pool at 50 is recorded.

One thing to fix: your notes say "Tue Oct 1", but Oct 1 is a Thursday. Which is right?
```

**Every piece of work ends the same way.** Nothing is written until you pick a number:

```text
Keep any of this? Nothing is saved until you reply with numbers, or "none".
1. Save log: wf-01, postmortem. First outage write-up for payments-api.
2. Save note: config changes need a second reviewer (decision)
3. Next: incident-comms, a customer-facing summary of the same outage
```

## Three promises

1. **It never invents a specific.** No name, number, date, version or URL that is not in your words
   or a source it read. When it cannot confirm something, it says so and asks.
2. **It checks before it ships.** Quotes must really be in the source. Numbers in a claim must match
   the source. Every URL must have been seen. A separate checker, which never saw the draft,
   verifies high-stakes claims. One command, `check.py`, prints `PASS` or a numbered list of fixes.
3. **It remembers only what you approve.** Your knowledge base is plain Markdown on your machine,
   with a git history so any change can be undone. Saved answers come back word for word next time.

## What you get

| Skill | Use it when you say |
|---|---|
| `flarehand` | Anything that should end in a deliverable: a reply, a plan, a diagnosis, a write-up |
| `flarehand-ground` | "Check this before I send it." "Are the numbers right?" |
| `flarehand-review` | "Review this PR." "What's wrong with this plan?" |
| `flarehand-grill` | "Grill me on this plan." "Poke holes in it." |
| `flarehand-remember` | "Remember this." "What did we decide about pricing?" "Forget that." |

Behind them:

- **12 workflows** that cover how work actually goes wrong. Diagnose without anchoring on a guess.
  Hand off so the next team does not bounce it. Compress for a specific reader. Reconcile two things
  that should match. Find the pattern in many items. Critique before someone else does.
- **60 templates** in ten groups, most following a public framework they cite. Postmortem,
  decision record, design doc, product brief, business case, OKRs, runbook, SOP, release notes,
  customer reply, job description, interview scorecard, investor update and more.
  [See the catalog.](docs/templates.md)
- **Graded reviews** with seven lenses, where every finding is checked by someone who did not find
  it, and anything nobody checked is reported as unchecked.
- **Redaction before anything goes out**: credentials, personal data, health details, money and
  internal hosts are flagged before you send.

## It grows with you

flarehand starts useful on the first request and gets more useful the more you work with it.

- **Do the work first.** No setup form. It detects your name, time zone and tools, and does the job.
  Only then does it ask three optional questions, and whether it may keep a knowledge base.
- **It notices, then asks.** Say you cut the risks section from two status reports in a row. It
  offers: save as a) mine b) team playbook c) not now d) never ask.
- **Your team's way, shared.** A `.flarehand/` folder in a repository holds your team's templates,
  glossary and house rules. Your own preferences shape the output. Team rules always apply.
  [How playbooks work.](docs/teams-and-playbooks.md)
- **Nothing hidden.** `kb.py about-me` lists everything it learned, where it came from, and the
  command that undoes it.

## Install

Python 3.9 or later makes everything work. There is nothing else to install.

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

**Cursor, Copilot, Devin, Factory and others** read the same repository.
[The install guide](docs/install.md) has the steps for each tool.

**Skills only, for any agent that reads Agent Skills** (no hooks):

```bash
npx skills add FlareWare-Solutions/flarehand
```

Then try: *"Turn these notes into a status update for my manager"*, followed by your notes.
[Getting started](docs/getting-started.md) walks through the first session.

## What it stores, and what it sends

- **Your knowledge base** is a folder of plain Markdown at `~/.flareware/flarehand`
  (`%USERPROFILE%\.flareware\flarehand` on Windows). It is written only after you say yes, kept in a
  local git history so any change can be undone, and never pushed anywhere.
- **Session files** go to your system temp folder: snapshots of sources you cite, and a checkpoint
  saved before your agent compacts the conversation. The checkpoint is deleted when the session
  ends, and anything left is pruned after 7 days.
- **Team playbooks** are read from a `.flarehand/` folder in your repository, or a folder you name.
  They hold templates and rules only, never anything about a person.
- **Network.** flarehand sends no telemetry. When it checks a claim it fetches only pages that
  already appeared in your session. Your agent sends your conversation to its own model provider,
  as it always does.
- **Hooks** run on your machine, in Python, and print a line or two of context for your agent. They
  never block, and they never write inside the plugin folder.

The full detail is in [privacy and data](docs/privacy-and-data.md).

## Measured, not claimed

flarehand is tested with `claude plugin eval` on 37 realistic cases across roles. Each case runs
three times with the plugin and three times without, scored by an independent judge model.

| | With flarehand | Without |
|---|---|---|
| Mean score, all 37 cases | **0.99** | 0.84 |
| Work requests (28 cases) | **0.99** | 0.79 |
| Fired on requests it should ignore (haiku, React, cover letter...) | 0 of 27 runs | |

Some of the biggest differences:

- Not inventing documentation links: 1.00 vs 0.56.
- Softening a blunt reply without losing a fact: 1.00 vs 0.56.
- Keeping a legal question to the facts: 1.00 vs 0.44.
- Doing the work first on a first run: 0.98 vs 0.48.
 How the suite works, and the honest
caveats, are in [evals](docs/evals.md). The scripts behind it have 809 unit tests.

## Documentation

| | |
|---|---|
| [Getting started](docs/getting-started.md) | Your first session, step by step |
| [Install](docs/install.md) | Every tool, what works where, Windows notes |
| [How it works](docs/how-it-works.md) | The pipeline, routes, workflows and entry points |
| [Grounding](docs/grounding.md) | Labels, sources, checks, and what it will never do |
| [Memory and learning](docs/memory-and-learning.md) | The knowledge base, saved answers, the learning loop |
| [Teams and playbooks](docs/teams-and-playbooks.md) | Sharing templates, glossaries and house rules |
| [Templates](docs/templates.md) | All 60 templates and the frameworks they follow |
| [Privacy and data](docs/privacy-and-data.md) | Exactly what is stored and sent |
| [Commands](docs/commands.md) | Every script and subcommand |
| [FAQ](docs/faq.md) and [troubleshooting](docs/troubleshooting.md) | When something is not right |
| [Architecture](docs/architecture.md) | How the repository fits together |

## Credits

flarehand stands on good ideas from others:

- [superpowers](https://github.com/obra/superpowers) by Jesse Vincent. It showed that skills work
  best as mandatory workflows, that verification comes before completion, and how to ship one
  plugin to many agents.
- [grill-me](https://github.com/mattpocock/skills) by Matt Pocock, for the interview style: a
  round of questions, each with a recommended answer, and look it up before you ask.
- The [Google developer documentation style guide](https://developers.google.com/style), whose word
  list the optional Google profile adapts under CC BY 4.0.
- [Lucide](https://lucide.dev) icons (ISC), which the flarehand mark is drawn from. See
  [the brand notice](assets/brand/NOTICE.md).
- The research on grounding and attribution cited in [grounding](docs/grounding.md).

## Contributing

Issues and pull requests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first: flarehand has
to pass its own writing rules, and every change runs the unit tests and the validator.

## License

MIT. See [LICENSE](LICENSE). The flarehand name and mark belong to Flareware.

<p align="center"><sub>Made by <a href="https://github.com/FlareWare-Solutions">Flareware</a></sub></p>
