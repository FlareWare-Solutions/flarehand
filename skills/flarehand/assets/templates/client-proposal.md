---
template: client-proposal
title: Client proposal or bid response
workflow: wf-05
serves: [bid-manager, sales-engineer, account-executive, consultant, agency-lead, founder]
source_status: general-practice
team_sources: []
basis:
  - "Shipley, Managing Federal Proposals (compliance checklist, compliant outline, color team reviews) - https://www.shipleywins.com/training/managing-federal-proposals"
  - "Shipley, overview of color team reviews - https://www.shipleywins.com/training/an-overview-of-color-team-reviews"
  - "FAR 15.204-1 uniform contract format, Sections L and M - https://www.acquisition.gov/far/15.204-1"
verified_on: 2026-09-14
tags:
  group: sell
  roles: [sales, consulting, founder, operations]
  frequency: per-event
  audience: external
next: [statement-of-work, deal-summary]
learn:
  - "Do you already have a past proposal or response you like? Paste it or tell me where it lives, and I will follow its shape instead of this one."
  - "Is this a response to an RFP, RFI or tender, or a proposal the client did not ask for in a formal document?"
  - "Who decides bid or no-bid, and who signs off pricing, legal terms and the final submission?"
---
<!-- Template: client-proposal, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- Two modes. Formal response: fill everything, the compliance matrix first. Unsolicited proposal: skip the compliance matrix and the reviews table, and lead with the client's problem. -->
<!-- This holds the buyer's name, pricing and personal data. Run python3 scripts/redact.py <file> before any draft goes outside the bid team. -->

# Proposal: <client>, <title or reference>

## Draft

### Executive summary

<!-- The client's problem and the outcome they want come first. What you offer comes second. Respect any page limit. -->

### Compliance matrix

| Req ID | Section and page | Requirement, word for word | Shall, must or should | Response section | Owner | Status | Answer source |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

<!-- The Owner, Status and Answer source columns are for the bid team. Submit only the columns the issuer asks for, or none if it does not ask for a matrix. Every shall, must and will becomes a numbered row. Map instructions and evaluation criteria too, which US federal bids put in Sections L and M. -->

### Approach and answers

For each requirement, give the Req ID, the answer, and where the answer came from.

- Compliance: complies / partly complies / planned / does not comply
- Evidence: product documentation, a case study, or an approved library answer with its last review date

<!-- Never answer yes from memory. Security and accessibility answers use supplied evidence only. A planned answer is a commitment: ask who approves those. -->

### Team and experience

<!-- Who will do the work, and relevant past work the client can check. Only references you have permission to name. -->

### Pricing and commercial terms

<!-- Copy figures from the approved pricing. Never compute or estimate a price here, and name who approved it. -->

## Bid plan
<!-- author-only -->

<!-- For the bid team only. Fill it first; none of it goes into the submitted proposal. -->

### Opportunity summary

- Client, document type (RFP, RFI, RFQ, tender, or none) and reference number: [your input]
- Due date, time zone and submission method: [your input]
- Question deadline, and addenda received so far: [your input]
- Page limits, format rules and mandatory forms: [your input]
- Bid or no-bid decision, who made it, and when: [your input]

<!-- If a request says RFI or RFP and your industry also uses those letters for something else, ask which sense is meant before drafting. -->

### Win themes

| Client need | Our discriminator | Proof, with its source |
|---|---|---|
| | | |

<!-- A discriminator is something this client values that other bidders cannot claim. Proof is something an evaluator can check. -->

### Reviews before submission

| Review | What it checks | Date | Reviewers |
|---|---|---|---|
| Pink team | The outline and early draft follow the strategy | | |
| Red team | Reads as the evaluator and predicts the score | | |
| Final check | Compliance, forms, format and upload | | |

## MISSING - you must supply

- Requirements with no Owner, or with no sourced answer.
- Pricing, legal terms, signatures and mandatory forms still waiting for approval.

## Notes for the reviewer
<!-- author-only -->

<!-- Choices made, answers worth a second look, and anything written from general practice rather than your team's own version. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
