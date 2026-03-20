# G-Trade Strategy Gate Research Review

This document is the research companion to [strategy.md](./strategy.md). The existing strategy doc explains what the system does. This file focuses on whether the current gate stack is aligned with the literature, where the evidence is strong or weak, and which gates should be kept, tightened, replaced, or revalidated.

Scope:

- Current implementation reviewed from [`config/default.yaml`](../config/default.yaml), [`src/engine/decision_matrix.py`](../src/engine/decision_matrix.py), [`src/engine/risk_manager.py`](../src/engine/risk_manager.py), and [`src/engine/trading_engine.py`](../src/engine/trading_engine.py)
- Research emphasis on intraday futures-relevant work: market microstructure, scheduled news, intraday seasonality, volatility clustering, regime switching, technical-rule robustness, and execution risk
- Literature window: foundational work from the 1980s through recent 2024-2025 papers that materially bear on gate design

Research status: reviewed and drafted on March 20, 2026.

---

## 1. Bottom line

The current G-Trade gate architecture is directionally correct. The broad design choice to separate scoring from vetoes is well supported by both market microstructure theory and modern systematic-trading practice. The strongest parts of the current stack are:

- time-of-day segmentation
- event blackouts
- spread and execution-quality gating
- regime blocking
- hard risk overlays and circuit breakers

The weakest parts are not the existence of the gates, but the way several thresholds are currently parameterized:

- `Outside` is too broad to behave like a researched market regime
- volatility gates are short-window and largely unconditional on time-of-day
- macro blackout windows are fixed-clock heuristics instead of announcement-specific policies
- the midday mean-reversion confirmation gate is conceptually sound but currently too coarse in code because it is not side-specific
- several static thresholds should likely become zone-conditioned quantiles rather than absolute constants

If the goal is "best possible system," the research does not support removing gates. It supports making the gate stack more conditional, more clock-aware, and more explicitly tied to measured market quality.

---

## 2. Current gate inventory

The current system has four distinct classes of gates. Keeping them separated is important.

| Gate class | Current examples | What research says |
|---|---|---|
| Alpha-alignment gates | regime blocklists, ORB middle rejection, midday mean-reversion confirmation | Valid when they align strategy type with market state |
| Microstructure gates | `execution_degraded`, `spread_too_wide`, quote-age checks | Strong support; these are among the highest-value gates in intraday systems |
| Volatility-state gates | `atr_percentile_too_high`, `atr_spike_active`, volatility circuit breaker | Strong support in principle, but threshold design matters a lot |
| Governance / rollout gates | launch gate, market-hours guard, daily loss, trade caps, flatten-only zones | Not alpha sources, but strongly justified as safety controls |

That separation should remain an invariant. The literature repeatedly shows that strategy failure often comes from forcing a valid signal through the wrong market state or the wrong execution state, not from signal absence alone.

---

## 3. Gate-by-gate research audit

### 3.1 Time-of-day segmentation and hot zones

Current implementation:

- `Pre-Open`, `Post-Open`, `Midday`, `Close-Scalp`
- optional fallback `Outside` zone when `trade_outside_hotzones` is true

Research support:

- Foundational intraday work consistently documents that volatility, trading intensity, and price behavior vary sharply by clock time rather than remaining stationary through the day.
- Wood, McInish, and Ord (1985) documented unusually high return variance at the beginning and end of the trading day.
- Harris (1986) found that a large share of intraday return differences accrues near the open.
- Andersen and Bollerslev (1997) showed that intraday periodicity is a first-order feature of high-frequency returns and must be modeled rather than treated as noise.

Assessment:

- Strongly supported.
- The hot-zone idea is one of the most defensible parts of the system.
- The weak point is the catch-all `Outside` state. Research supports explicit time buckets with distinct microstructure, not one residual bucket that can include pre-open drift, midday chop, post-lunch liquidity recovery, and late-session positioning.

Verdict:

- Keep hot-zone segmentation.
- Replace `Outside` with named researched windows if it remains live-tradable.

### 3.2 Launch gate and shadow/live zoning

Current implementation:

- `launch_gate_enabled`
- live entries only in configured zones
- shadow zones continue to score and log

Research support:

