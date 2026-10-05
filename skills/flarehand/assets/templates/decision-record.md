---
template: decision-record
title: Decision record
workflow: wf-05
serves: [engineer, architect, engineering-manager, product-manager, team-lead, director]
source_status: mixed
team_sources: []
basis:
  - "Michael Nygard, Documenting Architecture Decisions (context, decision, status, consequences) - https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions"
  - "MADR, Markdown Any Decision Records (decision drivers, considered options, pros and cons), MIT and CC0 - https://adr.github.io/madr/"
  - "Atlassian Team Playbook, DACI decision roles (driver, approver, contributors, informed) - https://www.atlassian.com/team-playbook/plays/daci"
  - "Bain and Company, RAPID decision roles. RAPID is a Bain trademark, so this template only names RAPID-style roles - https://www.bain.com/insights/rapid-tool-to-clarify-decision-accountability/"
verified_on: 2026-10-04
tags:
  group: decide
  roles: [engineering, product, leadership, any]
  frequency: per-event
  audience: team
next: [project-charter, design-doc]
learn:
  - "Does your team already keep decision records, for example an adr folder in the repo or a page in your wiki? Paste one you like and I will follow its shape instead of this one."
  - "Who has the final say on a decision like this one, and who must be asked before it is made?"
  - "Where do decision records live, and how are they numbered?"
---
<!-- Template: decision-record, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- One decision per record. A record is never edited after it is accepted. A later decision supersedes it, and both link to each other. -->

# Decision record: <the decision, as a short phrase, such as "Store events in one table">

## Draft status

| Field | Value |
|---|---|
| Record id | DR-<number> |
| Status | proposed / accepted / rejected / superseded by DR-<number> |
| Date | <YYYY-MM-DD> |
| Decision owner | <one person, the approver> |
| Driver | <who runs the decision to a close> |

## Context and problem

<!-- The situation that forces a choice, in two to five sentences. Name the constraints: time, money, skills, systems already in place. Say why it has to be decided now. Facts carry a label. -->

- <fact that shapes the decision> [your input]

## Decision drivers

<!-- What a good answer must do, most important first. These are the measures every option is judged on. -->

1. <driver>
2. <driver>

## Options considered

<!-- Include doing nothing. Give each option a fair hearing, in the same depth. -->

| Option | Good, because | Bad, because | Fits the drivers? |
|---|---|---|---|
| Do nothing | | | |
| <option A> | | | |
| <option B> | | | |

## Decision

<!-- Active voice: "We will ...". Name the chosen option and the one or two drivers that decided it. -->

We will <the chosen option>, because <the deciding reason>.

## Consequences

<!-- What gets easier, what gets harder, and the work this creates. Include the signal that would make you revisit it. -->

- Easier:
- Harder:
- Follow-up work, each with an owner:
- Revisit if:

## Roles
<!-- optional -->

<!-- RAPID-style or DACI roles, when more than one team is involved. Exactly one person decides. -->

| Role | Who |
|---|---|
| Driver, who runs the process | |
| Approver, who decides | |
| Contributors, who give input | |
| Informed, who hear the outcome | |

## Links
<!-- optional -->

- Supersedes or superseded by:
- Related records, tickets and evidence:

## MISSING - you must supply

- <fact, option or approver with no source>: <who has it>

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
