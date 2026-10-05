---
template: functional-spec
title: Functional specification
workflow: wf-05
serves: [business-analyst, product-manager, developer, consultant, solution-architect]
source_status: mixed
team_sources: []
basis:
  - "ISO/IEC/IEEE 29148:2018 Requirements engineering - https://standards.ieee.org/ieee/29148/6937/"
  - "Given When Then (Martin Fowler) - https://martinfowler.com/bliki/GivenWhenThen.html"
verified_on: 2026-09-14
tags:
  group: plan
  roles: [product, engineering, consulting, qa]
  frequency: per-event
  audience: team
next: [user-story, test-plan, design-doc]
learn:
  - "Does your team already have a spec or requirements document you like? Paste it or tell me where it lives, and I will follow its shape instead of this one."
  - "Is this for one customer request, a product enhancement, or an internal change, and how deep should it go: business rules only, or screens, fields and data changes too?"
  - "Who signs off the spec before development starts, and does the customer see it?"
  - "Where does the finished spec live: on the ticket, in a wiki, or somewhere else?"
---

<!-- Template: functional-spec, used by wf-05. The learn questions in the frontmatter come first. -->

# Functional specification: <feature or change>

## Draft

<!-- The specification itself. Every subsection below belongs to the draft. -->

### Document control

- Ticket or case number: <ABC-1234> <!-- Strip the customer name. The case number is enough to trace it. -->
- Product area, feature and screen: <for example Billing, Invoices, Apply credit>
- Author, reviewers, status and date: <names>, draft for review / approved, <YYYY-MM-DD>

### Objective

<!-- One paragraph: what changes, for whom, and why. -->

### Background: how it works today

<!-- The current behaviour, with the exact screen, report or endpoint name. Check names against the product or the code first. -->

### Scope

- In scope: <each change, one line each>
- Out of scope: <what this spec does not cover>

### Functional requirements

| ID | The system shall | Acceptance criteria | Priority |
|---|---|---|---|
| FR1 | <one requirement> | <a result a tester can pass or fail> | must / should / could |

<!-- One requirement per row. Write criteria as Given, When, Then when the rule has a sequence. -->

### User interface

<!-- For each screen: field label, control type, default value, validation and list of values source. Add a screenshot or mock-up. -->

### Data and database changes

<!-- Tables, columns, views, stored procedures and migrations. If something other code depends on changes, list what depends on it. -->

### API changes

<!-- Endpoint, method, new or changed fields, and a sample response. Write None if there are no API changes. -->

### Security and permissions

<!-- Which roles or permissions can see or change what. Permissions are a common cause of works-for-me. -->

### Error handling

| Situation | What the system does | Message the user sees |
|---|---|---|
| <invalid or missing input> | | |

### Assumptions and dependencies

- <assumption, or another team, patch or configuration this needs> [ASSUMPTION, verify]

### Testing and validation

<!-- The scenarios QA must cover: each requirement, data integrity, performance and regression. -->

### Documentation, training and release

<!-- API docs, help topics, release notes input and training. Name who updates each one. -->

### Change history

| Date | Ticket | What changed |
|---|---|---|
| <YYYY-MM-DD> | <ABC-1234> | <first draft> |

## MISSING - you must supply

- <field>: <who has it, and how to get it>

## Notes for the reviewer
<!-- author-only -->

<!-- Open decisions, conflicting requests, and anything that needs a second look. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
