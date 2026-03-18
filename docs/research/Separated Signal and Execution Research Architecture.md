# Separated Signal and Execution Research Architecture for ES Intraday Trading

*Reference: strategy/research only. Current operator interface is CLI-only; see [../README.md](../README.md) and [../OPERATOR.md](../OPERATOR.md).*

## Market and Execution Data Requirements  
We require both **bar data** (e.g. 1-minute OHLCV) and **tick/BBO-level data** (timestamped trades, best bid/ask quotes, and ideally full depth).  
- **Bar-only mode:**  Aggregated bars (open/high/low/close/volume) with timestamps and session tags.  Use for macro features and entry signals when tick data isn’t needed.  
- **Tick/BBO mode:**  Millisecond-resolution trades and quote updates (Level I or II).  This allows modeling queue position, order-book liquidity, and the exact execution sequence.  One can compute order-flow features and queue imbalance directly from quotes【25†L877-L885】.  
- **Order-book depth:** Top-of-book queue sizes and, if possible, deeper levels.  These feed models of fill probability: e.g. a heavy far-side queue (negative imbalance) predicts higher chance of a near-side limit order filling【25†L877-L885】.  
- **Execution logs or fills:** Historical trade reports from our own orders (simulated or live) to calibrate slippage and fill-time models.  Without actual fills, we rely on tick data to infer what would have happened.  Transaction costs (fees/spread) must also be included.  

In summary, the bar-only version uses aggregated 1m data, while the tick-aware version requires raw trade/quote feeds and depth.  Both use the same ES symbols and market session info, but the tick version adds microstructure detail needed for realistic execution modeling.

## Layered Architecture  
We design a pipeline with clear functional layers: **Market-State → Signal → Selection → Order Placement → Fill Modeling → Exit → Risk Governor**.  Each stage produces either predictions (ML targets) or decisions:

- **Market-State Layer:** Analyzes context (time-of-day, volatility regime, macro news).  Predicts labels like “high-volatility open” or “midday calm.”  These regime features condition the next layers (e.g. adjusting sensitivity of signals or aggressiveness of execution).  
- **Directional Signal Layer:** Generates trading ideas (long/short) based on price patterns or ML forecasts (e.g. “go long next up-tick”).  It predicts short-horizon price moves or directional probabilities (e.g. probability the ES will move up by X ticks in N seconds).  It does *not* assume any fill or price — it’s purely about direction.  
- **Trade Selection Layer:** Filters and sizes signals.  From the signals produced, it selects which trades to take, and how large, based on risk/portfolio rules.  For example, if three long signals arrive simultaneously, this layer might execute only the strongest or scale each.  It can be rule-based (e.g. “max one breakout per window”) or learned.  
- **Order Placement Layer:** Converts selected trades into concrete orders.  It decides **order type** (market vs limit vs stop-limit, etc.), price offsets, and scheduling.  For instance, given a bullish signal, it might choose between immediately sending a market order or posting a passive limit at +1 tick.  The output is a set of orders to send to the broker/exchange.  
- **Fill-Modeling Layer:** *During simulation*, this layer predicts the outcome of each planned order.  It estimates **fill probability**, expected execution time, and slippage for that order.  For example, it might output “75% chance this bid limit order fills within 30s at price X+0.5” or an expected fill price distribution.  This is often an ML or statistical model trained on historical microstructure data【50†L27-L34】【23†L802-L807】.  In a live system, a simple version might run too (for example, deciding to cancel a stale order), but it is primarily used in backtesting to simulate realistic fills instead of assuming success.  
- **Exit Logic Layer:** Manages trade exits.  It applies profit targets or stop-loss rules.  This could be as simple as “exit after +2 ticks or –2 ticks” or more complex (dynamic stops based on market-state).  Like entries, exit triggers can be market or limit orders, and this layer decides those.  
- **Risk/Kill-Switch Layer:** Watches overall risk.  It implements hard rules (kill-switches) such as “if total loss > \$X, stop all trading” or “if drawdown exceeds Y, flatten positions.”  This layer is typically rule-based for reliability.  

Each layer’s output feeds the next: e.g. the signal layer only tells *what* to trade, and the placement layer then figures out *how* to trade it, with the fill model ensuring we capture execution realities.  This separation ensures changes in one layer (say, tuning the predictor) don’t corrupt others (execution logic stays honest).

