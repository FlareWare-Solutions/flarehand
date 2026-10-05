# review-code - reviewing code, a change or a whole skill

**Scope.** Reviewing a pull request, a branch, a commit, a folder, or a whole skill or repository.
Each lens gets a grade, and someone checks every finding against the code before anyone sees it. For
reviewing a document, plan or deal, read `wf-10-critique.md`.

## Contents

- What your team already says
- Before you start
- The seven lenses
- Checking every finding
- Grading
- Fanning out to sub agents
- Reviewing a skill or a prompt
- The report, and posting it
- Making it theirs

## What your team already says

Most teams have written review rules somewhere. Read them before you judge anything, because the
team's own standard beats a generic one.

- **House rules.** Run `python3 scripts/review.py rules`. It lists every rule in `house-rules.md`
  from their knowledge base and from each team playbook, with the layer it came from. Rules add up.
  A team rule always applies, and a personal file can add a rule but never remove one.
- **The repo's own config.** Run `python3 scripts/review.py configs --repo <the repo>`. It names
  the linter and style configs at the repo root, such as `.editorconfig`, `pyproject.toml`, an
  ESLint or Prettier config, or `.golangci.yml`. Those rules are the project's standard. Skip what
  the tool already enforces, and say which tool ran.
- **Playbook templates.** A team playbook may carry its own `code-review` template or review lenses.
  `kb.py template get code-review` finds the right one.
- **Public standards, cited by URL.** Where the team says nothing, judge against a public source and
  name it. Read the current page before you quote one, because pages change.
  - Security: the OWASP Top 10, https://owasp.org/Top10/
  - Security: the OWASP Application Security Verification Standard,
    https://owasp.org/www-project-application-security-verification-standard/
  - Style: the language's own guide, such as PEP 8, https://peps.python.org/pep-0008/
  - Style: the Google style guides, https://google.github.io/styleguide/

`review.py brief <lens>` puts the house rules and the repo configs into every lens brief, so each
reviewer gets the same standard.

When they have no house rules, say so once, and offer to save the rules they state while you work:
`kb.py rule add`. When a team keeps a rule only in someone's head, it is not a rule a review can
check.

An AI review is a first pass. A person reads the code and decides whether each flag is real. That is
why this workflow verifies every finding.

Split the work between lints and review. Lints catch the rules you can write down. Review catches what
needs judgment. When the same finding keeps coming back, suggest a lint rule or a house rule.

**Look for an existing review skill.** A team may already have a review skill or checklist for that
language. Read `skill-discovery.md`. Use theirs rather than reinventing it.

## Before you start

Find out four things. Get them from the environment first, and ask only for what it cannot tell you.

1. **What is under review, against what.** For git: `git diff --stat <base>...HEAD` and
   `git log --oneline <base>..HEAD`. For one commit: `git show --stat <rev>`. For another version
   control system, its own diff command. For a whole folder, list the files and say you are
   reviewing all of it.
2. **What it was meant to do.** The ticket or request and its acceptance criteria. You judge
   completeness against that, so a review without it says so.
3. **Whether the author tested and analysed it.** If not, say that first. Still review it if they ask.
4. **Which lenses.** All seven by default. A small fix may not need perspectives. Ask once, and use
   their saved choice after that.

Reviewing is read only. Running tests locally is fine. Never push, merge, approve or comment without a
plain yes.

## The seven lenses

The full wording lives in `assets/review-lenses.tsv`. Run `python3 scripts/review.py lenses` to see it.

| Lens | The question |
|---|---|
| Correctness | Does it do what it says it does? Fact check every claim against the code. |
| Regressions | What worked before that this change could break? |
| Completeness | Does it cover the whole ask, including errors, edge cases, tests and docs? |
| Code quality | Would the team accept it, by the team's own standard for that language? |
| References and docs | Do the links, citations and docs hold up when you read them? |
| Dynamic or hardcoded | Will a hardcoded value go stale, or suit only one OS, role or tool? |
| Perspectives | Who will meet this change, and what would each of them notice? |

