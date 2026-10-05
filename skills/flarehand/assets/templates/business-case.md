---
template: business-case
title: Business case or budget request
workflow: wf-05
serves: [manager, director, program-manager, finance-partner, founder, public-sector-officer]
source_status: sourced
team_sources: []
basis:
  - "HM Treasury, The Green Book: appraisal and evaluation in central government (the Five Case Model) - https://www.gov.uk/government/publications/the-green-book-appraisal-and-evaluation-in-central-government"
  - "HM Treasury, Guidance on developing business cases for projects and programmes (2026) - https://assets.publishing.service.gov.uk/media/6a4390675b6406df58c14006/Guidance_on_Developing_Business_Cases.pdf"
verified_on: 2026-10-04
tags:
  group: money
  roles: [leadership, finance, project, operations, any]
  frequency: per-event
  audience: exec
next: [project-charter, exec-brief]
learn:
  - "Does your organisation have a business case or budget request form already? Paste it and I will follow its shape instead of this one."
  - "Who approves this spend, and above what amount does it need a fuller case?"
  - "Where do the cost and benefit figures come from, and who in finance checks them?"
---
<!-- Template: business-case, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- Two modes. Full case: fill all five cases. Budget request: fill the Budget request summary, then one or two lines per case. The five cases come from the HM Treasury Five Case Model; the wording here is our own. -->
<!-- Every figure is copied from a named source. The assistant does not estimate costs, benefits or returns. -->

# Business case: <proposal>

## Draft status

| Field | Value |
|---|---|
| Mode | full case / budget request |
| Sponsor and author | |
| Approver and decision date | |
| State | draft / in review / approved / declined |

## Budget request summary
<!-- optional -->

- The ask: <amount, period, cost centre or budget line>
- What it buys:
- What happens if the answer is no:
- Decision needed by:

## Strategic case

<!-- Is there a case for change? Where things stand, the problem or opportunity, the objectives you can measure, and how it fits the organisation's plans. -->

- Current state:
- Problem or opportunity:
- Objectives, each measurable:
- Fit with strategy:

## Economic case

<!-- Does it give the best value? A long list cut to a short list. Always include doing nothing or the minimum. -->

| Option | Benefits | Costs | Main risks | Preferred? |
|---|---|---|---|---|
| Do nothing or the minimum | | | | |
| | | | | |

## Commercial case

<!-- Can it be bought or delivered on good terms? Supplier route, contract type, key terms. Write "Not applicable: delivered by our own staff" when nothing is bought. -->

## Financial case

<!-- Is it affordable? Costs by year, where the money comes from, and the effect on the budget. Copy figures; write any sum out for finance to check. -->

| Year | Capital | Running costs | Savings or income | Source |
|---|---|---|---|---|
| | | | | |

- Funding source:
- Checked by, in finance:

## Management case

<!-- Can it be delivered? Who owns it, the plan and milestones, the main risks, and how benefits will be tracked after delivery. -->

- Senior owner:
- Milestones:
- Top risks and owners:
- How and when you will measure benefits:

## MISSING - you must supply

- <figure, option or approval with no source>: <who has it>

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