## Definitions of Layers and Outputs  
- **Market State:** Predicts or classifies the current regime (volatility level, intraday hot zone, trend vs. range).  Might use cluster/classifier ML or simple volatility thresholds.  Its output is an index or set of state variables that downstream modules use to modulate behavior.  
- **Directional Signal:** Predicts price movement.  For example, it might output a probability \(P(\text{up move in next minute})\), or a predicted return.  This could be rule-based (technical indicators) or ML-based.  It does *not* assume instant fills — it’s purely about expected price direction from data.  
- **Trade Selection:** Decides which signals to act on and position size.  For instance, it might implement: “only take trades with signal strength > threshold, and scale size by confidence.”  It may also ensure diversity (not too many correlated trades) and obey position limits.  Output: a list of trades (symbol, side, size) to place.  
- **Order Placement:** Decides order type and parameters for each trade.  Outputs specific orders (e.g. “buy 2 ES contracts with a limit order at B+1 tick, valid for 5s” or “sell 1 contract at market”).  It may use simple heuristics (e.g. “use market orders for stops”) or incorporate ML predictions (e.g. “if model says fill-prob is high, use limit; else market”).  
- **Fill Modeling:** Predicts execution details for an order.  E.g.: *Fill probability*, *expected time-to-fill*, *expected fill price*, *adverse selection risk*.  Typical targets (ML outputs) include the probability of execution within a horizon and the conditional fill time【23†L802-L807】.  
- **Exit Logic:** Given an open position, decides exit orders.  Might predict when to take profit or how wide to set stops.  Could be rule-based (“stop = entry ± 3 ticks”) or ML (“given current price and hold time, P(trade ends profitably)”).  In simulation, it outputs exit orders similar to order-placement.  
- **Risk Governor:** At each tick/bar, evaluates overall metrics (cumulative P&L, volatility, limit thresholds).  It outputs an action: continue trading or disable.  For instance, daily loss > threshold triggers an “all-stop” signal.  

## ML Targets by Layer  
Examples of sensible ML outputs (targets) for this system include:  
- **Directional move probability:** e.g. \(P(\Delta \text{price} > 0 \text{ in next }30s)\).  A classifier or probability forecast.  
- **Fill Probability:**  \(P(\text{limit order executes within }T)\).  Formally, \(P(T_{\text{fill}} < T)\).  (Equivalently, a cumulative density of fill time)【23†L802-L807】.  This is crucial for choosing between limit vs. market.  
- **Conditional Fill Time:**  \(E[T_{\text{fill}}\mid T_{\text{fill}}<T]\).  Useful when sizing or deciding to cancel vs. wait.  
- **Expected Slippage:**  Difference between intended price and expected execution price for a market order of given size.  This can be a regression on order size, volume, volatility.  
- **Adverse Excursion Risk:**  The probability or expected magnitude of a move *against* the position after entry.  For example, if we fill on a buy limit, how likely is a further drawdown before profit?  This correlates with book imbalance: e.g. a heavy near-side queue (positive imbalance) implies the market is more likely to move against your buy (adverse selection)【25†L877-L885】.  
- **Time-to-Fill Distribution:**  Instead of a single number, output a full distribution over fill times (via an RNN or survival model), as done in recent research【50†L27-L34】.  
- **Regime Labels:** A multi-class classification of market regime (e.g. “trending”, “mean-reverting”, “high vol”, “low vol”).  

Not all ML targets need to be complex.  For instance, regime detection might start with simple volatility thresholds (rule), and later be replaced by an ML classifier.  Critically, targets like fill probability and expected slippage directly quantify execution cost, which informs order placement choices【50†L27-L34】.

## Rule-Based vs. ML Components  
Begin with rule-based logic for foundational parts, then layer in ML for refinement:  
- **Rule-based first:**  Risk gates (daily loss limits, emergency stops), session filters, and sizing caps should be rules.  Basic signal triggers (e.g. an indicator threshold) can also be rule-based initially.  Order-type defaults (e.g. “always use market order for exits”) can start as simple heuristics.  
- **ML enhancements:**  Directional signals, fill-time/fill-prob models, and perhaps dynamic stops can be improved with ML once enough data is available.  For example, one could start with fixed stop distances and later train a model to adjust stops by market state.  
- **Hybrid decisions:**  Order-placement (market vs limit) might use a rule (“use market if urgent”) augmented by an ML estimate of fill probability.  E.g. if predicted fill-prob is below 50%, switch to market order.  
- **Kill-switch and core risk:** These should always remain deterministic rules for safety and auditability.  

The layered approach means we can introduce ML in isolation.  For instance, swap in an ML fill-model without altering the signal logic.  This modular design prevents overfitting across stages and respects that some decisions (like maximum drawdown) are naturally rule-based.

## Order Placement: Execution Styles  
Key order types and their trade-offs:  

