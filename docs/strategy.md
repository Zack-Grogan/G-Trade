# G-Trade ES Hot-Zone Strategy — Operator & Research Narrative

This document describes **how the live system thinks about the market** in trading terms: time structure, signals, vetoes, risk, and execution. It is not a developer manual, but each section points to **where the logic lives in code** so you can verify behavior.

**Primary implementation:** weighted score matrix in [`src/engine/decision_matrix.py`](../src/engine/decision_matrix.py), orchestration in [`src/engine/trading_engine.py`](../src/engine/trading_engine.py), risk in [`src/engine/risk_manager.py`](../src/engine/risk_manager.py), regime in [`src/engine/regime.py`](../src/engine/regime.py), defaults in [`config/default.yaml`](../config/default.yaml).

---

## 1. What we are trying to do

**Instrument:** ES (configurable symbol, default ES).  
**Style:** Intraday, **morning-first**, time-zone segmented (“hot zones”) with different playbooks per zone, but only the **Pre-Open** window is live by default. Later windows continue to score/log for evidence rather than trade live unless re-promoted.

**Core idea:**  
At each decision bar, the system builds a **rich feature snapshot** (price vs VWAP bands, RSI, Bollinger-style extension, order flow, spread/quote quality, regime, etc.), converts those into **directional scores** (long / short / flat bias), then applies **hard vetoes** (risk filters) before any entry is even considered. Entries only occur when scores are **decisive** and **gates** (launch zone, risk, market-hours guard, broker) allow it.

This matches a common institutional pattern: **separate “alpha” (scoring) from “risk & microstructure gates” (vetoes).** The code makes that split explicit.

---

## 2. Aggressiveness: how selective is this system?

**Verdict: medium-to-conservative on entries, with a layered defense.**  
It is **not** a high-frequency scalper firing on every micro-tick; it is **not** a single “always trade the trend” bot. It is designed to **trade rarely relative to bar updates** when:

- Scores exceed a **minimum level** and **beat the other side by a gap** (`min_entry_score`, `min_score_gap`, `flat_bias_buffer` in config / [`DecisionMatrixEvaluator.evaluate`](../src/engine/decision_matrix.py)).
- **Hard vetoes** are empty; `reduced_risk` is only a sizing posture and does **not** block an otherwise valid entry.
- **Launch gate** allows live entries only in configured “live” zones (see §4).
- **Risk limits** and **circuit breakers** permit a new trade.
- **Market-hours guard** (if enabled) does not block new entries ([`src/engine/market_hours.py`](../src/engine/market_hours.py), [`TradingEngine`](../src/engine/trading_engine.py)).

