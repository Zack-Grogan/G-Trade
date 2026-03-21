# Morning-First Architecture

This is the active research-to-runtime guide for the current trader. It distills the archived March 2026 research into the minimal architecture and policy needed to reproduce the only recent edge that was both **profitable** and **clean enough to trust**.

## Source of truth

Primary evidence:

- [`docs/archive/research/Morning-Regime-Packet-2026-03-19.md`](../archive/research/Morning-Regime-Packet-2026-03-19.md)
- [`docs/archive/research/Trader Research Roundup 2026-03-19.md`](../archive/research/Trader%20Research%20Roundup%202026-03-19.md)

Supporting context only:

- [`docs/archive/research/Order-Flow and Auction-Structure.md`](../archive/research/Order-Flow%20and%20Auction-Structure.md)
- [`docs/archive/research/Regime Labeling Framework.md`](../archive/research/Regime%20Labeling%20Framework.md)
- [`docs/archive/research/Rigorous Validation Philosophy.md`](../archive/research/Rigorous%20Validation%20Philosophy.md)

## What the March research actually proved

### 1. The edge was morning-specific

The only recent cluster worth prioritizing was the `04:30-05:00 AM PT` entry window, which maps to the repo's **`Pre-Open`** zone.

- March winners:
  - `2026-03-16 04:31 PT` long
  - `2026-03-17 04:36 PT` long
  - `2026-03-19 04:35 PT` short
- The `23:00 PT` cluster was the clearest recent negative control.

### 2. The edge was not one-directional

The winning cluster contained both longs and shorts. The launch posture should remain **direction-agnostic** inside the morning regime.

### 3. The bot did find the March 19 short

The system found the `pre-open_short_matrix` setup and submitted the order. The failure was in **execution-state truth / order adoption**, not alpha generation.

### 4. The long realized holds are not clean evidence of intentional all-morning hold logic

The March 19 exit was contaminated by stale working-order state and later position adoption. The research supports a **morning-primary bounded session policy**, not a claim that the strategy proved 6-10 hour discretionary hold alpha.

The active profile is therefore **not trying to reproduce the export’s 6-8 hour realized holds**. It is trying to preserve the **morning entry window and live/shadow posture** while enforcing bounded session exits that were explicitly recommended for launch.

One intentional policy expansion beyond the raw packet wording is that the runtime session bounds cap **the open positions the runtime is responsible for**, not only positions perfectly tagged as Pre-Open-origin. That choice is deliberate: it keeps the morning posture bounded after restarts, broker adoption, or imperfect zone attribution.
In practice, when `live_entry_zones` is populated, the engine applies these bounds to **live-zone positions** plus **adopted / unknown-position-origin** cases. In engine terms, “unknown” includes positions whose `entry_zone` metadata is missing/empty. When the live list is intentionally empty as a full stand-down posture, session exits can still cap open runtime positions while launch gating blocks new entries.

## What must stay live

These are the parts of the newer architecture that should be preserved:

- broker-truth and position-adoption fixes
- executor fail-closed behavior
- stale pending-ID cleanup
- observability durability and replay/tape infrastructure
- the March 18 fix: **Pre-Open should not hard-veto `STRESS` at the matrix layer when risk is still `NORMAL`**

## What should remain the active operating posture

- **Pre-Open is the primary live zone**
- **Post-Open, Midday, and Outside may score/log, but should stay shadow by default**
- **Close-Scalp remains a scheduler-level `flatten_only` window**
  - it is not a separate live edge claim; it exists to tighten exit-only behavior late in the session map.
- **Both long and short remain enabled**
- **Session policy is morning-bounded**
  - runtime checkpoint flatten starts at `10:00 AM PT` and may retry while a position remains open
  - runtime hard flat: `11:30 AM PT`
  - these bounds apply to **live-zone positions by default**, and also to **adopted / unknown-origin** positions as a safety fallback
- **1 contract remains the default live posture until the edge is re-proved forward**
- **Stress stays conservative rather than permissive**
  - `STRESS` score multipliers remain damped (`0.3`) so the March 18 matrix-veto fix does not silently become a broader live-risk expansion.
- **Outside remains score/log only, not a new live experiment**
  - `Outside` keeps a fuller legacy-style shadow scoring profile for telemetry continuity and stays non-live by default.
  - those `Outside` weight choices are a **shadow-only research tuning**, not something the March packet independently proved.

## Default migration note

The **operator YAML profile** in [`config/default.yaml`](../../config/default.yaml) is intentionally morning-first.

Bare `Config()` is now treated as a **library/test-oriented shape**, not as the authoritative operator launch profile. It still shares the current alpha/risk dataclass defaults, but it does **not** automatically imply the shipped operator posture for launch-gate lists, session-exit enablement, or 1-contract operator caps. External or older integrations that do not call `load_config()` should set launch-gate, session-exit, and sizing fields explicitly.

## What is optional or lower-value for the Monday profile

These research threads are useful, but should not drive Monday implementation unless new evidence says they matter:

- detailed order-flow theory as the main explanation for Pre-Open wins
- broad regime-taxonomy expansion
- generic all-session hot-zone research
- any change justified only by “more configuration” rather than recent empirical edge

## Implementation rules for future changes

1. Treat **Pre-Open `zone_weights`** as the frozen feature mix unless fresh evidence justifies a change.
2. Prefer **fewer policy layers** over more clever scoring knobs.
3. If a rule suppresses valid Pre-Open trades, require evidence that it improves outcomes before keeping it.
4. Do not widen live trading beyond the morning profile without fresh evidence.
5. Validate morning changes with **live/tape evidence**, not deprecated bar-only replay.

## Current repo translation

The current active repo target is:

- **morning-first**
- **empirically anchored**
- **modern execution-safe**

That means:

- keep the fixed execution / broker / observability stack
- keep the core risk protections
- remove or neutralize policy layers that mostly reduce morning trade frequency without strong evidence
- avoid speculative “all hot zones should work” architecture
