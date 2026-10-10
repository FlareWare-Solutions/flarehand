<div align="center">

![flarehand: a hand holding a flame](assets/brand/icon-160.png)

# flarehand

**Turns a vague ask into the right deliverable, every fact sourced.<br>
Remembers only what you approve, and re-checks it before reuse.**

**[flarehand.flareware.app](https://flarehand.flareware.app)**

[![MIT license](https://img.shields.io/badge/license-MIT-F64A68)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-5%20skills-FC5338)](https://agentskills.io)
![Works in Claude Code, Codex, Cursor, Gemini CLI and Copilot](https://img.shields.io/badge/works%20in-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20Cursor%20%C2%B7%20Gemini%20%C2%B7%20Copilot-6B6577)
![Python 3.9+, standard library only](https://img.shields.io/badge/python-3.9%2B%2C%20no%20dependencies-6B6577)
[![Eval results](https://img.shields.io/badge/evals-0.97%20vs%200.83%20without-F0399A)](docs/evals.md)

</div>

---

Most work requests arrive as one vague line, and a capable agent will happily guess. It invents
plausible numbers and links, adopts whatever theory you mentioned, and forgets everything by
tomorrow.

**flarehand** is an open-source plugin for Claude Code, Codex, Cursor, Gemini CLI and Copilot that
does the thinking first. It names the deliverable you need. It looks up what it can, then asks only
the questions that change the result. It labels every specific with where it came from, and checks
the draft before you see it. What you choose to keep goes into a plain Markdown knowledge base on
your machine. Ask the same question next month and you get the same answer, word for word, after it
re-checks that its sources have not changed.

## See it work

**A weak prompt becomes a clear job.** One vague line, and flarehand works out what is needed
(reply trimmed):

```text
You:        customer says the export is broken

flarehand:  Sounds like you need a diagnosis: what is actually failing, and why. Then probably
            a reply to the customer. Say "just go" and I will start from what we have.

            Reported cause: "the export is broken" [stated, unverified]

            Questions, each with my default:
            1. What exactly happens? Error text, or a file that looks wrong? (file looks wrong)
            2. When did it last work? (recently, so check the last release first)
            3. Every customer, or just this one? (just this one)

            Possible causes, each with what would confirm or rule it out: ...
```

Behind that reply, a lookup table chose the route, the workflow and how many questions to allow. It
flagged that the customer's theory must stay unverified. The agent searched your knowledge base and
the sources for your role before asking you anything.

**Memory with receipts.** A saved answer keeps a copy of the source it cites. When the source
moves, flarehand notices before it repeats itself (output trimmed):

```text
$ recall.py "how many rows can a csv export hold"
REPLAY: print the saved answer word for word.

  (the documentation page changes)

$ ground.py pins check
drift  csv-export-limit: the expected quote is no longer there.
       Closest: "CSV exports are limited to 100,000 rows per file."

$ recall.py "how many rows can a csv export hold"
RECHECK: it rests on a pinned source that changed. Show what changed, then answer again.
```

**Nothing is kept until you say so.** Every piece of work ends with a menu, never a silent save:

```text
Keep any of this? Nothing is saved until you reply with numbers, or "none".
1. Save log: wf-01, postmortem. First outage write-up for the payments service.
2. Save note: config changes need a second reviewer (decision)
3. Next: incident-comms, a customer-facing summary of the same outage
```

## Why flarehand

1. **One vague line in, the right deliverable out.** It names what you need, looks up what it can,
   and asks at most three or four questions, each with a recommended answer. "Just go" works any
   time.
2. **Every specific shows where it came from.** Claims carry labels like `[verified: S3]` or
   `[ASSUMPTION, verify]`. Scripts confirm each quote is in the saved source, the numbers match,
   and every link was actually seen.
3. **Nothing is remembered until you say yes.** Your knowledge base is plain Markdown in your home
   folder, with a local git history and no remote. `about-me` shows what it learned, and `forget`
   takes any of it back.
4. **Ask again, get the same answer, with receipts.** An approved answer replays word for word with
   the snapshot it cites. A similar question is shown to you first, and a changed source triggers a
   re-check.
5. **It learns how you work, and asks first.** Make the same edit twice and it offers to keep it as
   your preference or your team's. Run the same chain of steps three times and it offers to turn it
   into a workflow of your own.
6. **Rewrites are built to keep every fact as strong as you wrote it.** Tidying or softening starts
   from a list of the claims, adds no promise, and flags every date or fix commitment for you to
   confirm.
7. **It does not adopt the reporter's theory.** "They say it's permissions" stays labelled
   unverified everywhere, including the customer reply. A diagnosis weighs at least three causes.
8. **It knows where to stop on legal, finance and HR.** It summarises and compares the source text,
   never concludes liability or computes what you owe, and says who decides.
9. **A check before anything leaves your machine.** It scans for credentials, personal data, money,
   internal hosts and client identifiers, shows what it found, and lets you decide.
10. **Your team's way, without losing the safety checks.** A `.flarehand/` playbook shares
    templates, glossary words and house rules. Team rules always apply, and no personal file can
    switch a check off.

## Everything it does

<details>
<summary><b>Turns a weak prompt into a clear job</b></summary>

- **A deterministic router.** A table of over 1,600 rows picks the route, the workflow, the
  template, how much to ask, and which risks apply. The same words always route the same way. When
  two readings are close, it shows both.
- **Names the deliverable first**, in your words, before any work.
- **Looks it up before asking.** Your knowledge base, your files, the git history and the sources
  that fit your role come first. Finding facts is its job, not yours.
- **A capped round of questions.** None for a quick lookup, up to three for your own work, up to four
  a round for anything a customer, an executive or an auditor will read. Each question carries a
  recommended answer, and "just go" accepts them all.
- **Drafts first when you already gave the facts.** Notes to write up or a draft to tidy get done
  straight away. Gaps go on a MISSING list that names who can answer each one, and never suggests
  an answer.
- **Asks which meaning you intend**, but only for words you or your team saved in a glossary.
- **Offers the jobs that fit** when a request is too unclear to route, and stays out of the way for
  general coding or personal writing.
- **Grill mode.** `flarehand-grill` stress-tests a plan in rounds, then hands back the decisions,
  assumptions and open questions.

</details>

<details>
<summary><b>Gives your agent a method, not just a prompt</b></summary>

- **Standing rules that hold every turn.** Never invent a specific. Keep every fact and never
  strengthen one. Lead with the artifact. They sit at the top of the skill so they survive a long
  session.
- **A nine-step pipeline**: orient, classify, name, recall, ground, interview, run, check, record.
- **12 workflows** for how work goes wrong: diagnose without anchoring, hand off so the next team
  does not bounce it, compress for a reader, translate across expertise, reconcile two things that
  should match, find themes, plan, critique, list exhaustively, re-tone, and more.
- **60 templates** in ten groups, from postmortems and decision records to OKRs, job descriptions,
  release notes and investor updates. Each has required sections, cites the framework it follows,
  and says whether its shape is sourced or general practice. [See the catalog.](docs/templates.md)
- **One check before anything ships.** `check.py` runs the grounding, link, style, citation and
  section checks, plus redaction for outbound text. It prints `PASS` or a numbered fix list, and the
  agent repeats until it passes.
- **Survives long sessions.** Before your agent compacts the conversation, a hook saves where the
  work stood: the job, the claims and their labels, the sources, the MISSING list, the unanswered
  save menu and the latest draft. Afterwards the agent is pointed back to it. It is deleted when the
  session ends.
- **Works without a shell, too.** Every script step has a written by-hand method.

</details>

<details>
<summary><b>Grounds every claim in a source</b></summary>

- **Nine labels**, from `[verified: S3]` and `[your input]` to `[stated, unverified]`,
  `[conflict: S2 vs S5]`, `[stale]` and `[ASSUMPTION, verify]`. Text you will send stays clean, with
  the labels listed in the notes after it.
- **Raw snapshots, checked by script.** A quote must really be in the saved copy of its source. Every
  number, date and version in a claim must appear in its quote. A near miss is shown but never
  passes.
- **Links must have been seen.** A URL in the draft must come from your words or a tool result.
- **A second opinion for anything that matters.** A claim earns `verified` only after a checker that
  never saw the draft records its verdict. High-stakes claims go to a vote.
- **Source tiers and freshness.** Numbers, versions, security and legal claims need a primary or
  official source. Fast-changing facts go stale after a week, docs after three months.
- **Conflicts are shown, never averaged**, with each source's tier and date.
- **No web? It says so.** It grounds in your files, git and connected tools, and lists what to
  confirm.
- **Guardrails** for a stated cause, for outbound text, for legal, finance and HR questions, and
  for anything that would write to production.

</details>

<details>
<summary><b>Keeps a knowledge base you can read, trust and undo</b></summary>

- **Plain Markdown on your machine**, at `~/.flareware/flarehand`, with a local git history and no
  remote. It opens as an Obsidian graph if you like.
- **A save menu, never a silent save.** A yes covers only the numbers you pick.
- **Provenance on every line**: where it came from, how, when, and whether it is confirmed or only
  suspected. A guess can never be stored as confirmed.
- **Freshness.** Notes carry a review-by date, and a note that is due is never presented as settled.
- **Linked notes.** When a note comes due, everything that depends on it is flagged too. Old facts
  are retired with an end date, never deleted.
- **Saved answers replay word for word**, with their evidence kept beside them. A hand edit or a
  changed source forces a re-check. A question that only looks similar is shown to you first.
- **Pinned sources.** Name the page a recurring answer rests on and the quote it must still hold.
  flarehand reports when it drifts.
- **A work log with the reason**, and an undo for the last entry.

</details>

<details>
<summary><b>Learns about you, with permission</b></summary>

- **Detects instead of asking.** Name, time zone, locale and tools come from your system. It never
  guesses your employer.
- **Does the work first.** On a first run you get the deliverable, then three optional questions and
  a choice: keep a knowledge base, or just this session.
- **Learns from your edits.** Cut the risks section twice and it offers to make that your default.
  At most one offer per session, answered mine, team, later or never.
- **Turns loops into your own workflows.** A chain of steps you repeat becomes a note, then a
  routed workflow with its own template and checks.
- **Reads your existing setup, if you let it**: CLAUDE.md, AGENTS.md, a style guide, or a pasted
  memory export. It shows what it would keep before keeping it.
- **A voice card** from one sample of your writing, used as rough guidance.
- **Roles in your own words.** The order it tries sources in learns from what you actually cite.
  New to a job? Thirty days of extra explanation, on request.
- **Always shows its working.** `about-me` lists every learned item, the layer it came from, and the
  command that undoes it. Every so often it checks in: keep, edit or forget?

</details>

<details>
<summary><b>Works for a team, not just for you</b></summary>

- **Playbooks.** A `.flarehand/` folder in a repository holds your team's templates, glossary, house
  rules, pinned sources and workflows. A company playbook can sit above team ones.
- **Shapes and rules layer differently.** Your template beats the team's, which beats the shipped
  one. Rules add up: a team rule always applies, and nothing can remove it.
- **Reviews use your standards.** Seven review lenses read your house rules and your repository's
  own linter settings. Each finding is confirmed by a second pass, and grades follow a fixed rule.
- **Nothing personal is shared.** Playbooks hold shapes and rules only, never notes, logs, answers
  or anything about a person. flarehand never pushes them for you.

</details>

<details>
<summary><b>Private, careful and portable</b></summary>

- **No telemetry.** The network is used only to fetch a source you are checking, or when you ask it
  to test your connection.
- **Sensitive data is your call, asked once.** A password, an id number or someone's health detail
  stops a save until you decide, and it tells you each time it applies that choice.
- **Fair notes about people.** It records behaviour, not character. Inferences and opinions stay
  marked as suspected. It keeps that someone is away, never why.
- **Hooks that stay out of the way.** They run in Python, always exit cleanly, and never write
  inside the plugin folder.
- **Runs in many agents.** Claude Code, Codex, Cursor, Gemini CLI, Copilot, and any tool that reads
  Agent Skills. Python 3.9 or later, standard library only.

</details>

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

Then try *"Turn these notes into a status update for my manager"*, followed by your notes.
[Getting started](docs/getting-started.md) walks through the first session.

## What it stores, and what it sends

- **Your knowledge base** is a folder of plain Markdown at `~/.flareware/flarehand`
  (`%USERPROFILE%\.flareware\flarehand` on Windows). It is written only after you say yes, kept in a
  local git history, and never pushed anywhere.
- **Session files** go to your system temp folder: snapshots of sources you cite, and the
  checkpoint saved before a compaction. The checkpoint is deleted when the session ends, and
  anything left is pruned after 7 days.
- **Team playbooks** are read from a `.flarehand/` folder in your repository, or a folder you name.
- **Network.** No telemetry. Your agent sends your conversation to its own model provider, as it
  always does.

The full detail is in [privacy and data](docs/privacy-and-data.md).

## Measured, not claimed

flarehand is tested with `claude plugin eval` on 37 realistic cases across roles. Each case runs
three times with the plugin and three times without, scored by a separate judge model. The numbers
below are the 1.0.0 confirmation run: one full run on the release commit, with an Opus agent and a
Sonnet judge.

| | With flarehand | Without |
|---|---|---|
| Mean score, all 37 cases | **0.97** | 0.83 |
| Work requests (28 cases) | **0.96** | 0.78 |
| Fired on requests it should ignore | 0 of 27 runs | |

The biggest differences show where it helps most:

| Case | With | Without |
|---|---|---|
| Doing the work first on a first run | 0.98 | 0.48 |
| Stress-testing a plan with grill mode | 1.00 | 0.52 |
| Keeping a legal question to the facts | 1.00 | 0.44 |
| Not inventing documentation links | 1.00 | 0.56 |
| Offering the right style for a runbook | 0.92 | 0.46 |

These cases are our own, and a model does the judging, so read them as a guide rather than a
benchmark. How the suite works, its caveats and the known gaps are in [evals](docs/evals.md). The scripts behind
flarehand also have over 800 unit tests.

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
to pass its own writing rules, and every change runs the unit tests and the validator. Please follow
the [code of conduct](CODE_OF_CONDUCT.md), and report security problems as [SECURITY.md](SECURITY.md)
describes.

## License

MIT. See [LICENSE](LICENSE). The flarehand name and mark belong to FlareWare Solutions.

<div align="center"><sub>Made by <a href="https://github.com/FlareWare-Solutions">FlareWare Solutions</a></sub></div>
