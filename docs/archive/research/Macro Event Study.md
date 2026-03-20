# Research Plan for ES Macro Event Study: Intraday Trading & Execution Quality

*Reference: strategy/research only. Current operator interface is CLI-only; see [../README.md](../README.md) and [../OPERATOR.md](../OPERATOR.md).*

## Core Research Questions  
- **How do major scheduled macro events affect intraday ES trading?**  Identify how volatility, liquidity, spreads, and execution costs change before, during, and after news releases (e.g. FOMC announcements, 8:30 ET US data, etc.).  
- **Do different event types induce distinct “regimes”?**  Test whether Fed announcements or high-impact economic releases create market conditions so abnormal that trading should be blocked or handled with special logic.  
- **What is the timing and duration of event impacts?**  Determine how long volatility and liquidity remain abnormal after each event (minutes, tens of minutes, etc.) and whether effects differ by time-of-day “hot zone” (pre-market, open, midday, etc.).  
- **What execution-quality risks arise?**  Measure how slippage, fill rates, and spread–depth conditions degrade around events, and whether traders systematically profit or lose in these periods.  
- **When should normal strategies resume?**  Establish objective criteria for resuming trading after an event (e.g. X minutes after release or certain metric thresholds).  

These questions focus on **market behavior and tradability**, not on macroeconomics per se.  They drive a practical research program to decide if, and how, events should be blocked or traded (with dedicated logic) versus waited out.  For example, do pre- and post-Fed windows exhibit so much volatility that they should be “no-trade” or require special treatment【20†L41-L45】【33†L67-L74】?

## Event Categories to Study  
Define event types precisely.  Categories include:  
- **Scheduled U.S. macro releases (8:30 ET, others).**  E.g. nonfarm payrolls, CPI, PPI, retail sales, GDP, unemployment, Fed Beige Book, ISM, etc.  These often occur at fixed times (mostly 8:30, some at 9:00 or 10:00 ET).  
- **FOMC meeting days (rate announcements and statements).**  Typically 2:00 ET statements (Fed rate decisions), often followed by 2:30 ET press conferences or mid-week meeting minutes at 2:00 ET Wed.  
- **Fed-related scheduled events.**  Including Fed Chair speeches (e.g. 10:00 ET press conferences or congressional testimony), Fed minutes, Fed surveys (e.g. Senior Loan Officer survey), or Fed-sponsored events.  
- **Non-U.S. high-impact events (as control or comparisons).**  Possibly include major ECB/BoJ meetings, but primarily U.S.-centric (ES futures focus).  
- **Control days (“no-event” days).**  Days without any scheduled high-impact releases or Fed events, to serve as baselines for intraday behavior.  
- **Overlapping or adjacent events.**  When multiple news releases fall in short succession (e.g. consecutive days or same morning), tag them separately and consider compound effects.  

Use official economic calendars (e.g. Bloomberg/Economic Time Series, Econoday) to time-stamp each event.  Mark events by release time and anticipated direction (positive/negative surprise), and exclude events outside market hours.

