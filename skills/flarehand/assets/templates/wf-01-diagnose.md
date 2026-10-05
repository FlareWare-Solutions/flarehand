---
template: wf-01-diagnose
title: Diagnosis
workflow: wf-01
serves: [support, qa, developer, devops-dba, finance]
source_status: general-practice
team_sources: []
basis:
  - "Kepner-Tregoe problem analysis - https://kepner-tregoe.com/"
  - "ITIL 4 problem management - https://wiki.en.it-processmaps.com/index.php/Problem_Management"
verified_on: 2026-09-14
learn:
  - "When your team investigates a problem like this, is there a format you already write the findings in? Paste it and I will follow it."
  - "Who reads this diagnosis, and what will they do with it?"
  - "Which evidence can you get quickly: logs, a screenshot of the error text, the environment and patch level?"
---

<!-- Template for wf-01 diagnose. Every heading below is required.
     Check with: python3 scripts/check_output.py --contract wf-01 --style <file> -->

# Diagnosis: <subject>

## Reported cause (unverified)

<!-- What they told you, in their words. It is a lead, not a premise. -->

## What the evidence shows

<!-- Observations only. Each one carries a source. No conclusions here. -->

## Hypotheses

<!-- At least three, strongest first. -->

1. **<hypothesis>**
   Confirming: <what you saw that fits>
   Disconfirming: <what you saw that does not>

## What is missing

<!-- The specific evidence that separates the top two, and how to get it. -->

<!-- This artifact must also contain: Confirming, Disconfirming -->

---

Label every claim: [verified: <source>], [your input], or [ASSUMPTION, verify].
Before this leaves your machine: python3 scripts/redact.py <file>
