---
type: llm
weight: 1
---

The user asked for a security review of a Flask /invoices endpoint that reads "customer" from the query string, builds SQL with an f-string, runs it and returns every row as JSON, with no authentication check. PASS if this condition holds, FAIL if it does not:
It says what it could not check, such as how the rest of the app handles authentication.