**Regressions need the base.** Find the callers of anything changed or removed. Grep finds the
callers in this repo. The history finds what used to depend on it: the moves are in
`references/sources.md` under "Walk the history", such as `git log -S <symbol>`, `git log -L`,
`git blame` and co-change counts. Neither one sees a caller in a repo that is not checked out
here. Say so, and ask, or read it through an MCP server when one is connected. For a database or
API change, check the public contract: what other systems read, and the published spec. Run the tests
on the base and on the change when you can, and compare.

**Perspectives come from the change, not from a fixed list.** There is no set number. You judge
which ones matter, and the person decides when the list is long.

1. **Find them.** Read the diff, the ticket and the repository. Think of the people who use it, run
   it, support it, integrate with it, audit it or maintain it. Add where it runs: the operating
   system, browser or device, the language, the scale, accessibility needs, and other AI tools.
2. **Keep only a real stake.** Write one sentence naming each perspective's concrete stake in this
   change, such as "integrators: the response field `rate` is renamed". No sentence means it is out.
3. **Rank them** by impact times likelihood. Impact is how bad and how reversible the harm is, and
   how much the person depends on it. Likelihood is whether the change touches what they use.
   Deadlines and compliance raise the urgency.
4. **Required ones always stay.** A team names standing perspectives in its house rules, under a
   heading such as `## Perspectives`. Every brief carries them, and they are never dropped.
5. **Merge overlaps.** Two perspectives that would find the same problems are one perspective.
6. **Decide the scope with the person when it is long.** Review every perspective with a real stake.
   The list may be long: more than about five optional ones, or more than one pass can do well. Then
   show the ranked list with your recommended picks, and let them choose. "Just go" accepts your picks.
7. **Read it as each one, through a scenario.** "As the on-call engineer at 3 a.m., reading these
   logs", not "think like an operator". When subagents are available, give each perspective its own
   reader with the same change and its own scenario. Otherwise take one pass per perspective, plus one
   plain pass, because a role can hide an ordinary bug.
8. **Report what you skipped.** List the perspectives reviewed, and those considered but skipped,
   each with a one-line reason.

Every finding cites its evidence, a file and line or a quote, and names the consequence for that
person. A role voicing a feeling is not a finding. A simulated user is not user evidence: say where
real user, accessibility or locale testing is needed. Leave mechanism-level problems, such as a
security flaw, to their own lens.

| The change | Perspectives that usually matter |
|---|---|
| A database migration | The DBA, the on-call engineer, every system that reads those tables |
| A checkout or signup page | A customer on a phone, a screen-reader user, support answering the tickets |
| A command-line tool | A Windows user, a first-time installer, the CI job that runs it |
| A public API change | The client developer, the mobile app on an older version, the docs reader |
| A billing or pricing change | The customer, finance reconciling the invoice, sales explaining it |
| A skill or a prompt | The least experienced person who installs it, someone on a different AI tool |

**Dynamic or hardcoded is the lens people skip.** A version number, a count, a model name or a URL
written into code or docs is true on the day someone wrote it. Look each one up when someone uses it,
or give it a checked date and a way to check it again.

## Checking every finding

AI reviewers are sometimes confidently wrong. So a finding is a claim until someone checks it against
the code. Whoever checks it must not be whoever found it.

| Verdict | Means | Needs |
|---|---|---|
| `confirmed` | Seen in the code | Where, and the lines that show it |
| `plausible` | Likely, not proven from the code alone | What would prove it |
| `rejected` | The code does not do that | One line saying why |

Report confirmed and plausible findings, each labelled. Drop rejected ones, but count them. A high
rejected count tells you the review was noisy.

Also say what the review did not look at. A review that lists its own blind spots is more useful than
one that sounds complete.

## Grading

Grades come from a rule, not a feeling, so the same findings always get the same grades.

```bash
python3 scripts/review.py grade findings.jsonl --most-likely "<one sentence>"
```