## Event-Study Methodology for ES  
Implement a high-frequency event-study design tailored to ES futures:  
- **Data Collection:** Acquire tick-by-tick ES trade and quote data, covering extended market hours (CME Globex 24h).  Include at least one full year (5+ years ideal) of data to get enough events and control days.  Timestamp precision should be sub-second if possible.  
- **Event Identification:** Create a master list of event timestamps (down to the second).  For each event, record the exact release time (ET) and a measure of surprise (reported value minus consensus) if available.  Flag events by category (Fed vs macro, etc.).  
- **Event Windows:** For each event, define symmetric pre-, event-shock, and post-event windows.  For example: 15–30 minutes before the release (pre-event baseline), the “immediate reaction” window (e.g. 0–1 or 0–5 minutes after), and a “post-event” period (e.g. 5–30 minutes after).  Ensure windows do not overlap with other events or market open/close. Control for time-of-day seasonality by comparing each event window to the same clock time on non-event days.  
- **Control Sample:** Select “clean” non-event periods at the same times of day as benchmarks.  For instance, for a 8:30 ET CPI release, use 8:30 ET windows on surrounding days without major news to form a baseline.  Also include random or matched windows on control days.  
- **Data Cleaning:** Remove outliers and erroneous ticks (fat-finger quotes, spikes).  Adjust for day-light savings or holiday schedules.  Ensure pre-event window is not contaminated by known leaks or early news.  
- **Normalization:** Normalize metrics by recent volatility or volume to compare across days.  For example, express realized volatility during the event window relative to the average volatility of that time-of-day.  This controls for intraday patterns【20†L38-L45】.  
- **Statistical Tests:** Compare metrics in event vs control windows.  Use paired t-tests or nonparametric tests to see if differences are significant.  Use regressions if quantifying effects (e.g. regress 1-min returns or volatility on a dummy for event window).  Check for cross-sectional differences by event type, and whether effects differ by hot-zone segment.  
- **Regime Characterization:** Identify whether event windows constitute a distinct market regime: e.g. do they show systematically higher volatility/spreads?  Compute effect sizes (e.g. volatility ratios, spread multiples) and test if they breach pre-set thresholds (e.g. >×2 normal levels).

This method leverages high-frequency analysis as in Ederington & Lee (1993, 1995) who show that “most of the price adjustment to a major announcement occurs within the first minute, [but] volatility remains substantially higher than normal for roughly fifteen minutes”【20†L41-L45】.  Here, we extend this to multiple events and link to execution metrics.

## Metrics to Compare  
Compute and compare a suite of intraday market-quality metrics for each period:  
- **Realized Volatility:** Sum of squared returns (e.g. 1-second or 1-minute returns) in each window.  Compare to baseline.  (Ederington & Lee find vol “remains higher than normal” for ~15 min after news【20†L41-L45】.)  
- **Range Expansion:** High–low price range during the event window (or spikes beyond normal range), as a multiple of normal range.  
- **Spread Proxies:** Use quoted bid-ask spread or *effective spread* (2× distance from mid-price to trade price).  Proxy: (ask–bid)/mid or use volume-weighted spreads.  Expect spreads to **widen** sharply on announcement news【29†L421-L424】.  
- **Depth/Liquidity Proxies:** Measure order book depth at best bid/ask (e.g. aggregated size of top 1–3 levels) or total executed volume in the window.  Also use *liquidity ratios* like volume traded per price move.  Anticipate market-makers pulling back (depth ↓) during shocks.  
- **Slippage/Impact:** For hypothetical marketable orders of fixed size (e.g. 1 contract or 5 contracts), compute the average price slippage (difference between intended price (mid) and execution).  Alternatively, measure *price impact*: how far price moves immediately after executing a trade at the touch.  
- **Fill Quality:** For limit orders placed at the inside or near-inside quotes, measure fill rates (percentage filled) and time-to-fill in each window.  Compare “fast” order submission success before vs after news.  
- **Breakout Follow-Through:** Define a “breakout” as a large directional move in the immediate minutes after the event.  Measure how often price continues in the same direction for X additional minutes versus reversing.  (This relates to the literature on overshoot: Ederington & Lee (1995) find initial overreaction corrected within a few minutes【33†L67-L74】.)  
- **Mean-Reversion Failure Rate:** After the typical reversal period (e.g. 2–5 minutes post-event), measure the rate at which prices fail to revert to the pre-event price (or fail to mean-revert fully).  A high failure rate may indicate enduring shocks.  

Group these metrics into categories (volatility, spread-depth, execution, pattern-follow-through).  For each metric, compute summary statistics (mean, median) in pre-, during-, and post-event windows, and test differences.  Plot distributions or cumulative densities for clarity.