- This is not really a market-structure question. It is a deployment-control question.
- In systematic trading practice, staged rollout and shadow evaluation are standard controls to separate signal research from capital exposure.

Assessment:

- Strong operational control.
- It should remain separate from alpha logic.

Verdict:

- Keep as-is.
- Do not merge launch policy into the score matrix.

### 3.3 Scheduled-event blackout

Current implementation:

- fixed blackout schedule under `blackout_events`
- matrix veto `event_blackout`
- risk manager blackout state can also block trading or force flattening

Research support:

- News and scheduled macro releases have large and abrupt effects on returns, volatility, spreads, and order flow.
- Andersen, Bollerslev, Diebold, and Vega (2003) showed that high-frequency price jumps in FX are tightly linked to macro surprises.
- Kurov, Sancetta, Strasser, and Wolfe (2018) found pre-announcement drift before several U.S. macro releases, starting roughly 30 minutes before official release time in some cases.
- Hu, Pan, Wang, and Zhu (2022) showed significant pre-announcement returns in S&P 500 futures before NFP, GDP, ISM, and FOMC-related releases.
- Wachter and Zhu (2018) and the later "Macroeconomic Announcement Premium" literature reinforce that scheduled announcements are special return and risk states, not ordinary bars.

Assessment:

- Strongly supported.
- The issue is granularity. The current implementation uses a fixed set of clock times with symmetric `pre_minutes` and `post_minutes`. The literature suggests heterogeneity by announcement type, release protocol, leak risk, and post-release digestion.

Verdict:

- Keep the blackout concept.
- Upgrade from fixed-clock heuristic to announcement-tier policy:
  - tier 1: FOMC, CPI, NFP, GDP, major ISM
  - tier 2: secondary macro releases
  - tier 3: optional stand-down only if historical impact justifies it

### 3.4 Execution-quality, spread, and quote-freshness gating

Current implementation:

- `execution_tradeable`
- `require_execution_tradeable`
- `spread_too_wide`
- quote age folded into execution state

Research support:

- This is among the best-supported gate families in the literature.
- Demsetz (1968), Glosten and Milgrom (1985), and Kyle (1985) establish the basic logic: wider spreads and thinner/liquidity-stressed markets raise adverse selection costs.
- Cont, Kukanov, and Stoikov (2014) show that short-horizon price changes are tightly connected to order flow imbalance and depth.
- Ito, Yamada, Takayasu, and Takayasu (2020) show that even apparent arbitrage must be evaluated through execution-risk and fill-risk rather than signal alone.
- Recent staleness work shows that lack of timely price adjustment is itself an informative market-quality signal, not a harmless data nuisance.

Assessment:

- Very strong support.
- Static thresholds are acceptable as hard failsafes but not ideal as full-quality policy.
- For ES, `max_spread_ticks: 4` is reasonable as a dislocation veto, but it is too coarse to serve as the only liquidity-quality cutoff for entries.

Verdict:

- Keep and strengthen.
- Split into two layers:
  - hard fail: clearly untradeable or stale
  - soft degradation: trade allowed only if score edge is unusually strong

### 3.5 Price staleness and quote-age logic

Current implementation:

- quote-age is measured in feature extraction
- stale quotes reduce `execution_state`
- a quote can still be treated as tradeable up to the configured threshold

Research support:

- Bandi, Reno, and coauthors' recent staleness work argues that stale prices carry economic information about liquidity and should not be ignored.
- "Systematic staleness" (2024) and "Jumps or Staleness?" (2024) both show that stale prints can distort inference and can masquerade as jump or volatility structure if untreated.

Assessment:

- Supported and increasingly important.
- The current implementation is simple and useful, but the research suggests staleness should be monitored explicitly, not only buried inside a composite execution score.

Verdict:

- Promote quote staleness to first-class telemetry.
- Consider separate gating for stale quotes versus wide spreads because they imply different failure modes.

### 3.6 Volatility gates: ATR percentile, ATR acceleration, and circuit breaker

Current implementation:

- `atr_percentile_too_high`
- `atr_spike_active`
- risk-manager volatility circuit breaker using recent ATR history

Research support:

