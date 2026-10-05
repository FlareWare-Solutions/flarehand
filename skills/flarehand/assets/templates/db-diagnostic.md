---
template: db-diagnostic
title: Database diagnostic report
workflow: wf-01
pack: engineering
serves: [dba, developer, data-engineer, sre, escalation-engineer, support-engineer]
source_status: mixed
team_sources: []
basis:
  - "PostgreSQL documentation, Using EXPLAIN - https://www.postgresql.org/docs/current/using-explain.html"
  - "MySQL Reference Manual, EXPLAIN output format - https://dev.mysql.com/doc/refman/8.4/en/explain-output.html"
  - "Microsoft SQL Server, display an actual execution plan - https://learn.microsoft.com/en-us/sql/relational-databases/performance/display-an-actual-execution-plan"
  - "Oracle Database 19c SQL Tuning Guide, Generating and Displaying Execution Plans - https://docs.oracle.com/en/database/oracle/oracle-database/19/tgsql/generating-and-displaying-execution-plans.html"
  - "Kepner-Tregoe Problem Analysis, The New Rational Manager chapter 2 - https://kepner-tregoe.com/wp-content/uploads/2025/08/The-New-Rational-Manager-Chapters-1-2-PA.pdf"
verified_on: 2026-10-04
tags:
  group: build-run
  roles: [data, engineering, devops, support]
  frequency: per-event
  audience: team
next: [rca, sql-build]
learn:
  - "Do you already have a database diagnostic report you like? Paste one and I will follow its shape instead of this one."
  - "Which database and version is it, and which tools do you use to look at it, such as psql, a monitoring dashboard, or the vendor's console?"
  - "Which environments may you query yourself, and which need a DBA to run the query for you?"
---
<!-- Template: db-diagnostic, used by wf-01. The learn questions in the frontmatter come first. -->

# Database diagnostic: <symptom>, <object>, <environment>

## Scope and safety

| Field | Value |
|---|---|
| Database, version and environment | |
| Customer, tenant or internal | |
| Schemas and objects examined | |
| Time window examined (time zone) | |
| Who ran the queries | |
| Changes made | none |

<!-- Read-only. Never create, alter or recompile anything on a shared or customer database while diagnosing. Turning on extra logging or tracing is a change: record it, and record when you turned it off. -->

## Reported cause (unverified)

<!-- What the reporter believes: the database is slow, an index is missing, something is locked. A lead, not a finding. -->

## Symptom

- What is slow or failing, and where it shows (screen, endpoint, job or report):
- Error text word for word, including every database error code:
- How long it takes now, and how long it took when it last worked:
- When it started, and what changed near then:

## What the evidence shows

- SQL captured, with parameter values, and how you captured it:
- Execution plan, and the method you used to get it:
- Statement statistics for the time window:
- Waits, locks and blocking sessions:
- Row counts, statistics dates and other query results:

<!-- Where to look. PostgreSQL: EXPLAIN (ANALYZE, BUFFERS), pg_stat_statements, pg_stat_activity, pg_locks. MySQL: EXPLAIN ANALYZE, the slow query log, performance_schema, SHOW ENGINE INNODB STATUS. SQL Server: the actual execution plan, Query Store, sys.dm_exec_requests, sys.dm_os_wait_stats. Oracle: DBMS_XPLAN.DISPLAY_CURSOR, V$SQL, V$SESSION, and AWR or Statspack if licensed. -->
<!-- An estimated plan can differ from the plan that ran, especially with bound parameters. Prefer the plan that actually ran. EXPLAIN ANALYZE runs the statement, so never use it on a data change in production. -->

## Queries run

```sql
-- paste each query exactly as you ran it, with the time you ran it
```

<!-- Only read-only statements belong here. For an endpoint, list every SQL call and separate session setup from the business queries. -->

## Hypotheses

### 1. <most supported>
Confirming:
Disconfirming:

### 2. <next>
Confirming:
Disconfirming:

### 3. <next>
Confirming:
Disconfirming:

<!-- Common candidates: a plan change, stale statistics, a missing or unused index, a function called once per row, data growth, lock contention, connection pool exhaustion, or a repeated query nobody needs. -->

## What is missing

<!-- The query, plan or log that separates the top two, and who has the access to get it. -->

## Recommendation

- Proposed change, for the owner to decide:
- Expected effect, and how you will measure before and after:
- Owner and approver:

<!-- Recommend only; do not apply. Who approves a database change on this environment? Ask; do not assume. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
