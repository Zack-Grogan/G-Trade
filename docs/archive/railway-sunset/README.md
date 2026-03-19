# Railway sunset archive

Railway was retired from the active G-Trade workflow on 2026-03-19.

## Why it was retired

- the live trading workflow had already moved to the Mac
- Railway was no longer materially helping execution, debugging, or operator decisions
- the local stack now covers the required surfaces: CLI, Flask console, SQLite durability, broker truth, regime analysis, trade review, and logs

## What replaced it

- **ingest / analytics / MCP / web / RLM** were replaced operationally by the local trader stack
- **SQLite** is the active source of truth
- **CLI + local Flask console** are the active operator interfaces

## Historical service inventory

- `g-trade-ingest`
- `g-trade-analytics`
- `g-trade-mcp`
- `g-trade-web`
- `g-trade-rlm`

## Historical repo mapping

See [repository-imports-2026-03-19.md](../repository-imports-2026-03-19.md) for the imported repo origins and SHAs.

## Archived notes retained here

- `implementation_plan.md`
- `IMPLEMENTATION-SUMMARY.md`
- `repo-audit-and-boundaries.md`
- `linear-backfill-issues.md`
- `linear-backfill-issues.json`
- `march-18-data-recovery-analysis.md`
- `railway-services-assessment.md`
- `railway-usage-policy.md`
- `railway-bridge-authentication-failure-analysis.md`

Git history retains the full retired codebase from the import commit onward, so the archive here stays intentionally compact.
