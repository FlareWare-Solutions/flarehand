---
template: wf-02-elicit
title: Questions to ask
workflow: wf-02
serves: [support, product, implementation, sales]
source_status: general-practice
team_sources: []
basis:
  - "GitHub spec-kit clarify step - https://github.com/github/spec-kit"
verified_on: 2026-09-14
learn:
  - "Do you already have a question list or intake form for this? Paste it and I will build on it."
  - "Who will you send these questions to, and what can they realistically find out?"
  - "How many rounds of back and forth can you afford: one, or several?"
---

<!-- Template for wf-02 elicit. Every heading below is required.
     Check with: python3 scripts/check_output.py --contract wf-02 --style <file> -->

# Questions to ask: <subject>

## What I already know

<!-- The facts in hand, with where each came from. Shows you read their message. -->

## Questions

<!-- Ordered by what unblocks the most. -->

1. **<question>**
   Recommended: <the answer you would assume>
   Why it matters: <what changes depending on the answer>

## If you would rather not answer

<!-- What you will assume instead, and the risk that carries. -->

<!-- This artifact must also contain: Why it matters -->

---

Label every claim: [verified: <source>], [your input], or [ASSUMPTION, verify].
Before this leaves your machine: python3 scripts/redact.py <file>
