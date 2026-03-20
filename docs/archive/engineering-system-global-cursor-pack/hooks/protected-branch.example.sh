#!/usr/bin/env bash
# Example: warn when pushing to a protected branch. Set BRANCH and PROTECTED_BRANCHES.
# Install: copy to your hook path; integrate with git pre-push or your workflow.
set -euo pipefail
BRANCH="${1:-$(git branch --show-current)}"
PROTECTED_BRANCHES="${PROTECTED_BRANCHES:-main,master,production}"
for b in ${PROTECTED_BRANCHES//,/ }; do
  if [[ "$BRANCH" == "$b" ]]; then
    echo "WARNING: Pushing directly to protected branch '$b'. Prefer a PR."
    exit 1
  fi
done
exit 0
