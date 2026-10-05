---
max_turns: 25
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Bash, Skill]
tags: [trigger, product, founder, writeup, template]
---

Write a decision record from this thread.

Priya (eng lead): For the event store, Postgres with a partitioned table handles our 3M events a day fine. DynamoDB would mean a new on-call skill set.
Tom (CTO): I care about cost more than scale right now. Postgres it is unless the numbers say otherwise.
Lee (finance): Before we commit, can someone get me a monthly cost estimate for both? I haven't seen one.
Priya: I'll have the estimate by Friday.
Tom: OK. Going with Postgres, pending Lee's cost check.
