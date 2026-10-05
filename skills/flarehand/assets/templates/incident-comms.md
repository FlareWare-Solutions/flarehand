---
template: incident-comms
title: Incident status update
workflow: wf-05
serves: [incident-commander, support-manager, sre, communications, customer-success]
source_status: sourced
team_sources: []
basis:
  - "Atlassian Statuspage, incident statuses (investigating, identified, monitoring, resolved) - https://support.atlassian.com/statuspage/docs/create-an-incident/"
  - "PagerDuty Incident Response, external communication guidelines - https://response.pagerduty.com/during/external_communication_guidelines/"
  - "Atlassian, incident communication best practices - https://www.atlassian.com/incident-management/incident-communication"
verified_on: 2026-10-04
tags:
  group: respond-support
  roles: [support, devops, engineering, operations, marketing]
  frequency: per-event
  audience: external
next: [postmortem]
learn:
  - "Does your team have status page wording or past updates you liked? Paste them and I will match their tone."
  - "Who must approve an update before it is posted, and how often do you promise updates during an incident?"
  - "Where do updates go: a public status page, customer email, an in-app banner, or an internal channel?"
---
<!-- Template: incident-comms, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- One block per phase. Fill the current phase. Keep earlier phases as the history, and write "Not yet" under phases you have not reached. -->
<!-- Never state a cause before it is confirmed. Never promise a fix time you do not control. Always give the next update time. -->

# Incident update: <service or feature>, <current phase>

## Investigating

<!-- What users see, that you are looking into it, and when you will update next. No guesses at the cause. -->

> We are looking into reports that <what users see>. <Who is affected, if known.> We will post the next update by <time, time zone>.

## Identified

<!-- The cause in plain words, only once it is confirmed. What you are doing, and any workaround users can apply. -->

> We have found the cause of <the problem> and are working on a fix. <Workaround, if any.> Next update by <time, time zone>.

## Monitoring

> A fix is in place and we are watching to make sure <the service> has fully recovered. <What users should do, if anything.> Next update by <time, time zone>.

## Resolved

<!-- When it started and ended, who was affected, and what happens next, such as a postmortem. -->

> We have resolved this incident. Between <start> and <end> (time zone), <who> could not <do what>. <What to do if a problem remains.> We are sorry for the disruption. <Promise of a follow-up, only if one is planned.>

## Internal update
<!-- optional -->

<!-- For leaders and customer-facing staff: more detail, business impact, what to tell customers who ask, and who to contact. -->

## Draft notes
<!-- author-only -->

<!-- For the author and reviewers only. Leave this section out of the published or sent text. -->

| Field | Value |
|---|---|
| Incident id | |
| Current phase | investigating / identified / monitoring / resolved |
| Audience and channel | |
| Approved by | |
| Next update by (time and time zone) | |

## MISSING - you must supply

- <time, scope or approval not yet confirmed>: <who has it>

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
