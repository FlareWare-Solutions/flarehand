---
template: data-migration
title: Data migration plan
workflow: wf-09
pack: engineering
serves: [data-engineer, implementation-consultant, solution-architect, developer, dba, project-manager]
source_status: mixed
team_sources: []
basis:
  - "GAO Federal Information System Controls Audit Manual (FISCAM) GAO-09-232G, section 4.3 interface and conversion controls - https://www.gao.gov/assets/gao-09-232g.pdf"
  - "Microsoft Dynamics 365 implementation guide, configuration and migration data - https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/data-management-configuration-data-migration"
  - "Microsoft Dynamics 365 implementation guide, go-live checklist data migration section - https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/prepare-go-live-checklist"
verified_on: 2026-09-14
tags:
  group: build-run
  roles: [data, engineering, consulting, project]
  frequency: per-event
  audience: team
next: [cutover, test-plan]
learn:
  - "Does your team already have a migration plan or mapping document you like? Paste it or tell me where it lives, and I will follow its shape instead of this one."
  - "How many trial loads do you usually run before the final one, and which figures does the data owner sign off on?"
  - "How do you load data: the target system's import tools, SQL scripts, an ETL tool, or your own code?"
---

<!-- Template: data-migration, used by wf-09. The learn questions in the frontmatter come first. -->

# Data migration plan: <project>

## What done looks like

<!-- Checkable: every in-scope object loaded into production, reconciled to the source, and signed off by the named data owner. -->

## Scope

| Object | Source system | History or open items only | As-of date | Owner |
|---|---|---|---|---|
| | | | | |

<!-- List what you are not migrating too, and where that data will live. Name each environment you load into. -->

## Load order

<!-- Setup comes before master data, and master data comes before transactions. The target system's docs usually say which setup must exist first. -->

1. Setup and reference tables
2. Master data, such as customers, suppliers, products, users or accounts
3. Opening balances or current state
4. Open transactions and history

## Mapping

| # | Target field | Type | Required | Format or valid values | Source field | Transform rule | Sample | Comments |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | |

<!-- Start from the target's import template where one exists. Name the uniqueness key that stops a record loading twice. Read each import tool's limits before you map: some fields cannot be imported and need another plan. -->

## Trial loads

| Trial | Environment | Date | Objects | Exit criteria | Result |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |

<!-- Load into staging, validate, fix, re-validate, then process. Log every rejected row and its fix. -->

## Reconciliation

| Object | Measure | Source value | Target value | Difference | Explanation | Signed off by |
|---|---|---|---|---|---|---|
| | Record count | | | | | |
| | Control total, such as a net balance | | | | | |

<!-- Tie control totals and record counts between source and target, and explain every difference. Where the new system calculates something differently, expect some differences and explain each one. [verified: https://www.gao.gov/assets/gao-09-232g.pdf] -->

## Steps

<!-- The final run inside the cutover window. Give each step an Owner and a check. Copy these rows into the cutover plan. -->

| # | Step | Owner | Needs | Check it worked |
|---|---|---|---|---|
| 1 | Freeze the source at the agreed cut-off time | | | Last transaction id noted |
| 2 | Extract, and keep an untouched copy of the files | | 1 | Record counts captured |
| 3 | Transform and load in the load order above | | 2 | No rejected rows left |
| 4 | Reconcile, then get the data owner's sign-off | | 3 | Every difference explained |
| 5 | Clear the staging tables once sign-off is in | | 4 | Staging tables empty |

## Riskiest step

<!-- Usually step 4 on the final run, because there is no time left to reload. Say which object is most likely to fail and what you do then. -->

## Rollback

<!-- Before users work in production, you can delete the loaded data or restore the backup and reload. After they start, you correct forward. Say which applies to each object. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->

## What is missing or assumed

<!-- Anything you had to assume, and anything only someone else can supply. A plan with an
invisible assumption costs an hour. Say it here, and name who can answer it. -->