## Time-Window Structure Around Events  
Design multiple nested windows tailored to capture different phases:  
- **Pre-Event (Baseline):** Typically 5–30 minutes before the release, capturing “calm” conditions.  Can split into sub-windows (e.g. –30 to –15 and –15 to 0).  Ensure the pre-window is quiet (no earlier news at 8:25) and matches the same daily time-of-day on control days.  
- **Immediate Shock (Reaction):** Very short window right after the announcement (e.g. 0–1 min or 0–3 min).  This captures the fastest adjustment.  Literature shows “numerous small, rapid price changes that begin within 10 seconds and complete within 40 seconds”【33†L67-L74】.  
- **Intermediate Adjustment:** The few minutes after shock (e.g. 1–5 min).  This is when any overreaction may correct.  We expect overshoot in first 40 seconds and a correction by minute 2–3【33†L67-L74】.  
- **Post-Event Stabilization:** Extended post-window (e.g. 5–30 min).  Track when volatility and spreads decay toward normal.  Ederington & Lee found volatility still high up to ~15 min after and “slightly elevated for several hours”【20†L41-L45】.  We can empirically see when metrics return to baseline.  
- **Extended Aftermath (Optional):** 30–60 minutes after or until zone end.  To see if late-arising effects persist (sometimes volatility decays slowly).  

For example, for an 8:30 ET release one might use: Pre = 8:00–8:30, Shock = 8:30–8:31, Mid = 8:31–8:35, Post = 8:35–9:00.  Windows should avoid overlapping with the next scheduled event or market open/close.  The exact durations can be adjusted after preliminary analysis (e.g. if shocks last longer).

Use the pre-event window both as a baseline and to detect any *leakage* (abnormal volatility before release).  The immediate shock window should be very tight to avoid noise.  Then monitor how quickly metrics normalize in successive windows.  This structured approach separates **information shock** (first minutes) from **liquidity recovery** (tens of minutes later)【20†L41-L45】【33†L67-L74】.

## Segmenting Results by Hot Zone  
Analyze results separately by intraday segment (“hot zone”), since baseline behavior differs by time of day:  
- **Window 1 (6:30–8:30 ET):** Pre-U.S. open / Globex open segment.  Liquidity often ramps up here.  Macro news in pre-market (rare, but e.g. Fed Beige Book at 14:00 prev. day has some effect).  Execution risk is already typically higher early.  
- **Window 2 (9:00–11:00 ET):** Morning U.S. cash session.  High baseline volume and volatility.  Contains the 8:30–9:00 segment where most data hits occur.  News here may compound with opening volatility.  
- **Window 3 (12:00–13:00 ET) and Nested 12:45–13:00:** Lunch hours.  Lower baseline liquidity.  If events (e.g. Europe data at 8:00 GMT = 4:00 ET, no, or Fed survey mid-day), examine midday shocks.  The nested 15-minute slot captures any micro-structure effect (maybe large orders or re-open flows).  
- **(If needed, also Morning after open (8:30 open) vs late afternoon differences.)**  

Compute each metric within each hot zone.  Compare whether, for instance, an 8:30 ET CPI has a different volatility multiplier when it occurs in the 9–11 zone (U.S. open) versus when a Fed press conference at 14:30 ET (after noon).  This reveals if the same event “regime” has varied impact by zone.  It may justify, for example, blocking events only in certain zones.

Hot-zone segmentation also helps define training modules: you might build separate models for the 9–11 window around macro news versus normal 9–11 trading.

## Determining Trading Regimes: Block vs Dedicated vs Resume  
We need objective criteria to classify each event type into:  
- **“No-Trade” Window:** If an event consistently produces extremely adverse conditions (e.g. spreads ×3–5 normal, depth collapses, slippage huge), then flag that event or immediately after as a black-out.  For instance, if average realized volatility spikes 5×, fills fail, and 90% of market orders suffer excessive slippage, we “block” trading during a specified post-event interval.  
- **Dedicated Event Module:** If an event has a repeatable effect pattern that a specialized strategy can exploit (e.g. predictable overshoot and reversion), then treat it as a separate regime.  Criteria: high statistical significance of return predictability or volatility patterns in that window, distinct from control periods.  Eg, if after Employment surprises, the first minute tends to overshoot then mean-revert with consistent probability, one could design a micro-module (like fade the initial move).  If **trading during the event can be profitable on average** (even after costs), consider a special module.  
- **Resume Normal Trading:** If event impact is mild or short-lived, or if metrics return to baseline quickly, then treat it as essentially normal market.  Rule-of-thumb: after X minutes (determined empirically, say 10–15 min), if volatility and spreads drop below a threshold (e.g. 1.2× normal) and execution metrics stabilize, switch back to standard algorithms.  

