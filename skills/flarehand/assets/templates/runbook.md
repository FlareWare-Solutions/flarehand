---
template: runbook
title: Runbook
workflow: wf-09
serves: [devops, sre, dba, release-manager, developer, it-operations]
source_status: mixed
team_sources: []
basis:
  - "Google SRE book, Introduction (playbooks and MTTR) - https://sre.google/sre-book/introduction/"
  - "Google SRE workbook, On-Call (playbook content and upkeep) - https://sre.google/workbook/on-call/"
verified_on: 2026-09-14
tags:
  group: build-run
  roles: [devops, engineering, data, operations]
  frequency: per-event
  audience: team
next: [sop, postmortem]
learn:
  - "Do you already have a runbook or deployment plan you like? Paste it or tell me where it lives, and I will follow its shape instead of this one."
  - "Is this for a planned change, like a deployment or upgrade, or for responding to an alert or outage?"
  - "Which environment is this for, who is allowed to change it, and who gives the go or no-go?"
  - "How does your team undo a change today: restore a backup, redeploy the previous build, flip a flag, or something else?"
---

<!-- Template: runbook, used by wf-09. The learn questions in the frontmatter come first. -->

# Runbook: <change or procedure> on <environment>

## Summary

- What it does: <one sentence>
- When to use it: <planned deployment, or the alert or symptom that triggers it>
- Environment, hosts and services: <names>
- Window: <date, start time, expected duration>
- Owner: <who runs it>
- Approver: <name> <!-- Who approves changes to this environment at your company? Ask; do not assume. -->

## What done looks like

<!-- Concrete and checkable: a version on a screen, a service running, a smoke test passing. -->

## Before you start

- [ ] Access to every host, job and database in the steps <!-- Credentials live in your secrets manager. Never paste one here. -->
- [ ] Artifacts ready: <file path, image tag or build number>
- [ ] Backup taken: <database, tables or files> <!-- Back up the rows or files you will change before you change them. -->
- [ ] Users told: <who, how and when>
- [ ] Go or no-go given by: <name and time>

## Steps

<!-- One action per step. Each step names its Owner, what it needs first, and how to check it worked. -->

1. **<Stop or prepare>** (Owner: <who>, needs: nothing)
   - Run: `<exact command, job name or clicks>`
   - Check it worked: <what you see>. Expected time: <minutes>.
2. **<Install or change>** (Owner: <who>, needs: step 1)
   - Run: `<exact command>`
   - Check it worked: <log line, status or screen>. Expected time: <minutes>.
3. **<Deploy>** (Owner: <who>, needs: step 2)
   - Run: `<exact command>`
   - Check it worked: <what you see>. Expected time: <minutes>.
4. **<Start and hand back>** (Owner: <who>, needs: step 3)
   - Run: `<exact command>`
   - Check it worked: <what you see>.

## Verify

- [ ] Log in and open <the changed screen>
- [ ] Call <one endpoint> and get <expected status>
- [ ] Logs show no new errors since <time>

## Riskiest step

<!-- Which step, why, how you will notice it failing, and the point after which you cannot go back. -->

## Rollback

<!-- Write your tested rollback here, or say plainly that there is none. -->

- Roll back when: <the trigger, and who decides>
- Steps: <numbered, with commands, in the same shape as above>
- Data: <restore from the backup taken before step 1>
- Check it worked: <what you see>

## If something goes wrong

| Symptom | Likely cause | What to do | Escalate to |
|---|---|---|---|
| <exact error or behaviour> | | | <team or person> |

## Communication

<!-- Start, finish and failure messages: who gets them, and through which channel. -->

## Runbook history

| Date | Who | What changed |
|---|---|---|

<!-- Runbooks go stale as fast as the system changes. Update this one after every use. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->

## What is missing or assumed

<!-- Anything you had to assume, and anything only someone else can supply. A plan with an
invisible assumption costs an hour. Say it here, and name who can answer it. -->