- Volatility clustering is one of the deepest and most stable stylized facts in finance.
- Engle (1982) and Bollerslev (1986) are foundational for conditional-volatility modeling.
- Andersen and Bollerslev (1997) show intraday volatility is both persistent and periodic.
- Recent volatility-forecasting work continues to improve on static models, but the common message remains: volatility regimes should be forecast conditionally and with time-of-day awareness.

Assessment:

- Strong support for the existence of volatility gates.
- Weaker support for the current parameterization.
- `atr_percentile` is currently measured against only the most recent 50 non-NaN ATR values. That is a short baseline for an intraday futures product with strong open/close seasonality.
- A midday volatility percentile computed against the open is not the same object as a midday volatility percentile computed against other midday observations.

Verdict:

- Keep the gate family.
- Replace global or short-horizon percentile logic with clock-bucketed realized-volatility baselines.
- Prefer zone-conditioned percentiles and jump-aware filters over a single unconditional `0.7` threshold.

### 3.7 Regime filters

Current implementation:

- deterministic 3-state classifier: `TREND`, `RANGE`, `STRESS`
- zone vetoes block specific regimes

Research support:

- Hamilton (1989) is the standard foundation for regime-switching logic.
- Subsequent trading literature broadly supports conditioning strategy families on regime rather than assuming one policy fits every state.
- Recent research still favors regime-aware systems, but it also shows that regime estimation error matters. Confidence and hysteresis are often as important as the label itself.

Assessment:

- Strongly supported in concept.
- The current simple classifier is reasonable for a transparent live system.
- The risk is not that regime gating exists, but that hard state assignment can flicker near boundaries.

Verdict:

- Keep regime gating.
- Add regime confidence and transition hysteresis before using the regime as a hard blocker.

### 3.8 Opening-range and ORB-middle rejection

Current implementation:

- `reject_orb_middle`
- `inside_orb_middle` veto in `Pre-Open`
- ORB breakout features contribute to the score

Research support:

- The open is a high-information, high-uncertainty period.
- Opening-auction and opening-price-discovery literature supports the idea that the open is structurally special and that ambiguous midrange conditions are lower quality than clean acceptance or rejection.
- Direct academic evidence for "ORB midpoint rejection" as a universal edge is weaker than the evidence for time-of-day segmentation itself.

Assessment:

- Moderate support.
- This is a plausible structure filter, not a universally validated alpha gate.

Verdict:

- Keep as a candidate gate.
- Revalidate empirically rather than treating it as a settled truth.

### 3.9 Midday mean-reversion confirmation

Current implementation:

- midday blocks `TREND` and `STRESS`
- veto on high EMA slope
- veto on strong breakout follow-through
- mean reversion requires band penetration, RSI extreme, and wick rejection

Research support:

- The broad idea is defensible: mean reversion performs best in range-bound, liquidity-stable, non-breakout conditions.
- The technical-rule literature is mixed on raw oscillator and band signals.
- Brock, Lakonishok, and LeBaron (1992) found evidence for simple technical rules in historical data, but later work repeatedly warns that many apparent technical edges are fragile once data-snooping, structural change, and costs are handled.
- Sullivan, Timmermann, and White (1999) is the canonical warning on data-snooping in technical-rule evaluation.
- More recent surveys still find that unconditional technical-rule profitability is inconsistent, while conditional and regime-aware use remains more plausible.

Assessment:

- Conceptually strong as a filter, not strong as a standalone alpha proof.
- The current stack is better than naive RSI/Bollinger mean reversion because it adds wick rejection and trend suppression.
- There is a code-level issue: `missing_mean_reversion_confirmation` clears if either `mean_reversion_ready_long` or `mean_reversion_ready_short` is true. That means a long entry can pass because a short confirmation exists, and vice versa. Research logic argues confirmation should be side-specific.

Verdict:

- Keep the filter family.
- Make confirmation side-specific before treating this gate as production-grade.

### 3.10 Zone lateness and time-stop logic

Current implementation:

- `zone_too_late`
- per-zone `max_hold_minutes`
- flatten-only close scalp zone

Research support:

- More practical than theoretical, but still sensible.
- Intraday edge decays with clock time, especially for strategies relying on a specific session microstructure.
- Time stops are widely used to control thesis decay and adverse late-session exit conditions.

Assessment:

- Sound operationally.
- Should be validated empirically by hold-time decay curves, not folklore.

