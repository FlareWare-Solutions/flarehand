---
template: wf-11-enumerate
title: Coverage set
workflow: wf-11
serves: [qa, implementation, sales, support]
source_status: general-practice
team_sources: []
basis:
  - "ISO/IEC/IEEE 29119 test design overview - https://en.wikipedia.org/wiki/ISO/IEC_29119"
verified_on: 2026-09-14
learn:
  - "Do you have an existing list for this that I should extend rather than replace? Paste it."
  - "Where does this list live afterwards: TestRail, a spreadsheet, Jira, or a document?"
  - "What does a missed case cost here?"
---

<!-- Template for wf-11 enumerate. Every heading below is required.
     Check with: python3 scripts/check_output.py --contract wf-11 --style <file> -->

# Coverage set: <subject>

## What is covered

<!-- The thing under test, pinned: screen, endpoint, version, environment. -->

## Coverage dimensions

<!-- The axes you walked, and why those ones. This is what proves coverage. -->

## Cases

<!-- Each with a precondition, steps and an expected result. -->

## Negative and edge cases

<!-- Kept separate on purpose, because mixed in they get skipped. -->

## Gaps you must fill

<!-- What was out of reach, and what it would take. -->

---

Label every claim: [verified: <source>], [your input], or [ASSUMPTION, verify].
Before this leaves your machine: python3 scripts/redact.py <file>
