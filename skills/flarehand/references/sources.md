# sources - where to look first, and how to walk the history

**Scope.** Which kinds of source to look in for this person and this question, and in what order.
How to answer "what changed" with git rather than a search. For checking what you found, read
`grounding.md`. For keeping a copy of it, read `evidence.md`.

## Contents

- Look before you ask
- The source kinds
- The order, from a script
- Roles, and a role of their own
- Pins and team preferences
- Learning from what they cite
- Project detection
- Walk the history, not search
- Pinned sources
- What no source covers

## Look before you ask

Finding facts is your job, never the person's. If the answer could differ from one team or one
project to the next, look it up. Table columns, a flag's behaviour, which file owns a feature, how
their team ships a release. If the answer would be the same anywhere, general knowledge is fine,
labelled as such.

Look in the cheapest place that could hold it first. What they said this session costs nothing.
Their knowledge base costs one command. The repository and its history are on disk. The web is
last, because it is the slowest and the least sure.

## The source kinds

| Kind | What it holds | Default tier |
|---|---|---|
| `user` | What the person said or pasted this session | T0 |
| `kb` | Their knowledge base: notes, saved answers, kept evidence | T0 |
| `repo` | Files in the repository they work in | T0 |
| `git` | That repository's history: commits, diffs, blame | T0 |
| `playbook` | Their team's written way of working: `.flarehand/` playbooks, onboarding, runbooks | T0 |
| `mcp` | MCP servers the harness has, such as a ticket tracker | T3 until you say otherwise |
| `official` | Official documentation, specs, changelogs, standards | T2 |
| `secondary` | Reputable secondary sources: known publications, vendor blogs, books | T3 |
| `forum` | Forums, Q&A sites, personal blogs | T4 |

An MCP server can be a system of record, such as an issue tracker, or a search tool. Say which when
you stage what it returned: `--tier T0` for a system of record. `grounding.md` has the tiers.

## The order, from a script

The same source matters differently to different people. So the order comes from a script, not from
memory:

```bash
python3 scripts/sources.py order "<their words>" --path <the folder they are working in>
```

It combines five signals, the same way every time. `user` and `kb` always come first.

1. **The question.** "Why did this change" puts `git` first. "How do we" puts `playbook` first.
   "Which version" puts `official` first. "The ticket" puts `mcp` first. The words live in
   `assets/source-tiers.tsv`, as `signal` rows.
2. **Their project.** A git repository lifts `repo`. A file that names a technology, such as
   `pyproject.toml`, lifts `official` and names the docs to prefer.
3. **Their roles.** Each kind of work has a preferred order of source kinds. A developer starts from
   the repository and its history. A support analyst starts from the team playbook and the ticket.
   Most people do more than one kind of work, so the orders merge, and the stronger tier wins.
4. **Their pins and their team's preferences.** A kind or a domain fixed at `primary`, `secondary`
   or `never`.
5. **Their usage.** A kind or a domain that keeps helping them moves up, after several different
   days.

Each row prints a concrete next step for this harness and this folder. That means the `kb.py search`
to run, the repository to search and the `git log` to start from. It also names the playbooks, the MCP
servers and the official docs domains it found. Look at the rows in order. Look at a row marked
`only_if_weak` only when nothing so far gave a T0 to T2 source with a word-for-word quote.

**Hints.** A line that starts with `Hint: ` is an action to take this session. The `--json` output
lists them under `hints`. One says the question asks what changed, so walk the history. Another
says the person is new and the script found no playbook, so ask where their team keeps onboarding notes.

## Roles, and a role of their own

`sources.py role` prints every role their own words point at, because most people do more than one
kind of work. Confirm the list, then set it with `sources.py role --set <role>,<role>`. Add or drop
one with `--add` or `--remove`. Roles change only with a yes.

When nothing on the list fits, they can define one:

```bash
python3 scripts/sources.py role --new <name> --like <closest role>
```

That writes `source-tiers.tsv` in their knowledge base, read after the shipped table. A role there
replaces the shipped rows for that name. Edit it to change the order. `sources.py kinds` shows what
each kind holds and which ones their roles use.

When someone keeps citing kinds that belong to a role they do not have, `sources.py role` suggests
adding it. When one of several roles goes unused for months, it suggests reviewing it. It never
changes a role on its own.

## Pins and team preferences

```bash
python3 scripts/sources.py pin official primary
python3 scripts/sources.py pin forum never
python3 scripts/sources.py pin docs.example.com primary
python3 scripts/sources.py pin forum --clear
```

A pin takes a source kind or a domain. It holds until cleared. `never` removes a kind even when the
question asks for it, and drops a domain from the preferred list. Only the question's own signals
rank above a pin.

A team can set the same preferences in its playbook's `sources.tsv`, as `prefer` rows. The
knowledge base can hold that file too. A personal pin beats a team preference for the same kind or
domain, because a preference is a shape, not a check.

`sources.tsv` columns are `type`, `key`, `value`, `expect` and `note`:

| type | key | value | expect |
|---|---|---|---|
| `prefer` | a kind or a domain | `primary`, `secondary` or `never` | empty |
| `pin` | the recurring question's intent | a URL, a path, `git:<rev>:<path>` or `mcp:<server>:<id>` | the quote it must still hold |