Verdict:

- Keep.
- Validate by conditional expectancy versus holding time and zone time remaining.

### 3.11 Trade caps, daily loss caps, and circuit breakers

Current implementation:

- max daily loss
- max position loss
- max consecutive losses
- max trades per hour, zone, and day
- reduced-risk and circuit-breaker state machine

Research support:

- These are risk-governance tools more than alpha filters.
- The literature on regime shifts and clustered volatility strongly supports the existence of capital-preservation overlays after losses or volatility shocks.

Assessment:

- Strongly justified as governance.
- These should not be optimized for return maximization alone.

Verdict:

- Keep as hard risk overlays.
- Recalibrate from drawdown and serial-loss distributions, not from signal hit rate alone.

---

## 4. Research timeline: newest to oldest

This section is intentionally reverse-chronological so the most recent material is visible first while still anchoring the stack in foundational work.

| Year | Source | Why it matters for G-Trade |
|---|---|---|
| 2025 | Safari and Schmidhuber, "Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades" | Recent evidence that trend and reversion behavior is horizon-dependent, which supports different gate logic by clock time and holding horizon |
| 2024 | Bandi et al., "Systematic staleness" | Supports explicit stale-price and low-update gating as genuine liquidity signals |
| 2024 | Kolokolov and Reno, "Jumps or Staleness?" | Warns that apparent jump structure can be contaminated by staleness, relevant to ATR spike interpretation |
| 2024 | Lucke, Maas, and von Memerty, "The predictive ability of technical trading rules" | Recent skepticism on unconditional technical-rule value; supports conditional rather than universal use of technical indicators |
| 2022 | Ait-Sahalia, Fan, Xue, and Zhou, "How and When are High-Frequency Stock Returns Predictable?" | Reinforces that intraday predictability is state-dependent and tied to price, volume, and transaction events |
| 2022 | Hu, Pan, Wang, and Zhu, "Premium for heightened uncertainty" | Strong support for announcement-specific gating and pre-announcement drift awareness in index futures |
| 2020 | Ito et al., "Execution Risk and Arbitrage Opportunities in the Foreign Exchange Markets" | Reinforces that execution quality can dominate apparent signal quality |
| 2018 | Kurov et al., "Price Drift Before U.S. Macroeconomic News" | Supports standing down before certain releases and treating leak-risk windows as special states |
| 2018 | Wachter and Zhu, "The Macroeconomic Announcement Premium" | Reinforces that announcement days are structurally distinct return/risk environments |
| 2015 | Hinterleitner et al., "A Good Beginning Makes a Good Market" | Supports the idea that the market open is structurally special and merits specialized controls |
| 2014 | Cont, Kukanov, and Stoikov, "Price Impact of Order Book Events" | Strong support for OFI and market-depth-aware gating |
| 1999 | Sullivan, Timmermann, and White, "Data-Snooping, Technical Trading Rule Performance, and the Bootstrap" | Core warning against over-believing indicator-based gates without rigorous validation |
| 1997 | Andersen and Bollerslev, "Intraday periodicity and volatility persistence in financial markets" | Core support for time-of-day-aware volatility and session gating |
| 1992 | Brock, Lakonishok, and LeBaron, "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns" | Foundational but not decisive support for technical-rule conditioning |
| 1989 | Hamilton, "A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle" | Foundational regime-switching logic |
| 1986 | Bollerslev, "Generalized autoregressive conditional heteroskedasticity" | Foundational volatility-regime logic |
| 1986 | Harris, "A transaction data study of weekly and intradaily patterns in stock returns" | Foundational open-driven intraday seasonality evidence |
| 1985 | Kyle, "Continuous Auctions and Insider Trading" | Foundational market-depth and adverse-selection logic |
| 1985 | Glosten and Milgrom, "Bid, ask and transaction prices..." | Foundational spread and informed-trading logic |
| 1985 | Wood, McInish, and Ord, "An Investigation of Transactions Data for NYSE Stocks" | Foundational open/close volatility evidence |
| 1982 | Engle, "Autoregressive Conditional Heteroskedasticity..." | Foundational volatility clustering |

---

## 5. What the literature most strongly supports changing

### 5.1 Replace `Outside` with researched windows

