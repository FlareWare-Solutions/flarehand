---
template: test-plan
title: Test plan
workflow: wf-11
serves: [qa-engineer, qa-automation, developer, product-manager, test-lead]
source_status: mixed
team_sources: []
basis:
  - "ISO/IEC/IEEE 29119-3:2021 test documentation (overview of parts and documents) - https://en.wikipedia.org/wiki/ISO/IEC_29119"
verified_on: 2026-09-14
tags:
  group: build-run
  roles: [qa, engineering, product]
  frequency: per-event
  audience: team
next: [runbook, release-notes]
learn:
  - "Does your team already have a test plan you like? Paste it or tell me where it lives, and I will follow its shape instead of this one."
  - "Where do test cases live today: a test management tool, a spreadsheet, tickets, or code? Which are automated, and with what?"
  - "Which environment and build do you test on, and who decides that testing is finished and the change can ship?"
  - "How does your team rate defects: severity, priority, or both?"
---

<!-- Template: test-plan, used by wf-11. The learn questions in the frontmatter come first. -->

# Test plan: <story, feature or release>

## What this plan covers

- Thing under test: <screen, report, endpoint or ticket>
- Build or version: <build number, commit or version>
- Platforms: <web, mobile, desktop, API>
- Out of scope: <what this plan does not test, and why>

## Approach and environment

- Test types: <functional, regression, API, performance, accessibility, exploratory>, manual or automated
- Environment: <name and URL> <!-- Name the environment exactly. Ask which one gets nightly builds and which mirrors production. -->
- Logins, roles and permissions: <one line each> <!-- Never paste a password. Name where it is stored. -->
- Test data: <records needed, and how many>
- Where results go: <test tool, spreadsheet, or a comment on the ticket>

## Risks that drive testing

| Risk | Likelihood | Impact | What we test because of it |
|---|---|---|---|
| <what could go wrong> | high / med / low | high / med / low | <case IDs> |

## Coverage dimensions

<!-- Name the axes before writing a single case. The dimensions prove the coverage. -->

| Dimension | Values to walk |
|---|---|
| Role or permission | <roles that can and cannot use the feature> |
| Deployment | <hosted, self-hosted, region> |
| Platform and browser | <list> |
| Data volume | none, 1, one more than a page of results, the largest realistic set |
| Network, for mobile | good connection, poor connection, offline |
| Version | <oldest supported, current> |
| Data state and sequence | <new, edited, deleted, archived; order of actions> |

<!-- Lists longer than one page and limits on result counts are where paging bugs hide. Find the real limits in the code or the docs. -->

## Cases

<!-- Every case has a precondition, steps and an expected result, and traces to an acceptance criterion. -->

| ID | Traces to | Precondition | Steps | Expected result | Priority |
|---|---|---|---|---|---|
| TC1 | AC1 | <state and data> | 1. <action> 2. <action> | <what you see> | high |
| TC2 | AC2 | | | | |

### Regression

- <existing behaviour this change could break> <!-- Shared code is the usual path: a change for one platform can break another that uses the same code. -->

## Negative and edge cases

| ID | Case | Expected result |
|---|---|---|
| NE1 | User without the needed permission | <access refused, with a clear message> |
| NE2 | Required field empty or invalid | <validation message, nothing saved> |
| NE3 | More records than one page holds | <paging loads every record> |
| NE4 | Mobile on a very poor network | <screen stays responsive, data saves> |
| NE5 | Clients of an API that changed | <each known client still works> |

## Entry and exit criteria

- Start when: <build deployed, data ready, story in testing>
- Finished when: <all high cases pass, no open blocker> <!-- Who gives go or no-go at your company? Ask; do not assume. -->
- Defect rating: <your severity and priority scale>

## Gaps you must fill

- <what was out of reach, and what it would take to cover it>

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
