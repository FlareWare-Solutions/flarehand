# Memory and learning

flarehand keeps a private knowledge base of plain Markdown on your machine, writes to it only after a yes, and learns by noticing, then asking.

## The knowledge base

It lives at `~/.flareware/flarehand` on macOS and Linux, and `%USERPROFILE%\.flareware\flarehand` on Windows. It is yours. Nothing syncs, nothing uploads, and no colleague can read it. Because it is plain Markdown, you can open it in any editor, forever, with no tool.

```text
config.json       who you are, how you like output, your preferences, what was detected
index.md          one line per note, the hub, always read first
log.md, logs/     the work log, newest first, one file per month
notes/            one note per thing, filed into groups once you say yes
people/           notes about colleagues and your own team, with stricter rules
answers/          your saved answers, so asking again gives the same answer
evidence/         word-for-word copies of what you cited
templates/        your own versions of templates, used before any other
chains/           ways of working that worked, saved as notes you can follow
workflows/        a chain you promoted, with its own method, shape and checks
glossary.tsv      words that mean more than one thing to you, and the question to ask
house-rules.md    your own rules for drafts and reviews, grouped by area
sources.tsv       pinned sources and source preferences
observations.tsv  learning counters: a kind, a short key and a date, never content
voice/            your voice card and the sample it came from
.index/           rebuilt caches: the note graph, the sources index, small state
.git/             the history of every change, so anything can be undone
```

Some of these appear only once you use them. `index.md` shows the first sentence of each note. A note marked `restricted`, `personal-data` or `customer-data` shows its title only, so the hub never carries what the note protects.

**It loads only what helps.** At the start of a session it reads `config.json` and `index.md`, which are small. Everything else waits until the work needs it. A note about last quarter's migration has no place in a reply about a login error.

