# Linear backfill issues

Suggested issues to create in the G-Trade Linear project, derived from [Tasks.md](../Tasks.md), [Current-State.md](../Current-State.md), and the TUI Sunset plan.

| Title | Description | Type |
|-------|-------------|------|
| Phase 7 — Hardening | Backpressure on outbox size, alerts on queue growth, replay/consistency checks, recovery/rollback runbook (optional/future). Source: Tasks.md Phase 7. | feature |
| E2E validation | Confirm full path (Mac bridge → ingest → Postgres → analytics/MCP/web) in your environment with a test run. Source: Tasks.md Open / future. | task |
| Track new work in Linear | Migrate from Tasks.md checklist to Linear for new features and ops work; keep Tasks.md for completed migration only. Source: Tasks.md. | task |
| Outbox backpressure | Implement backpressure when outbox size exceeds a threshold. Phase 7 / Current-State. | feature |
| Alerts on queue growth | Add alerts or monitoring when bridge outbox/queue growth indicates backlog or ingest slowness. Phase 7 / Current-State. | feature |
| Replay and consistency checks | Replay/consistency checks between local observability store and Railway Postgres. Phase 7 / Current-State. | feature |
| Recovery and rollback runbook | Short runbook for recovery and rollback when bridge or ingest fails or data is inconsistent. Phase 7 / Current-State. | task |
| Integration/E2E tests vs Railway | Add integration or E2E tests against real Railway services; document how to run them. Current-State. | task |

**Note:** The first three may already exist in G-Trade (e.g. GDG-211, GDG-212, GDG-213). To avoid duplicates, either create only the new issues manually in Linear, or remove the first three entries from `linear-backfill-issues.json` before running the script.

Create issues with `scripts/linear_backfill.py` using `LINEAR_API_KEY`, `LINEAR_TEAM_ID`, and `LINEAR_PROJECT_ID` (see [linear-setup.md](linear-setup.md)).
