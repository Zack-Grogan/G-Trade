#!/usr/bin/env bash
# Example: warn on dangerous patterns in the last command (source from your hook or use as reference).
# Install: copy to your hook path and chmod +x; integrate with your workflow.
set -euo pipefail
# Example pattern check (customize as needed)
if echo "${*:-}" | grep -qE 'rm\s+-rf\s+/|:(){|git push.*--force'; then
  echo "WARNING: Command may be destructive. Confirm before proceeding."
  exit 1
fi
exit 0
