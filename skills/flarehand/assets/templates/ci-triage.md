---
template: ci-triage
title: Failing test or build triage
workflow: wf-01
pack: engineering
serves: [qa-automation, developer, release-manager, devops, sre]
source_status: mixed
team_sources: []
basis:
  - "Martin Fowler, Eradicating Non-Determinism in Tests - https://martinfowler.com/articles/nonDeterminism.html"
  - "Google Testing Blog, Flaky Tests at Google and How We Mitigate Them - https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html"
  - "Kepner-Tregoe Problem Analysis, The New Rational Manager chapter 2 - https://kepner-tregoe.com/wp-content/uploads/2025/08/The-New-Rational-Manager-Chapters-1-2-PA.pdf"
verified_on: 2026-10-04
tags:
  group: build-run
  roles: [engineering, qa, devops]
  frequency: per-event
  audience: team
next: [code-review, knowledge-article]
learn:
  - "Do you already write up failing tests or builds in a way you like? Paste an example and I will follow its shape instead of this one."
  - "Which CI system and suite is failing, for example GitHub Actions, GitLab CI, Jenkins, CircleCI or Buildkite, and unit, integration or end-to-end tests?"
  - "What is your team's rule for rerunning, skipping or quarantining a test, who approves it, and where does the outcome go?"
---
<!-- Template: ci-triage, used by wf-01. The learn questions in the frontmatter come first. -->

# CI triage: <pipeline or job>, <test or step>

## Failure

| Field | Value |
|---|---|
| CI system, pipeline and job | |
| Test id or build step | |
| Platform, runner, device or browser | |
| First failing run, with link | |
| Last passing run, with link | |
| Environment, login and data used | |
| Runs on the same commit | failed N of M |

<!-- Passing and failing on the same commit is the only proof of flakiness. Without that count, flaky is a guess. -->

## Reported cause (unverified)

<!-- What people already say: it is flaky, the environment is down, somebody's commit broke it. A lead, not a verdict. -->

## What the evidence shows

- Failure message, word for word:
- Failing step or stack trace extract:
- Commits between the last pass and the first failure:
- Deploys, dependency updates, runner image changes or data refreshes in that window:
- Fails locally, on retry, or only in parallel runs:

<!-- Open the failed job's full log and quote the first real error, not the last line. Note whether a scheduled or a commit-triggered run failed, and whether caches were used. -->

## Bucket
<!-- optional -->

<!-- Test failures only. For a build failure, delete this section and go straight to the hypotheses. -->

- [ ] A. Mechanical or selector: the test looks for the wrong thing. One fix often clears many tests.
- [ ] B. Framework or environment flakiness: it passes on retry or fails only under load. Change the run strategy, not the test.
- [ ] C. Data reachability: the test needs a record the environment does not guarantee. Name the data it needs.
- [ ] D. Real bug or test logic error: only a person can judge. Say why.

<!-- Clear them in cost order, and pick D only when A, B and C clearly do not fit. A trace that dies looking for a missing element is usually A; the app throwing is more likely D. -->

## Hypotheses

### 1. <most supported>
Confirming:
Disconfirming:

### 2. <next>
Confirming:
Disconfirming:

### 3. <next>
Confirming:
Disconfirming:

<!-- Usual sources of non-determinism: shared state between tests, fixed sleeps instead of waits, remote services, the clock and time zones, test order, and resource leaks. -->

## What is missing

<!-- The run or comparison that separates the top two, such as a rerun on the last passing commit or on one worker. -->

## Decision

- Action: fix the test / change the run strategy / seed data / file a defect / quarantine
- Owner:
- Ticket:
- How you will confirm the fix:

<!-- A quarantined test needs an owner and a limit on time or count, or nobody fixes it. What limit does your team use? Ask. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
