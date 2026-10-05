---
type: regex
target: last_message
match: not_contains
flags: i
weight: 3
---

\b\d[\d,.]*\s*(?:k\s*)?(?:requests?|calls?|req|rps|rpm)\b(?:\s*(?:per|/|an?|each)\s*(?:second|minute|hour|day|sec|min|s|m|h)\b)?
