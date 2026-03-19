# Local launch and test

## 1. Environment

- Copy `.env.example` to `.env` if you need local overrides.
- Keep `.cursor/mcp.json` and `.codex/config.toml` local-only.
- Review [ENV.md](ENV.md) for the active local env contract.

## 2. Start the trader

```bash
cd es-hotzone-trader
es-trade service install
es-trade service start
es-trade service doctor
```

Default local endpoints:

- `http://127.0.0.1:31380/health`
- `http://127.0.0.1:31381/`
- `http://127.0.0.1:31381/debug`

## 3. Verify local runtime

```bash
cd es-hotzone-trader
es-trade status
es-trade broker-truth
es-trade analyze launch-readiness
es-trade service logs --source app --lines 200
pytest -q
```

## 4. Browser validation

Check the local Flask console:

- `/` — console
- `/chart` — live chart
- `/trades` — trade list
- `/logs` — parsed runtime/operator logs
- `/system` — launch readiness and health

## 5. Monday readiness checklist

1. launchd service healthy
2. broker truth matches selected account
3. SQLite readable and current
4. local Flask console reachable
5. launch gating and exit policy reflect the intended session posture
