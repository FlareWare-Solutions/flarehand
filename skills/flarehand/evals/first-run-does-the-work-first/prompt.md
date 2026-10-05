---
max_turns: 25
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Bash, Skill]
tags: [trigger, first-run, memory, writeup]
---

Write a help article for our support site on resetting two-factor authentication for a user in the Northwind admin console. Steps: go to Admin > Users, search for the user, open their profile, click Reset 2FA, then tell the user to sign in again and enroll a new device. Only workspace owners and admins can do this. Every reset is recorded in the audit log.
