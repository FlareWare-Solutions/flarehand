---
template: status-report
title: Project status report
workflow: wf-04
serves: [project-manager, services-project-manager, program-manager, consultant, customer-success, team-lead]
source_status: general-practice
team_sources: []
basis:
  - "Microsoft Dynamics 365 implementation guide, project status reports and steering groups - https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/project-governance-classic-structures"
  - "PMI PMBOK Guide, Eighth Edition (2025), overview - https://en.wikipedia.org/wiki/Project_Management_Body_of_Knowledge"
verified_on: 2026-09-14
tags:
  group: communicate
  roles: [project, consulting, customer-success, leadership]
  frequency: weekly
  audience: exec
next: [exec-brief, risk-register]
learn:
  - "Does your team already have a status report you like? Paste one or tell me where it lives, and I will follow its shape instead of this one."
  - "Who reads it: the sponsor, your delivery lead, a steering committee, or the client? How often, and on which day?"
  - "Do you use red, amber and green, and what turns an area red on your team?"
  - "Do you report budget as hours or money against the plan, and where do those figures come from?"
---

<!-- Template: status-report, used by wf-04. The learn questions in the frontmatter come first. -->

# Status report: <project>, <period>

| Area | Status | Trend | One-line reason |
|---|---|---|---|
| Overall | green, amber or red | better, same or worse | |
| Schedule | | | |
| Budget | | | |
| Scope | | | |
| Customer dependencies | | | |

<!-- Ask what each colour means on this team before you pick one. A colour with no reason next to it gets challenged. -->

## The ask

<!-- The decision or help you need from this reader, with a date. If you need nothing, write: For information only. -->

## What happened

<!-- Three to five sentences, outcome first. Answer: are we on track, what are the main risks or issues, and what do we need from the reader. -->

- <what happened> [verified: <source>]

## Detail

### Milestones

| Milestone | Planned date | Forecast or actual | Variance | Note |
|---|---|---|---|---|
| | | | | |

<!-- Compare actual progress with the plan. Explain every slip, its cause and its effect. -->

### Budget

| Measure | This period | To date | Budget or SOW total | Remaining |
|---|---|---|---|---|
| Hours | | | | |

<!-- Every figure carries a source, such as the time report you exported. Ask where your team takes hours from. -->

### Top risks and issues

| ID | Item | Owner | Action | Due |
|---|---|---|---|---|
| | | | | |

<!-- Pull only the items this reader must know about from the RAID log. Do not restate the whole log. -->

### Waiting on the customer

| Item | Asked on | Needed by | Effect if late |
|---|---|---|---|
| | | | |

### Environments and dependencies

<!-- Name the version on each environment when testing or go-live waits on it, and any upgrade the client must take first. -->

### Next period

-

## Still open

<!-- What is unresolved, who owns it, and by when. An honest open item beats a tidy false certainty. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
