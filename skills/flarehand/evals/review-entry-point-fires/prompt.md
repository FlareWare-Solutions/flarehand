---
max_turns: 25
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Bash, Skill]
tags: [trigger, entry-point, review, engineering, security]
---

Do a security review of this endpoint before I ship it.

```python
@app.route("/invoices")
def invoices():
    customer = request.args.get("customer")
    sql = f"SELECT * FROM invoices WHERE customer_name = '{customer}'"
    rows = db.execute(sql).fetchall()
    return jsonify([dict(r) for r in rows])
```