## Learning from what they cite

Ask once, at first run: *"May I keep a list of which kinds of source help you, such as your
repository or a docs site? Kinds, domains and dates only, never what you asked or what I answered."*
Then run `sources.py learning --on` or `--off`.

With it on, step 9 runs `python3 scripts/sources.py used <S# ids or locators>`. It records the kind,
the web domain if there is one, and the day. No question, no answer, no address, no content.

A kind or a domain moves up only after three uses on three different days, within sixty days. One
busy afternoon moves nothing. Learning never overrides a pin, because a kind pinned low gets used
less and so cited less. When their citations disagree with a pin anyway, the order shows a
suggestion. Ask before changing it. Work they saved counts too, whether or not the list is on,
because they approved keeping it.

**New-starter mode.** When `kb.py init --started` recorded a date in the last thirty days, `playbook`
moves to primary, and its hint says to read onboarding pages first. After the first month, a note
says why the order changed back.

## Project detection

```bash
python3 scripts/sources.py project --path <folder>
```

It looks in the folder and its parents, up to the repository's top, for files that name a
technology. Each one names the official docs to prefer.

| File | Technology | Docs |
|---|---|---|
| `package.json` | JavaScript | nodejs.org, developer.mozilla.org, docs.npmjs.com |
| `pyproject.toml`, `requirements.txt` | Python | docs.python.org, packaging.python.org |
| `go.mod` | Go | go.dev, pkg.go.dev |
| `Cargo.toml` | Rust | doc.rust-lang.org, docs.rs |
| `pom.xml`, `build.gradle` | Java and Kotlin | docs.oracle.com/en/java, docs.gradle.org |
| `pubspec.yaml` | Dart and Flutter | dart.dev, docs.flutter.dev |
| `*.csproj` | .NET | learn.microsoft.com/dotnet |
| `Gemfile` | Ruby | ruby-doc.org, rubygems.org |

The full list is the `project` rows of `assets/source-tiers.tsv`. A page on one of these domains
stages as T2 by default. A known forum stages as T4. Anything else on the web stages as T3 until you
say otherwise.

## Walk the history, not search

A search ranks text by words. The history holds the record of what changed, when, by whom and why.
That answers questions a search cannot, and diagnose, reconcile, enumerate and review ask exactly
those questions. Use a search to find the first thing. Then walk.

| The question | The move | Worth it when |
|---|---|---|
| What calls this, or what uses it | `git grep -n '<name>'` | Removing or renaming anything |
| Which commit added or removed this text | `git log -S '<text>' --oneline` | You have the exact line |
| Which commits touched lines matching a pattern | `git log -G '<regex>' --oneline` | The text varies, such as a changed number |
| How did this function or range evolve | `git log -L <start>,<end>:<file>` or `git log -L :<func>:<file>` | One function, many small edits |
| Who last changed each line, and in which commit | `git blame -L <start>,<end> <file>` | A single line looks wrong |
| Where did this file come from | `git log --follow --oneline -- <path>` | Someone renamed or moved it |
| What keeps changing alongside this | `git log --name-only --format= -- <path>`, then count the other files | A fix in one place keeps breaking another |
| What did it look like then | `git show <rev>:<path>`, with `git rev-list -1 --before=<date> HEAD` | Comparing now with a known-good date |
| What changed in a window | `git log --since=<date> --until=<date> -- <path>` | "It broke last week" |
| Why is it written this way | `git log -S`, then `git show <rev>` to read the message | The commit message is the answer |

Cite a file at a revision as `git:<rev>:<path>`. Stage it with
`python3 scripts/ground.py fetch git:<rev>:<path>`, which resolves the revision to a full hash so
the citation does not move when the branch does.

**Where each workflow needs this.** A diagnosis asks what changed, so walk the history before you
form a theory. A reconcile asks when two things stopped matching, so compare `git show` at two
dates. An enumeration has to be exhaustive, so use `git ls-files` or `git grep -l`, not a ranked
search. A code review has to find the callers of anything removed, so `git grep` for each one.

**It is not free.** A walk costs more commands than a search, and `git log -L` and `-G` read the
whole history. Do it when the question is about a link, a cause or a change. A single fact with a
citation stays one search and one quote.

## Pinned sources

A question that comes up often should get the same source every time. A pinned source names the
question's intent, the canonical locator, and the quote that source must still hold.

```bash
python3 scripts/ground.py pins add release-process --locator https://example.com/release \
  --expect "Releases ship on the second Tuesday"
python3 scripts/ground.py pins plan
python3 scripts/ground.py pins check
```

`pins check` re-fetches each one and reports `ok`, `drift` or `gone`. It fetches a URL, reads a file,
and reads `git:` with `git show`. An `mcp:` item is read by you: save its text and pass it with
`--results`. The check date goes in the knowledge base's `.index/state.json`, never in the skill.
`grounding.md` has the rest.

## What no source covers

Say so plainly rather than filling the gap. No document does not mean no team way. Ask how their
team does it, and offer to save their version, in their knowledge base or their team's playbook.

When a request names a system you cannot reach, say which one, and ask for the piece you need.
