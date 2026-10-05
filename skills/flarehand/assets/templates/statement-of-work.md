---
template: statement-of-work
title: Statement of work or change order
workflow: wf-05
serves: [services-project-manager, consultant, solution-architect, account-manager, agency-lead, freelancer]
source_status: mixed
team_sources: []
basis:
  - "Statement of work, typical sections - https://en.wikipedia.org/wiki/Statement_of_work"
  - "Change order, definition - https://en.wikipedia.org/wiki/Change_order"
  - "Microsoft Dynamics 365 implementation guide, stage gates and change boards - https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/project-governance-classic-structures"
verified_on: 2026-09-14
tags:
  group: sell
  roles: [consulting, project, sales, founder]
  frequency: per-event
  audience: external
next: [project-charter, project-closeout]
learn:
  - "Any draft: does your team already have a statement of work or change order you like? Paste it or tell me where it lives, and I will follow its shape."
  - "Statement of work: when the client sends requirements, do you answer them line by line in their document, or write your own scope document?"
  - "Change order: how do you price a change: a fixed fee, hours at a rate, or hours drawn from a bank in the statement of work, and who signs on each side?"
---
<!-- Template: statement-of-work, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- Two modes. Keep the block you need under Draft and delete the other. Ask the learn questions marked Any draft, plus the ones for that mode. For the report at the end of an engagement, use project-closeout. -->

# <Statement of work or change order>: <engagement>

## Draft

### Statement of work

| Section | Content |
|---|---|
| Purpose | Why the client is doing this |
| In scope | Each deliverable, system, site and environment covered |
| Out of scope | Named exclusions, one per line |
| Deliverables and schedule | What is due and when |
| Client responsibilities and assumptions | |
| Acceptance criteria | How the client accepts each deliverable |
| Commercial terms | Fixed fee or time and materials, and the payment schedule |
| Change control | How a change order gets raised, priced and signed |
| Approval | Names, roles and dates on each side |

<!-- Answer each client requirement explicitly. When something was not discussed, say plainly that it is not in scope. A silent gap becomes a dispute. -->

### Change order

| Field | Content |
|---|---|
| Reference | SOW section, and the ticket or request number if one exists |
| Requested change | What the client asked for, in their words |
| Why it is a change | The SOW line it falls outside |
| Proposed solution | |
| Expected behaviour | Numbered, one testable statement each |
| Impact | Effort, cost, schedule, and what stays unchanged |
| Risks and testing | Where you will test it, and the regression you will run |
| Approval | Version, date, prepared by, and each approver's name, role, signature and date |

## MISSING - you must supply

<!-- Every field with no source, and who can supply it. For example, the rate, the payment schedule, or the name of each signatory. -->

## Notes for the reviewer
<!-- author-only -->

<!-- Choices you made, and anything worth a second look, such as a scope line that could read two ways. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
