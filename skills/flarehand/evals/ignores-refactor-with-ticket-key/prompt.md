---
max_turns: 5
timeout_seconds: 150
allowed_tools: [Read, Glob, Grep, Skill]
tags: [near-miss]
---

For TOOL-1234, refactor this into a list comprehension: def f(xs):
    out = []
    for x in xs:
        out.append(x * 2)
    return out
