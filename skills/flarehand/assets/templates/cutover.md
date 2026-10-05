---
template: cutover
title: Go-live cutover plan and readiness checklist
workflow: wf-09
pack: engineering
serves: [implementation-consultant, project-manager, release-manager, solution-architect, devops, data-engineer]
source_status: mixed
team_sources: []
basis:
  - "Microsoft Dynamics 365 implementation guide, go-live checklist - https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/prepare-go-live-checklist"
  - "Microsoft Dynamics 365 implementation guide, prepare to go live - https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/prepare-to-go-live"
  - "Microsoft Dynamics 365 implementation guide, support strategy and hypercare - https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/transition-to-support"
verified_on: 2026-09-14
tags:
  group: ship
  roles: [engineering, consulting, project, devops, data]
  frequency: per-event
  audience: team
next: [project-closeout, runbook]
learn:
  - "Does your team already have a cutover plan or go-live checklist you like? Paste it or tell me where it lives, and I will follow its shape instead of this one."
  - "Who makes the go or no-go call, does the client sign it too, and how many rehearsals do you usually run first?"
  - "Do you run the old and new systems side by side for a period, and how long does hypercare last after go-live?"
---

<!-- Template: cutover, used by wf-09. The learn questions in the frontmatter come first. -->

# Cutover plan: <project>, go-live <date>

## What done looks like

<!-- One or two checkable sentences: what runs in production, for whom, from which date, and what the old system does from then on. -->

## Scope and cutover window

| Item | Value |
|---|---|
| Systems, features and users going live | |
| Deployment | hosted or self-hosted |
| Environments and the version on each | |
| Cutover window | start, end, and the latest go or no-go time |
| Parallel run, if any | what runs twice, and for how long |

## Readiness checklist

<!-- Every row is a go or no-go criterion. Agree the rows with the client before the window opens, and attach evidence to each. -->

| # | Criterion | Owner | Evidence | Status |
|---|---|---|---|---|
| R1 | Configuration finished in the documented order and verified | | | |
| R2 | Approval limits and permissions reviewed by whoever owns them | | | |
| R3 | One end-to-end test per scenario type, run through to the final output | | | |
| R4 | User acceptance testing finished, with open items owned and dated | | | |
| R5 | Final data migration reconciled and signed off | | | |
| R6 | Users trained, access assigned, cut-off dates sent | | | |
| R7 | Support contact and escalation path confirmed for day one | | | |

## Steps

<!-- One row per step. Give each an Owner, a planned start, a duration, the steps it needs first, and a check that proves it worked. -->

| # | Step | Owner | Start | Duration | Needs | Check it worked |
|---|---|---|---|---|---|---|
| 1 | List fixes and custom changes that exist only in the test environment | | | | | List saved |
| 2 | Back up the target, refresh it from production if planned, reapply the step 1 list | | | | 1 | Backup name recorded |
| 3 | Rehearse steps 6 to 10 and record real timings | | | | 2 | Timings fit the window |
| 4 | Go or no-go meeting on the readiness checklist | | | | 3 | Decision and names recorded |
| 5 | Freeze entry in the old system at the agreed cut-off time | | | | 4 | Last transaction id noted |
| 6 | Take the final extract | | | | 5 | Record counts captured |
| 7 | Load and reconcile the final migration | | | | 6 | Control totals tie out |
| 8 | Save the old system's outputs, then run the same process in the new one | | | | 7 | Differences explained |
| 9 | Smoke test production: one transaction per scenario type | | | | 8 | Expected output seen |
| 10 | Tell users the new system is live, with the support contact | | | | 9 | Message sent |

<!-- Step 8: save the old system's report before you rerun anything, because a rerun can overwrite it. -->

## Riskiest step

<!-- Usually step 7, because it runs once, late, inside the window. Say what you do if the totals do not tie out by the go or no-go time. -->

## Rollback

<!-- Name the point of no return, usually the first live transaction in production. Before it you restore and reopen the old system. After it you fix forward. -->

- Point of no return:
- Backup to restore, and where it sits:
- Who can call a rollback:
- How users hear about it:

## Hypercare and handover

<!-- Hypercare is a period of raised support right after go-live. Ask how long your team runs it and what ends it. -->

- Length and exit criteria:
- Daily triage call, and who attends:
- How users raise a case, and how you tell a defect from a setup or training problem:
- Handover to support, and the closeout report due date:

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->

## What is missing or assumed

<!-- Anything you had to assume, and anything only someone else can supply. A plan with an
invisible assumption costs an hour. Say it here, and name who can answer it. -->
