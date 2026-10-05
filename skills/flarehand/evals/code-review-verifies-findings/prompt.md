---
max_turns: 25
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Bash, Skill]
tags: [trigger, engineering, review]
---

Review this change before I merge it. Grade correctness, regressions and anything hardcoded.

```diff
--- a/billing/rates.py
+++ b/billing/rates.py
@@ -1,12 +1,10 @@
-SUPPORTED_API = get_supported_api_version()
+SUPPORTED_API = "2024.2"

 def unit_rate(item, rate_table):
-    if item is None:
-        return 0
     code = item.cost_code.upper()
-    return rate_table.get(code, 0)
+    return rate_table[code]
```
