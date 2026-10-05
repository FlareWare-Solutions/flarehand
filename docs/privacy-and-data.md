# Privacy and data

This page lists exactly what flarehand stores and where, what it sends over the network and when, and how to delete all of it.

## The short version

- flarehand has no server, no account, no telemetry and no analytics. It sends nothing to Flareware.
- It keeps a private knowledge base on your machine, and only after you say yes.
- Session files go to your system temp folder and are deleted after the session, or after 7 days at most.
- Its scripts touch the network only to fetch a page you or a tool named, or to run a link or web check. Each case is listed below.
- Before anything leaves your machine, it scans the text for credentials and personal data, shows you what it found, and lets you decide.
- It never writes inside the plugin folder.

**Your AI tool is separate.** flarehand runs inside an agent such as Claude Code, Codex or Cursor. That tool sends your conversation, and whatever the agent reads, to its model provider under that tool's own terms. flarehand does not change that. It only decides what the agent reads from your knowledge base, and it reads only what the current request needs.

## What is stored, and where

### On your machine, after your yes

| What | Where | When it is written | How long it stays |
|---|---|---|---|
| The knowledge base | `~/.flareware/flarehand`, or `%USERPROFILE%\.flareware\flarehand` on Windows | After you answer `a) yes` at first run, then only for the save-menu lines you pick | Until you delete it |
| Its git history | `.git/` inside the knowledge base | After every write, recording that write | Until you delete it. There is no remote. |
| A pointer to a moved knowledge base | `~/.flareware/flarehand/config.json`, holding only the new path | Only when you run `kb.py init --root <folder> --set-default` | Until you delete it |
| Team playbook files | `.flarehand/` in your repository | Only when you run a command with `--team`, or `kb.py playbook init` | Until you remove them. flarehand never commits or pushes them. |