- **Market Order:**  Executes immediately at the best available prices.  Guarantees fill but incurs full spread plus any market movement.  Market orders are used when immediacy outweighs cost.  (As a reference, “market orders execute immediately at the best current price”【50†L45-L52】.)  
- **Passive Limit Order:**  Posted at or better than the current bid/ask.  Captures favorable price (better than mid), but may never fill if price moves away.  We face **non-fill risk**.  For example, a buy limit at B could sit unfilled if bids move down.  Bar-heavy edges rely on these to reduce cost, but require modeling \(P(\text{fill})\).  
- **Stop-Market Order:**  A stop-loss that becomes a market order when triggered.  Once the trigger is hit, a market order executes immediately.  Execution is guaranteed after trigger, but price is uncertain – in fast moves the fill price can be far from the trigger (adverse slippage).  Use for guaranteed exits at the cost of potential gap risk.  
- **Stop-Limit Order:**  A stop that becomes a *limit* order at trigger.  This gives price control, but the same non-fill risk as a limit.  In practice, a stop-limit may never execute if the market rapidly passes the limit.  As Investopedia notes, a stop-limit “combines a stop-loss trigger with a limit order”【43†L334-L343】, providing precise entry/exit control but **“not guaranteed to be executed”**.  If the market “drops quickly or gaps” past the limit price, the order simply never fills【43†L375-L380】.  This can leave you exposed if your stop fails.  
- **Trailing Stop:** A dynamic variant where the stop price moves with the market.  Can be set as either stop-market or stop-limit on trigger, inheriting the above traits.

**Comparison by setup type:**  For example, breakout trades often use stop-market or immediate market entries to catch momentum (accepting some slippage), while pullback or mean-reversion trades may favor passive limit entries (to improve price) with the risk of missing the move.  Micro-scalping (ultra-short trades) typically requires immediate fills, so uses market or IOC orders.  

## Differences by Strategy Module  
- **Breakout Modules:** Expect a rapid trend.  Often use aggressive entries (stop-market orders or small market orders) to avoid missing the move.  Stops might be further away (wider) to avoid getting hit by noise.  Exit might use partial limit orders to secure profit.  
- **Pullback/Continuation Modules:** Rely on counter-move entries.  They often post limit orders a few ticks into the move.  Position sizes are usually smaller (since the signal is weaker), and stops tighter.  Here execution is more passive: you’d rather miss a fill than pay too much slippage.  
- **Lunch/Dry-Range Modules:** The midday window (12:00–1:00) is low-volatility.  Edges are small.  Traders might only trade if they can post both ends (market-neutral) or take tiny scalps.  Fill rates drop around noon【25†L877-L885】, so often only small, patient orders are placed.  Many systems simply stay out or treat this as a time of high non-fill risk.  
- **Micro-Scalps:** Very short-duration trades (seconds).  Require lightning-fast execution.  Strategies rely on order-flow signals and use small market/IOC orders to ensure fill.  Here execution speed (and queue position in the order book) is the dominant factor, more so than the predictive signal.

## Backtesting Blueprint (Realistic Execution)  
To test this honestly, backtests must model execution details:

- **Use appropriate data frequency:** In the bar-only mode, simulate fills within each bar (e.g. assume limit orders could fill anywhere between open and close). In tick mode, replay each trade/quote tick and match orders against them.  
- **Explicit fill modeling:** Never assume a submitted order will fill at your intended price.  For limit orders, use a fill-probability model (e.g. learned via ML【50†L27-L34】) or empirical ratios.  E.g. “Given a buy limit at best bid, there is 60% chance to fill in 1 minute, 30% in 10s,” etc. Draw a random fill outcome accordingly.  Record partial fills if modeling multiple sizes.  
- **Slippage on market orders:** Simulate walking the book.  You can approximate by consuming quoted sizes: e.g., if selling 3 contracts into the bid side, match against the top 3 bids.  Or add a random slippage drawn from historical market order impacts.  
- **Latency and queue position:** If the signal emerges at time t, add a small latency (e.g. 100–200ms) before the order hits the book.  That can mean other orders arrived first.  In tick replay, compute your rank in queue: if N orders were at that price ahead, wait for N market trades before your order.  If data aren’t sufficient, approximate by lowering fill probability.  
- **Stop execution:** If a stop is triggered mid-bar, execute it at the first available price beyond the stop (not necessarily the bar-close price).  For a stop-market, assume execution at the worst price reached; for a stop-limit, apply the same fill model at the limit price.  
- **Partial and staggered orders:** If simulating larger orders, break them into child orders to more realistically mimic execution.  
- **Multiple scenarios:** Backtest over many non-overlapping periods to avoid overfitting.  Include “walk-forward” tests.  Test sensitivity: e.g. double the slippage, shrink time delays, to see if edge vanishes.  

The key is to **avoid idealizations**.  As one study warns, strategies that “appear effective in backtests may perform poorly in live environments” if they ignore execution costs【7†L98-L104】.  A robust backtest thus includes random delays, partial fills, and the chance of missed orders.  

