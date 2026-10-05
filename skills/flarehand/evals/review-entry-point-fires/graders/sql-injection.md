---
type: llm
weight: 2
---

The user asked for a security review of a Flask /invoices endpoint that reads "customer" from the query string, builds SQL with an f-string, runs it and returns every row as JSON, with no authentication check. PASS if this condition holds, FAIL if it does not:
It flags SQL injection in the f-string query and gives a parameterised-query fix as code.
