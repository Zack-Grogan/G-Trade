# Project onboarding: Linear

One-time setup so the repo is trackable in Linear and generated docs stay current.

## Linear

1. **Setup:** [docs/engineering-system/linear-setup.md](../engineering-system/linear-setup.md) — create a Linear workspace and project (name **G-Trade**, team GDG), add Linear MCP in Cursor, and follow branch/commit/PR conventions.
2. **Backfill issues:** Create the suggested issues from [docs/engineering-system/linear-backfill-issues.md](../engineering-system/linear-backfill-issues.md) in your Linear project (manually or via `python scripts/linear_backfill.py` with `LINEAR_API_KEY` and `LINEAR_TEAM_ID` set). Create issues and reference documents in the **G-Trade** project only (not other workspace projects).

## Generated docs

Refresh machine-maintained maps under `docs/generated/` after significant doc or structure changes:

```bash
python scripts/generate_docs_index.py
```

Run from the G-Trade repo root (workspace root where `docs/` and `scripts/` live).

## Quick links

- [Linear setup](../engineering-system/linear-setup.md)
- [Engineering system overview](../engineering-system/overview.md)
