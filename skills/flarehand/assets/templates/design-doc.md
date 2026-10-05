---
template: design-doc
title: Design doc
workflow: wf-05
serves: [engineer, architect, tech-lead, engineering-manager, data-engineer, sre]
source_status: mixed
team_sources: []
basis:
  - "Malte Ubl, Design Docs at Google (context and scope, goals and non-goals, the design, alternatives, cross-cutting concerns) - https://www.industrialempathy.com/posts/design-docs-at-google/"
verified_on: 2026-10-04
tags:
  group: plan
  roles: [engineering, data, devops, security]
  frequency: per-event
  audience: team
next: [decision-record, test-plan, runbook]
learn:
  - "Does your team have a design doc or RFC template already? Paste one you liked and I will follow its shape instead of this one."
  - "Who reviews and approves designs on your team, and how long does review usually take?"
  - "Which cross-cutting concerns does your organisation always ask about, such as security, privacy, cost or accessibility?"
---
<!-- Template: design-doc, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- A design doc earns its keep on trade-offs. If there is only one sensible way to build it, write a short note instead. -->

# Design doc: <system or change>

## Draft status

| Field | Value |
|---|---|
| Author | |
| Reviewers and approver | |
| State | draft / in review / approved / built / abandoned |
| Last updated | |
| Links | <ticket, product brief, decision records> |

## Context and scope

<!-- The system as it is, and the part this change touches. Short. Assume the reader knows the domain but not this corner of it. -->

## Goals and non-goals

<!-- A non-goal is something a reader might reasonably expect that this design will not do. -->

Goals:

- 

Non-goals:

- 

## Proposed design

<!-- Start with an overview a reader can hold in their head, then the detail: components, data and storage, interfaces and APIs, key flows. A diagram helps. Explain why, not only what. -->

### Overview

### Data and interfaces

### Key flows

## Alternatives considered

<!-- Each real option, and the trade-off that ruled it out. "We did not think of it" is not an alternative. -->

| Alternative | Why not |
|---|---|
| | |

## Cross-cutting concerns

| Concern | How this design handles it |
|---|---|
| Security | |
| Privacy and data retention | |
| Reliability and failure modes | |
| Observability | |
| Performance and cost | |
| Accessibility | |
| Migration and compatibility | |

## Rollout and testing

- How we will test it:
- How it rolls out, such as behind a flag or in stages:
- How to roll it back:
- What tells you it is working in production:

## Open questions
<!-- optional -->

- <question>: <who answers it>

## MISSING - you must supply

- <number, limit or dependency with no source>: <who has it>

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
