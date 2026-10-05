---
template: themes-report
title: Themes report
workflow: wf-08
serves: [ux-researcher, product-manager, support-manager, hr, marketing, customer-success]
source_status: general-practice
team_sources: []
basis:
  - "Braun and Clarke, reflexive thematic analysis (six phases, and themes as patterns of shared meaning around a central idea) - https://www.thematicanalysis.net/doing-reflexive-ta/"
  - "Nielsen Norman Group, affinity diagramming (group bottom-up, and do not discount a small cluster) - https://www.nngroup.com/articles/affinity-diagram/"
verified_on: 2026-09-14
tags:
  group: learn
  roles: [research, product, support, marketing, hr, customer-success]
  frequency: per-event
  audience: team
next: [exec-brief, product-brief, knowledge-article]
learn:
  - "Do you already have a themes or trends report you like? Paste it or tell me where it lives, and I will follow its shape instead of this one."
  - "Where do the items come from: a ticket export, a survey tool, a spreadsheet, or pasted text?"
  - "Does your team have a fixed category list or tagging scheme these themes must map onto?"
  - "Who reads the report, and what will they decide with it?"
  - "How often do you run this, and should the theme names stay the same between runs so you can compare?"
  - "May the report quote people word for word, or must you strip names and customer details from quotes first?"
---
<!-- Template: themes-report, used by wf-08. The learn questions in the frontmatter come first. -->
<!-- The research synthesis output of the themes workflow. It works on tickets, survey answers, feedback, or a set of interview snapshots from user-interview. -->

# Themes report: <what you read> from <start date> to <end date>

**Every count below comes from counting the items. There are no percentages and no estimates.**

## What I read

<!-- The number of items actually read, not the number in the system. If it is a sample, say how you picked it. -->

- Items read: 
- Source: <export, survey, file name and date pulled>
- Period: 
- All items or a sample: 
- Left out, with a count and reason: <duplicates, blank or spam>

## What this report is for

<!-- The decision it feeds, and any existing category list the themes must map onto. -->

## How I built the themes

<!-- Read every item before grouping. Code each item, group codes into themes, check each theme against its items, then name it. -->

Each item sits in exactly one theme, or in What did not fit. That is why the counts add up to the total.

## Themes

<!-- A theme name predicts what is inside it. Usability issues fails. Users cannot tell which approval step an invoice is waiting on passes. -->

### Theme 1: <specific name> (n = <count>)

- What it is: 
- Example 1, word for word (<item id>): "<quote>"
- Example 2, word for word (<item id>): "<quote>"
- Change over the period: <only if the dates show it>

### Theme 2: <specific name> (n = <count>)

- What it is: 
- Example 1, word for word (<item id>): "<quote>"
- Example 2, word for word (<item id>): "<quote>"
- Change over the period: 

<!-- Copy quotes exactly. A theme with fewer than two real quotes is not ready. -->

## Counts

<!-- Whole numbers counted from the items. Write each as n of N. No percentages, and no words like most or about a third. -->

| Theme | Count | Item ids or filter used |
|---|---|---|
| Theme 1 | | |
| Theme 2 | | |
| Did not fit | | |
| Total read | | |

## What did not fit

<!-- List each leftover with its id and a short quote. Then say whether they look like noise or a thin signal. Do not drop a small group because it is small. -->

| Item id | Short quote | Noise or thin signal? |
|---|---|---|
| | | |

## Limits of this read

<!-- What could skew it: a sample, one customer raising many items, a gap in dates, or items you could not open. -->

## Suggested next step

<!-- Who decides, and on what. A theme that keeps returning is a candidate for a knowledge article (wf-05). -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
