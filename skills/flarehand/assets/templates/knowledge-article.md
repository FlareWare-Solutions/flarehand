---
template: knowledge-article
title: Knowledge article or known error
workflow: wf-05
serves: [support-analyst, support-engineer, technical-writer, it-helpdesk, developer, qa]
source_status: mixed
team_sources: []
basis:
  - "KCS v6 Practices Guide, Technique 5.1 KCS article structure (issue, environment, resolution, cause) - https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040/010/020"
  - "KCS v6 Practices Guide, Technique 5.2 KCS article state (work in progress, not validated, validated, archived) - https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040/010/030"
  - "ITIL problem management terms (problem, known error, workaround, known error database), IT Process Maps ITIL wiki - https://wiki.en.it-processmaps.com/index.php/Problem_Management"
verified_on: 2026-09-14
tags:
  group: respond-support
  roles: [support, engineering, documentation, qa]
  frequency: per-event
  audience: external
next: [customer-reply]
learn:
  - "Does your team have a knowledge article or known error format already? Paste one you like and I will follow its shape instead of this one."
  - "Where will this be published, who searches there, and who has to review an article before others rely on it?"
  - "What words would someone type when they hit this problem?"
---
<!-- Template: knowledge-article, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- Two modes. Answer: a question or how-to with a known resolution. Known error: a problem with a documented cause and a workaround, but no permanent fix yet. Fill Known error details only in that mode. -->
<!-- Written so the next person finds it instead of asking. Strip customer names, project names and figures. An article that names one customer helps one customer. -->

# <the problem, in the words someone would search for>

## Issue

<!-- What the person sees, in their words, then any error text pasted word for word. Their words are what make it findable. For a how-to, one line saying what the task is, from their words only. Never guess when or why someone needs it: put that on the MISSING list. -->

## Environment

<!-- Product, version, platform, configuration and role or permissions where this applies. Say where it does not apply, too. An article that applies to everything applies to nothing. -->

## Resolution

<!-- The steps that fix it, numbered, exact and checkable. In known error mode, this is the workaround: say who can apply it, its side effects and how to undo it. -->

1. 
2. 

## Cause
<!-- optional -->

<!-- Leave this section out of a how-to. Fill it only when a source gives the cause. Why it happens, briefly. Add a cause test: how the next person proves this cause applies to their case. This stops the fix being applied to a different problem. -->

- Cause:
- Cause test:

## Known error details
<!-- optional -->

| Field | Value |
|---|---|
| Cause | confirmed / suspected |
| Permanent fix | none yet / in progress / shipped in <version> |
| Ticket or problem record | |
| Look-alike errors with a different cause | |

<!-- Leave the shipped version empty until release notes or the ticket confirm it. Never guess a version number. When the fix ships, update the article and retire the workaround. -->

## Draft notes
<!-- author-only -->

<!-- For the author and reviewers only. Leave this section out of the published or sent text. -->

| Field | Value |
|---|---|
| Mode | answer / known error |
| Article state | work in progress / not validated / validated / archived |
| Audience | internal / customer-facing |
| Linked cases or tickets | |
| Last checked | |

## MISSING - you must supply

- <field>: <who can supply it>

---

<!-- No customer names, project names, dollar figures or personal data. -->
<!-- If this is the third linked case, say so. It is a candidate for a product fix. -->
<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