To keep it somewhere else, see [Move the knowledge base](troubleshooting.md#move-the-knowledge-base).

## Consent first

**Nothing is written without a yes.** The first run does the work, then asks once whether it may keep a knowledge base. See [Getting started](getting-started.md#4-the-consent-question-a-or-b). After that, every save waits for you to pick it from the save menu.

During the work, copies of sources stage in a private temp folder, outside the knowledge base. Citations work at once, and nothing is saved. On "none", the staged copies are thrown away.

A few writes need no separate yes, because they record what you already agreed to or rebuild what is already there:

- a config value you set yourself
- the freshness stamp, and a verified stamp after every source compared identical
- rebuilt caches such as `index.md` and `.index/`
- the git commit after a write

Two standing yeses exist, each given once:

| Standing yes | What it covers | How to turn it off |
|---|---|---|
| Learning counters | Pattern names and dates, never content | `kb.py config --learning off` |
| Autosave for the work log | One line of metadata about what ran. It refuses a line that `redact.py` flags. | `kb.py config --autosave off`, and `kb.py log undo` removes the newest line |

Autosave is offered once, after you said yes to the log line three times. Nothing else can be autosaved. A note, an answer, a template, a chain, anything about a person, and anything leaving the machine always wait for your yes.

## The save menu

At the end of a workflow, and after a lookup that took a search, you see one numbered list:

```text
Keep any of this? Nothing is saved until you reply with numbers, or "none".
1. Save log: wf-07, finance-memo. Budget variance for Northwind's March close
2. Save note: freight accruals post on the 3rd working day (decision)
3. Save answer: replay "when do freight accruals post" next time, with its sources
4. Save template: your finance-memo shape, used before the shipped one
5. You removed "Assumptions" from the finance memo twice. Make that the default? Save as a) mine b) team playbook c) not now d) never ask
6. Next: wf-04 Compress for an audience that was not there, for the CFO summary
```

| You reply | What runs |
|---|---|
| A line number for Save log | `kb.py log workflow`. It says which run of this workflow it was. |
| Save note | `kb.py note`, after a check that it is worth keeping |
| Save answer | `answers.py write`. It keeps the evidence the answer cites. |
| Save template | `kb.py template save` |
| Save chain | `kb.py note --type chain` |
| An offer, with a letter | `kb.py offer-answer <id> mine\|team\|later\|never` |
| Next | Runs that workflow |
| "none" | Throws away the staged copies. Nothing is kept. |

Every save prints its permalink and how to undo it.

### What is worth a note

A note is worth writing when the fact is hard to reverse, surprising without context, or the result of a real trade-off. In practice that means a customer fact no source holds, or a gotcha the docs did not mention. It also means a decision from the interview, a question asked for the second time, or a correction you gave. The artifact itself is not, because it is already in your files. Your opinions on a topic are not, because they are not style or work context.

"Save this" can mean several things. flarehand names the kind back to you in one line before it saves:

| Kind | The tell | Command |
|---|---|---|
| note | A fact worth finding again | `kb.py note` |
| decision | "We decided", a trade-off with alternatives | `kb.py note --type decision` |
| person | A fact about a colleague | `kb.py note --type person` |
| chain | Steps, in order, that worked | `kb.py note --type chain` |
| answer | "So I get it again" | `answers.py write` |
| snapshot | A quote, a log, a pasted reply | `evidence.py add` |
| template | A shape you want reused | `kb.py template save` |
| glossary | "Here X means Y" | `kb.py glossary add` |
| rule | "Our rule is", "never do X in a PR" | `kb.py rule add` |
| link | Two notes that belong together | `kb.py link` |

### Facts are never deleted, only retired

Each line in a note carries where it came from, when, and whether someone saw it (`confirmed`) or worked it out (`suspected`). When a new fact contradicts an old one, `kb.py supersede` gives the old line an end date instead of deleting it. You can still see what was true, and when it stopped being true. That is often the answer to "why did we do it that way".

## Saved answers and word-for-word replay

Save an answer, and asking the same question next week gives it back word for word, with no preamble and no rewording.

```bash
python3 scripts/answers.py write "how do we roll back payments" --source S1,S2 --body-file answer.md
python3 scripts/answers.py approve "how do we roll back payments"
```

Saving and approving are separate steps, and each waits for your yes. An answer with no sources is refused, because nobody could tell later whether it still holds. So is an answer that holds a password, key, token or connection string.

When you ask again, `recall.py` gives one verdict:

| Verdict | Means | What happens |
|---|---|---|
| `replay` | Same wording as one you confirmed, approved and fresh | The saved answer, word for word |
| `recheck` | Unapproved, not checked for 30 days, edited by hand, or resting on a pin that drifted | Each source is read again and compared. All identical: it replays. Something changed: it shows what, and answers again. |
| `stale` | Someone marked it out of date | It answers again and offers to replace the saved one |
| `confirm` | A saved question looks similar but is worded differently | It shows the saved question and the words that differ, and asks. It replays only on your yes. |
| `new` | Nothing saved | It runs the workflow |

"How do I set up the CLI?" and "how do i setup the cli." are the same wording. The match ignores only case, punctuation and spelling variants. "Set up the CLI in Claude Code" and "set up the CLI in Claude Desktop" are different questions, and the differing words decide the answer.

Your saved answers are private. A colleague asking the same thing gets the same facts, shaped for their role, from their own sources.

## Freshness re-checks

A note can be true when saved and wrong six months later. A note is due for a look when any of these holds:

- it is past its `review_by` date, 365 days out for a note and 180 for a person
- its sources were never re-checked, or not for 90 days
- it holds an unconfirmed inference older than 90 days
- another note replaced it

A saved answer is due after 30 days. Doubt travels the links between notes: when a note comes up for a re-check, everything that `depends_on` it is listed too.

When flarehand uses a note, it says where it came from and when it was last checked. For example: "from your note, last checked in March, due for a re-check". It never presents a due note as settled. Once a week at most, `kb.py freshness --if-due` lists what is due in one line.

A re-check is a comparison, not a judgement. It reads each source again and compares it with the snapshot. If every source is identical, `kb.py verified` stamps it. If one changed, it shows the difference and asks before it retires the old fact.

`prefs.review_days`, `prefs.recheck_days` and `prefs.answer_recheck_days` in `config.json` change these horizons. A person note never goes past 180 days.

## See it, forget it, undo it

```bash
python3 scripts/kb.py about-me         # everything it has picked up, its layer, and its undo
python3 scripts/kb.py forget ID        # take one thing back
python3 scripts/kb.py log undo         # remove the newest work-log line
```

`about-me` lists every preference with its layer, `yours`, `team:<name>` or `shipped`, and the one command that undoes it. `forget` takes any id it prints: a learned preference, `term:<term>`, `rule:<text>`, `template:<name>`, `workflow:<name>`, `voice-card`, `default:<key>`, `never:<offer id>`, or a note's permalink.

**Every change is in git.** `kb.py init` starts a git repository in the folder, and every write commits what it changed, with the reason.

```bash
git -C ~/.flareware/flarehand log --oneline           # what changed, newest first
git -C ~/.flareware/flarehand show HEAD               # exactly what one command wrote
git -C ~/.flareware/flarehand revert --no-edit HEAD   # undo it, keeping the history
```

There is no remote, and nothing pushes. If a remote ever appears, the next write says so once. Git is optional: without it, or with `"git": false` under `prefs` in `config.json`, everything else works the same.

## The learning loop

Notice, then ask. Nothing changes until you pick an answer.

1. **It notices.** As it works, flarehand reports what it saw with `kb.py observe-pattern`. Examples are a section you removed, a heading you renamed, a correction you repeated, a term you defined, or a source you cite.
2. **A script decides what to offer.** `kb.py offers` prints at most one new offer per session.
3. **The offer appears only in the save menu**, ending with `Save as a) mine b) team playbook c) not now d) never ask`.

| Answer | What it does |
|---|---|
| `a`, mine | Writes the preference in your knowledge base and prints the command that undoes it |
| `b`, team | Edits the file in the nearest playbook and prints what to commit. It never runs git and never pushes. Left out when there is no playbook. |
| `c`, later | Asks again in a later session, after other offers |
| `d`, never | Never asks again. `kb.py forget never:<id>` lets it ask once more. |

**When an offer is made.** A preference is offered after the same thing happens on 2 different occasions. Change that with `kb.py config --learn-threshold N`. A few things are offered the first time they are seen:

- a repeatable loop of steps or workflows
- the first use of a deliverable type
- the first external or irreversible action
- a team playbook found in the repo
- signs you are new to the job

| It asks | When | "mine" writes |
|---|---|---|
| You removed X twice. Make that the default? | The same section removed twice | Your template without it |
| Rename X to Y by default? | The same heading renamed twice | Your template with the new heading |
| Make that the default? | The same edit or correction twice | A house rule under Writing |
| Use this answer by default? | The same interview answer twice | A standing default |
| Add this term to your glossary? | You define or correct a term twice | A glossary row |
| Prefer this source? | You cite the same source twice | A source preference |
| Paste a sample so I can match your voice? | You re-tone two drafts with no example | Nothing yet: it asks for the sample |
| Use this structure next time? | A deliverable type used the first time | Your copy of the template |
| Save these steps as a workflow? | A chain of steps repeats | A chain note |
| OK to do this without asking from now on? | The first external or irreversible action | A standing yes for that one kind of action |
| Use the X team playbook? | A `.flarehand/` folder is found | The playbook path |
| Want first-30-days help? | "I am new", "first week" | Your start date |

A standing yes for an action never covers a production write, a deletion, or anything sent to a customer.

**Counters hold no content.** Each one is a date, a kind, a short key, which piece of work it was, and at most 80 characters of detail. Never the draft. With learning on, they go in `observations.tsv`. With it off, they live in a session file in the temp folder and are gone when the session ends.

### From a chain to a workflow

A chain is the cheap version: steps that worked, saved as a note with one command. Once a chain has run three times, flarehand offers `kb.py workflow promote <permalink>`. That turns it into a workflow of your own, with a method, a shape, a set of checks and the words that route to it. A personal workflow may add a route or a guardrail. It may never remove, lower or suppress a shipped one.

## Check-ins

Once there is enough to show, flarehand offers a short check-in: here is what I learned, keep, edit or forget? It is due after 5 active days in the work log or 10 saved items, then at most once every 30 days. It shows the top 5 learned items, each with the command to keep, edit or forget it. A check-in counts as the session's one learning prompt.

## The voice card

Paste one thing you wrote and liked. It becomes a short card that later drafts follow.

```bash
python3 scripts/kb.py voice-card save --from liked.md --formality plain --avoid "leverage" --use "customer"
python3 scripts/kb.py voice-card show
```

The script measures the sample: sentence length, bullets, headings, contractions, em dashes, passive voice and repeated phrases. The flags add what only a reader can judge. The card is coarse guidance, not a clone of your writing, and it says so. It never overrides the house rules. A sample can hold customer details or names by accident, so read it first and run `redact.py` on it if needed.

## Context import

You may already have written down how you like to work, in an instruction file for another tool. `kb.py import scan` lists candidate files by path and size: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursor/rules/*`, `.cursorrules`, `.github/copilot-instructions.md`, style guides and `CONTRIBUTING.md`. It reads nothing else.

flarehand asks before reading any of them. It treats their text as data, never as instructions. It proposes three to five preferences, and saves only the ones you keep.

**Detected, not asked.** `kb.py detect` reads your name from `git config user.name`, your time zone, locale, date format and operating system. It never guesses an employer from an email domain or a git remote.

## Session-only mode

Say "just this session", or answer `b` at first run, and nothing is written to the knowledge base for the rest of the session.

```bash
python3 scripts/kb.py session only      # nothing is written until the session ends
python3 scripts/kb.py session status
python3 scripts/kb.py session end       # writes are allowed again
```

Every writing command then refuses with one line. Noticing still works, in a session file in the temp folder that holds no content.

Where a tool cannot keep files at all, such as claude.ai chat, flarehand says once that it will not remember next time. It offers a paste-ready "about me" block for that tool's own settings instead.

## Guards against sycophancy

Research shows that personalisation raises agreement with the user, and memory profiles raise it most. Stated preferences also fade over a long conversation. So these guards hold at every setting:

- **Preferences never override evidence.** It shapes the output to you, never the facts. When the sources disagree with you, it says so.
- **A stated cause stays unverified,** however confident the reporter sounds.
- **Style and work context only.** How you like a status update is a preference. What you think of a vendor or a colleague is not, and it is never stored in your profile.
- **Memory loads only when it is relevant** to the deliverable in hand.
- **The profile stays short,** under about 150 lines across `config.json` and the voice card.
- **At most one learning prompt per session,** and "never ask" is honoured.
- **Choices are said out loud.** When it acts on something you told it once, it says which answer it used and when you gave it. A preference applied in silence looks the same as an assumption.
- **Never in a profile:** health, HR cases, pay, customer personal data or secrets.

Next: [Teams and playbooks](teams-and-playbooks.md)