| Grade | When |
|---|---|
| `fail` | Any confirmed blocking finding |
| `concerns` | Any confirmed should-fix finding, or any plausible blocking finding |
| `pass` | Everything else, including minor findings |
| `not checked` | The lens was not run, or nothing records that it was |

The overall grade is the worst lens grade. A lens that was not checked never counts as a pass. It is
listed beside the overall grade instead.

Blocking means it must not merge. Should fix means fix it soon. Minor is a nit. Mark a problem in code the
change did not touch as `outside_change`. The report lists it without grading it.

Without a shell, apply the same table by hand, and order findings by severity, then lens.

## Fanning out to sub agents

Fanning out runs the lenses at the same time, each with a fresh read. It costs more time and usage, so
do it when they ask for it, or offer it when the change is large. Say what it costs.

**In a tool with sub agents, such as Claude Code:**

1. Start one sub agent per lens, all at once. Give each the output of
   `python3 scripts/review.py brief <lens>`, the diff or file list, and the standards you found.
2. Each returns JSON lines: one coverage line, then its findings, all marked plausible.
3. Start a separate checker with `python3 scripts/review.py brief --verify` and every finding. For a big
   review, split the findings across several checkers. None of them checks their own findings.
4. Put the checked lines in one file and run `review.py grade`.
5. Collect every `sources` entry from the checked findings. Run
   `python3 scripts/evidence.py add` for anything a sub agent quoted but did not stage.
   Run `python3 scripts/evidence.py list` before you offer to save anything. A sub agent
   stages into the same folder you do, so otherwise you never learn it is there.

Skip step 5 and a fanned-out review loses what each sub agent read. A finding nobody can re-read is
a finding nobody can re-check.

Use the model they ask for. Otherwise, give the checker a model at least as capable as the reviewers.

If a sub agent fails, for example because a sign-in expired, rerun only that lens. Until then it shows
as not checked.

**In a tool without sub agents,** such as Copilot chat or Claude Desktop chat, run the lenses one at a
time. Read the change again for each lens, rather than working from memory of the last one. Then check
the findings in a separate pass. Same lenses, same rule, same report.

## Reviewing a skill or a prompt

A skill is code and instructions together, so all seven lenses apply. Add these checks:

- **Correctness:** look up the current skill spec and each tool's limits. Never recall them, because
  they change. Run the skill's own validator if it has one.
- **Completeness:** it should fire when it should, and stay quiet when it should not. Look for both
  kinds of eval case.
- **References:** every file the skill mentions exists, and every script runs on each OS it claims.
- **Dynamic or hardcoded:** counts, versions, model names and product names belong in a lookup or a
  dated table.
- **Perspectives:** read it as the least experienced person who will install it, and as someone on a
  different AI tool.

## The report, and posting it

Use the `code-review` template. `review.py grade` writes every section of it: the verdict, grades,
findings, gaps and an empty PR comment. Pass `--reviewed`, `--ticket` and `--tested` so the Verdict
table is complete, or replace each `[your input]` by hand. You write the one sentence under "Most
likely to fail", with `--most-likely` or in the file. Then run
`python3 scripts/check_output.py --template assets/templates/code-review.md report.md`.

For a PR comment, use three parts: what you liked, what to keep an eye on, and the decision. The
non-blocking items can carry Conventional Comments labels (https://conventionalcomments.org/). The
comment reflects their read of the code, not yours. Posting is outbound, so run `redact.py` first and
wait for a yes. Post with `gh pr comment`, `glab`, an MCP server, or let them post it.

## Making it theirs

Many engineers already have a review prompt they trust. When someone shows you theirs, map it onto
lenses. Then offer two saves:

- Their report shape: `python3 scripts/kb.py template save code-review --from theirs.md`.
- Their own lenses: add rows to `templates/review-lenses.tsv` in their knowledge base, with the same
  header as `assets/review-lenses.tsv` and keys of their own. `review.py` runs them after the shipped
  lenses. A personal list adds lenses. It never hides or rewords a shipped one.

The grading rule stays the same whatever lenses they pick. That is what keeps one review comparable
with the next.
