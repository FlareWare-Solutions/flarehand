---
template: wf-07-reconcile
title: Comparison
workflow: wf-07
serves: [support, qa, finance, legal, product]
source_status: general-practice
team_sources: []
basis:
  - "PCAOB AS 2305 substantive analytical procedures - https://pcaobus.org/oversight/standards/auditing-standards/details/AS2305"
verified_on: 2026-09-14
learn:
  - "Does your team have a standard way of reporting differences? Paste an example and I will follow it."
  - "Which of the two sides is meant to be correct?"
  - "How much difference is normal here, so I can label noise as noise?"
---

<!-- Template for wf-07 reconcile. Every heading below is required.
     Check with: python3 scripts/check_output.py --contract wf-07 --style <file> -->

# Comparison: <subject>

## What was compared

<!-- Both sides pinned: name, version, patch, environment, date. -->

## Differences that matter

<!-- Ranked by consequence, not by size. Each with why it matters. -->

## What explains your symptom

<!-- The one difference most likely responsible, and how to confirm it. -->

## Noise

<!-- Expected differences, named so nobody chases them. -->

## Could not compare

<!-- What was out of reach, and why. -->

---

Label every claim: [verified: <source>], [your input], or [ASSUMPTION, verify].
Before this leaves your machine: python3 scripts/redact.py <file>