The knowledge base holds plain Markdown and a few small tables. Its layout is in [Memory and learning](memory-and-learning.md#the-knowledge-base). In particular:

| File or folder | What it holds |
|---|---|
| `config.json` | Your name, your role in your own words, your usual readers, your tools and your settings. What `kb.py detect` found: time zone, locale, date format and operating system. Which Python to use. |
| `notes/`, `people/`, `chains/` | Notes you chose to save |
| `answers/` | Saved answers, each with the slice of the ledger it cites |
| `evidence/` | Word-for-word copies of sources a saved item cites |
| `templates/`, `workflows/`, `glossary.tsv`, `house-rules.md`, `sources.tsv` | Your own shapes and rules |
| `observations.tsv` | Learning counters, only with learning on: a date, a kind, a short key, which piece of work, and at most 80 characters of detail. Never the text of a draft. |
| `.index/usage.jsonl` | With learning on: which kinds of source and which web domains helped, and the day. No question, no answer, no full address. |
| `.index/state.json` and other caches | Rebuilt from the notes: the note graph, the sources index, and dates such as the last freshness check and pin check |
| `voice/` | Your voice card and the sample it came from, only if you gave one |

### In the system temp folder, without asking

These are session state, not knowledge. They never go into the knowledge base, so they need no yes. Python's `tempfile` module picks the folder: `%TEMP%` on Windows, `$TMPDIR` on macOS, `/tmp` on Linux.

| What | Where in the temp folder | What it holds | Deleted |
|---|---|---|---|
| Staged snapshots and the ledger | `flarehand-staging/<id>/` | Copies of the sources the agent read this session, `sources.jsonl` and `claims.jsonl` | On "none" in the save menu. Otherwise files older than 7 days are dropped the next time anything is staged. |
| The compaction checkpoint | `flarehand-staging/checkpoints/` | Written just before your tool compacts a long conversation. It holds the job, your own words, every labelled claim and its source, and the MISSING list. It also holds unanswered save-menu lines, what was already saved, the files written and the latest draft. | When the session ends, or after 7 days if a crash left it behind. VS Code has no session-end event, so there it waits for the 7 days. |
| Hook state | `flarehand-staging/hooks/` | Per conversation: whether flarehand ran, how far through the transcript the hook has read, and the transcript's path | After 7 days |
| Session files | `flarehand-sessions/` | Session-only mode, and learning counters when learning is off. No content. | After 7 days |

On macOS and Linux, the staging folder, the checkpoint and the hook state are created readable by your user account only. Set `FLAREHAND_SESSION_DIR` to move the session files somewhere else.

### Never

- Nothing is written inside the plugin or skill folder. Installers replace it on every update.
- Nothing is written to your knowledge base before you agree to keep one.
- Nothing is uploaded or synced. There is no cloud copy.

## What goes over the network, and when

The scripts use Python's standard library and make network calls in these cases only:

| When | Script | Request | Sent to |
|---|---|---|---|
| The agent stages a web page as a source | `ground.py fetch URL` | One GET of that page. The user agent says `flarehand-ground/1.0 (an agent skill fetching one page for a person)`. | The site in the URL |
| A pinned web source is re-checked | `ground.py pins check` | One GET per pinned URL | The pinned sites |
| You or the agent ask whether a draft's links are alive | `ground.py urls --live` | A HEAD, or a GET if HEAD fails, per URL in the draft | The sites in the draft |
| You or the agent ask whether a dead link ever existed | `ground.py urls --wayback` | One query per dead or unseen URL, carrying that URL | `archive.org`, the Internet Archive |
| You ask whether this machine can reach the web | `doctor.py --check web` | One HEAD request | `https://example.com/` |

Rules that govern those calls:

- **Only URLs it saw.** The agent fetches only a URL that appeared in your words or a tool result this session. It never guesses one.
- **No URL check is on by default.** `--live` and `--wayback` run only when named. `doctor.py --capabilities` uses no network unless `--check web` is given.
- **Nothing about you is sent.** A fetch carries the URL and the standard request headers, never your notes, your draft or your config.
- **A fetched page is data.** `ground.py fetch` keeps the visible text, drops scripts and styles unread, and runs nothing. Text in a page that reads like an instruction is treated as text to quote.
- **In the Codex sandbox the network is off**, so none of these calls work there. Grounding falls back to files, git, MCP servers and what you paste.

Everything else stays local: `classify.py`, `sources.py`, `recall.py`, `answers.py`, `evidence.py`, `kb.py`, `layers.py`, `redact.py`, `check.py`, `check_output.py`, `review.py`, `package.py`, `validate_skill.py`, and the hooks. Some of them run local `git` commands, such as `git show` to read a file at a revision, or `git config user.name` to detect your name. None of them talks to a git remote.

**MCP servers and your tool's own web tools** are your tool's, not flarehand's. The agent may use them to find sources, under your tool's permissions. flarehand treats any call that changes data as a production write. That includes a POST, PUT or DELETE, an MCP tool that writes, a deploy or a force push. It makes one only when you asked for the change in plain words this session.

### What the doctor reads

`doctor.py` only reads. It looks at:

- your operating system, Python version, shell, and whether git is installed
- the names of environment variables, to tell which agent is running. It never reads their values, and it skips any name containing KEY, TOKEN, SECRET or PASSWORD.
- the MCP config files of Claude Code, Claude Desktop, Copilot, Codex, Cursor, Gemini and VS Code, for **server names only**. Those files can hold URLs with tokens in them.
- whether a knowledge base and playbooks exist
- your time zone and locale

## What the hooks do

Hooks run only in tools that support plugin hooks. All five go through one launcher, `hooks/run-hook.cmd`, and one Python dispatcher, `hooks/hook.py`. Every hook exits 0 whatever happens, never asks, never blocks, never writes in the plugin folder, and makes no network call.

| Hook | Event | What it reads | What it writes | What it prints |
|---|---|---|---|---|
| Session start | Session starts, resumes, clears or compacts | After a compaction, whether a checkpoint exists | Nothing | One line naming the flarehand skill to use for each kind of work request. After a compaction, one more line naming the checkpoint file to read. |
| Prompt submit | Before each of your messages | The transcript file your tool names, only the part added since last time | The hook state file in the temp folder | Once flarehand has run in this conversation, one line of house voice: plain words, no em dashes. Otherwise nothing. |
| Stop | When the agent finishes a reply | The last reply and the transcript | Hook state | Nothing, unless you turned the gate on with `kb.py config --voice-gate on`. Then a reply with an em dash is held once for a rewrite. Off by default. |
| Pre-compact | Before your tool compacts the conversation | The transcript | The checkpoint file in the temp folder | Nothing |
| Session end | When the session ends | Nothing | Deletes this session's checkpoint | Nothing |

Hooks act only in a conversation where flarehand ran. The prompt-submit and stop hooks also skip code, inline code, URLs and HTML when they look for em dashes.

Tools differ. Gemini CLI runs none of these hooks, by design. Codex shows you the hooks for review before they run. Cursor does not run the stop gate. See [Install](install.md#what-works-where).

## Before anything leaves your machine

"Local is fine. Outbound is a decision, and it is yours." Raw customer data can sit in your knowledge base, which is on your machine and does not sync. Content may be about to leave, by email, a ticket comment, a PR comment, a post or a customer reply. At that moment flarehand runs the redaction scan:

```bash
python3 scripts/redact.py DRAFT_FILE
```

It looks for:

- credentials, tokens and connection strings, in config form and in plain sentences
- API keys with a known prefix, such as Stripe, Slack, Google, GitHub, OpenAI and Anthropic
- government ids and card numbers
- email addresses and phone numbers
- common English words for health and reasons for absence
- dollar amounts
- IP addresses and internal hosts, plus any domain in your `## Internal domains` house rules or `prefs.internal_domains`
- company names with a corporate suffix such as Inc, Ltd or LLC, and tenant ids
- customer, contract and invoice numbers
- file paths with a username in them
- `[opinion]` lines

Every rule lives in `skills/flarehand/assets/redact-patterns.tsv`, so you can read exactly what it matches.

**It never redacts silently, and it never refuses to go on.** It shows what it found and offers three choices. Send as it is. Redact it, where `redact.py --apply` writes a cleaned copy. Or stop and check with whoever owns the data.

A credential gets its own sentence, because someone has to rotate it. So does another customer's name in a reply.

**It is a pattern check, not a reader.** It cannot know that a bare name like "Northgate" is a client. It misses a company name with no known suffix, and a token split across two lines. It misses health words it does not know or in another language. It misses family circumstances, protected characteristics, and anything confidential under a signed agreement. So flarehand also reads the draft with the audience in mind.

**Examples use reserved data,** and the scan lets it through:

- email addresses at example.com, example.org or example.net
- phone numbers from 555-0100 to 555-0199
- IP addresses in 192.0.2.x, 198.51.100.x or 203.0.113.x
- a company whose name starts with Example

**Outbound text carries only confirmed facts.** Nothing interpreted or assumed goes into text someone else will read. An ambiguous phrase stays as you wrote it, with the question in the notes after the draft.

## Sensitive data rules

### Sensitivity levels

Every note records one, and the level travels with the note.

| Level | Means | Example |
|---|---|---|
| `public` | Could go on a website | A product feature description |
| `internal` | Fine inside your organisation | A process note |
| `customer-data` | Belongs to a client | Case details, their config, their volumes |
| `personal-data` | Identifies a person | Anything about an individual. Notes in `people/` by default. |
| `restricted` | Regulated or contractual | Payroll, signed terms, security findings |

The hub `index.md` shows only the title of a `restricted`, `personal-data` or `customer-data` note.

### Asked once, then said out loud

Some things deserve a question before they land in your files, because a git commit keeps what it saves. The scripts stop the first time, ask, store your answer, and say which answer they used every time it applies.

| What | Asked as | Answers |
|---|---|---|
| Passwords, keys, tokens, connection strings | `credentials_in_notes` | `keep` or `redact` |
| Government ids and full card numbers | `ids_in_notes` | `keep` or `redact` |
| Health, or why someone is away, in a note about a person | `health_in_notes` | `keep` or `leave-out` |

`kb.py choice` lists your answers. `kb.py choice KEY --clear` makes it ask again. A kept credential that is still live needs rotating all the same.

No script can spot a protected characteristic, such as age, disability, pregnancy, religion, race, sex, sexual orientation, gender identity, or family or marital status. flarehand asks in the session before keeping any of them. A formal HR document about one person is drafted in the session and not saved, because HR's process holds that record. Examples are a review, a warning or an improvement plan.

Two things never bend. Anything a signed agreement says not to keep stays out. Anything leaving the machine goes through `redact.py` and waits for your yes, every time.

### Never kept

The scripts refuse these:

- A saved answer that holds a password, key, token or connection string, or that cites a snapshot holding one.
- A work-log line written by autosave that `redact.py` flags.
- A source that is one of flarehand's own reference files. Guidance is not evidence.

flarehand's rules keep these out, and the playbook commands write only shapes and rules:

- In your profile (`config.json` and the voice card): health, HR cases, pay, customer personal data, secrets, or your opinions on a topic.
- In a team playbook: notes, logs, saved answers, evidence, learning counters, voice samples, and anything about a person.

## Notes about people

Notes about colleagues are useful, and they are about real people who never agreed to be written about. The defaults flarehand suggests:

- **Behaviour, not character.** "Asked for load-test numbers before approving the design, on 2026-08-14" is useful and fair. "Difficult to work with" is neither.
- **Observed and inferred stay apart.** What you saw is `status: confirmed`. A pattern you worked out is an `[inference]`, and your own view is an `[opinion]`. Both stay `status: suspected`, and the scripts refuse to mark them confirmed.
- **Source and date every line.**
- **Only what serves the work.** Who owns and decides what, how they like to receive things, what they committed to.
- **Availability, never the reason.** "Away until 2026-10-15" is fine. Why is not.
- **They expire.** A person note comes up for review after 180 days at most.
- **Write as if they will read it.** They may have a legal right to see notes about them, opinions included. Where they work decides which law applies, so HR confirms it.
- An `[opinion]` line in anything outbound is flagged by `redact.py` and left in place even with `--apply`, so you add whose view it is or remove it.

How you write about people is your call. Two things hold whatever your style: inferences and opinions stay suspected, and health details are asked about once.

## For legal, finance and HR

flarehand drafts, summarises and compares. It never gives a legal conclusion, a liability figure or a computed amount, and it never advises or signs. It shows the source text and says who decides. A security questionnaire is answered only from evidence you supplied, with every unsupported claim marked, because someone signs it.

## Deleting everything

To delete one item, use `kb.py forget ID` (see `kb.py about-me` for ids). To delete everything:

1. **Remove the plugin.** See [Install](install.md#uninstall).
2. **Delete the knowledge base and its history.** On macOS and Linux:

   ```bash
   rm -rf ~/.flareware/flarehand
   ```

   On Windows, in PowerShell:

   ```powershell
   Remove-Item -Recurse -Force "$env:USERPROFILE\.flareware\flarehand"
   ```

   If you moved it with `--set-default`, delete the folder you chose as well. The default folder then holds only the pointer.
3. **Delete the session files.** On macOS and Linux:

   ```bash
   rm -rf "${TMPDIR:-/tmp}/flarehand-staging" "${TMPDIR:-/tmp}/flarehand-sessions"
   ```

   On Windows, in PowerShell:

   ```powershell
   Remove-Item -Recurse -Force "$env:TEMP\flarehand-staging", "$env:TEMP\flarehand-sessions"
   ```

   These clear themselves within 7 days anyway.
4. **Team playbooks** are files in your repository. Remove them the way you remove any committed file.

To keep your notes but erase their history, delete only the history: `rm -rf ~/.flareware/flarehand/.git`. The next write starts a fresh history from what is in the folder then. There is no remote, so this erases every copy of the history. Removing a credential from a note does not remove it from the history, so this is the way to do that.

Nothing is backed up by flarehand. If you want a copy of your knowledge base somewhere, that is your call to make.

Next: [Commands](commands.md)
