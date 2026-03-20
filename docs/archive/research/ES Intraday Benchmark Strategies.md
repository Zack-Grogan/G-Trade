# ES Intraday Benchmark Strategies

*Reference: strategy/research only. Current operator interface is CLI-only; see [../README.md](../README.md) and [../OPERATOR.md](../OPERATOR.md).*

We propose a set of simple, interpretable intraday trading rules for the E-mini S&P 500 (ES) designed as baseline benchmarks.  All strategies are backtested with realistic execution: we assume primarily **limit orders** or VWAP-style execution to approximate actual fills, since uncontrolled market orders and high-frequency trading can have most profits eaten by slippage【28†L705-L713】【28†L747-L754】.  Likewise, transaction costs and slippage are explicitly modeled, as incorporating realistic cost assumptions is known to reveal the true performance of a strategy【4†L43-L47】.  Parameter ranges are used instead of single “optimal” values to avoid overfitting【24†L15-L19】.  Each strategy targets specific “hot” trading windows and market regimes (trending vs. mean-reverting).  Below are four rigorous baseline strategies.  

### Strategy 1: Open-Range Breakout (ORB) + ATR Trailing Stop  
- **Ideal Hot Zones:** Morning session breakouts (e.g. 9:30–10:00 after cash open, or 6:30–8:30 if that period has a defined open range).  
- **Market Regime:** Strong trending or momentum markets (high volatility).  This catches early-day momentum after a range break.  
- **Entry:** At the close of the initial range period (e.g. first 10–30 min), mark the high/low. Enter long on a *continuation* break above the high (or short on break below the low) by a small buffer (e.g. a tick or minimal threshold). Confirm price moves beyond the range with volume. Optionally require a 1–2× ATR breakout move to filter false breaks.  
- **Exit:** Use a trailing stop set at a multiple of the ATR (Average True Range) from the entry price, allowing profit-taking as the trend extends.  For example, exit when price falls by *k*·ATR (with *k* typically 2–4).  Alternatively, close on any VWAP cross back or end-of-zone.  
- **Position Management:** Scale out or move stops to breakeven after partial profits.  Keep position size modest to limit risk.  If the price reverses and crosses the breakout range in the opposite direction (invalidating breakout), exit immediately.  
- **Order Types:** Entry can use a stop-limit or market-if-touched order at the breakout price; exits use a limit or market-at-stop (ATR stop) order. We assume fills at the quoted price when limit orders are executed, in line with execution benchmarking.  
- **No-Trade Filters:** Skip trades if the initial range is too tight (low volatility) or extremely wide (high risk).  Avoid trading near major economic news or FOMC announcements that occur during the zone.  Do not trade if the breakout is within the opening range (to avoid whipsaw) or if volume is unusually light.  
- **Key Parameters:** Initial range length (e.g. 10–30 min); breakout buffer (a tick or ATR fraction); ATR lookback period (e.g. 14–20 bars); ATR multiplier *k* for trailing stop (e.g. 2–4).  **Parameter Ranges:** Treat range length and ATR multiplier as tunable ranges to test robustness; avoid a single “optimal” fixed value【24†L15-L19】.  Use day’s true range or 1-min ATR.  

### Strategy 2: VWAP Pullback Continuation  
- **Ideal Hot Zones:** Mid-morning or afternoon trending periods (e.g. 9:30–11:00, or after lunch from 12:00).  VWAP-based continuation often works when a clear intraday trend is in place.  
- **Market Regime:** Sustained trend (either bullish or bearish) with healthy volume; momentum continuation.  
- **Entry:** Define VWAP from the start of the trading session (typically from 9:30). When price has clearly crossed and closed above VWAP by a threshold (e.g. 0.5–1 ATR), wait for a pullback: price must retrace toward VWAP but hold above it (for a long), indicating VWAP support. Enter long near VWAP on the bounce (e.g. when price moves 0.2–0.5 ATR back toward VWAP).  (Symmetrically, for a downtrend, wait for price to stay below VWAP and bounce downward.)  This is a “VWAP bounce” continuation entry.  Confirm with rising volume or order-flow (optional) to ensure interest.  
- **Exit:** Set a profit target of several ATRs above entry or trail a stop at e.g. 1–2 ATR.  Also exit if price crosses back through VWAP against the trade.  Optionally scale out in thirds.  
- **Position Management:** Use a portion of the full size if the pullback is shallow; add-on if trend shows strength.  Tighten stop to break-even after a move of ~1 ATR in favor.  
- **Order Types:** Entry uses a limit order near VWAP to avoid market impact.  Stops and targets are limit/stop-limit orders.  Because this is a medium-frequency trade (perhaps a few per day), limit orders improve realism.  
- **No-Trade Filters:** Do not trade if VWAP is flat or choppy (no discernible trend).  Skip trades in extremely volatile markets when VWAP support is unreliable.  Avoid entering within a few ticks of session open or close.  Confirm that the move above/below VWAP is accompanied by volume >VWAP average.  
- **Key Parameters:** VWAP source (standard intraday VWAP). Distance above/below VWAP to confirm trend (e.g. 0.5–1 ATR). Pullback threshold (how close to VWAP to trigger, e.g. within 0.2–0.5 ATR). Stop/target ATR multiples.  **Ranges:** The pullback thresholds and ATR multipliers should be tested over a range (e.g. pullback from 0.2× to 0.5× ATR) rather than fixed.  