## Hidden Assumptions (False Edges)  
Beware of these common backtest pitfalls:  
- **Perfect fills:** Assuming every order instantly executes at the target price (no spread/no delay) creates a false profit.  
- **Zero latency:** Updating positions instantaneously ignores communication and processing delay.  
- **Guaranteeing stops:** Treating stops like limit orders that fill exactly at the stop price. In reality, stop triggers send market orders, often at much worse prices.  
- **Ignoring partial fills:** Assuming you can always buy/sell your full desired size. In thin markets, only part may fill and the rest sits.  
- **Ignoring spread cost:** Using mid-price for fills effectively removes the half-spread cost.  
- **Stationarity:** Optimizing on one data set and assuming parameters hold forever. Market regime shifts can invalidate signals or change execution dynamics.  
- **Survivorship bias/Look-ahead:** Using future information or cherry-picking successful intervals.  

For example, a mean-reversion signal might look profitable on bar-data if you assume you always sell at the bar-high.  But if that was achieved only because the price later dropped, you were unknowingly using future knowledge.  Similarly, any strategy backtested without explicit fill modeling is almost certainly overstated.  In practice, many supposed edges “disappear” under realistic execution【7†L98-L104】.

## Recommended Production Architecture  
In a live system, we would implement the modules as separate services or containers:  

- **Data Ingestion Service:** Continuously fetches ES futures tick data, quotes, and news/event timestamps.  Cleans and timestamps everything into a database or feed.  
- **State Engine:** Maintains real-time features (volatility, bid/ask imbalance, regime flags) and publishes them.  
- **Signal Engine:** Runs the directional models on incoming data.  For example, it might be a Python/C++ service loading trained ML models (TensorFlow/PyTorch).  When a signal triggers, it publishes a trade intent (e.g. buy/sell with strength).  
- **Trade Selection & Risk Engine:** Another service that subscribes to signals, filters them by global risk constraints (like max daily loss, total exposure), and finalizes trade sizes.  If a kill-switch condition is met, it will discard signals and cancel outstanding orders.  
- **Execution Engine:** Receives approved trade orders and sends them to the broker.  It handles the chosen order type and monitors fills.  For example, it might post a limit order and wait; if unfilled after a timeout, it could retry or switch to market.  This engine can also simulate fills in backtesting: one can configure it with a “success_rate” (e.g. 95%) and artificial delay to mimic real conditions【51†L227-L233】【51†L234-L239】.  
- **Position Manager/Exit Engine:** Tracks open positions.  If a stop or target is hit (by signals from market data), it generates exit orders accordingly.  
- **Logging/Monitoring:** Everything is logged separately – for example, trading.log (orders/trades), error.log, performance.log (P&L, latency metrics)【51†L279-L288】.  Dashboards display fill rates, slippage, P&L curves, etc., for ongoing oversight.  
- **Scalability:** Use message queues (Kafka, RabbitMQ) to decouple services.  Each module (data, signal, execution, etc.) runs independently so one can be restarted or tuned without halting the pipeline.  

This production setup cleanly separates **signal generation** from **order execution**.  The Signal engine never speaks directly to the market – it just emits high-level trade intents.  The Execution engine handles all market interaction, with its own models for fills and slippage.  This modularity makes testing and iteration much safer and clearer.

## Signal vs. Execution – Where’s the Real Edge?  
Finally, consider: *what part of the ES intraday “edge” is genuine signal versus execution mechanics?*  In practice, many apparent edges in backtests are actually artifacts of execution assumptions.  For example, a mean-reversion entry that looks profitable on 1-minute bars may yield near-zero profit once the spread and slippage are included【7†L98-L104】.  Conversely, clever execution tactics (e.g. posting an aggressive limit in front of marketable flow) can squeeze out profits even if the underlying signal is modest.  

Research confirms this: strategies that ignore execution costs often see their historical gains evaporate when traded live【7†L98-L104】.  That’s why we compare performance under *idealized* fills versus *realistic* execution.  Profit that disappears under the realistic model wasn’t true alpha—it was just the result of a model’s perfect-fill illusion.  

In summary, **signal** is the forecast (when and why to trade), and **execution** is the mechanism (how and whether that forecast is realized).  By separating them, we can identify which profits come from predictive power and which come from order-management.  If an “edge” vanishes once real-world execution is considered, it was never a true predictive edge【7†L98-L104】.

**Sources:** We cite literature on execution-aware algorithmic trading.  For example, Olby *et al.* show that backtests ignoring realistic execution produce misleading profits【7†L98-L104】.  Recent work on ML-based fill modeling demonstrates how estimating fill probability and time can *significantly reduce execution cost*【50†L27-L34】.  We also draw on industry examples of modular trading pipelines【51†L227-L233】 and microstructure analysis of limit-order fills【25†L877-L885】【23†L802-L807】. These underline the importance of modeling execution explicitly and keeping signal and execution logic distinct.

