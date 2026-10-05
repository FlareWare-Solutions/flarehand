---
template: escalation-packet
title: API escalation packet
workflow: wf-03
serves: [support-engineer, escalation-engineer, developer-advocate, integration-engineer]
source_status: general-practice
team_sources: []
basis:
  - "Supportbench, writing bug reports engineers act on (support to engineering escalation) - https://www.supportbench.com/write-bug-reports-engineers-love-support-to-engineering-template/"
  - "Institute for Healthcare Improvement, SBAR tool (Situation, Background, Assessment, Recommendation) - https://www.ihi.org/resources/tools/sbar-tool-situation-background-assessment-recommendation"
  - "RFC 9457, Problem Details for HTTP APIs (the fields an API error response can carry) - https://www.rfc-editor.org/rfc/rfc9457"
verified_on: 2026-10-04
tags:
  group: respond-support
  roles: [support, engineering]
  frequency: per-event
  audience: team
next: [customer-reply, knowledge-article]
learn:
  - "Does your team have an API triage guide or escalation checklist? Paste it and I will build the packet to match."
  - "Which deployment is this: hosted, self-hosted, or a specific region or tenant?"
  - "Which team owns the failing endpoint, and what do they send back most often as incomplete?"
---

<!-- API escalation packet. Fuller than the generic wf-03 template, for a failing API call.
     Check with: python3 scripts/check_output.py --contract wf-03 --citations <file>
     Anything required and empty prints as MISSING. It never silently disappears. -->

# API escalation packet: <short description>

## Situation

What is wrong, who it affects, and how bad. One or two sentences.

## Background

### 0. Client

- Deployment: hosted / self-hosted / other
- Tenant, account or region: <if hosted>
- Customer environment: <name and URL>
- Version: <from the version endpoint, build info or release notes>

### 1. Request

- Endpoint path:
- Method:
- Request body, with secrets removed:

### 2. Response

- Status code:
- Error message:
- Request or correlation id:
- Full response body: [verified: evidence/<hash>.txt]

### 3. Reproduction

**On the customer environment**
1.

**On an internal environment**
1.

Does it reproduce internally? yes / no / not tried

## Assessment

### 4. Triage path

Every question asked and the answer given, numbered, in order.

### 5. What has been ruled out

So nobody repeats the work.

## 6. Evidence and findings

<!-- Evidence is in the name so a reader, and check_output.py, can see the evidence is here. -->

Each item with a source: logs, traces, metrics or the code. Include timing if it is relevant.

## Recommendation

What you want engineering to do, and by when.

## MISSING - you must supply

- <field>: <who can get it, and how>

---

**Before filing.** Compare the customer's version with the latest internal build. If yours is newer
and the problem does not reproduce there, recommend the upgrade path instead of opening a defect.

**Not every escalation is a defect.** Rate limit or quota raises go to whoever owns capacity.
Questions about intended behaviour go to Product. Only the rest becomes a defect
for the team that owns the endpoint.
