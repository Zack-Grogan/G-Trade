# Local launch and test

## 1. Environment

- Copy `.env.example` to `.env` if you need local overrides.
- Keep `.cursor/mcp.json` and `.codex/config.toml` local-only.
- Review [ENV.md](ENV.md) for the active local env contract.

## 2. Start the trader

```bash
cd /Users/zgrogan/Repos/G-Trade
es-trade service install
es-trade service start
es-trade service doctor
```

There is no local HTTP console. Use the CLI for runtime inspection:

- `es-trade status`
- `es-trade health`
- `es-trade debug`

## 3. Verify local runtime

```bash
cd /Users/zgrogan/Repos/G-Trade
es-trade status
es-trade broker-truth
es-trade analyze launch-readiness
es-trade service logs --source app --lines 200
pytest -q
```

## 4. Operator validation

- Confirm `logs/runtime/runtime_status.json` reflects the expected phase and run id.
- Use `es-trade db snapshots --limit 5` (or equivalent) to confirm SQLite is recording state snapshots.
- Use `es-trade analyze launch-readiness` for the explicit launch gate summary.

## 5. Monday readiness checklist

1. launchd service healthy (`es-trade service doctor`)
2. broker truth matches selected account
3. SQLite readable and current
4. CLI `status` / `debug` show expected runtime (or SQLite-backed snapshot when inspecting another process)
5. launch gating and exit policy reflect the intended session posture
