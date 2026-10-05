---
template: incident-report
title: Incident report for handoff
workflow: wf-03
serves: [support-analyst, support-engineer, it-helpdesk, devops, sre, escalation-engineer]
source_status: mixed
team_sources: []
basis:
  - "ITIL incident management terms (incident, incident record, escalation), IT Process Maps ITIL wiki - https://wiki.en.it-processmaps.com/index.php/Incident_Management"
  - "ITIL problem management terms (problem, known error, workaround), IT Process Maps ITIL wiki - https://wiki.en.it-processmaps.com/index.php/Problem_Management"
  - "Institute for Healthcare Improvement, SBAR tool (Situation, Background, Assessment, Recommendation) - https://www.ihi.org/resources/tools/sbar-tool-situation-background-assessment-recommendation"
  - "Kepner-Tregoe Problem Analysis, The New Rational Manager chapter 2 - https://kepner-tregoe.com/wp-content/uploads/2025/08/The-New-Rational-Manager-Chapters-1-2-PA.pdf"
verified_on: 2026-10-04
tags:
  group: respond-support
  roles: [support, devops, engineering, operations]
  frequency: per-event
  audience: team
next: [rca, incident-comms, knowledge-article]
learn:
  - "Does your team already have a case or incident handoff format you like? Paste one and I will follow its shape instead of this one."
  - "Where do your cases live, for example a help desk, Jira or ServiceNow, and which fields does it force you to fill?"
  - "How does your team set priority, and what does the receiving team most often send back as incomplete?"
---
<!-- Template: incident-report, used by wf-03. The learn questions in the frontmatter come first. -->
<!-- For a failing API call, escalation-packet is fuller. This record covers every other case. -->

# Incident report: <case id and one-line symptom>

<!-- SBAR order: Situation, Background, Assessment, Recommendation. The receiver learns what is wrong before why, and the ask is never buried. -->

## Situation

<!-- One or two sentences: what is broken, who it affects, and how bad. -->

## Background

### Record

| Field | Value |
|---|---|
| Case id | |
| Opened (date, time, time zone) | |
| Reported by, and their role | |
| Customer, tenant or site | |
| Environment, URL and version | |
| Feature, screen or service | |
| Status | |
| Current owner or tier | |
| Handing off to | |

<!-- Version and environment come first, because the receiving team asks for them first. -->

### Impact and priority

- Who it happens to, how many, and who it does not happen to:
- What they cannot do, in business terms:
- Impact and urgency:
- Priority:

<!-- Priority usually combines impact and urgency. How does your team set it, and what are the levels called? Ask; do not assume. -->

### Symptom as reported

<!-- The reporter's own words, and the exact error text pasted in full. Do not paraphrase either. -->

### Reported cause (unverified)

<!-- What the reporter or a colleague believes is wrong. It is a lead, not a finding, so keep it out of the Situation. -->

### Reproduction

1.
2.
3.

- Reproduces on the reporter's environment, and on yours: yes / no / not tried for each
- How often: every time, or how many attempts out of how many
- User role or permissions used:

<!-- One action per step, starting from a neutral state. Could not reproduce? Say so, and list what you tried. -->

## Evidence

- Error text or log extract, with timestamp and time zone: [verified: evidence/<hash>.txt]

<!-- Every item needs a source. Paste error text rather than a screenshot, so request and correlation ids survive. -->

## Assessment

<!-- What you think is going on, each claim labelled for how sure you are. -->

### Workaround

<!-- What restores service for now, who applied it, whether it worked, and any side effect. Write none if there is none. -->

### What has been tried and ruled out

| When | Who | Check or action | What it showed |
|---|---|---|---|
| | | | |

## Recommendation

- What you want the receiving team to do, and by when:
- Handoff type: defect / configuration or access request / product question / other
- Related known error, problem record or ticket:

<!-- Not every escalation is a defect. Before filing one, compare the reporter's version with the latest. If yours is newer and it does not reproduce there, the answer may be an upgrade. -->

## MISSING - you must supply

- <field>: <who can get it, and how>

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
