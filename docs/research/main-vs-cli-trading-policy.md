# `main` vs `cli` — engine & execution policy drift

This document is the **deep-dive** companion to branch comparison: what changed in **code paths** and **config**, how that **moves outcomes** (entries, holds, exits), and how to **approximate `main`’s trading policy** while staying on `cli`’s more configurable codebase.

**Audience:** operators and AI agents tuning Pre-Open / “morning” edge.  
**Frozen research artifact:** Pre-Open **`alpha.zone_weights`** (long/short/flat) — same numeric weights on `main` and current `cli` in `config/default.yaml`. The **blend of features** (ORB, opening drive, ETH VWAP, trend, OFI, execution) was not redesigned; **policy around those scores** did change.

---

## 1. Decision matrix: what `main` actually did

### Score construction (`evaluate`)

| Step | `main` | `cli` |
|------|--------|-------|
| Weighted sum from `zone_weights` | Yes | Yes (same YAML for Pre-Open) |
| `side_adjustment` | No | Optional additive offset |
| `regime_multipliers` on long/short | No | Multiplies scores by regime |

**Outcome:** On `cli`, a given bar can produce **different** long/short numbers than `main` for the **same** raw features whenever regime ≠ neutral multipliers (1.0) or side offset ≠ 0. That changes **who wins** long vs short and **magnitude** vs thresholds.

### Entry (flat, `allow_entries`)

| Gate | `main` | `cli` |
|------|--------|-------|
| Dominant vs minimum | `dominant_score >= min_entry_score` | `dominant_score >= max(min_entry_score, zone_min_entry_score[zone])` |
| Gap | `score_gap >= min_score_gap` | Same |
| Flat bias | `dominant_score >= flat_bias + flat_bias_buffer` | Same |

**Outcome:** Stricter effective floor when `zone_min_entry_score` > `min_entry_score` (e.g. Pre-Open 5.5 vs global 5.0). Setting every zone’s override **equal to** `min_entry_score` restores **`main`-like** single-threshold behavior.

### While in position — exits

| Rule | `main` | `cli` |
|------|--------|-------|
| STRESS regime | Flat | Flat (same) |
| Opposite side dominates by `reverse_score_gap` | Flat | Flat (same) |
| Matrix decay | `long_score` / `short_score` vs **global** `exit_decay_score` | vs **per-zone** `zone_exit_decay_score` (fallback `exit_decay_score`) |
| Time stop | `held_minutes >= zone_hold_limit` **always evaluated** | `held_minutes >= limit` only if **`limit > 0`** |

**Critical outcome — matrix decay**

- `main`: one threshold (**1.5** in default yaml) for decay exits everywhere.
- `cli` default yaml: Pre-Open **-999** → decay condition “score &lt; -999” effectively **never** triggers `matrix_decay`; exits lean on **stops / trailing / other** rules instead.
- `cli` Post-Open/Midday **0.0**: for a long, exit when `long_score < 0` (not when &lt; 1.5). That is **much** easier to hit than `main`’s 1.5 bar — **very different** exit frequency vs `main` for those zones.

**Critical outcome — time stop**

- `main` with **positive** `max_hold_minutes` (e.g. Pre-Open **40**): hard time exit after 40 minutes.
- `main` code path `held_minutes >= limit` with **limit 0** would force time-stop whenever `held_minutes >= 0` (almost always) — i.e. **broken** for zero; production `main` presumably used **nonzero** holds from yaml.
- `cli` with **0**: **disables** matrix time-stop (intentional). That **extends** holds vs old **40m** Pre-Open cap — big P&amp;L and trade-shape change.

### Vetoes (`_evaluate_vetoes`)

| Veto | `main` | `cli` |
|------|--------|-------|
| Spread too wide | Always if rule set | Skipped when `quote_is_synthetic` (replay) |

**Live outcome:** **Same** as `main` when `quote_is_synthetic` is false (real BBO). Differences appear in **deprecated** bar replay, not in live morning session.

### Regime classifier (`regime.py`)

| | `main` | `cli` |
|---|--------|-------|
| Spread / vol / quote-rate → STRESS | Always evaluated | Skipped when `quote_is_synthetic` |

**Live outcome:** Same as `main` when not synthetic.

---

## 2. Config cleanup note

- **`min_dominant_feature_score`** was removed from the active config surface because it never affected the runtime engine. Older configs may still load it as a deprecated ignored key via [`src/config/loader.py`](../../src/config/loader.py).

---

## 3. Risk manager & execution (high level)

- **`risk`**: `cli` tightens **max_trades_per_zone** and **max_daily_trades** vs `main` defaults → fewer entries even when the matrix signals. **`max_trades_per_hour`**, **circuit breakers**, and **evaluation drawdown mirror** (if enabled) can also block entries or force flatten — align these when chasing **`main`-like** trade counts.
- **`strategy.launch_gate`**, **`live_entry_zones` / `shadow_entry_zones`**: Even with identical matrix math, trades only submit when the session/account gate allows live entries for that zone.
- **`market_hours_guard`**: When enabled, **new entries** are blocked outside configured windows (evaluation may still run). `main` default yaml had **no** guard block; disabling or matching policy avoids extra drift.
- **`executor`**: `cli` adds mock/replay realism (e.g. probabilistic limit touch fills, hashing). **Live** order submission semantics remain limit/market + protection; replay P&amp;L is **not** comparable to `main` without matching `replay_execution` settings.

