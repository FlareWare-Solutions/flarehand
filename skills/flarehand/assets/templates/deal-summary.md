---
template: deal-summary
title: Deal summary, close plan or call recap
workflow: wf-05
serves: [account-executive, sales-engineer, account-manager, sales-manager, founder]
source_status: general-practice
team_sources: []
basis:
  - "MEDDICC and MEDDPICC elements - https://meddicc.com/meddpicc-sales-methodology-and-process"
  - "Salesforce, what a mutual action plan contains - https://www.salesforce.com/blog/mutual-action-plan/"
verified_on: 2026-09-14
tags:
  group: sell
  roles: [sales, founder, customer-success]
  frequency: per-event
  audience: team
next: [client-proposal, statement-of-work]
learn:
  - "Do you already have a close plan, mutual action plan, deal review or call recap you like? Paste one with the customer details removed, and I will follow its shape instead of this one."
  - "Does your team qualify deals with MEDDICC, MEDDPICC, BANT or its own list, and where do deal notes and stages live, such as Salesforce or HubSpot?"
  - "Who reviews your deals, how often, and what do they always ask first?"
---
<!-- Template: deal-summary, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- This holds customer names, contract values and personal data. Run python3 scripts/redact.py <file> before it goes to the buyer or a shared channel. -->

# Deal summary: <close plan, mutual action plan, deal review or call recap> for <account>

## The deal at a glance

- Piece: close plan / mutual action plan / deal review / call recap
- Account and opportunity name, as the CRM shows them: [your input]
- Stage, close date and amount, copied from the CRM: [your input]
- Who reads this: the buyer, your manager, a forecast call, or only you
- The buyer's compelling event, and its date: [your input]

<!-- Never invent a customer, a figure, a date or a quote. A blank field beats a plausible guess. Close here means signing the deal. -->

## Draft

<!-- Keep only the block for the piece you are writing, and delete the rest. -->

### Qualification, for a close plan or deal review

| Element | What we know | Evidence | Gap | Next action and Owner |
|---|---|---|---|---|
| Metrics | | | | |
| Economic buyer | | | | |
| Decision criteria | | | | |
| Decision process | | | | |
| Paper process | | | | |
| Implicate the pain | | | | |
| Champion | | | | |
| Competition | | | | |

<!-- These are the MEDDPICC elements. If your team uses its own variant or CRM field names, swap them in and save that version. -->

### Mutual action plan

| Date | Milestone | Buyer owner | Our owner | Status |
|---|---|---|---|---|
| | | | | |

<!-- Work back from the buyer's compelling event. Both sides own tasks, or it is a checklist, not a mutual plan. -->

### Deal review

- The ask of the reviewer: a decision, help, or information only.
- What changed since the last review.
- The biggest risk, and what would end the deal.
- Stakeholder coverage: who takes part, and who you have not met yet.
- Forecast category, using your team's definitions: [your input]

### Call recap

- Date, attendees and their roles.
- What we heard, with quotes taken only from your notes or a transcript.
- What we agreed.
- Next steps, each with an Owner and a date.
- Open questions, and who will answer each one.

<!-- A recap to the buyer uses their words and your commitments. Keep internal deal strategy out of it. -->

## MISSING - you must supply

- CRM fields that are blank or out of date, and where to confirm them.
- Stakeholders you have not identified, and who might know them.
- Any figure, date or quote with no source.

## Notes for the reviewer
<!-- author-only -->

<!-- Choices made, gaps worth a second look, and anything written from general practice rather than your team's own version. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
