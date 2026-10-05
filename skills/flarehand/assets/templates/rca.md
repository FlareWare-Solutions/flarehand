---
template: rca
title: Root cause analysis
workflow: wf-01
serves: [support-engineer, escalation-engineer, support-manager, developer, sre, dba]
source_status: general-practice
team_sources: []
basis:
  - "Google SRE Book, Postmortem Culture - https://sre.google/sre-book/postmortem-culture/"
  - "Google SRE Book, Example Postmortem - https://sre.google/sre-book/example-postmortem/"
  - "Kepner-Tregoe Problem Analysis, The New Rational Manager chapter 2 - https://kepner-tregoe.com/wp-content/uploads/2025/08/The-New-Rational-Manager-Chapters-1-2-PA.pdf"
  - "ITIL problem management terms (problem, known error, workaround), IT Process Maps ITIL wiki - https://wiki.en.it-processmaps.com/index.php/Problem_Management"
verified_on: 2026-09-14
tags:
  group: respond-support
  roles: [support, engineering, devops, data]
  frequency: per-event
  audience: team
next: [postmortem, knowledge-article, incident-comms]
learn:
  - "Does your team already have a root cause or postmortem document you like? Paste it and I will follow its shape instead of this one."
  - "Who will read this: engineers, a support manager, executives, or the customer?"
  - "What makes your team write one: a severity level, a customer request, repeat cases, or something else?"
  - "Who reviews the root cause before it is shared, and who signs it off?"
  - "Where do follow-up actions get tracked, and who owns them?"
---
<!-- Template: rca, used by wf-01. The learn questions in the frontmatter come first. -->

# Root cause analysis: <one object, one fault>

## Status

| Field | Value |
|---|---|
| Cause status | confirmed / most probable, not yet verified / unknown |
| Authors, reviewers and date | |
| Related tickets and case ids | |

<!-- Use the Cause status word everywhere below. Only a verified cause may be called the root cause, here or to a customer. -->

## Summary

<!-- Three sentences: what happened, who it affected and for how long, and the cause at its current status. Blameless: describe what the system allowed, never who got it wrong. -->

## Timeline

| Date and time (time zone) | Event | Source |
|---|---|---|
| | | |

<!-- Include when it last worked, what changed near then, first report, detection, mitigation and resolution. -->

## Reported cause (unverified)

<!-- What the customer or first responder believed caused it, in their words. It is a lead, so do not repeat it as a finding. -->

## Problem specification

| | IS | IS NOT, but could be |
|---|---|---|
| What: object and fault | | |
| Where | | |
| When: first seen, and any pattern | | |
| Extent: how many, and the trend | | |

<!-- Kepner-Tregoe: compare IS with the closest IS NOT, then ask what is distinctive and what changed. -->

## What the evidence shows

<!-- Observations only, each with a source: a query result, a log line, a config file. Turn on more detailed logging only where it is safe, and record when you turned it off. -->

## Hypotheses
### 1. <most supported>
Confirming:
Disconfirming:
Explains every IS and IS NOT row: yes / no

### 2. <next>
Confirming:
Disconfirming:

### 3. <next>
Confirming:
Disconfirming:

## What is missing

<!-- The specific log, query or test that separates hypothesis 1 from 2, and who can run it. -->

## Confirmed cause

- Root cause, and the trigger that set it off:
- Contributing factors:
- The test that verified it:
- What restored service, and the end-to-end check afterwards:

<!-- Fill this only after a controlled reproduction or a fix that stopped the symptom, otherwise write not yet confirmed. -->

## Action items

| Action | Type | Owner | Ticket | Status |
|---|---|---|---|---|
| | mitigate / prevent / process | | | |

## Lessons learned

- What went well:
- What went wrong:
- Where we got lucky:

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