Research does not support treating all non-hot-zone time as one state. If `Outside` remains live, it should be split into named windows with separate gate policies.

Candidate replacement:

- `Early-ETH`
- `Late-PreOpen`
- `Late-Morning`
- `Early-Afternoon`
- `Power-Hour`

### 5.2 Make event blackouts announcement-specific

The current fixed `08:30`, `10:00`, `14:00` model is an acceptable launch heuristic but not a best-in-class policy.

Better research-aligned approach:

- maintain a release calendar with event identity
- assign pre/post windows by event tier
- optionally add leak-sensitive pre-window treatment for historically drift-prone releases

### 5.3 Move volatility gates to clock-conditioned baselines

Instead of asking whether ATR is high relative to the last 50 bars in any environment, ask whether current volatility is high relative to similar bars:

- same zone
- same weekday
- same session type
- same announcement tier if applicable

### 5.4 Keep microstructure gates hard, but make them state-aware

A strong score should not overrule clearly degraded execution. Research is most aligned with:

- hard veto for stale or dislocated markets
- softer penalty for modest quality deterioration
- stronger OFI/depth validation when entering in fast conditions

### 5.5 Make midday MR confirmation side-specific

The current logic is too permissive at the side level. Research logic supports:

- long entry requires long confirmation
- short entry requires short confirmation
- neutral state if neither side confirms

### 5.6 Add hysteresis to regime transitions

Hard regime flips can create gate churn and unstable vetoes. A modest transition buffer is well aligned with the regime literature and with live-system robustness.

---

## 6. Recommended gate hierarchy for the next iteration

If the system is pushed toward a more research-defensible design, the gate order should be:

1. Market-hours and compliance guard
2. Announcement and event-risk guard
3. Execution-quality and staleness guard
4. Volatility-state guard
5. Regime-alignment guard
6. Strategy-shape guard
7. Score decisiveness and sizing
8. Launch / rollout policy

That order matters. Marketability and execution quality should veto before indicator interpretation.

---

## 7. Validation standard required before promoting any gate

The technical-rule and data-snooping literature is clear: indicator-like gates should not be trusted because they are intuitive.

Minimum standard:

- purged walk-forward validation
- explicit slippage and spread-cost modeling
- separate evaluation by zone
- evaluation by announcement and non-announcement subsets
- failure analysis on trend days, volatility shocks, and stale-quote periods
- ablation tests for each gate family
- side-specific confusion analysis for long and short filters

Questions every gate should answer:

- Did it improve expectancy or only reduce trade count?
- Did it improve tail risk after costs?
- Did it help only in one zone?
- Did it degrade performance on rare but important days?
- Is its edge stable after threshold perturbation?

---

## 8. Priority recommendations

Priority 1:

- replace live `Outside` with explicit windows
- make midday confirmation side-specific
- move announcement gating from fixed-clock to named-event logic

Priority 2:

- rebuild volatility gates on zone-conditioned realized-volatility and jump baselines
- separate stale-quote telemetry from spread telemetry
- add regime hysteresis / confidence

Priority 3:

- re-estimate spread and quote-age cutoffs by zone and event tier
- validate late-zone and hold-time rules with expectancy decay studies
- promote only those technical-shape gates that survive bootstrap and walk-forward stress

---

## 9. References

Recent and directly relevant:

