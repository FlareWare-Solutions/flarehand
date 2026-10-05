---
template: sql-build
title: Database change build plan
workflow: wf-09
pack: engineering
serves: [developer, dba, data-engineer, release-manager, qa-engineer]
source_status: mixed
team_sources: []
basis:
  - "Pramod Sadalage and Martin Fowler, Evolutionary Database Design (every change as a versioned migration script, applied in order) - https://martinfowler.com/articles/evodb.html"
  - "Scott Ambler and Pramod Sadalage, Refactoring Databases catalog (transition periods for changes others depend on) - https://databaserefactoring.com/"
verified_on: 2026-10-04
tags:
  group: build-run
  roles: [engineering, data, devops]
  frequency: per-event
  audience: team
next: [code-review, runbook]
learn:
  - "Does your team already have a migration checklist or database change process you like? Paste it or tell me where it lives, and I will follow its shape instead of this one."
  - "Which database and migration tool do you use, such as PostgreSQL with Flyway, MySQL with Liquibase, SQL Server with migrations in the app, or Oracle with plain scripts?"
  - "Which release must this change make, who reviews database changes, and does it touch one customer's data or everyone's?"
---

<!-- Template: sql-build, used by wf-09. The learn questions in the frontmatter come first. -->
<!-- Database changes ship as versioned scripts in the repo, applied in order by a tool or a process, never typed by hand into a shared database. -->

# Database change plan: <ticket> <short description>

## What done looks like

<!-- Every changed object installs from committed scripts on a clean database and on a copy of production, with no new errors or invalid objects, and the change reaches the target release. -->

## Change summary

- Ticket: <ABC-1234>
- Target release or branch: <ask which release the change must make; do not assume>
- Database and version: <PostgreSQL / MySQL / SQL Server / Oracle / other, with version>
- Migration tool: <Flyway / Liquibase / Alembic / Rails / EF Core / plain scripts / other>
- Schemas touched:
- Data change: none / one customer or tenant / all

## Objects changed

| Object | Type | Schema | New or changed | Who depends on it |
|---|---|---|---|---|
| <name> | table / column / index / view / function / procedure / trigger / data | | new / changed | <apps, reports, APIs, other teams> |

<!-- Install order, roughly: types and sequences, tables, columns, constraints, indexes, views, functions and procedures, triggers, then data. Your tool may decide this for you. -->

## Steps

1. **Write the migration** (Owner: <developer>, needs: nothing)
   - Name and number it the way your tool expects. One logical change per migration.
   - Check it worked: the tool lists it as pending, in the right order.
2. **Make it safe to run twice, or guard it** (Owner: <developer>, needs: step 1)
   - Use guards such as IF NOT EXISTS where your database supports them, or rely on the tool's history table.
   - Check it worked: running it again changes nothing.
3. **Back up the rows you will change** (Owner: <developer>, needs: step 1)
   - For a data correction, copy the affected rows to a backup table or export first.
   - Check it worked: the backup row count matches the rows you will change.
4. **Run it on a clean local database and on a copy of production data** (Owner: <developer>, needs: steps 2 and 3)
   - Check it worked: no errors, no new invalid objects, timings acceptable, nothing else changed.
5. **Check what depends on it** (Owner: <developer>, needs: step 4)
   - Search code, views, reports and APIs for every changed object. A rename or drop needs a transition period.
   - Check it worked: you list each dependent with its fix, or mark it unaffected.
6. **Code review** (Owner: <reviewer>, needs: step 5)
   - Check it worked: approved, including locking, long-running statements and tenant isolation.
7. **Commit and merge** (Owner: <developer>, needs: step 6)
   - Check it worked: the pipeline applies the migration to the first shared environment.
8. **Apply through each environment to production** (Owner: <release owner>, needs: step 7)
   - Check it worked: the migration history table shows it on each environment.

## Riskiest step

<!-- Usually the data correction or a change that locks a big table. Say which rows, how many, how long a lock could last, and when you will run it. -->

## Rollback

<!-- Many tools have a down migration, but data changes rarely reverse cleanly. Write yours, or say plainly that you will fix forward. -->

- Objects: <a down migration, or a new forward migration>
- Data: <the statement that restores rows from the backup in step 3>
- Who decides: <name> <!-- Ask; do not assume. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->

## What is missing or assumed

<!-- Anything you had to assume, and anything only someone else can supply. A plan with an
invisible assumption costs an hour. Say it here, and name who can answer it. -->
