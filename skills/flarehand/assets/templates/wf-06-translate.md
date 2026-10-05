---
template: wf-06-translate
title: Explanation
workflow: wf-06
serves: [general, support, sales, implementation]
source_status: general-practice
team_sources: []
basis:
  - "Plain Language Guidelines - https://www.plainlanguage.gov/guidelines/"
verified_on: 2026-09-14
learn:
  - "How much do you already know about this area, so I start at the right level?"
  - "Will you need to explain this to someone else afterwards? If so, who?"
  - "Would an example from your own work make this clearer? Tell me what you are working on."
---

<!-- Template for wf-06 translate. Every heading below is required.
     Check with: python3 scripts/check_output.py --contract wf-06 --style <file> -->

# Explanation: <subject>

## In plain words

<!-- One or two sentences with no jargon at all. -->

## How it actually works

<!-- The mechanism, with conditions and exceptions kept. Define new terms inline. -->

## Terms you now need

<!-- Two or three, each defined in one sentence. -->

## What this means for you

<!-- Tied to the job they are actually doing. -->

## What is missing

<!-- What the source did not say, and who can answer it. Explaining past a gap is
how a confident wrong answer spreads. -->

---

Label every claim: [verified: <source>], [your input], or [ASSUMPTION, verify].
Before this leaves your machine: python3 scripts/redact.py <file>