### Strategy 3: Lunch-Session VWAP Mean Reversion  
- **Ideal Hot Zones:** Midday lull (e.g. 12:00–1:00, especially 12:45–13:00 nested).  Usually before or after lunch when trading is relatively quiet.  
- **Market Regime:** Range-bound or quiet conditions (low volatility, lacking a strong trend).  Traders often see price reverting to VWAP during midday.  
- **Entry:** Measure the distance of price from VWAP (anchored to session start). If price is an extreme number of ATRs above VWAP (e.g. >2–3 ATR) during the lunch zone, enter a short (expecting reversion); if price is well below VWAP by that amount, enter a long.  The entry is ideally a limit order at or near VWAP+entry-threshold, so one buys/sells near the "overextended" edges.  Confirm with mean-reverting patterns (e.g. histogram CCI crossing back).  
- **Exit:** Close the trade as price returns to VWAP (or use a fixed moderate target, e.g. 1 ATR).  Set a stop at maybe 4–5 ATR from entry (far beyond VWAP) to control the rare trend-break scenario.  Since moves are small, aim for a quick reversion.  
- **Position Management:** Keep small size; these trades should capture small mean-reversion moves.  Exit fully on reversion or end-of-zone if not hit, to avoid overnight exposure.  
- **Order Types:** Enter with passive limit orders at the measured threshold level to avoid pushing the move (since the move is against the momentum). Use limit or market orders to exit at VWAP or target.  
- **No-Trade Filters:** Do not trade if the wider market has a big event (midday news) or if volatility suddenly jumps (break of VWAP by >4 ATR).  Avoid when VWAP is trending strongly (since mean-reversion assumptions break down).  
- **Key Parameters:** Reversion threshold (e.g. 2–3 ATR away from VWAP); VWAP anchor (session open). Maximum stop distance (e.g. 4–5 ATR). These should be tested over ranges (e.g. threshold 2×–4× ATR) to ensure not overfitting.  

### Strategy 4: Order-Flow–Assisted ORB Breakout  
- **Ideal Hot Zones:** Same early-morning or major auction periods (e.g. market open 9:30–10:30) where volume spikes.  Requires high liquidity for order-flow signals.  
- **Market Regime:** Strong directional moves confirmed by order-flow imbalance.  Good in liquid trending markets (e.g. after a big announcement).  
- **Entry:** First identify a standard ORB breakout (as in Strategy 1). Then apply an order-flow filter: e.g. confirm a positive Volume Delta (buy imbalances) near the breakout or a strong trade-volume surge. Only take the breakout long (or short) if the cumulative volume delta or footprint chart shows aggressive buying (selling). This reduces false breakouts.  
- **Exit:** Same ATR trailing stop or VWAP stop as Strategy 1, to let the move run. One might use a tighter stop since entry had extra confirmation.  
- **Position Management:** Use smaller size than standard ORB, since additional signal increases confidence. Optionally pyramid if additional order-flow pushes come in.  
- **Order Types:** Entry might still use a stop-limit at the breakout price. Order-flow data implies a passive or limit entry could await bigger fills. Exits remain ATR stops or profit limit orders.  
- **No-Trade Filters:** If order-flow is neutral or against the breakout (e.g. price up but delta negative), skip the trade.  Require that trade volume against spread crosses a threshold.  Skip trading on low-liquidity days (where footprint is unreliable).  
- **Key Parameters:** Same base ORB parameters plus order-flow thresholds (e.g. minimum net buy volume at breakout). Filter conditions should be broad; for example, require >0 (or a small percentage of daily volume) net volume imbalance, but test a range of imbalance sizes.  

