---
template: wf-12-retone
title: Rewrite
workflow: wf-12
serves: [general, support, hr, marketing, sales]
source_status: general-practice
team_sources: []
basis:
  - "Plain Language Guidelines - https://www.plainlanguage.gov/guidelines/"
verified_on: 2026-09-14
learn:
  - "Is there a message you sent before whose tone you liked? Paste it and I will match it."
  - "Who reads it now, and how is that different from who it was written for?"
  - "Is there anything that must stay word for word?"
---

<!-- Template for wf-12 retone. Every heading below is required.
     Check with: python3 scripts/check_output.py --contract wf-12 --style <file> -->

# Rewrite: <subject>

## Rewritten

<!-- The new version. -->

## What changed

<!-- Tone moves only. Name them. -->

## Facts kept unchanged

<!-- Every claim from the original. Walk this list against the rewrite. -->

## Check before sending
<!-- optional -->

<!-- One line per date, release or promise in the draft: is it confirmed? Leave the section out only when the draft makes no commitment. -->

---

Label every claim: [verified: <source>], [your input], or [ASSUMPTION, verify].
Before this leaves your machine: python3 scripts/redact.py <file>
