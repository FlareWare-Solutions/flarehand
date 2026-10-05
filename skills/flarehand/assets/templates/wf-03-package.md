---
template: wf-03-package
title: Handover packet
workflow: wf-03
serves: [support, qa, product, sales]
source_status: general-practice
team_sources: []
basis:
  - "Institute for Healthcare Improvement, SBAR tool (Situation, Background, Assessment, Recommendation) - https://www.ihi.org/resources/tools/sbar-tool-situation-background-assessment-recommendation"
  - "Supportbench escalation standard - https://www.supportbench.com/write-bug-reports-engineers-love-support-to-engineering-template/"
verified_on: 2026-10-04
learn:
  - "Does the receiving team have a template they insist on? Paste it and I will match it exactly."
  - "What does that team send back most often, so we can make sure it is already answered?"
  - "Where does this go: a Jira issue, a case note, an email, or a chat thread?"
---

<!-- Template for wf-03 package. Every heading below is required.
     Check with: python3 scripts/check_output.py --contract wf-03 --style <file> -->

# Handover packet: <subject>

## Situation

<!-- One or two sentences. What is wrong, who it affects, and how bad. -->

## Background

<!-- Environment, version, history, reproduction steps, and who it happens to. -->

## Evidence

<!-- Each item with a source. Use [verified: evidence/<hash>.txt] for snapshots. -->

## Assessment

<!-- What you think is going on, each claim labelled. What has been ruled out, so nobody repeats it. -->

## Recommendation

<!-- What you want the receiving team to do, and by when. -->

## MISSING - you must supply

<!-- Every required field with no source. Name who can get each one. -->

<!-- This artifact must also contain: [verified: -->

---

Label every claim: [verified: <source>], [your input], or [ASSUMPTION, verify].
Before this leaves your machine: python3 scripts/redact.py <file>