---

## 4. How to get **as close as possible** to old (`main`) setup on `cli`

Keep **`zone_weights`** (especially Pre-Open) as your **researched** baseline. Then align **policy knobs** with `main`:

### A. Neutralize new score shaping (match `main` math)

Restore **`main`’s** global thresholds (not only weights): `min_score_gap`, `reverse_score_gap`, and `full_size_score` must match **`main`** defaults or you will still get different entry frequency, reversal exits, and half vs full size.

```yaml
alpha:
  min_entry_score: 5.0
  min_score_gap: 2.0
  reverse_score_gap: 2.5
  full_size_score: 6.5
  exit_decay_score: 1.5
  side_adjustment:
    long: 0.0
    short: 0.0
  regime_multipliers:
    TREND: { long: 1.0, short: 1.0 }
    RANGE: { long: 1.0, short: 1.0 }
    STRESS: { long: 1.0, short: 1.0 }
  zone_min_entry_score:
    Pre-Open: 5.0
    Post-Open: 5.0
    Midday: 5.0
    Outside: 5.0
  zone_exit_decay_score:
    Pre-Open: 1.5
    Post-Open: 1.5
    Midday: 1.5
    Outside: 1.5
    Close-Scalp: 1.5   # if present; else fallback to exit_decay_score
```

### B. Restore `main` hold and MR behavior

```yaml
strategy:
  mr_time_stop_minutes: 20
  trade_outside_hotzones: true   # if you want main’s broader geography

alpha:
  max_hold_minutes:
    Pre-Open: 40
    Post-Open: 55
    Midday: 20
    Close-Scalp: 5
    Outside: 30
```

### C. Restore `main` risk caps

```yaml
risk:
  max_trades_per_zone: 3
  max_daily_trades: 10
```

### D. Shadow / live zones

`main` default had **Pre-Open** live and **Post-Open, Midday, Outside** in shadow — adjust `live_entry_zones` / `shadow_entry_zones` to match how you actually traded when “winning at 4am” (usually **Pre-Open** live only).

### E. Optional: `market_hours_guard`

`main` default yaml had **no** `market_hours_guard_*` block. If you want **closer** behavior to old defaults, set `market_hours_guard_enabled: false` **or** document why the guard is on (it **blocks new entries** in closed windows).

---

## 5. What you **cannot** match without `main` checkout

- **Exact** line-for-line legacy code paths (already replaced). **Policy parity** is via **config** + understanding above.
- **Replay / bar API** paths: deprecated `replay-topstep` is not authoritative; use **tape** for validation.

---

## 6. Summary table — outcome direction

| Change vs `main` | Typical effect |
|------------------|----------------|
| Higher `min_score_gap` / `reverse` / `full_size` | Fewer entries; harder reversal exit; full size rarer |
| `zone_min_entry_score` > global | Fewer entries in that zone |
| `regime_multipliers` ≠ 1 | Scores rescaled; TREND long bias etc. |
| Pre-Open `zone_exit_decay` = -999 | Matrix decay exit **off** → longer holds unless other exits fire |
| Other zones `zone_exit_decay` = 0 | Decay at score &lt; 0 → **more** flats vs `main`’s 1.5 |
| `max_hold_minutes` = 0 | Matrix time-stop **off** vs old 40m Pre-Open cap |
| Lower daily/zone trade caps | Fewer trades |

---

## CLI+ branch (repo default `config/default.yaml`)

As of branch **`CLI+`**, the committed default config implements this blend:

- **Main-equivalent:** `min_score_gap` 2.0, `reverse_score_gap` 2.5, `full_size_score` 6.5, `zone_min_entry_score` all **5.0**, `zone_exit_decay_score` all **1.5**, `max_hold_minutes` restored (Pre-Open **40**, etc.), `mr_time_stop_minutes` **20**, risk **3 / zone** and **10 / day**.
- **Cli retained:** Pre-Open-only **live** entries, **market hours guard**, evaluation mirror fields (off), infrastructure and tape replay unchanged.
- **Research visibility retained:** **`trade_outside_hotzones: true`** with **`Outside` shadow-only**, so later sessions still score/log without widening live execution.
- **Conservative improvement retained:** `STRESS` `regime_multipliers` stay **0.3**, preserving the March 18 “do not hard-veto Pre-Open STRESS” fix without turning stress into a neutral live-entry regime.
- **Session-bound runtime policy:** checkpoint flatten at `10:00 PT` and hard-flat at `11:30 PT` now cap open runtime positions under the morning-first profile, including restart/adoption cases where zone attribution may be imperfect.

This section refers to the shipped **operator YAML profile** in [`config/default.yaml`](../../config/default.yaml). Bare `Config()` defaults are intentionally more neutral for library/test callers.

---

## Related

- [../Current-State.md](../Current-State.md) — replay fidelity  
- [../replay/replay-topstep-deprecated.md](../replay/replay-topstep-deprecated.md) — bar replay deprecation  
- [`config/default.yaml`](../../config/default.yaml) — live policy knobs  
