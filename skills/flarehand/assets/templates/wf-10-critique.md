---
template: wf-10-critique
title: Review
workflow: wf-10
serves: [general]
source_status: general-practice
team_sources: []
basis:
  - "Gary Klein pre-mortem method - https://hbr.org/2007/09/performing-a-project-premortem"
verified_on: 2026-09-14
learn:
  - "Is there a review checklist or standard this has to meet? Paste it and I will review against it."
  - "Who decides based on this, and what happens if it is wrong?"
  - "Which part are you least sure about?"
---

<!-- Template for wf-10 critique. Every heading below is required.
     Check with: python3 scripts/check_output.py --contract wf-10 --style <file> -->

# Review: <subject>

## Most likely to fail

<!-- One sentence. The thing to fix if nothing else gets fixed. -->

## Findings

<!-- Strongest first. Drop anything you could not check. -->

- **<finding>** Severity: blocking / should fix / minor. Where: <the part it affects>.
  Fix: <concrete>

## Worth keeping

<!-- What already works, so it survives the edit. -->

## What this review did not cover

<!-- What you did not read or could not check, and why. A review that says nothing here reads as one that checked everything. -->

<!-- This artifact must also contain: Severity -->

---

Label every claim: [verified: <source>], [your input], or [ASSUMPTION, verify].
Before this leaves your machine: python3 scripts/redact.py <file>
