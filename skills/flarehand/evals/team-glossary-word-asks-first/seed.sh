#!/usr/bin/env bash
# Seeds a team playbook whose glossary says "migration" has three meanings on this team.
# Run by `claude plugin eval --scaffold` in the empty workspace, before the agent starts.
set -euo pipefail
git init -q .
mkdir -p .flarehand
printf '%s\n' '{"name": "northwind-platform", "owner": "Northwind platform team"}' > .flarehand/playbook.json
printf 'term\tmeanings\task\tadded\n' > .flarehand/glossary.tsv
printf 'migration\tcustomer data import | database schema change | cloud platform move\tWhich migration do you mean: a customer data import, a database schema change, or the cloud platform move?\t2026-09-01\n' >> .flarehand/glossary.tsv
printf '# Northwind platform\n\nShared shapes and rules for the platform team.\n' > README.md
