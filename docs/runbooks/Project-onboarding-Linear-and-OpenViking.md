# Project onboarding: Linear and OpenViking

One-time setup so the repo is trackable in Linear and queryable via OpenViking in Cursor.

## Linear

1. **Setup:** [docs/engineering-system/linear-setup.md](../engineering-system/linear-setup.md) — create a Linear workspace and project (name **G-Trade**, team GDG), add Linear MCP in Cursor, and follow branch/commit/PR conventions.
2. **Backfill issues:** Create the suggested issues from [docs/engineering-system/linear-backfill-issues.md](../engineering-system/linear-backfill-issues.md) in your Linear project (manually or via `python scripts/linear_backfill.py` with `LINEAR_API_KEY` and `LINEAR_TEAM_ID` set). Create issues and reference documents in the **G-Trade** project only (not other workspace projects).

## OpenViking

1. **First-time ingest:** [docs/engineering-system/openviking-integration.md](../engineering-system/openviking-integration.md) — ensure `~/.openviking/ov.conf` and workspace dir exist, then run from G-Trade repo root (workspace root): `python scripts/onboard_openviking.py`. This regenerates `docs/generated/` and ingests `docs/`, `AGENTS.md`, and `README.md` into OpenViking.
2. **Refresh:** Run the same command after doc or structure changes, or use the Cursor command **Refresh OpenViking** (or `/refresh-openviking`).

## Quick links

- [Linear setup](../engineering-system/linear-setup.md)
- [OpenViking integration and first-time ingest](../engineering-system/openviking-integration.md)
- [Engineering system overview](../engineering-system/overview.md)