**Why it feels “tight” in Midday:**  
Midday is weighted toward **mean-reversion** features and adds **strict confirmation** (see §6.3). That is intentional: academically and practically, **mean reversion works best when paired with confirmation filters**; raw “price stretched” signals alone are prone to trend days. See [RSI overbought/oversold caveats](https://www.investopedia.com/articles/active-trading/042114/overbought-or-oversold-use-relative-strength-index-find-out.asp) and [Bollinger band mean-reversion context](https://www.investopedia.com/terms/b/bollingerbands.asp).

**Default position sizing:** risk module caps contracts from account and ATR ([`RiskManager.calculate_position_size`](../src/engine/risk_manager.py)); shipped `account.max_contracts` is **5** with `default_contracts: 1` unless sizing scales within that cap (see [`docs/OPERATOR.md`](OPERATOR.md)).

---

## 3. Time architecture: hot zones and sessions

### 3.1 Hot zones (when the playbook applies)

The clock is split into named windows (e.g. Pre-Open, Post-Open, Midday). The scheduler resolves **which zone you are in** ([`src/engine/scheduler.py`](../src/engine/scheduler.py)). If you are outside all configured zones but `trade_outside_hotzones` is true, the matrix treats the context as **`Outside`** ([`_effective_zone`](../src/engine/decision_matrix.py)).

### 3.2 ETH vs RTH context inside features

For the **Pre-Open** zone, the engine uses **ETH** session context for VWAP-style features; elsewhere it uses **RTH** session context ([`extract_features`](../src/engine/decision_matrix.py)). That aligns with how practitioners separate **overnight** vs **cash-session** behavior.

### 3.3 Launch gate: “shadow” vs “live” entries

**Launch gate** is a separate concept from the matrix score. It answers: *“Even if the matrix says LONG/SHORT, are we allowed to actually enter in this zone?”*  
Configured via `strategy.launch_gate_enabled`, `live_entry_zones`, `shadow_entry_zones` ([`config/default.yaml`](../config/default.yaml), [`_zone_live_entry_allowed`](../src/engine/trading_engine.py)).

- **Live entry zones:** entries may be submitted when other gates pass.
- **Shadow zones:** the system may still **score, log, and record decision snapshots** for research, but **blocks live entries** with outcome `shadow_only_zone`. The shipped default keeps `strategy.practice_shadow_trading_enabled` on so the practice account can trade shadow zones for mirror-style research while live remains blocked; you can still turn it off in YAML if you need stricter stand-down behavior.
- **Default posture:** `Pre-Open` live; `Post-Open`, `Midday`, and `Outside` shadow-only; `Close-Scalp` remains a scheduler-driven `flatten_only` window rather than a separate live edge.
- **Stand-down posture:** you may keep `launch_gate_enabled: true` with an empty `live_entry_zones` list to force full shadow-mode operation. When `session_exit_enabled` is still on, the morning session policy can still cap any open runtime position during checkpoint / hard-flat windows; “no live zones” is not the same thing as “ignore any existing exposure.”

This is a **risk / rollout** control, not a market-direction signal.

---

## 4. The signal engine (trader’s view)

### 4.1 Features → scores

For each zone, the config defines **weights** for long, short, and flat bias (`alpha.zone_weights`). The engine:

1. Computes normalized features (e.g. trend vs VWAP, pullback quality, extension, wick rejection, order-flow z-score).
2. Forms **long_score**, **short_score**, **flat_bias** as weighted sums.
3. Compares them to thresholds to decide **LONG / SHORT / NO_TRADE / HOLD / FLAT** (position management).

See [`evaluate()`](../src/engine/decision_matrix.py).

### 4.2 Regime (TREND / RANGE / STRESS)

A lightweight **3-state classifier** ([`DeterministicRegimeClassifier`](../src/engine/regime.py)) uses EMA slope, ATR ratio, spread, quote rate, OFI, and event flags.  
**STRESS** is treated conservatively: many zones veto it outright, and the default morning-first profile also damps score contribution with `regime_multipliers.STRESS = 0.3` rather than treating stress as a neutral live-entry regime. This preserves the March 18 fix (“Pre-Open no longer hard-vetoes STRESS at the matrix layer”) without turning stress into a free pass.

### 4.3 Stops and targets

Stops and targets are **ATR-scaled** from the snapshot ([`_risk_targets`](../src/engine/decision_matrix.py)), consistent with Wilder’s ATR as a volatility yardstick ([ATR overview](https://en.wikipedia.org/wiki/Average_True_Range); [Investopedia ATR](https://www.investopedia.com/articles/trading/08/average-true-range.asp)).

---

## 5. Veto audit — every hard gate (what it means, where it lives)

Vetoes are computed in [`_evaluate_vetoes()`](../src/engine/decision_matrix.py) and appended for risk state in [`evaluate()`](../src/engine/decision_matrix.py). They are logged on `matrix_state` lines and stored in SQLite `decision_snapshots` for forensics.

### 5.1 Global / cross-cutting vetoes

| Veto | Meaning | Code | Research / practice anchor |
|------|---------|------|---------------------------|
| `event_blackout` | Economic/news blackout window active | [`_evaluate_vetoes`](../src/engine/decision_matrix.py) | Event risk is a standard reason to stand down intraday. |
| `risk_circuit_breaker` | Risk manager in circuit-breaker state | [`evaluate()`](../src/engine/decision_matrix.py) | Circuit breakers are standard risk overlays. |
| `reduced_risk` | Reduced size / stricter posture | [`risk_manager.py`](../src/engine/risk_manager.py), [`TradingEngine._determine_contracts`](../src/engine/trading_engine.py) | Size down, do not hard-block a valid entry. |
| `risk_circuit_breaker` (risk manager) | Separate from matrix veto; can block trading | [`risk_manager.py`](../src/engine/risk_manager.py) | Hard stop when the risk manager trips. |
| `outside_zone` | Not in a tradable zone context | [`evaluate()`](../src/engine/decision_matrix.py) | Time segmentation. |

### 5.2 Execution quality vetoes

| Veto | Meaning | Code | Anchor |
|------|---------|------|--------|
| `execution_degraded` | Spread too wide or quote too stale vs `require_execution_tradeable` | [`_evaluate_vetoes`](../src/engine/decision_matrix.py), `execution_tradeable` in `extract_features` | Microstructure: toxic spreads and stale quotes precede bad fills. |
| `spread_too_wide` | Spread exceeds `max_spread_ticks` for that zone | [`_evaluate_vetoes`](../src/engine/decision_matrix.py) | Same theme. |

### 5.3 Volatility vetoes

| Veto | Meaning | Code | Anchor |
|------|---------|------|--------|
| `atr_percentile_too_high` | Current ATR is **high vs its recent distribution** (percentile over recent ATR window) | [`_evaluate_vetoes`](../src/engine/decision_matrix.py) | ATR measures volatility magnitude ([Wilder / ATR](https://en.wikipedia.org/wiki/Average_True_Range)); filtering high-volatility regimes reduces whipsaw in MR-style contexts. |
| `atr_spike_active` | ATR **acceleration** too high | [`_evaluate_vetoes`](../src/engine/decision_matrix.py) | Detects rapid volatility expansion. |

**Note:** `atr_percentile` is computed from the last **50** non-NaN ATR values in [`extract_features`](../src/engine/decision_matrix.py). On a short history or after a volatility jump, percentiles can read **very high**—that is expected behavior for a **relative** vol filter.

### 5.4 Regime vetoes

| Veto | Meaning | Code | Anchor |
|------|---------|------|--------|
| `regime_<name>` | Regime is in `blocked_regimes` for that zone (e.g. RANGE, STRESS) | [`_evaluate_vetoes`](../src/engine/decision_matrix.py) | Trend strategies underperform in chop; MR strategies underperform in strong trends—**regime alignment** is standard. |

### 5.5 Zone-specific vetoes

| Veto | Zone | Meaning | Code | Anchor |
|------|------|---------|------|--------|
| `inside_orb_middle` | Pre-Open | Price near ORB midpoint when `reject_orb_middle` | [`_evaluate_vetoes`](../src/engine/decision_matrix.py) | ORB literature emphasizes **breakout vs chop**; mid-range is ambiguous ([ORB overview](https://www.moneymarketinsights.com/p/opening-range-breakout-orb-strategy)). |
| `trend_flat` | Post-Open | VWAP slope and EMA slope both flat | [`_evaluate_vetoes`](../src/engine/decision_matrix.py) | Avoid low-conviction trend entries. |
| `ema_slope_outside_range` | Midday | Trend strength too high for MR-style midday | [`_evaluate_vetoes`](../src/engine/decision_matrix.py) | MR works best when range/two-sided behavior dominates. |
| `zone_too_late` | Midday | Too few minutes left in zone | [`_evaluate_vetoes`](../src/engine/decision_matrix.py) | Time stop / avoid late illiquid exits. |
| `breakout_follow_through_active` | Midday | ORB breakout feature too strong | [`_evaluate_vetoes`](../src/engine/decision_matrix.py) | Avoid fighting breakout days. |
| `missing_mean_reversion_confirmation` | Midday | MR requires **band penetration + RSI extreme + wick rejection** | [`_evaluate_vetoes`](../src/engine/decision_matrix.py), flags in `extract_features` | Combines **band** + **RSI** + **price action**—standard MR stack ([Bollinger](https://www.investopedia.com/terms/b/bollingerbands.asp), [RSI](https://en.wikipedia.org/wiki/Relative_strength_index)). |

### 5.6 Other gates (not always in `vetoes` list)

These are **not** necessarily duplicated in `active_vetoes` but **block or alter behavior**:

| Mechanism | Effect | Code |
|-----------|--------|------|
| Launch gate | Blocks entries in shadow zones | [`_zone_live_entry_allowed`](../src/engine/trading_engine.py) |
| Market-hours guard | Blocks **new entries** when closed; signals still run | [`MarketHoursGuard`](../src/engine/market_hours.py), [`TradingEngine`](../src/engine/trading_engine.py) |
| Market closed (broker) | Order rejected outside hours | [`TopstepClient.place_order`](../src/market/topstep_client.py) — broker is fallback truth |
| Risk limits | `max_daily_trades`, `max_trades_per_hour`, per-zone caps, etc. | [`risk_manager.py`](../src/engine/risk_manager.py) |

---

## 6. Mean reversion confirmation — what “correct” looks like

**Midday** MR confirmation is **intentionally strict**:

- **Long MR:** lower Bollinger penetration, RSI ≤ oversold threshold, meaningful lower wick rejection.
- **Short MR:** upper penetration, RSI ≥ overbought, upper wick rejection.

Defined in [`extract_features`](../src/engine/decision_matrix.py) (`mean_reversion_ready_long/short`) and gated in [`_evaluate_vetoes`](../src/engine/decision_matrix.py).

**Why this is “correct” in a trading sense:**  
Mean reversion without confirmation is **especially fragile** in index futures when a trend day persists ([RSI can stay oversold/overbought in trends](https://www.investopedia.com/articles/active-trading/042114/overbought-or-oversold-use-relative-strength-index-find-out.asp)). Requiring **price + oscillator + rejection** is a standard way to reduce false positives.

---

## 7. Execution and risk (high level)

- **Orders:** submitted through the execution layer after matrix + gates ([`src/execution/executor.py`](../src/execution/executor.py)).
- **Stops / targets:** ATR-based from [`_risk_targets`](../src/engine/decision_matrix.py).
- **Session exit:** morning-bounded flatten policy by **local clock** in PT for the live runtime. Default profile starts checkpoint flatten attempts at `10:00 PT`, retries if the position remains open, and hard-flats by `11:30 PT` ([`_should_flatten_for_session_policy`](../src/engine/trading_engine.py), config in `strategy.session_exit_*`). This applies to live-zone positions by default and expands to adopted/unknown-origin positions as a safety fallback for restart/adoption cases.

---

## 8. How to audit vetoes in production

1. **Logs:** search for `matrix_state` lines in `logs/trading.log` (see [`docs/OPERATOR.md`](OPERATOR.md)).
2. **SQLite:** `decision_snapshots.active_vetoes_json` and `feature_snapshot_json` ([`src/observability/store.py`](../src/observability/store.py)).
3. **CLI:** `es-trade db events` / `es-trade db snapshots` (see [`docs/OPERATOR.md`](OPERATOR.md)).

---

## 9. References (external)

These are **general market-structure / quant references** that align with the *mechanisms* used in code (not claims that this exact implementation was backtested against them).

1. **Average True Range (ATR)** — J. Welles Wilder; volatility and stop scaling. [Wikipedia](https://en.wikipedia.org/wiki/Average_True_Range), [Investopedia](https://www.investopedia.com/articles/trading/08/average-true-range.asp).  
2. **Relative Strength Index (RSI)** — Wilder oscillator; overbought/oversold and MR caveats. [Wikipedia](https://en.wikipedia.org/wiki/Relative_strength_index), [Investopedia RSI](https://www.investopedia.com/articles/active-trading/042114/overbought-or-oversold-use-relative-strength-index-find-out.asp).  
3. **Bollinger Bands** — volatility bands; MR interpretation. [Investopedia](https://www.investopedia.com/terms/b/bollingerbands.asp).  
4. **VWAP** — intraday benchmark; institutional execution and mean-reversion framing. [Trading-revealed (education)](https://www.trading-revealed.com/education/vwap-in-modern-markets-strategic-calculation-institutional-benchmarking-and-algorithmic-implementation/).  
5. **Opening range / breakout** — time-window structure around the open. [ORB guide (third-party)](https://www.moneymarketinsights.com/p/opening-range-breakout-orb-strategy).  
6. **Intraday seasonality / volatility shape** — time-of-day structure in index markets. [SSRN intraday volatility patterns](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3202021) (academic; methodology varies).  
7. **Order flow imbalance** — microstructure pressure; OFI-style features. [arXiv survey](https://arxiv.org/abs/2408.03594) (high-frequency context).

---

## 10. Maintenance

When you change **zone weights**, **vetoes**, **launch gate**, **risk limits**, or **market-hours guard**, update:

- [`config/default.yaml`](../config/default.yaml)
- [`docs/OPERATOR.md`](OPERATOR.md) if operator-visible behavior changes
- This document if the **trading strategy narrative** changes

---

*Document version: aligned with G-Trade hot-zone matrix (`hotzone-v3`) and local-only runtime.*
