---
type: llm
weight: 1
---

The user asked for a security review of a Flask /invoices endpoint that reads "customer" from the query string, builds SQL with an f-string, runs it and returns every row as JSON, with no authentication check. PASS if this condition holds, FAIL if it does not:
Each finding has a location, a severity and a fix, and it grades the lenses it used.
