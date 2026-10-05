---
template: wf-09-plan
title: Plan
workflow: wf-09
serves: [general, implementation, devops-dba, developer]
source_status: general-practice
team_sources: []
basis:
  - "Google SRE workbook on runbooks - https://sre.google/workbook/"
verified_on: 2026-09-14
learn:
  - "Does your team already have a checklist or plan format for this? Paste it and I will use it."
  - "Who is doing the work, and what access do they have?"
  - "What must not break while this happens?"
---

<!-- Template for wf-09 plan. Every heading below is required.
     Check with: python3 scripts/check_output.py --contract wf-09 --style <file> -->

# Plan: <subject>

## What done looks like

<!-- Concrete and checkable. -->

## Before you start

<!-- Prerequisites, access, and anything to have open. -->

## Steps

<!-- Exact commands or clicks. Nobody should need you to run these. -->

1. **<step>** (owner: <who>, needs: <step n>)
   - <exact command or click>
   - Check it worked: <how>

## Riskiest step

<!-- Which one, why, and what to do if it goes wrong. -->

## Rollback

<!-- How to undo it, or a plain statement that you cannot. -->

<!-- This artifact must also contain: Owner -->

## What is missing or assumed

<!-- Anything you had to assume, and anything only someone else can supply. A plan with an
invisible assumption costs an hour. Say it here, and name who can answer it. -->

---

Label every claim: [verified: <source>], [your input], or [ASSUMPTION, verify].
Before this leaves your machine: python3 scripts/redact.py <file>
