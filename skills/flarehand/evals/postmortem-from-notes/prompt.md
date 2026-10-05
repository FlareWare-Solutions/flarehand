---
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Bash, Skill]
tags: [trigger, engineering, writeup, template]
---

Turn my notes into a postmortem for the engineering team.

- Tue Oct 1, 14:05 UTC: deployed payments-api v2.14.0
- 14:12: alerts fired, checkout error rate hit 18%
- 14:20: on-call (Mei) paged, saw database connection timeouts
- 14:31: rolled back to v2.13.2
- 14:40: error rate back under 0.5%
- About 2,300 checkouts failed in that window (from the Grafana dashboard)
- Cause: Sam's PR changed the connection pool max from 50 to 5. The config change was in a separate file and nobody caught it in review.
- Actions: add a config lint to CI (Jordan, Oct 18). Alert on pool saturation (Mei, Oct 25).
