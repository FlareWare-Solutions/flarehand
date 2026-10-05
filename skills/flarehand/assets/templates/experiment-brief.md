---
template: experiment-brief
title: Experiment brief and readout
workflow: wf-05
serves: [product-manager, data-scientist, growth-marketer, analyst, engineer, designer]
source_status: mixed
team_sources: []
basis:
  - "Kohavi, Tang and Xu, Trustworthy Online Controlled Experiments (overall evaluation criterion, guardrail metrics, sample ratio checks) - https://experimentguide.com/"
  - "A/B testing, an overview of randomised controlled experiments online - https://en.wikipedia.org/wiki/A/B_testing"
verified_on: 2026-10-04
tags:
  group: decide
  roles: [product, data, marketing, engineering, design]
  frequency: per-event
  audience: team
next: [decision-record, launch-plan]
learn:
  - "Does your team already have an experiment plan or readout format you like? Paste one and I will follow its shape instead of this one."
  - "Which experiment tool do you use, and who owns the metric definitions it reports?"
  - "Who decides to ship, iterate or stop once the result is in?"
---
<!-- Template: experiment-brief, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- Two modes. Plan: fill everything down to the stopping rule before launch. Readout: add Results and Decision once it stops. Never change the metrics or the stopping rule after launch. -->

# Experiment: <short name>

## Draft status

| Field | Value |
|---|---|
| Mode | plan / readout |
| Experiment id and tool | |
| Owner | |
| State | planned / running / stopped / read out |
| Start and planned end | |

## Hypothesis

<!-- One sentence that a result can prove wrong. -->

If we <change>, for <who>, then <the main metric> will <move, and by how much>, because <the reason you believe it>.

## Metrics

<!-- One overall evaluation criterion decides the outcome. Guardrails protect what must not get worse. Copy every definition from the source that owns it. -->

| Kind | Metric | Definition and source | Threshold |
|---|---|---|---|
| Overall evaluation criterion | | | smallest change worth shipping: |
| Guardrail | | | worst acceptable change: |
| Guardrail | | | |
| Diagnostic | | | not used to decide |

## Design

- Unit of randomisation, such as user, account or session:
- Who is eligible, and who you exclude:
- Variants, and the traffic split:
- Minimum detectable effect:
- Sample size per variant, and the tool that calculated it: [your input]
- Run length, in whole weeks so weekdays and weekends both count:

## Stopping rule and decision

<!-- Agreed before launch. Peeking and stopping on the first good day inflates false wins. -->

- Stop when: <the planned sample or date is reached, or a guardrail breaches>
- Check before reading results: the split matches the plan (sample ratio check)
- Ship if: 
- Iterate if: 
- Stop and roll back if: 

## Results
<!-- optional -->

<!-- Readout mode. Copy figures from the experiment tool, with the date pulled. The assistant does not compute a statistic. -->

| Metric | Control | Treatment | Difference | Interval or p-value | Source |
|---|---|---|---|---|---|
| | | | | | |

- Sample ratio check passed: yes / no
- Guardrails held: yes / no, and which moved

## Decision and learnings
<!-- optional -->

- Decision: ship / iterate / stop
- What we learned, including a null result:
- What we would test next:

## MISSING - you must supply

- <metric definition, sample size or approval with no source>: <who has it>

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
