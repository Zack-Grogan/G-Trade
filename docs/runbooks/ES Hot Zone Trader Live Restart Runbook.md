# ES Hot Zone Trader Live Restart Runbook

## Scope

This runbook describes the safest restart path for the ES Hot Zone Trader after lifecycle hardening. It assumes the trader is launched from the repo root and that the operator wants a clean, auditable stop/start sequence with preserved restart intent.

## Runtime Artifacts

The trader now maintains runtime control artifacts under the log directory:

- `logs/runtime/trader.pid`
- `logs/runtime/lifecycle_request.json`
- `logs/runtime/runtime_status.json`

The runtime status file is the quickest local source of truth for:

- current PID
- current phase
- current run ID
- data mode
- latest lifecycle request metadata

Lifecycle events are also persisted into SQLite at:

- `logs/observability.db`

Relevant system event types include:

- `startup`
- `shutdown_requested`
- `shutdown`
- `startup_failed`

## Pre-Restart Checks

From the repo root, verify runtime control files and CLI output (no local HTTP server):

```bash
cat logs/runtime/runtime_status.json
es-trade status
es-trade debug
```

The local operator surfaces are the CLI and SQLite. `es-trade debug` prints JSON including `_runtime_state_source` (`in_process`, `sqlite`, or `status_file`).

Inspect the runtime state for:

- `status`
- `running`
- `data_mode`
- `lifecycle`
- `observability.run_id`

## Clean Stop

Request a clean stop with an explicit reason:

```bash
python3 -m src.cli.commands stop --reason operator_stop
```

Expected behavior:

- `lifecycle_request.json` is written with the stop request
- the running process receives `SIGTERM`
- the engine records `shutdown_requested`
- the engine stops market/execution services and flushes observability
- the engine records `shutdown`
- `trader.pid` is removed
- `runtime_status.json` moves to `stopped`

If the trader is already down, the command exits cleanly and reports that it is not running.

## Clean Restart

Preferred restart path:

```bash
python3 -m src.cli.commands restart --reason operator_restart
```

Optional mode override:

```bash
python3 -m src.cli.commands restart --reason operator_restart --mock
python3 -m src.cli.commands restart --reason operator_restart --live
```

Expected restart behavior:

1. A restart request is written to `lifecycle_request.json`
2. The old process receives `SIGTERM`
3. The old process records `shutdown_requested` and `shutdown` with `requested_action=restart`
4. The restart request remains on disk across the shutdown boundary
5. The new process starts and records `startup` with the carried restart metadata
6. `lifecycle_request.json` is cleared after successful startup
7. `runtime_status.json` returns to `running`

## Fresh Start

If the process is down and you want a normal launch:

```bash
python3 -m src.cli.commands start
```

For mock validation instead of live trading:

```bash
python3 -m src.cli.commands start --mock
```

## Post-Start Verification

After a start or restart, verify all of the following:

```bash
es-trade status
es-trade debug
python3 -m src.cli.commands events --limit 20 --category system
```

Healthy restart indicators:

- `runtime_status.json` shows `phase=running`
- `trader.pid` exists and matches the active Python PID
- `es-trade health` / `es-trade debug` return expected fields (see `_runtime_state_source` in debug output)
- recent system events include `startup`
- if this was a restart, the new `startup` payload includes:
  - `requested_action`
  - `operator_reason`
  - `request_id`
  - `request_source`

## When to Stop and Investigate

Do not proceed to live operation if any of the following are true:

- `startup_failed` appears in recent system events
- `runtime_status.json` remains in `starting`, `stopping`, or `error`
- the PID file points to a dead process
- `es-trade health` fails to return sensible output while the trader should be running
- recent lifecycle events show repeated shutdown errors

## Local Forensics Commands

Recent lifecycle events:

```bash
python3 -m src.cli.commands events --limit 50 --category system
```

Recent execution events:

```bash
python3 -m src.cli.commands events --limit 50 --category execution
```

Current runtime status artifact:

```bash
cat logs/runtime/runtime_status.json
```

Current lifecycle request artifact:

```bash
cat logs/runtime/lifecycle_request.json
```

## State reset and compliance (for major upgrades)

The local trader migration is complete. This section is retained for future major upgrades or when you need a clean freeze and state reset (e.g. before changing runtime behavior or after stuck state).

1. **Freeze:** Stop the trader and do not start it until the upgrade or fix is ready.
   ```bash
   python3 -m src.cli.commands stop --reason pre_migration_freeze
   ```
2. **Verify stopped:** Confirm `logs/runtime/trader.pid` is removed (or points to a dead process that you can clean up) and `es-trade status` shows the engine is not running.
3. **State reset (if needed):** If there was an unresolved entry or stuck state before stop:
   - Inspect `logs/runtime/runtime_status.json` and `logs/observability.db` (e.g. `events` table, last `run_id`).
   - Clear any stale `lifecycle_request.json` or `operator_request.json` under `logs/runtime/` so the next start sees a clean request state.
   - The engine’s startup reconciliation will re-sync with broker on next start; ensure no manual broker state is left that would conflict (e.g. open orders from a previous run that you intend to manage via the new process).
4. **Compliance gate:** Complete the checklist in [../Compliance-Boundaries.md](../Compliance-Boundaries.md) and run `scripts/compliance_gate.py` (or set `COMPLIANCE_GATE_ACK=1` after confirming).

Do not proceed with runtime changes until the freeze and state-reset steps are done and the compliance gate is satisfied.

## Notes

- Use `restart` instead of manually killing the process when possible.
- Use `--mock` for validation and dry runs.
- `docs/trades_export.csv` (repo root) remains manual reference only and is not part of the automated lifecycle or observability path.
