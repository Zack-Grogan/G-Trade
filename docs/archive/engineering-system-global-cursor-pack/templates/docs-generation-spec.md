# Docs generation script spec

A script (e.g. `scripts/generate_docs_index.py`) should:

1. **Be safe and idempotent:** No app runtime, no network, no mutation of source. Only write under a single output dir (e.g. `docs/generated/`).
2. **Produce machine-friendly artifacts**, as appropriate for the stack:
   - dependency-map.md
   - module-map.md
   - routes-map.md (or endpoints) if applicable
   - config-matrix.md
   - testing-map.md
   - entrypoints.md
   - change-impact-map.md
   - service-relationships.md (if multi-service)
3. **Run from repo root.** Document in script header and in docs/engineering-system/overview.md.
4. **Output dir:** Put a README in the output dir stating that files are generated and must not be hand-edited.

Implement in the repo's primary language (e.g. Python for Python repos). Parse pyproject.toml, package.json, or static analysis as needed; do not import application code that has side effects.
