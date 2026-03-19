---
description: Authored docs are authority; generated docs are refreshable indexes. Update docs when behavior or deployment changes.
alwaysApply: false
---

# Docs engine

**When this applies:** Changing behavior, deployment, config surface, or safety-relevant logic; or when doc structure (modules, routes, entrypoints) changes.

**Do this:**
- Update the relevant authored doc (OPERATOR, architecture, runbook, Compliance-Boundaries, or engineering-system) and note it in the change.
- Do not hand-edit files under docs/generated/; they are machine-maintained. Re-run `python scripts/generate_docs_index.py` when structure changes.
- For material strategy or compliance implications, add research traceability per docs/Compliance-Boundaries.md.

**Full procedure:** AGENTS.md "Documentation contract" and "What requires docs updates"; docs/engineering-system/overview.md (generated docs).