1. Safari, Sara A., and Christof Schmidhuber. "Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades" (2025). [arXiv](https://arxiv.org/abs/2501.16772)
2. Bandi, Federico M., et al. "Systematic staleness" (2024). [Journal of Econometrics](https://www.sciencedirect.com/science/article/pii/S0304407623002385)
3. Kolokolov, Aleksey, and Roberto Reno. "Jumps or Staleness?" (2024). [Journal of Business and Economic Statistics](https://www.tandfonline.com/doi/abs/10.1080/07350015.2023.2203207)
4. Lucke, Bernd, Christian Maas, and Jens von Memerty. "The predictive ability of technical trading rules" (2024). [Springer](https://link.springer.com/article/10.1007/s11408-023-00433-2)
5. Ait-Sahalia, Yacine, Jianqing Fan, Lirong Xue, and Yifeng Zhou. "How and When are High-Frequency Stock Returns Predictable?" (2022). [NBER](https://www.nber.org/papers/w30366)
6. Hu, Grace Xing, Jun Pan, Jiang Wang, and Haoxiang Zhu. "Premium for heightened uncertainty: Explaining pre-announcement market returns" (2022). [Journal of Financial Economics](https://www.sciencedirect.com/science/article/pii/S0304405X21004037)
7. Ito, Takatoshi, Kenta Yamada, Misako Takayasu, and Hideki Takayasu. "Execution Risk and Arbitrage Opportunities in the Foreign Exchange Markets" (2020). [NBER](https://www.nber.org/papers/w26706)
8. Kurov, Alexander, Alessio Sancetta, Georg Strasser, and Marketa Halova Wolfe. "Price Drift Before U.S. Macroeconomic News: Private Information about Public Announcements?" (2018). [Cambridge Core](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/price-drift-before-us-macroeconomic-news-private-information-about-public-announcements/E1AE41FB94D4F2CA5134410D5C82A0E2)
9. Wachter, Jessica A., and Yicheng Zhu. "The Macroeconomic Announcement Premium" (2018). [NBER](https://www.nber.org/papers/w24432)
10. Hinterleitner, Gernot, Ulrike Leopold-Wildburger, Roland Mestel, and Stefan Palan. "A Good Beginning Makes a Good Market" (2015). [PubMed / PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4550773/)
11. Cont, Rama, Arseniy Kukanov, and Sasha Stoikov. "The Price Impact of Order Book Events" (2014). [Oxford Academic](https://academic.oup.com/jfec/article-abstract/12/1/47/816163)

Foundational:

12. Sullivan, Ryan, Allan Timmermann, and Halbert White. "Data-Snooping, Technical Trading Rule Performance, and the Bootstrap" (1999). [LSE PDF](https://www.fmg.ac.uk/sites/default/files/2020-11/dp303.pdf)
13. Andersen, Torben G., and Tim Bollerslev. "Intraday periodicity and volatility persistence in financial markets" (1997). [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0927539897000042)
14. Brock, William, Josef Lakonishok, and Blake LeBaron. "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns" (1992). [JSTOR issue link](https://www.jstor.org/stable/i340161)
15. Hamilton, James D. "A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle" (1989). [Econometric Society](https://www.econometricsociety.org/publications/econometrica/1989/03/01/new-approach-economic-analysis-nonstationary-time-series-and)
16. Bollerslev, Tim. "Generalized autoregressive conditional heteroskedasticity" (1986). [RePEc / Journal metadata](https://ideas.repec.org/a/eee/econom/v31y1986i3p307-327.html)
17. Harris, Lawrence. "A transaction data study of weekly and intradaily patterns in stock returns" (1986). [ScienceDirect](https://www.sciencedirect.com/science/article/pii/0304405X86900449)
18. Kyle, Albert S. "Continuous Auctions and Insider Trading" (1985). [Econometric Society](https://www.econometricsociety.org/publications/econometrica/browse/1985/11/01/continuous-auctions-and-insider-trading)
19. Glosten, Lawrence R., and Paul R. Milgrom. "Bid, ask and transaction prices in a specialist market with heterogeneously informed traders" (1985). [ScienceDirect](https://www.sciencedirect.com/science/article/pii/0304405X85900443)
20. Wood, Robert A., Thomas H. McInish, and J. Keith Ord. "An Investigation of Transactions Data for NYSE Stocks" (1985). [vLex](https://law-journals-books.vlex.com/vid/an-investigation-of-transactions-855596199)
21. Engle, Robert F. "Autoregressive Conditional Heteroskedasticity with Estimates of the Variance of United Kingdom Inflation" (1982). [NDL metadata](https://ndlsearch.ndl.go.jp/books/R100000136-I1573387450394060416)

---

## 10. Suggested next research tasks

1. Build a zone-by-zone validation table for every current veto and overlay.
2. Split `Outside` into explicit windows and backfill decision-snapshot comparisons.
3. Add announcement identity and tier into the event context so blackout rules can be event-specific.
4. Rewrite midday confirmation to be side-specific, then compare before/after in replay.
5. Replace raw ATR percentile with zone-conditioned realized-volatility percentiles and jump flags.

