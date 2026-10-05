---
template: sop
title: Standard operating procedure
workflow: wf-05
serves: [operations-manager, quality-manager, lab-manager, support-manager, team-lead, compliance]
source_status: sourced
team_sources: []
basis:
  - "US EPA, Guidance for Preparing Standard Operating Procedures, EPA QA/G-6 (technical and administrative SOP structure) - https://www.epa.gov/quality/guidance-preparing-standard-operating-procedures-epa-qag-6-march-2001"
verified_on: 2026-10-04
tags:
  group: build-run
  roles: [operations, support, quality, compliance, any]
  frequency: per-event
  audience: team
next: [runbook, policy]
learn:
  - "Does your organisation already have an SOP format, numbering scheme or document control system? Paste an SOP you like and I will follow its shape."
  - "Who performs this procedure, and what training or sign-off do they need first?"
  - "Who approves the SOP, and how often must it be reviewed?"
---
<!-- Template: sop, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- An SOP is written for the person doing the work, at the moment they do it. One action per step. If a step needs judgement, say what to look for. -->

# SOP: <procedure name>

## Purpose and scope

- What this procedure achieves:
- When to use it:
- When not to use it, and what to use instead:
- Who it applies to:

## Definitions and roles

| Term or role | Meaning, or what they do |
|---|---|
| | |

- Training or qualifications needed before doing this:

## Safety, cautions and prerequisites

<!-- Warnings come before the steps they apply to, not after. List equipment, access, materials and conditions that must be in place. -->

- Cautions:
- Equipment, access or materials:
- Conditions that must be true before step 1:

## Procedure

<!-- Numbered. One action per step, starting with a verb. Give the expected result after any step where it can go wrong. -->

1. <action>
   - Expected result:
2. <action>
3. <if this, then do that; otherwise go to step n>

## Records and quality checks

- What to record, and where:
- How long to keep records:
- How a second person checks the work:
- What to do when a check fails:

## References and revision history

| Version | Date | Changed by | What changed |
|---|---|---|---|
| | | | |

- Related procedures, forms and standards:

## Document control
<!-- optional -->

| Field | Value |
|---|---|
| SOP number and version | |
| Owner | |
| Approved by and date | |
| Effective date | |
| Next review due | |

## Draft notes
<!-- author-only -->

<!-- For the author and reviewers only. Leave this section out of the published or sent text. -->

- State: draft / in review / approved / published
- Who must approve it before it takes effect:

## MISSING - you must supply

- <step detail, approval or reference with no source>: <who has it>

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
