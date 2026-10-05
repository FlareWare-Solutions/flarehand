# flarehand

Turns a one-line work request into the deliverable it needs, grounded in real sources, and remembers
only what you approve.

You type one line. It works out what you actually need and asks only the questions that change it.
It finds the facts itself and labels every specific with where it came from. Then it produces the
thing you actually ship, checks it, and offers to keep what was worth keeping.

It is for anyone who ships work: engineering, support, product, operations, sales, marketing,
finance, HR, founders, freelancers and students. It works alone, for a team, or across a company.

This file covers the `flarehand` skill on its own. The plugin, with its hooks and the four entry
points, is described in the repository's top-level README.

## Contents

- What it does
- Install
- First run
- What it does not do
- What is inside
- For maintainers

## What it does

**The work you ship.** Twelve workflows and sixty templates, among them:

- postmortems, root cause, incident reports, escalations, knowledge articles, customer replies
- decision records, design docs, product briefs, business cases, project charters, OKRs
- test plans, user stories, specs, release notes, runbooks, SOPs, docs pages
- weekly updates, status reports, executive briefs, business reviews, investor updates
- job descriptions, interview scorecards, onboarding plans, performance reviews, one-on-one notes
- client proposals, statements of work, case studies, press releases, research proposals
- code and document reviews: seven graded lenses, every finding checked by someone who did not
  find it

**Grounding.** Every specific claim carries a label, such as `[verified: S3]`, `[your input]` or
`[ASSUMPTION, verify]`. Scripts check that each quote really is in the source and
the numbers match. They check that no URL was made up, and that the source is fresh enough.

**Learning how you work.** Your team probably has its own way of writing a postmortem or a status
update. Show it once, and it uses your version from then on. When it notices you make the same change
twice, it asks whether to keep it as your preference or your team's. It never decides that for you.

**Remembering.** What you learned, what you decided, what worked. Saved as plain Markdown you own,
and only when you say yes. At the end of a piece of work it shows a short numbered list, "Keep any of
this?". You reply with the numbers you want. Save an answer, and asking the same question next week
gives it back word for word.

**Two writing styles.** The default `plain` voice is short sentences, plain words and no em dashes.
For documents others reuse, it offers the Google developer-docs style. Switch with
`kb.py config --style plain|google|none`.

**Things it will not do.** Guess at a fact. Agree with you about what caused a problem before
checking. Give a legal conclusion or a dollar figure it cannot source. Write to your knowledge base
without asking.

## Install

The easiest route is the plugin, which adds hooks and the entry points. Its install commands for
Claude Code, Codex, Cursor, Gemini CLI and Copilot are in the repository's README and in
`references/cross-tool.md`. The rest of this section installs this one skill by hand.

The ZIP opens to a folder called `flarehand`. That same ZIP works everywhere below, except the
Claude Desktop chat route, which wants the `.skill` file. When you send this to someone who is not
technical, send both `flarehand.skill` and `flarehand.zip`.

**Needs Python 3** for the scripts. macOS and Linux have it. On Windows, open PowerShell and run
`py -3 --version`. If that fails, download the Python install manager from
`https://www.python.org/downloads/` and run it. It installs for you only, so it needs no admin
rights. Say yes when it offers to add Python to PATH.

**Save the attachment first.** If the file came by email, save it to your Downloads folder before
anything below. Explorer hides the `.zip` ending, so the file shows as `flarehand`. That is fine.

**Claude Desktop chat, and no terminal.** Double-click `flarehand.skill`. Claude Desktop opens a
preview with a **Save skill** button. Press it. In chat it can structure, draft and run its checking
scripts, but it cannot keep a knowledge base. The Code tab in the same app has no such limit.

**Claude Code on macOS or Linux.** Paste this into Terminal:

```bash
mkdir -p ~/.claude/skills && unzip -o ~/Downloads/flarehand.zip -d ~/.claude/skills && ls ~/.claude/skills
```

**Claude Code on Windows.** Paste this into PowerShell:

```powershell
$d="$env:USERPROFILE\.claude\skills"; New-Item -ItemType Directory -Force $d | Out-Null; Expand-Archive -Force "$env:USERPROFILE\Downloads\flarehand.zip" $d; dir $d
```

**Linux without `unzip`.** Use the tarball, because `tar` is always there:

```bash
mkdir -p ~/.claude/skills && tar -xzf ~/Downloads/flarehand.tar.gz -C ~/.claude/skills && ls ~/.claude/skills
```

**Codex, Copilot, Cursor, Gemini CLI and most other agents.** Same as above, but unzip into
`~/.agents/skills`, which nearly every agent reads. `references/cross-tool.md` lists the folder each
tool reads, and what its sandbox changes.

**No terminal at all.** In claude.ai, open Customize, then Skills, then the plus button, then Upload
a skill. Pick the same ZIP. Code execution must be on in settings.

**Your whole team, in a repository.** Commit the folder to `.agents/skills/`, which Codex, Copilot,
Cursor and Gemini read. Claude Code reads `.claude/skills/`. Share your team's templates and rules
in a `.flarehand/` playbook beside it.

