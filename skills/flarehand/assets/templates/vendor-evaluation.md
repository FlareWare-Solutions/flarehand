---
template: vendor-evaluation
title: Vendor evaluation
workflow: wf-05
serves: [procurement, it-manager, engineering-manager, operations-manager, finance, director]
source_status: mixed
team_sources: []
basis:
  - "Weighted sum model, the method behind a weighted scoring matrix - https://en.wikipedia.org/wiki/Weighted_sum_model"
  - "Total cost of ownership, direct and indirect costs over the life of a purchase - https://en.wikipedia.org/wiki/Total_cost_of_ownership"
verified_on: 2026-10-04
tags:
  group: decide
  roles: [operations, engineering, finance, leadership, any]
  frequency: per-event
  audience: team
next: [decision-record, business-case]
learn:
  - "Does your team already have a vendor scorecard or selection template you like? Paste it and I will follow its shape instead of this one."
  - "Who makes the final choice, and who must approve the spend, the security review and the contract?"
  - "Over how many years should the cost of ownership run, and where do the price quotes come from?"
---
<!-- Template: vendor-evaluation, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- Agree the criteria and weights before anyone scores a vendor. Weights set after scoring bend toward a favourite. -->

# Vendor evaluation: <what you are buying>

## Draft status

| Field | Value |
|---|---|
| Decision owner | |
| Evaluators | |
| Decision needed by | |
| State | draft / criteria agreed / scoring / recommended / decided |

## Need and requirements

<!-- The problem this purchase solves. Must-haves are pass or fail gates: a vendor that fails one is out, whatever its score. -->

- The problem, in one or two sentences:
- Must-haves, each one pass or fail:
- Nice-to-haves, which the weights below cover:

## Criteria and weights

<!-- Weights are whole numbers that add up to 100. Write the sum out, so a reviewer can check it. Define what each score means before scoring. -->

| Criterion | Weight | What a 1 looks like | What a 5 looks like |
|---|---|---|---|
| Fit to requirements | | | |
| Total cost of ownership | | | |
| Security and compliance | | | |
| Support and vendor health | | | |
| Ease of adoption | | | |
| Total | 100 | | |

Sum written out: <w1> + <w2> + <w3> + <w4> + <w5> = 100

## Vendors considered

| Vendor | Passed the must-haves? | If not, which one failed | Source |
|---|---|---|---|
| | yes / no | | |

## Scores

<!-- One score per cell, each with the evidence behind it: a demo, a trial, a reference call, a document. Write each weighted total as a sum. -->

| Criterion | Weight | Vendor A score | Evidence | Vendor B score | Evidence |
|---|---|---|---|---|---|
| | | | | | |

Weighted total, Vendor A: <weight x score> + ... = <total> <!-- the reviewer reruns this arithmetic -->

## Total cost of ownership

<!-- Every figure comes from a quote, a contract or a named estimate. The assistant does not invent or compute a price. -->

| Cost over <n> years | Vendor A | Vendor B | Source |
|---|---|---|---|
| Licence or subscription | | | |
| Setup, migration and integration | | | |
| Training and internal staff time | | | |
| Support and upgrades | | | |
| Leaving: export, overlap, exit fees | | | |

## Risks and references

- Lock-in and how hard it is to leave:
- Security or privacy review result:
- Vendor stability and roadmap fit:
- References called, and what they said:

## Recommendation

<!-- The choice, the two or three reasons that decided it, and what would change the answer. -->

## MISSING - you must supply

- <quote, score, reference or approval still missing>: <who has it>

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
