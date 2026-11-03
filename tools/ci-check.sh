#!/usr/bin/env bash
# Preserve command status and expose bounded failure diagnostics as a check
# annotation, so validation remains diagnosable without signed log downloads.
set -uo pipefail
validation_log=$(mktemp)
trap 'rm -f "$validation_log"' EXIT
"$@" >"$validation_log" 2>&1
validation_status=$?
cat "$validation_log"
if [[ $validation_status -ne 0 ]]; then
    python3 - "$validation_log" <<'PY'
import sys
from pathlib import Path
message=Path(sys.argv[1]).read_text(errors='replace')[-12000:] or 'Validation command failed'
message=message.replace('%','%25').replace('\r','%0D').replace('\n','%0A')
print('::error title=Validation failure::'+message)
PY
fi
exit "$validation_status"
