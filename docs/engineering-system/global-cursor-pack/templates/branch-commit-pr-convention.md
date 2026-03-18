# Branch / commit / PR convention (template)

Copy or adapt for your repo. See also docs/engineering-system/github-workflow.md.

**Branch:** `fix/PROJ-123-short-name` or `feat/PROJ-456-feature` when issue exists; `dev/short-name` or `topic/short-name` when exploratory.

**Commit:** Reference issue when present (e.g. "Fix retry PROJ-123"). Optional: feat:, fix:, docs: prefix.

**PR:** Use repo PR template. Title reflects change; body links issue, summarizes changes and testing. Run tests and update docs before marking ready.

**Review:** Human review for non-trivial or safety-relevant changes. Agents do not merge without explicit approval unless team config says otherwise.
