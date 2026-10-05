---
template: finance-memo
title: Finance memo
workflow: wf-07
serves: [finance, controller, fp-and-a, accountant]
source_status: general-practice
team_sources: []
basis:
  - "PCAOB AS 2305 Substantive Analytical Procedures (expectation, threshold, corroborated explanations) - https://pcaobus.org/oversight/standards/auditing-standards/details/AS2305"
  - "FloQast month-end close checklist (sub-ledger to GL reconciliation, budget vs actual review) - https://www.floqast.com/blog/month-end-close-checklist"
verified_on: 2026-09-14
tags:
  group: money
  roles: [finance]
  frequency: per-event
  audience: team
next: [exec-brief]
learn:
  - "Does your team already have a variance commentary, flux or reconciliation memo you like? Paste it or tell me where it lives, and I will follow its shape instead of this one."
  - "Does your team keep a month-end close checklist, and which step of it does this memo belong to?"
  - "How big does a variance have to be before your team writes an explanation: a dollar amount, a percentage, or both?"
  - "Which reports do your figures come from, such as the trial balance, a sub-ledger aging, or the budget file?"
  - "Who prepares this memo, who reviews it, and how does the reviewer record the sign-off?"
  - "Who reads it in the end: the controller, the CFO, the auditors, or the board?"
---
<!-- Template: finance-memo, used by wf-07. The learn questions in the frontmatter come first. -->

# Finance memo: <entity, period, and account or report line>

**Every figure below comes from a named source. The assistant calculates nothing here. A named person verifies each figure.**

## Memo type and period

<!-- Variance commentary, flux analysis, or reconciliation. Name the entity, the period and the currency. -->

- Memo type: 
- Entity and period: 
- Compared against: <budget, forecast, prior month, prior year, or sub-ledger>

## What was compared

<!-- Pin both sides so anyone can rerun the comparison. A report name without a run date is not pinned. -->

| | Side A | Side B |
|---|---|---|
| Report or file | | |
| Run date and time | | |
| Entity, period, filters | | |

## Threshold for an explanation

<!-- Your team's rule for which differences need words. Ask; do not assume a number. -->

## Figures and their sources

<!-- Copy each figure from its source. Write the sum out. Leave the result blank unless the source states it; the verifier fills it. -->

| # | Line or account | Figure | Source (report, run date, row or cell) | Arithmetic written out | Result | Verified by |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

## Differences that matter

<!-- Ranked by consequence, not size. Give the business reason, not the number again. An explanation with no evidence stays Unexplained. -->

| Figure # | Over threshold? | Explanation | Evidence for the explanation | Status |
|---|---|---|---|---|
| | | | | Explained / Unexplained |

## What explains your symptom

<!-- The symptom is the variance or out-of-balance that made you look. Name the likely driver and the document that would confirm it. Mark it [ASSUMPTION, verify] until someone ties it out. -->

## Noise

<!-- Expected differences, such as timing, reclasses, exchange rates or rounding. Name each one so nobody chases it. -->

## Reconciliation tie-out

<!-- Reconciliation memos only. Detail total, summary total and GL control account should agree. Your ledger's own help usually lists the standard tie-outs for payables, receivables and other sub-ledgers. -->

| Check | Figure # (detail) | Figure # (summary or GL) | Agrees? | Checked by |
|---|---|---|---|---|
| | | | | |

## Proposed adjustments and open items

<!-- Proposed journal entries are proposals, not postings. Each one gets an owner and a due date. -->

## Could not compare

<!-- Anything out of reach, such as a report you could not run or a period still open. Say why. -->

## Review and sign-off

<!-- Who reviews this at your company, and how? Ask; do not assume. The reviewer reruns the arithmetic before signing. -->

| Role | Name | Date | Notes |
|---|---|---|---|
| Preparer | | | |
| Reviewer and verifier | | | |

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