**Decision rule design:** For each event type, calculate key metrics (e.g. 1-minute realized volatility, median spread, slippage) in the shock window and compare to historical norms (e.g. control days’ same-time values).  If (Metric_event / Metric_normal) exceeds a threshold (like 2× for volatility or spread), mark “high-risk”.  Combine signals (e.g. if both volatility and spreads exceed thresholds, or if fill rate < 50%).  Use p-values from pre/post comparisons to test significance.

For example, one might define:  
- If **post-event 5-min realized vol > 3× baseline and median spread > 2× baseline**, then label “event regime”.  
- If additionally past strategy backtest shows negative net return on simple strategies (or losses) in that regime, then classify as “No Trade.”  
- Otherwise, if event windows show enhanced opportunities (e.g. momentum), classify as “Trade with special logic.”

All rules should be validated statistically: e.g. test if following the no-trade rule indeed improves average execution costs, and if ignoring it leads to systematic slippage loss.  

## Data Requirements  
- **Minimum:** 1+ year of tick-level ES data (trades and quotes). Data should include timestamps at least to the second, ideally milliseconds, with bid/ask and trade prices/volumes.  Time coverage should include all overnight sessions to capture any unusual pre/post announcements (e.g. Asian/European data).  Also need a reliable macro calendar (timestamped news data).  
- **Ideal:** 3–5 years of ES data for robustness (ensures many events and varied market regimes).  Sub-second timestamps and full order-book depth (top 5 levels or more) to measure liquidity.  Ancillary data: trade identifiers (aggressor flag), trader-type flags if available.  Data on executed fills from your system (to calculate realized slippage).  Auxiliary price series (e.g. RTH vs globex differences).  
- **Preprocessing:** Clean data for outliers, and ensure event times align with data timestamps.  Possibly exclude CME-defined “settlement” moments if they conflict.  

Larger datasets allow finer segmentation (e.g. distinguishing high-impact vs low-impact versions of CPI) and more powerful statistical tests. However, even a single year covering key Fed cycles can reveal large effects.

## Common Pitfalls and Mistakes  
- **Overlooking Intraday Seasonality:**  Not adjusting for time-of-day patterns.  Volatility and spreads have natural intraday U-shape; failing to compare to same time controls will misstate event impact.  Always use contemporaneous control windows【20†L38-L45】.  
- **Ignoring Overlapping News:**  On days with multiple news items, attributing effects to one event can be invalid.  (Ozdagli (2013) warns that co-occurring announcements can amplify reactions【8†L72-L79】.)  Remove or separately flag days with clustered events.  
- **Insufficient Sample:**  Only testing on a few events leads to noise.  Require dozens of occurrences per category (e.g. 20+ Fed days, 30+ NFP releases).  Also beware of *release timing drift* (events sometimes shift by a few minutes); align precisely.  
- **Data Survivorship Bias:**  Using only actively traded seconds (ignoring wider quiet periods) can bias volatility measures.  Include all ticks.  
- **Confusing Expected vs Unexpected:**  News often has a consensus; only the surprise component should drive returns.  If possible, condition on “surprise” (actual minus forecast).  Otherwise, quieter news might dilute effects.  
- **Microstructure Biases:**  Not correcting for the bid-ask bounce or asynchronous quotes can bias return measures.  Ederington & Lee (1995) specifically correct for bid-ask effects in high-frequency returns【33†L71-L74】.  Use mid-price for volatility if focusing on fundamental moves.  
- **Ignoring Liquidity Dimensions:**  Focusing only on price moves overlooks that even if returns normalize, execution costs may remain high.  Always check liquidity/spread metrics, not just volatility.  
- **Lack of Control Group:**  Omitting control days leads to misinterpreting normal midday spikes as news effects.  

