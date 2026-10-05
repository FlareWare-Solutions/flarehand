---
template: risk-register
title: Project risk register or RAID log
workflow: wf-11
serves: [project-manager, program-manager, services-project-manager, consultant, solution-architect, team-lead]
source_status: general-practice
team_sources: []
basis:
  - "PMI PMBOK Guide and PRINCE2 risk register content, as summarised - https://en.wikipedia.org/wiki/Risk_register"
  - "PMI PMBOK Guide, Eighth Edition (2025), overview - https://en.wikipedia.org/wiki/Project_Management_Body_of_Knowledge"
  - "Microsoft Dynamics 365 implementation guide, risk register and status reports - https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/project-governance-classic-structures"
  - "Risk treatment options avoid, reduce, share, retain - https://en.wikipedia.org/wiki/Risk_management"
verified_on: 2026-09-14
tags:
  group: plan
  roles: [project, consulting, engineering, operations, leadership]
  frequency: weekly
  audience: team
next: [status-report, project-charter]
learn:
  - "Does your team already have a risk register or RAID log you like? Paste it or tell me where it lives, and I will follow its shape instead of this one."
  - "Do you keep risks, assumptions, issues and dependencies together in one log, and how do you rate a risk: high, medium and low, or a number?"
  - "How often do you review the log, with whom, and at what point does a risk get escalated?"
  - "Where does the log live: a spreadsheet, a project tool, tickets, or somewhere else?"
---

<!-- Template: risk-register, used by wf-11. The learn questions in the frontmatter come first. -->

# Risk register: <project>

<!-- RAID means risks, assumptions, issues and dependencies. A risk might happen. An issue has already happened. -->

## Coverage dimensions

<!-- Walk every row below before you list items. A dimension with nothing in it gets a line saying why. -->

| Dimension | Prompt question |
|---|---|
| Scope | Is any requirement unclear, or not agreed in writing? |
| Schedule | Which dates depend on something we do not control? |
| People | Who is a single point of knowledge, on either side? |
| Customer dependencies | What does the customer owe us, and by when? |
| Data | How clean is the source data, and who fixes it? |
| Environments and versions | Is each environment on the version the plan assumes? |
| Integrations | Which outside system must be ready, and who owns it? |
| Security and access | Are roles and permissions designed and tested? |
| Training and adoption | Will users get training before they test and go live? |
| Go-live | Does the rehearsed cutover or launch fit the window? |
| Commercial | Is effort tracking against the budget or the SOW hours? |

<!-- Prompts worth asking on most projects: a requirement nobody discussed sits outside the signed scope, and a test environment that waits on an upgrade delays testing. -->

## Cases

<!-- One row per item. Write a risk as: if this happens, then this is the effect. Every row needs an Owner and a review date. -->

| ID | Type | If this happens | Then this is the effect | Probability | Impact | Score | Owner | Response | Trigger | Status | Review date |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | Risk | | | | | | | | | Open | |
| A1 | Assumption | | | | | | | | | Open | |
| I1 | Issue | | | | | | | | | Open | |
| D1 | Dependency | | | | | | | | | Open | |

<!-- Score is probability times impact. Response is what you will do: avoid, reduce, share or accept the risk. Ask your team which scale they use before you fill these in. -->

## Negative and edge cases

<!-- Kept apart on purpose, because they get skipped when mixed in. -->

- Low probability, high impact risks, such as a failed final data migration inside the window:
- Assumptions that turn into issues if they break, such as the version in a test environment:
- Risks that cross into other projects or other customers:
- Risks hidden by a tool limit, such as an import that cannot bring in a value you need:
- A refresh of a test environment from production that overwrites fixes only the test environment had:

## Gaps you must fill

<!-- Which dimensions you could not assess, and who can. For example, the customer's own IT risks. -->

## Review and escalation

- Review cadence and attendees:
- Escalation rule, and who it goes to:
- Last reviewed:

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
