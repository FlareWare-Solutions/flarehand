# Commands

This page lists every script and subcommand you might run yourself, with its purpose and main flags, checked against each script's `--help`.

## Before you run anything

You rarely need these. flarehand runs them for you as part of each request. They are here for when you want to look, fix or undo something by hand.

- **Where to run them.** From the `skills/flarehand/` folder of your install, as `python3 scripts/NAME.py`. On Windows use `py -3` in place of `python3`. Never rely on a script being executable.
- **No installs.** Python 3.9 or later, standard library only.
- **Help everywhere.** Every script takes `--help`, and so does every subcommand: `python3 scripts/kb.py note --help`.
- **Exit codes.** 0 means fine, 1 means a check found something, 2 means a usage error.
- **None of them asks a question or blocks.**

Common flags:

| Flag | On | Does |
|---|---|---|
| `--json` | Most scripts | Machine-readable output |
| `--root ROOT` | Every script that reads the knowledge base | Use another knowledge base folder. Default: `~/.flareware/flarehand` |
| `--session SESSION` | `kb.py`, `answers.py` | The conversation's id. Default: `FLAREHAND_SESSION`, then the tool's own id, then today. |
| `--explain` | `classify.py`, `recall.py` | Readable output instead of JSON |

## doctor.py

Reports what this machine and tool can do. Read only.

| Flag | Does |
|---|---|
| `--capabilities` | What grounding can use: OS, Python, which agent, shell, git, MCP servers, knowledge base and playbooks |
| `--check AREA` | Limit the probe to `os`, `python`, `shell`, `harness`, `tools`, `git`, `mcp`, `kb`, `playbooks`, `skills`, `detect`, `web` or `all`. Repeatable. `web` is the only one that uses the network, and runs only when named. |
| `--no-network` | Kept for older instructions. The network is never used unless `--check web` is given. |

## classify.py

Works out which route a request needs: route, workflow, template, ceremony, risk flags, and any question to ask first.

```bash
python3 scripts/classify.py "write a postmortem for last night's checkout outage" --explain
```

| Flag | Does |
|---|---|
| `request` | Your words, exactly as typed, or `-` for standard input |
| `--explain` | Readable output |
| `--table TABLE` | Use a different router table, for testing a change |
| `--no-glossary` | Ignore every saved glossary, yours and your team's, for this run |

## sources.py

Decides which kinds of source to look in first, for you and this question.

| Subcommand | Does | Main flags |
|---|---|---|
| `order QUESTION` | The source order for a question, with a concrete next step per row | `--path` the folder you work in |
| `role` | Show, set, add or remove your roles | `--set a,b`, `--add`, `--remove`, `--new NAME --like ROLE` |
| `kinds` | What each source kind holds, and which ones you use | `--path` |
| `project` | Which technologies this folder uses, and their official docs | `--path` |
| `pin SOURCE [TIER]` | Pin a kind or a domain to `primary`, `secondary` or `never` | `--clear` |
| `learning` | Turn the usage list on or off, clear it, or show its state | `--on`, `--off`, `--clear` |
| `used IDS` | Record which kinds and domains helped. Only when learning is on. | S# ids or locators |

Source kinds are `user`, `kb`, `repo`, `git`, `playbook`, `mcp`, `official`, `secondary` and `forum`.

## ground.py

The grounding protocol: raw fetch, the claim ledger, checks, checker briefs and pinned sources.

| Subcommand | Does | Main flags |
|---|---|---|
| `fetch TARGET` | Raw fetch a URL, a `git:<rev>:<path>` or a file, and add it as a source | `--tier T0..T4`, `--timeout`, `--max-bytes`, `--repo` |
| `source add` | Add a source from a paste, an MCP read or a file | `--kind web\|file\|git\|mcp\|user`, `--locator`, `--file` or `--text`, `--tier`, `--method raw\|summary\|user_paste`, `--source-date`, `--title` |
| `source list` | List this session's sources | `--markdown` prints a Sources list, `--used-in DRAFT` limits it to what a draft cites |
| `claim add TEXT` | Add a claim to the ledger | `--source S1`, `--quote`, `--prefix`, `--suffix`, `--type number\|date\|version\|cause\|policy\|general`, `--freshness fast\|medium\|slow\|static`, `--label`, `--topic general\|security\|legal`, `--stakes normal\|high`, `--from` claim ids for an inference |
| `claim support CLAIM` | Add a second source to a claim | `--source`, `--quote`, `--prefix`, `--suffix`, `--conflict` when it disagrees |
| `claim list` | List the claims | |
| `verify [CLAIMS]` | Run every script check on the claims | |
| `urls DRAFT` | Check every URL in a draft was seen | `--seen FILE`, `--seen-url URL`, `--live`, `--wayback` |
| `lint DRAFT` | Check labels resolve and every specific is labelled | `--strict` |
| `checker-brief CLAIM` | Print the brief for an independent checker | |
| `verdict CLAIM VERDICT` | Record a checker's verdict: `SUPPORTED`, `PARTIAL`, `NOT_SUPPORTED` or `CONTRADICTED` | `--by NAME` (required), `--note` |
| `pins plan\|check\|add\|remove [INTENT]` | Pinned sources for recurring questions | `--locator`, `--expect` with add; `--playbook` to write to a playbook's `sources.tsv`; `--results`, `--no-stamp` with check; `--path` |

