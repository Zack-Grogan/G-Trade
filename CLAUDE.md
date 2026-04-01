# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

G-Trade is a local-only ES futures day trading system. It connects to Topstep via REST/WebSocket, evaluates a weighted decision matrix of technical signals, and executes trades through hot-zone time windows. The operator interface is a CLI (`es-trade`) backed by SQLite observability. There is no cloud dependency for trading or debugging.

## Commands

```bash
# Install (editable, with dev deps)
pip install -e ".[dev]"

# Run tests
pytest                           # all tests
pytest tests/test_foo.py         # single file
pytest tests/test_foo.py::test_bar  # single test
pytest -x                       # stop on first failure

# Lint / format
ruff check .
black .

# CLI (installed via pyproject.toml entry point)
es-trade --help
es-trade config       # show loaded config (no credentials needed)
es-trade status       # runtime status
es-trade health       # health check
```

Tests use mocks — no `.env` or Topstep credentials required. `asyncio_mode = "auto"` in pyproject.toml, so async tests need no markers.

## Architecture

### Data flow

```
TopstepClient (WebSocket quotes) → BarAggregator → DecisionMatrixEvaluator → TradingEngine → OrderExecutor → Topstep REST API
```

### Key modules

- **`src/engine/trading_engine.py`** — Main orchestrator. Runs the tick loop, aggregates bars, calls the decision matrix, manages position lifecycle. This is the central coordination point.
- **`src/engine/decision_matrix.py`** — Weighted score matrix ("alpha engine"). Computes directional features (long/short/flat) from indicators, applies zone-specific weights, produces `MatrixDecision` with score and direction.
- **`src/engine/scheduler.py`** — `HotZoneScheduler` manages time-based trading windows (Pre-Open, Post-Open, Midday, Close-Scalp). Zones have states: `PENDING → ACTIVE → CLOSING → CLOSED`.
- **`src/engine/risk_manager.py`** — Position limits, daily loss limits, drawdown tracking.
- **`src/execution/executor.py`** — Order state machine (`PENDING_SUBMIT → ACK_PENDING → WORKING → FILLED → PROTECTED → FLAT`). Handles bracket orders (stop-loss + take-profit), flattening, and reconciliation with broker state.
- **`src/market/topstep_client.py`** — Topstep REST auth + WebSocket market data. Produces `MarketData` snapshots. Handles account selection via `preferred_id_match` config.
- **`src/config/loader.py`** — Dataclass-based config. `load_config()` reads `config/default.yaml` (authoritative operator profile). Bare `Config()` is for tests and may differ on defaults.
- **`src/observability/store.py`** — SQLite durability for runs, events, snapshots, and trade review.
- **`src/analysis/`** — Post-hoc analysis tools. **Important:** `trade_analyzer.py` analyzes actual trades (proper approach); `matrix_correlation.py` analyzes raw signals (has look-ahead bias, not suitable for threshold optimization).

### Config

`config/default.yaml` is loaded by `load_config()` and is the authoritative runtime profile. Key sections: `account`, `hot_zones`, `sessions`, `strategy`, `scoring` (matrix weights), `risk`, `order_execution`.

### Strategies

`src/strategies/` contains zone-mapped strategies (`orb_strategy.py`, `vwap_mr.py`, `vwap_trend.py`, `flatten_strategy.py`). Each inherits from `base.py` and produces entry/exit signals consumed by the decision matrix.

## Core rules

1. Execution and broker logic stay in `src/` only.
2. SQLite is the source of truth for runs, events, snapshots, and trade review.
3. No cloud dependency for trading, debugging, or review.
4. Do not reintroduce a cloud-to-executor control path.
5. `config/default.yaml` via `load_config()` is the authoritative config — bare `Config()` is a test shape.
6. The `launchd` service commands are macOS-only.

## Extra care areas

Changes to `src/engine/`, `src/execution/`, `src/market/`, and `src/observability/` affect live trading and require extra caution. Run relevant tests before completing changes in these areas.

## Documentation contract

Update docs when changing: CLI surface, observability taxonomy, config keys, strategy/exit behavior, or compliance-relevant behavior. Generated docs under `docs/generated/` are machine-maintained — do not hand-edit.
