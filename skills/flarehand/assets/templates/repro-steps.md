---
template: repro-steps
title: Reproduction steps
workflow: wf-03
serves: [support-analyst, support-engineer, qa-engineer, developer]
source_status: general-practice
team_sources: []
basis:
  - "Institute for Healthcare Improvement, SBAR tool (Situation, Background, Assessment, Recommendation) - https://www.ihi.org/resources/tools/sbar-tool-situation-background-assessment-recommendation"
  - "Supportbench reproduction standard - https://www.supportbench.com/standardize-reproduction-steps-software-issues/"
verified_on: 2026-10-04
tags:
  group: respond-support
  roles: [support, qa, engineering]
  frequency: per-event
  audience: team
next: [incident-report, escalation-packet]
learn:
  - "Does the team that receives this expect a particular reproduction format? Paste one they accepted."
  - "Which environment, version and user role or permissions did this happen with?"
  - "Does it happen every time, or only sometimes?"
---

<!-- Reproduction steps. The single thing that decides whether a defect is accepted
     or bounced back. Check with: python3 scripts/check_output.py --style <file> -->

# Reproduce: <one line>

## Situation

<!-- One or two sentences: what breaks, for whom, and how often. -->

## Background

### Environment

- Environment and URL:
- Version or build:
- Customer, tenant or deployment type:
- User role or permissions used:
- Browser, device or client:

### Preconditions

What must be true before step 1. Data, configuration, permissions.

## Reproduction steps

1.
2.
3.

## Expected

What should happen.

## Actual

What happens instead. Error text word for word, not a description of it.

## How often

Every time / intermittently / once. If intermittent, say how many attempts out of how many.

## Evidence

[verified: evidence/<hash>.txt]

## Assessment

<!-- What you think is going on, each claim labelled. What you have already ruled out, so nobody repeats it. -->

## Recommendation

<!-- What you want the receiving team to do, and by when. -->

## MISSING - you must supply

- <what, and who has it>

---

**The user role is not optional.** The same screen often behaves differently by role or permission,
and that is a common cause of "works for me".

**Paste error text, do not screenshot it.** A screenshot loses request and correlation ids, which
engineers use to find the request in the logs.