## check.py

Every check on a draft, in one command. Prints `PASS` or a numbered `FIX:` list.

```bash
python3 scripts/check.py DRAFT_FILE --contract wf-05 --outbound
```

| Flag | Does |
|---|---|
| `file` | The draft, or `-` for standard input |
| `--contract ID` | Required sections for a workflow, such as `wf-03` |
| `--template PATH` | The template the draft follows |
| `--profile plain\|google\|none` | Which voice rules to apply |
| `--outbound` | It will leave the machine: run the redaction scan too |
| `--seen-url URL` | A URL you saw in a tool result or someone's words. Repeatable. |
| `--repo-root DIR` | Where cited repository paths live |

## evidence.py

Keeps word-for-word copies of what you cite.

| Subcommand | Does | Main flags |
|---|---|---|
| `add` | Stage a snapshot for this session | `--file` or `--text`, `--source`, `--kind`, `--sensitivity`, `--note`, `--keep` to save straight away (only after a yes) |
| `keep [HASHES]` | Move staged snapshots into the knowledge base | `--all` |
| `discard [HASHES]` | Throw staged snapshots away | `--all` |
| `get HASH` | Print a snapshot | `--max-chars` |
| `compare HASH` | Check a source still matches its snapshot. Exits 1 on a change. | `--file` the source's current text, or standard input |
| `list` | List snapshots | `--limit` |
| `verify` | Re-hash every kept snapshot, to catch hand edits | |

## recall.py

Says whether you already answered this question: `replay`, `recheck`, `stale`, `confirm` or `new`.

| Flag | Does |
|---|---|
| `question` | Your words |
| `--explain` | Readable output |
| `--exact-only` | Print just the exact form used for matching |
| `--key-only` | Print just the file key |

## answers.py

Your saved answers.

| Subcommand | Does | Main flags |
|---|---|---|
| `write QUESTION` | Save an answer. Refuses one with no sources or with a credential. | `--body` or `--body-file`, `--source` ids you used, `--no-sources`, `--archetype wf-NN`, `--replace` |
| `alias WORDING` | Record that a new wording asks the same question, after you confirmed it | `--to` the saved question |
| `approve QUESTION` | Mark an answer replayable | |
| `get QUESTION` | Print a saved answer | `--with-header`, `--max-chars` |
| `invalidate QUESTION` | Mark an answer out of date | `--why` (required) |
| `verified QUESTION` | Record that its sources still hold, resetting the 30 days | |
| `verify` | Re-hash every answer, to catch hand edits | |
| `list` | List saved answers | `--limit` |

## kb.py

The knowledge base engine. Every subcommand that writes refuses in a session-only session, and commits to the knowledge base's git history after it succeeds.

### Set up and settings

| Subcommand | Does | Main flags |
|---|---|---|
| `init` | Create the knowledge base, or update it | `--name`, `--role`, `--audience`, `--tools`, `--output`, `--voice plain\|google\|none`, `--adaptation guided\|balanced\|yours`, `--learning on\|off`, `--sample FILE`, `--started YYYY-MM-DD`, `--new-starter`, `--no-detect`, `--root DIR --set-default` |
| `detect` | Read your name, time zone, locale and OS. Read only. | |
| `import scan` | List instruction and style files to learn from. Read only. | `--path`, `--no-home` |
| `config` | Print the resolved configuration, or change a setting | See the table below |
| `session only\|end\|status` | Session-only mode: nothing written to the knowledge base | |
| `voice-card save\|show` | Keep or show a short card of how you write | `--from FILE`, `--formality`, `--use`, `--avoid` (repeatable) |
| `choice [KEY] [VALUE]` | List or record an answer once, so it stops asking | `--clear` to be asked again |

