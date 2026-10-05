#!/usr/bin/env bash
# Seeds a knowledge base in the run's temporary home, so this is not a first run and the save menu
# is the expected close. The person said yes to the knowledge base earlier; learning is off.
# Run by `claude plugin eval --scaffold`. HOME is the run's temporary home here.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
kb=""
for candidate in "$here/../../skills/flarehand/scripts/kb.py" "$here/../../../skills/flarehand/scripts/kb.py"; do
  if [ -f "$candidate" ]; then kb="$candidate"; break; fi
done
if [ -z "$kb" ]; then
  echo "seed.sh: cannot find skills/flarehand/scripts/kb.py from $here" >&2
  exit 1
fi
python3 "$kb" init --no-detect --learning off \
  --name "Alex Rivera" \
  --role "I look after renewals for mid-size customer accounts" \
  --audience "my VP and the account team" \
  --output "short bullets, numbers first" >/dev/null
