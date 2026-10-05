---
template: launch-plan
title: Launch plan
workflow: wf-09
serves: [product-marketing, product-manager, release-manager, marketing-manager, founder]
source_status: mixed
team_sources: []
basis:
  - "Pragmatic Institute, use product launch tiers to allocate launch resources - https://www.pragmaticinstitute.com/resources/articles/product/prioritize-product-launch-resources-with-launch-tiers/"
  - "Working Backwards, the PR/FAQ as the launch narrative written first - https://workingbackwards.com/concepts/working-backwards-pr-faq-process/"
verified_on: 2026-10-04
tags:
  group: ship
  roles: [product, marketing, engineering, sales, support]
  frequency: per-event
  audience: team
next: [release-notes, press-release, case-study]
learn:
  - "Does your team size launches with tiers or another scale? Tell me what each level includes and I will use it."
  - "Who gives the go or no-go on launch day, and who must sign off docs, support and legal readiness?"
  - "How do you turn a launch off if it goes wrong: a feature flag, a rollback, or something else?"
---
<!-- Template: launch-plan, used by wf-09. The learn questions in the frontmatter come first. -->

# Launch plan: <what ships>, <launch date>

## What done looks like

<!-- Checkable: who can use it, from when, and the adoption or revenue signal you expect by day 30. -->

## Launch tier

<!-- Use your team's tiers if it has them. Otherwise: Tier 1 is a major launch with press, campaign and full sales enablement. Tier 2 is a significant update for existing customers. Tier 3 is a minor change with a changelog entry. -->

- Tier:
- Why this tier:

## Audience and message

- Who it is for:
- The one-line message:
- Proof points, each with a source:
- PR/FAQ or brief: <link>

## Readiness checklist

| Area | Item | Owner | Status |
|---|---|---|---|
| Product | Feature complete, tested, behind a flag | | |
| Docs | Docs page and release notes ready | | |
| Support | Team trained, help articles ready | | |
| Sales | Enablement and pricing ready | | |
| Marketing | Announcement, page, email ready | | |
| Legal and compliance | Claims and terms reviewed | | |

## Steps

<!-- Count back from launch day. Each step has an Owner, a date, what it needs first, and how you check it is done. -->

| # | Step | Owner | Date | Needs | Check it worked |
|---|---|---|---|---|---|
| 1 | Readiness review | | launch minus 2 weeks | | Every row above is green or has a plan |
| 2 | Go or no-go | | launch minus 1 day | 1 | Decision and names recorded |
| 3 | Turn it on | | launch day | 2 | Users can reach it |
| 4 | Announce | | launch day | 3 | Messages sent |
| 5 | Watch the first day | | launch day | 3 | Error rates and support volume normal |

## Riskiest step

<!-- Usually turning it on, or announcing before it works for everyone. Say how you will notice a problem and how fast. -->

## Rollback

<!-- How to turn it off, who can call it, and what you tell users who already saw the announcement. -->

- Turn it off by:
- Who can call it:
- What we tell users:

## Measures after launch

| Measure | Day 1 | Day 7 | Day 30 | Source |
|---|---|---|---|---|
| | | | | |

## What is missing or assumed

<!-- Anything you had to assume, and anything only someone else can supply. Name who can answer it. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