`kb.py config` settings:

| Flag | Values |
|---|---|
| `--adaptation` | `guided`, `balanced` (default), `yours` |
| `--style` | `plain` (default), `google` for write-ups, `none` |
| `--voice` | `plain` (default), `google`, `none` |
| `--save-menu` | `full` (default), `compact` |
| `--labels` | `inline` (default), `compact`. Never none. |
| `--autosave` | `off` (default), `log` |
| `--learning` | `on`, `off` |
| `--learn-threshold N` | Occasions before a preference is offered. Default 2. |
| `--audience` | Who usually reads your work |
| `--new-starter` | `YYYY-MM-DD` for 30 days of new-starter help, or `off` |
| `--default QUESTION=ANSWER` | A standing answer to an interview question |
| `--unset-default QUESTION` | Forget a standing answer |
| `--voice-gate` | `on` holds a reply with an em dash once, in Claude Code. `off` (default). |

### Notes and the graph

| Subcommand | Does | Main flags |
|---|---|---|
| `note TITLE` | Create a note | `--type`, `--sensitivity`, `--tags`, `--aka`, `--source`, `--body` or `--body-file`, `--permalink`, `--why`, `--force` |
| `observe NOTE` | Add one fact to a note | `--text`, `--source` (both required), `--category`, `--status confirmed\|suspected`, `--via`, `--tag` |
| `supersede NOTE` | Retire a fact, or a whole note, without deleting it | `--match TEXT` or `--by PERMALINK`, `--until` |
| `link SOURCE RELATION TARGET` | Add a relation between notes, such as `depends_on` | `--since` |
| `get NOTE` | Print a note, with when it was last checked | |
| `search [QUERY]` | Find notes | `--type`, `--tag`, `--status`, `--limit` |
| `neighbors NOTE` | Walk the graph from one note | `--depth`, `--direction in\|out\|both`, `--relation` |
| `themes` | Groups of linked notes, largest first | |
| `rests-on [SOURCE]` | What of yours rests on a source, so you know what a changed page affects | |
| `organize` | File notes into groups. A dry run unless `--apply`. | `--apply` |
| `index` | Rebuild `index.md` and the graph cache | |

Note types are `case`, `chain`, `concept`, `decision`, `guide`, `index`, `log`, `meeting`, `person`, `process`, `project`, `reference`, `setup`, `system` and `term`.

### The work log

| Subcommand | Does | Main flags |
|---|---|---|
| `log OP` | Append to the work log. OP is `capture`, `update`, `reorg`, `lint`, `setup`, `answer`, `review` or `workflow`. | `--why` (required), `--note`, `--workflow`, `--template`, `--auto` only with autosave on |
| `log undo` | Remove this month's newest entry | |

### Freshness and health

| Subcommand | Does | Main flags |
|---|---|---|
| `freshness` | What needs a look: review dates, sources, unconfirmed inferences, due templates | `--if-due` stays quiet if it ran in the last 7 days |
| `verified NOTE` | Record that a note's sources were re-checked and still hold | `--why` |
| `lint` | Read-only health check: broken links, duplicate keys, missing sources, overdue notes | |
| `stats` | Counts and a freshness summary | |
| `tidy` | Remove empty sections and empty keys, never a fact. A plan unless `--apply`. | `--apply`, `--undo STAMP` |
| `migrate` | Bring notes written by an older version up to date, never dropping a fact | `--apply` |

### Templates, workflows, glossary and rules

| Subcommand | Does | Main flags |
|---|---|---|
| `template get\|save\|list\|reset [NAME]` | Use, save or reset your own or your team's version of a template | `--from FILE` with save, `--team PLAYBOOK`, `--path-only` with get |
| `workflow save\|list\|promote\|reset [NAME]` | Save, list or promote a workflow of your own | `--from FILE`, `--title`, `--why` |
| `glossary add\|remove\|list [TERM]` | Words with more than one meaning, and the question to ask | `--meaning` (repeat for each), `--ask`, `--team` |
| `rule add\|remove\|list [TEXT]` | House rules that drafts and reviews are checked against | `--area` (default Writing), `--team` |
| `playbook init\|list\|add-path\|remove-path [DIR]` | Make, list or add a team playbook | `--path`, `--name`, `--parent`, `--owner` with init |

### Learning, and undoing it