## Implementation Order and Sanity Checks

We recommend implementing the strategies in increasing complexity.  First code the **Open-Range Breakout** (1) as it has fewest moving parts.  Next add the **VWAP Continuation** (2), then the **Lunch Mean Reversion** (3).  Finally, implement the **Order-Flow–Assisted** variant (4) as an extension of (1).  The simplest breakout strategy (ORB) also serves as a **sanity-check model**: if very basic breakouts with ATR stops do not produce any edge, more complex strategies likely won’t either.  Conversely, the order-flow–assisted strategy is most likely to perform well in-sample but fail live, since it adds extra signals and degrees of freedom (increasing risk of overfitting).  We will cross-validate all baselines across regimes (high/low volatility days, trending vs. choppy days) to ensure robust performance【24†L15-L19】.  

## Common Evaluation Template

Each baseline is evaluated by a standardized suite of metrics, calculated per strategy and per zone:  

- **Win Rate:** Percentage of trades that are winners.  
- **Expectancy:** Average profit per trade (often computed as win rate × average win minus loss rate × average loss).  
- **Sharpe-like Metric:** A risk-adjusted return measure, e.g. annualized return divided by volatility (or Sortino ratio).  This normalizes for volatility differences, reflecting whether edge is meaningful.  
- **Maximum Drawdown:** Largest peak-to-trough loss. Important in leveraged futures trading.  
- **Time-in-Trade:** Average duration each position is held. Useful to gauge intraday vs overnight exposure.  
- **Trade Frequency:** Number of trades per day or per year.  High frequency can amplify slippage costs【28†L705-L713】.  
- **Slippage Sensitivity:** Measure how much performance degrades under varying slippage assumptions.  (For example, re-run PnL with +1 tick per round-trip and see impact.)  This is critical since high-frequency edges can vanish with realistic costs【28†L705-L713】.  
- **Regime Sensitivity:** Compare performance on different days (e.g. high vs low volatility, trending vs range-bound).  A robust baseline should not rely only on a specific regime.  

Each metric should be reported for each hot zone, as well as overall.  For fair comparisons across strategies and zones, we normalize on a per-hour basis or use risk-adjusted returns.  For example, compare Sharpe ratios rather than raw returns, and annualize expectancy by per-trade risk.  Trades are sized by a fixed risk per trade (e.g. using ATR-based position sizing) to equalize volatility exposure【28†L705-L713】【28†L867-L871】.  

## Fair Cross-Zone Comparison

Different hot zones have different liquidity and volatility profiles.  To compare strategies fairly, we assess all metrics *within* each zone and then aggregate.  That is, compute per-hour return or per-trade expectancy and Sharpe in each zone separately, then compare strategies on those normalized terms.  We also adjust slippage assumptions by zone (e.g. morning has tighter spreads than overnight).  In practice, one can normalize each strategy’s performance by the volatility of the window or convert PnL to a standardized metric (like Sharpe per zone) so that a hot-zone that trades 1 hour can be compared to one trading 2 hours.  This ensures we compare apples to apples (e.g. using equal risk per trade and comparable slippage costs across zones)【28†L705-L713】【24†L15-L19】.

## Starter Trio Recommendation

For an initial implementation, we suggest coding **Strategy 1 (ORB+ATR)**, **Strategy 2 (VWAP Continuation)**, and **Strategy 3 (VWAP Mean Reversion)**.  These three cover distinct behaviors: trend-breakout, trend-continuation, and range-reversion.  They are relatively simple, interpretable, and rely on well-known concepts.  Starting with this “starter trio” provides a broad benchmark set; adding Strategy 4 (order-flow) can come later if data permits.  

**Sources:** We base our design on industry practice and academic insights.  For example, realistic cost/slippage modeling is known to be critical for backtest accuracy【4†L43-L47】, and high-frequency tactics must be treated with caution【28†L705-L713】.  Similarly, VWAP-based filters are common in institutional trading (traders often buy below VWAP expecting reversion【17†L369-L374】).  We avoid overfitting by keeping parameter ranges broad【24†L15-L19】. These benchmarks serve as robust, “no-frills” reference models for more advanced systems.  

