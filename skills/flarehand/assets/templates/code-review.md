---
template: code-review
title: Code review
workflow: wf-10
pack: engineering
serves: [developer, tech-lead, architect, devops, qa-engineer, security-engineer]
source_status: mixed
team_sources: []
basis:
  - "Google Engineering Practices, What to look for in a code review - https://google.github.io/eng-practices/review/reviewer/looking-for.html"
  - "Conventional Comments, blocking and non-blocking labels - https://conventionalcomments.org/"
  - "OWASP Code Review Guide - https://owasp.github.io/www-project-code-review-guide/"
verified_on: 2026-09-14
tags:
  group: build-run
  roles: [engineering, devops, qa, security]
  frequency: daily
  audience: team
next: [ci-triage]
learn:
  - "Do you already have a review prompt or checklist you like? Paste it and I will grade against your lenses instead of these."
  - "Which lenses do you always want, and which do you skip for a small change?"
  - "Should I fan out to sub agents by default, only for big changes, or only when you ask?"
  - "What counts as blocking on your team?"
  - "Where does the result go: just to you, a PR comment, or a ticket comment?"
---
<!-- Template: code-review, used by wf-10. Read references/review-code.md first. review.py grade writes every section from the verified findings. Pass --reviewed, --ticket and --tested, or replace each [your input] by hand. -->

# Code review: <what was reviewed, against which base>

## Verdict

| Field | Value |
|---|---|
| Overall | pass / concerns / fail |
| Reviewed | <PR, branch, revision or folder>, against <base> |
| Ticket | <key, and the requirement it was checked against> |
| Tested and analysed before review | yes / no / unknown, and which analyzer ran |
| Not checked | <lenses, or none> |

## Most likely to fail

<!-- One sentence. The thing to fix if nothing else gets fixed. -->

## Grades

| Lens | Grade | Confirmed | Plausible | Rejected |
|---|---|---|---|---|
| Correctness | | | | |
| Regressions | | | | |
| Completeness | | | | |
| Code quality | | | | |
| References and docs | | | | |
| Dynamic or hardcoded | | | | |
| Perspectives | | | | |

## Findings

### Blocking

- **<finding>** Lens: <lens>. Severity: blocking. Where: `<path:line>`. Verified: confirmed, <what the code shows>. Fix: <concrete>

### Should fix

- **<finding>** Lens: <lens>. Severity: should fix. Where: `<path:line>`. Verified: plausible, not proven. To confirm: <what would prove it>. Fix: <concrete>

### Minor

<!-- Nits. Say "None." when there are none. -->

## Outside this change
<!-- optional -->

<!-- Problems in code the change did not touch. Not graded. Each one gets its own ticket, or goes to a team lead if it is big. -->

## What this review did not cover

<!-- Lenses not checked and why, files not read, and anything no tool could run. A reviewer can miss things, so say what was not looked at. -->

## PR comment
<!-- optional -->

<!-- Only if they will post it, and only after they have read the code themselves. Three parts: what you liked, what to keep an eye on (non-blocking), and the decision. Run redact.py first. Never post without a yes. -->