| Subcommand | Does | Main flags |
|---|---|---|
| `observe-pattern KIND KEY` | Count a pattern for the learning loop: a kind, a short key, a date, never your text | `--detail` (80 characters at most), `--occasion` |
| `offers` | What the save menu offers to learn, at most one new one per session | |
| `offer-answer ID mine\|team\|later\|never` | Apply your answer to an offer | `--value`, `--from FILE`, `--team` |
| `checkin [show\|done]` | What was learned, to keep, edit or forget | `--if-due` stays quiet unless one is due |
| `about-me` | Everything it has learned about you, its layer, and how to undo each | |
| `forget ID` | Take back one thing `about-me` lists | |

Pattern kinds are `chain`, `deliverable-first-use`, `playbook-found`, `external-action`, `new-starter`, `section-removed`, `section-renamed`, `correction`, `edit`, `interview-answer`, `term-defined`, `term-corrected`, `source-cited`, `labels-stripped` and `retone-no-sample`.

## layers.py

Finds playbooks and reads a file through every layer. Read only.

| Subcommand | Does | Main flags |
|---|---|---|
| `list` | The playbooks in use, nearest first | |
| `which RELPATH` | Every layer that has this file, highest first | `--shipped PATH` |
| `tsv RELPATH` | Rows of a table from every layer, highest first | `--shipped PATH` |

Global flags: `--cwd DIR` where to start looking for a repository's `.flarehand/`, `--root`, `--json`.

## redact.py

Finds things you may not want to send outside.

```bash
python3 scripts/redact.py DRAFT_FILE
python3 scripts/redact.py DRAFT_FILE --apply
```

| Flag | Does |
|---|---|
| `file` | The file to check, or `-` for standard input |
| `--apply` | Write a redacted copy |
| `--out OUT` | Where the redacted copy goes. Default: alongside, with `.redacted`. |
| `--min low\|medium\|high\|critical` | Lowest severity to report |
| `--domain DOMAIN` | An internal domain to flag, added to the configured ones. Repeatable. |

## check_output.py

Checks a file against the writing rules and output contracts. `check.py` calls it, and you can run it alone.

```bash
python3 scripts/check_output.py --style docs/README.md
python3 scripts/check_output.py --style - < reply.txt
```

| Flag | Does |
|---|---|
| `files` | Markdown or text files, or `-` to read a reply from standard input |
| `--style` | The plain-language checks |
| `--citations` | Check `[verified: ...]` markers |
| `--contract ID` | Required sections for a workflow, such as `wf-03` |
| `--template FILE` | Check against a template's own sections, such as your own |
| `--profile plain\|google\|none` | `plain` is the house voice. `natural` is its older name. `google` adds the document rules. `none` turns house style off and keeps the rules that protect facts. |
| `--strict` | Treat warnings as errors |
| `--ledger PATH` | A `sources.jsonl`, or its folder, for S# ids |
| `--repo-root DIR` | Where a cited code path lives |
| `--max N` | Most findings to print. Default 60. |

## review.py

Grades a review the same way every time.

| Subcommand | Does | Main flags |
|---|---|---|
| `lenses` | List the seven lenses, plus any of your own | |
| `brief [LENS]` | The brief for one reviewer, or for the verifier | `--verify`, `--repo` |
| `rules` | The house rules from every layer, which every review checks against | |
| `configs` | The linter and style configs at the root of the repository under review | `--repo` |
| `grade FINDINGS` | Grade a JSON-lines findings file and print the report | `--only`, `--most-likely`, `--reviewed`, `--ticket`, `--tested yes\|no\|unknown` |

## package.py

Builds the shareable archives and the plugin folder. For maintainers.

| Flag | Does |
|---|---|
| `--formats skill\|zip\|tar.gz\|plugin` | Which outputs to build. Several allowed. |
| `--out OUT` | Where to write them. Default: `dist/` at the repository root. |
| `--check` | Verify the skills and stop, build nothing |
| `--skip-validate` | Package even if validation fails |

## validate_skill.py

Checks that every skill, the manifests and the hooks will load in every tool. For maintainers.

| Flag | Does |
|---|---|
| `--strict` | Treat warnings as errors |
| `--json` | Machine-readable output |

## Called by the hooks

You do not run these in normal use. They are here for when you want to see what a hook would do.

| Script | Does | Try it |
|---|---|---|
| `voice_gate.py` | The house-voice reminder, and the opt-in em-dash gate | `python3 scripts/voice_gate.py --remind < prompt-event.json` |
| `checkpoint.py save\|restore\|end\|show` | Keeps where the work stood across a compaction | `python3 scripts/checkpoint.py show --session SESSION_ID` |

Next: [FAQ](faq.md)
