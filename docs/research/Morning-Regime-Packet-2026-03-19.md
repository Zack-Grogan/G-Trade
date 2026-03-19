# Morning Regime Packet

Generated: `2026-03-19`

## Scope

This note answers one narrow question for the Sunday/Monday launch:

- what conditions were present in the recent winning trades
- whether those conditions look direction-specific or regime-specific
- whether the observed 6-10 hour holds are intentional alpha or tracking drift
- what should stay live for the next market open

This is a research artifact, not a product feature. The Topstep CSV at [`/Users/zgrogan/Downloads/trades_export (1).csv`](/Users/zgrogan/Downloads/trades_export%20%281%29.csv) was used as external evidence only.

## Evidence Sources

- Topstep export: [`/Users/zgrogan/Downloads/trades_export (1).csv`](/Users/zgrogan/Downloads/trades_export%20%281%29.csv)
- Local SQLite:
  - [`/Users/zgrogan/Repos/G-Trade/es-hotzone-trader/logs/observability.db`](/Users/zgrogan/Repos/G-Trade/es-hotzone-trader/logs/observability.db)
  - `completed_trades`
  - `decision_snapshots`
  - `events`
  - `runtime_logs`
  - `market_tape`
- Current regime/launch commands:
  - `es-trade analyze regime-packet`
  - `es-trade analyze launch-readiness`
  - `es-trade broker-truth --focus-timestamp 2026-03-19T04:35:01.534-07:00`

## Method

- March 16 is treated as one valid initial trade and the rest of that day is excluded from edge estimation because that day still contained duplicate trade-tracking artifacts.
- The clean baseline is therefore 13 effective trades from the Topstep export.
- Local high-resolution trader telemetry is only available from March 18 onward, so detailed decision and market-tape reconstruction is strongest for March 19 and weaker for March 16-17.

## Topstep Export Summary

Effective trade count after the March 16 collapse: `13`

### Entry-hour summary, Pacific time

| Entry hour | Trades | Wins | Losses | Total PnL | Avg PnL | Avg hold |
|---|---:|---:|---:|---:|---:|---:|
| `04:00-04:59` | 3 | 3 | 0 | `$4,225.00` | `$1,408.33` | `7.39h` |
| `15:00-15:59` | 1 | 1 | 0 | `$12.50` | `$12.50` | `0.00h` |
| `21:00-21:59` | 1 | 1 | 0 | `$150.00` | `$150.00` | `0.02h` |
| `23:00-23:59` | 8 | 2 | 4 | `-$1,850.00` | `-$231.25` | `0.10h` |

### Clean morning winners

| Date | Entry PT | Exit PT | Side | Contracts | Realized PnL | Hold |
|---|---|---|---|---:|---:|---:|
| 2026-03-16 | `04:31` | `13:10` | Long | 1 | `$1,225.00` | `8.66h` |
| 2026-03-17 | `04:36` | `11:10` | Long | 1 | `$1,800.00` | `6.57h` |
| 2026-03-19 | `04:35` | `11:31` | Short | 1 | `$1,200.00` | `6.95h` |

## What The Current Data Proves

### 1. The recent edge is time-structured, not one-direction bias

The strongest recent cluster is the `04:30-05:00 AM PT` window, and it includes both long and short winners. That argues against forcing directional bias for the Sunday/Monday launch. The evidence is more consistent with a session-structure edge than with a permanent bullish or bearish model.

### 2. The 11 PM PT cluster is a negative control

The late-evening cluster is net negative and extremely short-lived. That is the clearest recent evidence that not every hot-zone or overnight context is worth live execution right now.

### 3. March 19 proves the bot found the short

The local telemetry around the March 19 short is explicit:

- `2026-03-19T11:34:00+00:00` (`04:34 AM PT`): `Pre-Open`, `active_session=ETH`, strong short decision, `short_score=7.8619`, `score_gap=18.8349`, `outcome=entry_submitted`, `outcome_reason=pre-open_short_matrix`
- `2026-03-19T11:35:01.545051+00:00`: runtime log `broker_order_submit order_id=2664440735 side=sell quantity=1 ... limit_price=6654.25`
- `2026-03-19T11:36:00+00:00` onward: repeated runtime logs `Entry skipped because an active entry order is already working for ES`

So the March 19 miss was not a signal-generation failure. The bot found the setup and sent the order. The problem was execution-state truth and adoption, which has since been patched.

### 4. The recorded March 19 exit duration is contaminated

The later March 19 close does not prove the live exit logic intentionally held the trade all morning.

The local evidence shows:

- the short was submitted in the morning
- the runtime then got trapped behind stale working-order state
- after the adoption fix was deployed, the trader restarted and adopted the broker short at `2026-03-19T18:31:52.600000+00:00`
- the adopted short was immediately flattened with `reason=stress_regime`

That means the March 19 realized exit is not clean evidence of an intentional 6.95-hour hold. It is partially contaminated by the order-tracking bug plus later broker-position adoption.

## What Is Still Unproven

### 1. Whether the 6-10 hour holds are real alpha

The current runtime configuration historically advertised much shorter hot-zone hold logic than the realized March 16-19 hold times. Because March 19 is contaminated, and March 16-17 do not have the same high-resolution local telemetry, we still do not have proof that the recent winners required all-day drift.

### 2. Whether the morning pattern is stable beyond a few sessions

The sample is too small to claim a durable seasonal law. The evidence is good enough to say "morning is the only recent cluster worth prioritizing," but not good enough to say "this will keep working for months" without fresh forward sessions.

### 3. Whether later hot zones deserve live promotion

There is not enough clean recent evidence to justify live Post-Open, Midday, or Outside execution for Monday. Those windows should keep scoring and logging, but they need promotion by evidence, not by assumption.

## Research Context

The market-structure backdrop supports the idea that the overnight-to-open transition is a meaningful ES decision window:

- CME describes E-mini S&P 500 futures as a nearly 24-hour price-discovery market and explicitly frames trading against the cash open as a distinct use case.
  - [Trading the S&P 500](https://www.cmegroup.com/education/articles-and-reports/trading-the-sp-500.html)
  - [Introduction to Trade at Cash Open (TACO)](https://www.cmegroup.com/education/courses/trading-at-a-basis-to-an-index-btic-taco/introduction-to-trade-at-cash-open-taco.html)
- Academic microstructure work also supports concentrated information flow and volatility around open/close transitions rather than uniform edge throughout the day.
  - Chan, Chan, and Karolyi, *Intraday Volatility in the Stock Index and Stock Index Futures Markets* ([DOI](https://doi.org/10.1093/rfs/4.4.657))
  - Giudici and Grossmann, 2025, intraday futures seasonality research ([DOI](https://doi.org/10.1002/jcaf.70005))

These sources support the current direction: prioritize the morning regime, but do not assume the same expectancy extends cleanly through the rest of the session.

## Launch Recommendation

For the Sunday/Monday launch:

- Keep `Pre-Open` live.
- Keep both long and short enabled.
- Keep `Post-Open`, `Midday`, and `Outside` scoring and logging, but do not promote them to live execution without fresh evidence.
- Keep the new session-aware exit bounds active:
  - checkpoint `10:00 AM PT`
  - hard flat `11:30 AM PT`
- Keep size at `1` contract.

## Bottom Line

The current evidence supports a `morning-primary`, regime-gated launch. It does not support an all-day, all-zone claim of edge. The right posture for Monday is:

- trust the morning entry engine
- do not force directional bias
- bound exits by session policy
- keep later windows in shadow until they prove they deserve promotion