**Check it landed.** Start a new session, then:

- Claude Code: type `/skills` and look for `flarehand`. Or run
  `python3 ~/.claude/skills/flarehand/scripts/doctor.py --capabilities`. On Windows use `py -3`.
- Other agents: run the same `doctor.py` line against the folder you unzipped into. In Codex,
  `$flarehand` calls the skill by name.
- claude.ai or Claude Desktop chat: ask "what kinds of work can you help me ship?". It should
  name this skill and offer the kinds of work it covers.

**If it does not pick up on its own.** Type `/flarehand` and your request on the same line. For a
whole team, add this to the repository's AGENTS.md or CLAUDE.md:

```markdown
## Work requests
For a deliverable, a review, a reply, a plan, a diagnosis, or saving and recalling notes, use the
flarehand skill before answering. General coding questions do not need it.
```

## First run

Ask it for something real. It does the work first, with sensible defaults, and asks nothing it can
detect for itself.

After the first piece of work it asks three optional things. What do you work on, in your own
words? Who usually reads your work? And, if you like, paste one thing you wrote for it to match. It also asks
whether it may keep a private knowledge base. Say "just this session" and nothing is written.

That folder is at `~/.flareware/flarehand`, or `%USERPROFILE%\.flareware\flarehand` on Windows. It
is plain Markdown. Nothing syncs and nothing uploads. You can open it in any text editor, and you can
delete it whenever you like.

It is also a git repository, so every change is recorded and any change can be undone. There is no
remote and nothing is pushed anywhere. `git -C ~/.flareware/flarehand log` shows what changed and
why. Git is optional. Without it, or with `"git": false` under `prefs`, everything else works the
same.

It fits itself to you as you use it, and it shows its working. `kb.py about-me` lists everything it
has picked up. Each line says which layer it came from, and the command that undoes it. Now and then it checks in:
here is what I learned, keep, edit or forget? What never bends, at any setting, is in
`references/adaptation.md`.

If you want to see it as a picture, it opens as an Obsidian vault. That is optional.

## What it does not do

Being straight about the limits saves you finding them the hard way.

**It cannot ground what it cannot reach.** Sometimes no web, file or MCP server can answer a
question. Then it says so, labels what it assumed, and lists what you need to confirm. It never invents a source.

**In claude.ai chat it cannot keep a knowledge base.** The method and the checking scripts still
work. It says so once, and offers a paste-ready "about me" block instead.

**Two people get the same facts, shaped for each of them.** Your saved answers are private to you.
When you ask the same question again, you get your saved answer back word for word. A colleague
asking the same thing gets the same facts, shaped for their role and their team's playbook. A
question that only looks like one you saved is shown to you first, never replayed on a guess.

**It will ask you questions.** More for things someone else acts on, fewer for a quick lookup. Say
"just go" at any point and it will proceed on stated assumptions.

## What is inside

```
SKILL.md          the router. Decides what you need and where to look.
references/       one file per workflow, plus grounding, sources, memory, privacy and setup
scripts/          Python, standard library only, nothing to install
assets/           the lookup tables, source tiers and the output templates
```

The scripts do the work that should never vary. They route a request, choose which sources to try
first and match a repeat question. They check quotes, numbers and URLs, find sensitive content, and
manage your notes. A lookup table returns the same answer forever. A model asked to remember a mapping
does not.

## For maintainers

```bash
python3 scripts/package.py             # build the archives for every skill, and the plugin folder
python3 scripts/validate_skill.py      # will it load in every tool
python3 scripts/check_output.py --style SKILL.md references/*.md
```

The unit tests and the live eval cases live in the flarehand repository, not in this folder, so an
install does not carry them. From a clone, run the repository's `tests/test_scripts.py` (no model,
about four minutes). Live evals need the plugin folder, because `claude plugin eval` targets a
plugin. The exact command, and how to check every case loads first, are in the repository's
`evals/consistency.md`.

Read the repository's `evals/consistency.md` before changing anything. Read `references/voice.md` before writing
anything, and run the style checker on it. The skill has to pass its own writing rules.

Three packaging rules exist for reasons that are not obvious, and `validate_skill.py` enforces all
three. No PowerShell script files, because Windows blocks downloaded ones. No binaries or launchable
files, because macOS gates those. No `.claude-plugin`, `agents`, `hooks` or `workflows` folder inside
the skill. Any of them makes Claude Code load the folder as a plugin instead of a plain skill.

The hooks live once, at the repository root in `hooks/`. One dispatcher, `hooks/hook.py`, serves
every tool that runs plugin hooks. It calls `scripts/voice_gate.py` and `scripts/checkpoint.py`.
Every hook exits 0 whatever happens, because a hook that fails can stop a compaction.

After a compaction an agent may keep only the start of `SKILL.md`. So the standing rules sit near
the top, before the pipeline. Keep them in the first 15,000 characters. `tests_checkpoint.py`
checks that.

**Improving it.** If you build a workflow or a template that works well, the skill saves it for
you. If it is worth having for everyone, open an issue at
`https://github.com/FlareWare-Solutions/flarehand/issues` with what it does and who would use it.
