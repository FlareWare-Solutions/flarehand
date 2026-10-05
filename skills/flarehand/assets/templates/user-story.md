---
template: user-story
title: User story or epic
workflow: wf-05
serves: [product-manager, product-owner, business-analyst, developer, qa-engineer]
source_status: mixed
team_sources: []
basis:
  - "INVEST in Good Stories and SMART Tasks (Bill Wake) - https://xp123.com/articles/invest-in-good-stories-and-smart-tasks/"
  - "Given When Then (Martin Fowler) - https://martinfowler.com/bliki/GivenWhenThen.html"
  - "Gherkin reference (Cucumber) - https://cucumber.io/docs/gherkin/reference/"
verified_on: 2026-09-14
tags:
  group: plan
  roles: [product, engineering, qa]
  frequency: per-event
  audience: team
next: [test-plan, functional-spec]
learn:
  - "Do you already have a story or epic you like? Paste it or give me its ticket key, and I will follow its shape instead of this one."
  - "Does your team write acceptance criteria as Given, When, Then scenarios, or as a plain checklist?"
  - "Is this one story, or an epic that you want split into stories?"
  - "Which fields does your board insist on, such as story points, fix version or labels, and who approves a story before work starts?"
---

<!-- Template: user-story, used by wf-05. The learn questions in the frontmatter come first. -->

# User story: <title as it will read on the board>

## Draft

<!-- The story as it will go onto the board. Every subsection below belongs to the draft. -->

### Summary

- Project and key: <ABC-1234, or new>, story / epic
- Parent epic: <key, or none>
- Who reads it, and what they do with it: <reader>

### Story

As a <user, such as a team lead approving expenses>, I want <one capability>, so that <one outcome>.

### Context

<!-- Why now: the request, the support case or the gap behind it. Strip customer names and figures. -->

### Acceptance criteria

<!-- Aim for 3 to 5 steps per scenario. Include at least one negative case: wrong permission, missing data or invalid input. -->

**AC1: <the rule, in plain words>**
- Given <starting state and data>
- When <the user does one thing>
- Then <the result anyone can observe>

**AC2: <what must not happen>**
- Given
- When
- Then

<!-- For a list screen, add a criterion for more records than one page holds. -->

### Out of scope

- <what this story leaves out on purpose, so nobody builds it by accident>

### INVEST check

| Check | Yes or no | If no, what to change |
|---|---|---|
| Independent: ships without waiting on another open story | | |
| Negotiable: states the need, not a fixed design | | |
| Valuable: a user or customer would notice it | | |
| Estimable: the team understands it well enough to size it | | |
| Small: fits in one iteration | | |
| Testable: every criterion has a clear pass or fail | | |

### Implementation notes
<!-- Only if your team puts the plan on the story. Order points logically, each showing progress within a day or two. -->

- [ ] <plan point> (<estimate>)

### Done when

- [ ] Every acceptance criterion passes on <environment and build>
- [ ] A reviewer approves the code
- [ ] Tests cover the new behaviour
- [ ] Docs, release notes input and screenshots, where your team asks for them
- [ ] <your team's other rule> <!-- Ask about fix version and release notes. Do not assume. -->

## MISSING - you must supply

- <field>: <who has it, and how to get it>

## Notes for the reviewer
<!-- author-only -->

<!-- Splits you considered, choices you made, and anything that needs a second look. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
