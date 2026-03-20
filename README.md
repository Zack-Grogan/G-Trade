# G-Trade

CLI-based ES hot-zone day trading system. Execution, broker integration, observability, and operator tooling run locally from this repo root.

## Operator interface

The active operator surfaces are the **CLI** and **local SQLite** observability (`es-trade db …`, state snapshots in `logs/observability.db`).

- `es-trade` — show help and commands
- `es-trade start` — start the trading engine (live)
- `es-trade stop` / `es-trade restart` — lifecycle
- `es-trade status` — one-screen runtime status
- `es-trade debug` / `es-trade events` / `es-trade config` / `es-trade balance` / `es-trade health`
- `es-trade broker-truth --focus-timestamp <iso>` — inspect selected-account broker truth and contradiction flags
- `es-trade analyze regime-packet|trade-review|launch-readiness` — local analysis against SQLite and broker truth
- `es-trade service install|uninstall|start|stop|restart|status|logs|doctor` — manage the local `launchd` wrapper
- `es-trade db runs|events|snapshots|bridge-health|logs|account-trades|sync-account-trades` — inspect the local durability store

Runtime inspection is via the CLI (`es-trade status`, `es-trade health`, `es-trade debug`) and SQLite; there is no local HTTP console.

## Active layout

- `src/` — trader runtime, engine, execution, broker client, observability, runtime state, analysis
- `config/` — default config and local runtime defaults
- `tests/` — trader test suite
- `docs/` — operator, architecture, research, runbooks, and archive notes
- `scripts/` — repo and trader utility scripts
- `.codex/` and `.cursor/` — project-specific AI operating assets and examples

## Historical records

- Former nested repo imports: [docs/archive/repository-imports-2026-03-19.md](docs/archive/repository-imports-2026-03-19.md)
- Railway retirement notes: [docs/archive/railway-sunset/README.md](docs/archive/railway-sunset/README.md)

## Start here

- [docs/README.md](docs/README.md)
- [AGENTS.md](AGENTS.md)
