---
template: business-review
title: Business review or success plan
workflow: wf-04
serves: [customer-success, account-manager, consultant, services-project-manager, sales-manager]
source_status: general-practice
team_sources: []
basis:
  - "Gainsight, The Essential Guide to Quarterly Business Reviews - https://www.gainsight.com/essential-guide/quarterly-business-reviews-qbrs/"
verified_on: 2026-09-14
tags:
  group: sell
  roles: [customer-success, sales, consulting]
  frequency: quarterly
  audience: external
next: [exec-brief]
learn:
  - "Do you already have a business review deck or success plan you like? Paste it or tell me where it lives, and I will follow its shape instead of this one."
  - "Where do health scores, usage figures and support data come from, and who defines what red, amber and green mean?"
  - "Is this review for the customer's executives, their day-to-day team, or internal prep, and which figures do you never show the customer?"
---
<!-- Template: business-review, used by wf-04. The learn questions in the frontmatter come first. -->
<!-- Quarterly, executive or annual business review, or a success plan review. This holds the customer's name, contract values, usage and people's names. Run python3 scripts/redact.py <file> before it goes beyond the account team. -->

# Business review: <customer>, <period>

## Meeting

- Type: quarterly business review, executive business review, or success plan review
- Date, length, and attendees with their roles: [your input]
- Reader: the customer's executives, their project team, or internal prep
- Products or services in use, with a start date for each: [your input]

<!-- Invite day-to-day users and the people who set direction. Send the agenda well ahead. Never invent a figure, a quote or an outcome. -->

## The ask

<!-- The decision or commitment you want from the customer, or 'for information only'. One or two sentences. -->

## What happened

<!-- Three to five sentences. Progress against their goals first, then the issue they are most likely to raise. -->

- <what happened> [verified: <source>]

## Detail

### Their goals and progress

| Customer goal | Success measure | Baseline | Now | Source | Status |
|---|---|---|---|---|---|
| | | | | | |

<!-- Goals are the customer's own, taken from the success plan. Every figure carries a source label. -->

### Adoption

- In use, and bought but not yet in use: [your input]
- Usage trend, with the data source and date range: [your input]

### Support cases and open issues

| Case | Area | Severity | Status | Next step | Owner |
|---|---|---|---|---|---|
| | | | | | |

<!-- For a fix in flight, name the release. For a customer reader: no internal names, no blame, no unconfirmed cause. -->

### Health and risks

- Health score and trend, using your team's definition: [your input]
- Risks to renewal or expansion, each with an Owner: [your input]

### Value delivered

<!-- Only outcomes the customer confirmed or the data shows. No projected return unless their finance team agreed the numbers. -->

### What is coming

<!-- Only roadmap items your product team has cleared for customers. -->

## Still open

| Action | Owner | Due |
|---|---|---|
| | | |

<!-- Book the next review before the meeting ends. Then update the health score and success plan with what you both agreed. -->

## Success plan, if this is one
<!-- optional -->

- Customer objectives, and the measure you both agreed for each one.
- Milestones, with dates and an Owner on each side.
- Stakeholders: executive sponsor, champion and day-to-day contacts.
- Risks, and how often you review the plan together.

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
