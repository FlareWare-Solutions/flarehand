---
template: meeting-notes
title: Meeting notes
workflow: wf-04
serves: [manager, project-manager, business-analyst, consultant, developer, chief-of-staff]
source_status: general-practice
team_sources: []
basis:
  - "Robert's Rules of Order FAQ 15 (minutes record what was done, not what was said) - https://robertsrules.com/frequently-asked-questions/"
  - "Atlassian Team Playbook, DACI decision framework (one approver per decision, record options and outcome) - https://www.atlassian.com/team-playbook/plays/daci"
verified_on: 2026-09-14
tags:
  group: communicate
  roles: [any]
  frequency: per-event
  audience: team
next: [decision-record, weekly-update]
learn:
  - "Do you already have a meeting notes format you like? Paste one or tell me where it lives, and I will follow its shape instead of this one."
  - "Where do action items go after the meeting: a ticket tracker, a shared list, email, or only these notes?"
  - "Who gets the notes, and does anyone who missed the meeting rely on them?"
  - "Will you give me a transcript, a recording summary, or your own rough notes?"
  - "How soon after the meeting do the notes go out, and does anyone approve them first?"
  - "Is this a recurring meeting whose open action items should carry forward each time?"
---
<!-- Template: meeting-notes, used by wf-04. The learn questions in the frontmatter come first. -->

# Meeting notes: <meeting name>, <date>

| Date and time | Attendees | Absent | Notes by | Next meeting |
|---|---|---|---|---|
| | | | | |

## The ask

<!-- What readers of these notes must do, and by when. If nothing, write For information only. One or two sentences. -->

## What happened

<!-- Three to five sentences for someone who was not there. Decisions and blockers first, not the order people spoke. -->

- <what happened> [verified: <source>]

## Decisions

<!-- Record a decision only when the person with authority made it in the meeting. Record what was decided, not the debate. -->

| # | Decision | Decided by | Source |
|---|---|---|---|
| D1 | | | |

<!-- Source is the transcript time or your notes, for example [verified: evidence/hash.txt] once you snapshot the transcript. -->

## Action items

<!-- One named person per action, never a team. An owner must have agreed in the meeting. No due date means it goes on the MISSING list. -->

| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| A1 | | | | Open |

## Carried forward from last meeting
<!-- optional -->

<!-- Every action still open from last time, with its status now. Anything not closed carries forward again. -->

| # | Action | Owner | Was due | Status now |
|---|---|---|---|---|
| | | | | |

## Detail

<!-- One short block per agenda topic. Outcomes and facts, not who said what. Figures carry a source. Leave out side remarks and opinions about people. -->

### <Agenda topic>

- Outcome: 
- Facts and figures, with sources: 

## Still open

<!-- Questions raised but not settled, and topics parked for later. Name who follows up. -->

## MISSING - you must supply

<!-- Owners, due dates or decisions the notes could not confirm. Name who can confirm each one. -->

- 

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