Understanding these pitfalls ensures the event-study is “clean.”  In particular, treat each hot zone and event category independently and validate that results aren’t driven by a few extreme days.

## Decision Framework  
Based on the analyses, formulate a decision rule tree for strategy design:  
1. **Does the upcoming period include a high-impact event?** (Check the calendar.)  
2. **If yes, identify event type (Fed vs Other macro).**  
   - For each type, apply pre-computed metrics thresholds (e.g. volatility multiplier, spread spike, liquidity drop).  
3. **If metrics breach thresholds (based on historical distribution), label the window “Event Regime”.**  
   - If “Event Regime” *and* historical expected PnL < 0 (after trading costs), then **Block Trading** in that window.  
   - If “Event Regime” *and* historical PnL > 0 (with strategy), allocate to a **Special Event Module** (e.g. fading or following momentum as appropriate).  
   - Else (metrics ≈ normal), **Use Normal Strategy**.  
4. **Define resumption rule:**  After the event starts, monitor real-time metrics (vol, spread).  Once they fall below a safe threshold (e.g. 1.2× baseline) *for a sustained minute*, switch from “Blocked/Module” to “Normal Trading” mode.  For example, if vol/spread calm after 10 minutes, or if price reverts and stabilizes, resume.  

This framework uses statistical evidence from the event study to set quantitative cutoffs.  Backtest the framework itself: simulate historical trading decisions with it and check if it improves returns or reduces drawdowns.  Refine thresholds until it performs well across multiple event types.

## What evidence would convince me to fully block event windows?  
Block an event window only if there is **overwhelming, consistent evidence** of untradability during that period.  Convincing evidence includes:  
- **Extreme Adverse Costs:**  If for an event type, the average realized slippage or effective spread jumps multiple times (e.g. 3×–5×) over normal, and this result is statistically significant.  For instance, if 90% of orders at market during event incur large losses.  
- **Liquidity Collapse:**  If market depth (e.g. aggregated volume at best bid/ask) falls to near-zero, causing market orders to ‘walk the book’.  E.g. average depth < 20% of normal.  
- **Persistent Volatility:**  If even after 15–30 min, realized volatility remains elevated and shows no sign of mean reversion.  (Contrary to expectation, instead of decaying, it stays at crisis levels).  
- **Negative Expected PnL:**  Historical backtests of simple strategies (e.g. time-weighted execution, or momentum) yield net losses (after costs) during those windows.  If no strategy can reliably capture alpha in that window, better to pause.  
- **Practical Experience:**  If traders or algorithms continually hit bad fills or trigger hunting (often reported qualitatively) during specific announcements.  This anecdotal evidence should match quantitative metrics.  

In short, one would need to see that **all** normal market-making or trend strategies fail and execution costs are consistently unacceptable.  For example, if on 10 prior FOMC statements, average trade profits were negative (after costs), while on non-FOMC days similar trades were positive, that argues for blocking FOMC windows.  The decision should be evidence-based: only if spreads and slippage spike and **never** recover in a short time.  

Ultimately, the trigger to fully block is when the risks **vastly outweigh** any potential edge.  If, for a given event, the standard deviation of returns *spikes* and the trading edge *vanishes or reverses*, we accept that as proof to stop trading until conditions normalize.  This “block” policy should be revisited periodically as market structure evolves (e.g. algorithmic market-making might improve over time), but initially err on the side of caution due to “execution quality deteriorates during fast event windows”【20†L41-L45】【29†L421-L424】.

**Sources:** The methodology and expected patterns draw on high-frequency event-study literature (e.g. Ederington & Lee 1993, 1995【20†L41-L45】【33†L67-L74】) and recent microstructure analyses of stress events【29†L421-L424】.  Trading-volume surges after announcements are documented (locals profit immediately【3†L59-L64】) and liquidity normally worsens sharply.  Our plan adapts these insights into practical research steps and decision rules.