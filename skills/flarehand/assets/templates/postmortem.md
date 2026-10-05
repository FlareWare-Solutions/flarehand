---
template: postmortem
title: Incident postmortem
workflow: wf-05
serves: [sre, devops, engineer, incident-commander, support-manager, engineering-manager]
source_status: mixed
team_sources: []
basis:
  - "Google SRE Book, Postmortem Culture: Learning from Failure (blameless postmortems, when to write one) - https://sre.google/sre-book/postmortem-culture/"
  - "PagerDuty Postmortem Documentation (process, roles and a postmortem template) - https://postmortems.pagerduty.com/"
  - "PagerDuty postmortem template - https://postmortems.pagerduty.com/resources/post_mortem_template/"
verified_on: 2026-10-04
tags:
  group: respond-support
  roles: [engineering, devops, support, operations]
  frequency: per-event
  audience: team
next: [incident-comms, knowledge-article, rca]
learn:
  - "Does your team already have a postmortem template or incident review page you like? Paste it and I will follow its shape instead of this one."
  - "What makes your team write a postmortem: a severity level, customer impact, data loss, or a request?"
  - "Where are action items tracked, and who reviews the postmortem before it is shared?"
---
<!-- Template: postmortem, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- Still hunting for the cause? Use the rca template first, then come back here. -->

# Postmortem: <incident title>, <date>

**Blameless. This describes what the system and the process allowed, never who to blame.**

## Draft status

| Field | Value |
|---|---|
| Incident id and severity | |
| Authors | |
| Reviewers | |
| State | draft / in review / final |
| Cause status | confirmed / most probable, not yet verified / unknown |

## Summary

<!-- Three or four sentences: what happened, who was affected and for how long, the cause at its current status, and how it ended. -->

## Impact

| Measure | Value | Source |
|---|---|---|
| Users or customers affected | | |
| Duration, start to end (time zone) | | |
| Failed requests, lost data or missed deadlines | | |
| Revenue or contract effect | | |

<!-- Copy every figure from a dashboard, log or report. A missing figure goes on the MISSING list. -->

## Timeline

| Time (time zone) | Event | Source |
|---|---|---|
| | Last known good | |
| | Trigger | |
| | Detected | |
| | Mitigated | |
| | Resolved | |

## Root causes and trigger

<!-- The trigger is what set it off. The root causes are the conditions that let the trigger cause harm. There is usually more than one. Use the cause status word above. -->

- Trigger:
- Root causes:
- Contributing factors:

## Detection and response

- How we found out, and how long it took:
- What helped the response:
- What slowed it down:

## What went well, what went badly, where we got lucky

- Went well:
- Went badly:
- Got lucky:

## Action items

<!-- Every action has one owner, a due date and a ticket. Prefer actions that prevent the class of problem over ones that patch this instance. -->
<!-- List the actions the team agreed. Any action you add beyond what the person gave you is a suggestion: set its Status to proposed and leave Owner and Due blank until the team agrees it. -->

| Action | Type | Owner | Due | Ticket | Status |
|---|---|---|---|---|---|
| | prevent / detect / mitigate / process | | | | agreed / proposed / done |

## Supporting material
<!-- optional -->

- Dashboards, logs, chat transcripts and related incidents:

## MISSING - you must supply

- <figure, time or owner with no source>: <who has it>

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
