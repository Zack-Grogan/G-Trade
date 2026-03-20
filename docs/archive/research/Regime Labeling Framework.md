# Regime Labeling Framework for ES Intraday Hot-Zone Trading

*Reference: strategy/research only. Current operator interface is CLI-only; see [../README.md](../README.md) and [../OPERATOR.md](../OPERATOR.md).*

We propose a **multi-dimensional regime taxonomy** tailored to ES futures hot zones, combining time-of-day context with measured volatility, trend/range, liquidity, event, and execution-quality labels.  Each label is defined quantitatively and updated in real time from market data.  Below we detail each dimension (meaning, inputs, thresholds, update frequency), how labels interrelate (mutual/exclusive, stackable), and practical schemes for research, live trading, and ML.

## Regime Dimensions and Definitions

- **Time-of-Day Regime:**  This captures **fixed windows** of the trading day.  For ES we use the specified hot zones (e.g. *Pre-Open* (6:30–8:30), *Open* (9:00–11:00), *Midday* (12:00–13:00), *Late Lunchtime* (12:45–13:00)).  These labels are based on the clock and known session structure, not price data.  *Meaning:* e.g. “Open session” denotes 9–11 window.  *Inputs:* Local time (configurable timezone).  *Threshold:* Exact window boundaries.  *Update:* Changes at window start/end (i.e. on the minute).  Time-of-day is **mutually exclusive** (only one active), and is a top-level context.  For example, the early pre-open zone often has macro news risk, while midday is typically low-volatility mean-reversion time【7†L145-L153】【11†L61-L66】.

- **Volatility Regime:**  Indicates current intraday volatility level.  *Meaning:* “High-vol” if recent price swings are large relative to normal; “Low-vol” if price action is subdued.  *Inputs:* Realized volatility metrics such as **ATR (Average True Range)**, short-term **standard deviation** of returns, or a **volatility index** feed (e.g. intraday VIX).  For example, traders often use ATR on a fixed window (e.g. ATR of the last 5–15 minutes) or the ratio ATR/price【11†L117-L124】【28†L309-L314】.  *Threshold:* e.g. ATR above a percentile of its day-of-week historical distribution could flag “high-volatility”, or a rolling Z-score >1.5 triggers high-vol.  One can also use **CUSUM change-detection** (e.g. thresholds at ±2σ changes in price variance【13†L72-L80】).  Practically, many desks mark regimes by “ATR > X” or by spikes in realized volatility【11†L117-L124】【28†L309-L314】.  *Update:* Continuously on each new bar (e.g. 1m or 5m).  This label **stacks with others** – a market can be both trending and high-vol【28†L218-L225】.

- **Trend/Range Regime:**  Classifies price geometry as **trending** vs **mean-reverting (ranging)**.  *Meaning:*  “Trending” if price exhibits a sustained directional move; “Ranging” if price oscillates around a flat value.  *Inputs:* Price-based indicators: **ADX (Average Directional Index)**, **Hurst exponent**, **efficiency ratio**, or simple net price movement vs volatility.  For example, an ADX(14) above ~25 on intraday data typically signals a strong trend【2†L413-L420】【4†L268-L270】, whereas ADX below ~20 indicates a sideways market.  Similarly, a Hurst exponent significantly above 0.5 (persistent) implies trend, while below ~0.5 implies mean-reversion【2†L425-L432】.  *Threshold:* Empirical values like ADX >25 = trend, <20 = range are common【2†L413-L420】.  Efficiency ratio (net move/total move) >0.5 could also flag trending.  *Update:* Compute each minute with a sliding window (e.g. last 5–15 bars).  This label is **not mutually exclusive with volatility** – you can have a “High-Volatility Trend” or “Low-Volatility Range”【28†L218-L225】.  

- **Liquidity Regime:**  Flags whether the market is currently **liquid (deep)** or **thin (fragile)**.  *Meaning:* “High Liquidity” means tight spreads, deep order book, and large volume; “Low Liquidity” means wide spreads, shallow book, low volume.  *Inputs:* Market microstructure data: bid-ask spread, order book depth at top levels, trade volume, and trade frequency.  For example, measure the *average spread* over the last minute and *cumulative volume* or *depth on BBO*.  One can also use volume percentiles (e.g. 1-min volume below 25th percentile = thin).  *Threshold:* E.g. ES spread >0.75 points or top-of-book depth <50 contracts could mark a thin market【7†L131-L139】.  Alternatively, a low trade count or low total volume during recent interval flags low liquidity.  *Update:* Real-time (each tick or 1s, aggregated to 1m).  Liquidity regime **overlaps other labels**: thin liquidity often coincides with high-volatility conditions and degrades execution【28†L316-L318】【28†L339-L344】.  

- **Event Regime:**  Marks **scheduled macroeconomic events** or other known catalysts.  *Meaning:* “Macro Event” (or “News”) regime denotes that a major release (e.g. Fed rate decision, CPI, NFP) is imminent or just occurred, as opposed to “Normal” when no high-impact news is pending.  *Inputs:* Economic calendar (like Bloomberg/FXStreet/etc) and event impact scores.  Label high-impact events (US CPI, GDP, FOMC, etc) as triggers【31†L133-L138】【31†L190-L198】.  *Threshold:* For example, label an event regime from a few minutes before to perhaps 15–30 minutes after the scheduled time if the data surprises.  One could also define sublevels (e.g. “Major News” vs “Minor News”).  *Update:* As per calendar times (pre-tag start and end).  Note this label is exogenous (calendar-driven) and can be “look-ahead” if using the known schedule.  It should be used carefully: calendar times are known, but one should not use actual data surprise (that’s forward-looking).  In practice, treat “News Regime” as a flag for heightened volatility and adapt strategy (separate from normal price data)【31†L133-L138】.  

- **Execution-Quality Regime:**  Reflects **trading cost conditions**.  *Meaning:* “Normal Execution” vs “Degraded Execution” (slippage-prone).  *Inputs:* Indicators of trade execution quality, such as realized bid-ask spread (e.g. average midpoint slippage), order fill rates, or queue waiting times.  For example, compute the effective spread of executions vs mid-price, or the ratio of marketable order fill success over the last interval.  If real-time data on fills is limited, proxies like spike in spreads or a drop in visible depth suffice.  *Threshold:* E.g. if observed slippage (difference between trade price and midpoint) exceeds a threshold, label “poor execution.”  Or spread widening by >2x normal.  *Update:* Very frequently (every few seconds).  High-volatility often causes execution regime degradation (spreads widen, fills worsen)【28†L316-L318】【28†L339-L344】.  This label can co-exist with others; it often correlates with high-vol and thin liquidity states.  

Each regime label is **formally defined by these quantitative criteria**.  In practice, desks often maintain a “regime scorecard” combining several signals (e.g. ADX, ATR, spreads) rather than one perfect rule【2†L375-L384】【13†L66-L72】.

## Label Relationships: Exclusive, Multi-label, Hierarchy

The regime labels form a **hierarchical multi-label system**:

- **Hierarchy:** *Time-of-Day* is a top-level segmenter.  For example, strategies can first check “are we in the open session or midday?” and apply different logic.  Within each window, the other regimes (volatility, trend, etc.) apply independently.  

- **Stacked/Multi-label:**  Volatility, trend/range, liquidity, and execution-quality are **orthogonal axes**.  You often have multiple active labels (e.g. “High-Volatility + Trending + Thin-Liquidity”).  As Aron Groups notes, a 2×2 of trend×volatility is minimal (trend/range *plus* high/low vol)【28†L218-L225】.  Thus labels **should stack**: each dimension adds information.  

- **Mutual Exclusivity:** Only some labels are mutually exclusive within a dimension.  For example, a regime cannot be both “Open session” and “Midday” at once – *time-of-day* is exclusive.  Similarly, in trend/range, you might allow a small neutral zone, but usually classify as one or the other.  However, *trend* vs *range* and *high-vol* vs *low-vol* are not mutually exclusive across dimensions; they combine to describe the full state【28†L218-L225】.  Event labels (news vs normal) are exclusive categories of calendar state.  Execution-quality can be thought of as binary (good/bad) or graded.  

In summary, use **one-hot for time windows**, but treat volatility, trend, liquidity, event, and execution as separate flags (often multi-hot).  A unified controller can interpret the stacked vector of current labels to adjust behavior.

## Labeling Schema: Offline, Live, and ML

- **Offline Research (Backtesting):**   Here one can label regimes using historical data with hindsight, but be careful to avoid using *future information* inadvertently.  For example, you might compute *realized volatility* or *future returns* as part of a regime label in a backtest, but any definition using future values is purely retrospective.  Instead, offline labels should mimic what you *could* have known at the time.  Regime rules should be applied as they would live (e.g. using a moving window ending at each bar) so as not to introduce lookahead.  Offline, you can “play back” 1m or tick data and generate labels with the same real-time rules.  ML training labels would typically use these offline labels as ground truth.  

- **Live Trading:**  Only use labels computable from current and past data.  For example, use the latest completed 1m bar to update volatility or ADX.  Do **not** use future bars to set today’s regime.  Time-of-day and scheduled news are known (so safe).  Always compute indicators causal (e.g. ADX with only prior bars).  Execution-quality indicators can use actual fills up to now.  The system then reacts in real time to the current regime vector.

- **ML Training:**  One can train ML models on offline-labeled data, but features must respect causality.  If using supervised ML for regime classification, feed the model only past features (price, vol, time) and the offline-assigned label.  Avoid label definitions that “peek” (e.g. labeling a bar as trending if the price afterwards went up – that would leak info).  Instead, train on the same rules above.  Also, because regimes are time-dependent, ML models should be retrained if market conditions shift (the definitions should hold consistently over data).  Note Aron Groups emphasizes regimes depend on timeframe: intraday label may differ from daily label【28†L250-L254】, so train at the appropriate horizon.

## Real-Time vs Retrospective Labels

- **Real-Time Labels:**  Time-of-day, volatility, trend, liquidity, and execution labels can all be made real-time by using only current/past data (e.g. 1m bars, current order book).  Economic **event** labels (schedule) are somewhat unique: the timing is known ahead (so real-time tag), but the *impact* isn’t known until after.  We treat “event regime” as a forward-looking flag (before release), but refrain from using the actual surprise itself as input except retrospectively.  

- **Retrospective-Only Labels:**  Avoid any label definition that requires future outcomes.  For example, a label like “price moved >1% in the next 5m” would be retrospective and not usable live.  Similarly, computing a volatility regime using the rest-of-day realized variance introduces lookahead.  Instead, use trailing-window measures.  If any dimension truly requires hindsight (e.g. computing realized vol of the *entire day* to define regime), mark it clearly as retrospective and use only in analysis, not live.  

- **Validity:**  We note that regime definitions can “fail” differently for different horizons【28†L250-L254】.  A regime filter for intraday should not use daily statements, and vice versa.  Keep each label’s time granularity consistent with its use.

## Hot-Zone Regime Priors

The hot trading windows have **statistically distinct regime priors**:

- **Early Window (6:30–8:30):**  Often dominated by **macro events and pre-open dynamics**. Liquidity is typically **lower** (thin book at pre-open)【7†L131-L139】. Expect higher chance of “Event Regime” (e.g. central bank announcements often land around 8:00–8:30 ET)【31†L133-L138】. Volatility can be high around news, but outside those times the market may be relatively subdued until the open. Trend signals may be weak due to limited participation.  

- **Open (9:00–11:00):**  Contains the NYSE open, typically the **highest volatility and liquidity** of the day【11†L155-L162】【7†L145-L153】. This is a classic **price-discovery regime**. Expect large volatility spikes, strong trends or whipsaws (the “Amateur Hour” 9:30–10:00 ET can see erratic moves)【11†L155-L162】. Regime priors: high probability of *High-Volatility + possibly Trending* immediately after open.  

- **Midday (12:00–13:00):**  Known to be the “dead zone” on ES: volume and volatility **drop sharply** after the morning session【11†L93-L95】. Regime is often low-volatility, mean-reverting (choppy)【11†L93-L95】. Liquidity may be moderate but often less than open. Trend signals rarely sustain; expectation is of pullbacks and range action.  

- **Late Lunchtime (12:45–13:00):**  This 15-min micro-window (within midday) is often even quieter. It may see position-squaring before the close-out of the session or before 1:15 CT expiration. Regime here tends toward flatness – few trending opportunities. Many traders treat it as a “no-trade” micro-regime or strictly mean-revert.  (We mark it separately since it may call for distinct rules, e.g. *“Flatten-only”* strategy.)  

Mapping each hot zone to priors guides default label settings. For example, the Open session starts with a high-volatility prior, whereas Midday starts with low-volatility.  The controller can load these as initial guesses and then override them as real-time signals evolve.

## Feature Sets for Regime Classification

- **Using 1-Minute Bars (and Volume):**  Only OHLC bars and bar volume are available.  The minimum features to approximate each regime dimension include:
  - *Trend/Range:*  Compute ADX(14) on the 1m series, or equivalently use rolling 5–15 minute net return vs sum-of-moves (efficiency ratio)【2†L413-L422】.  A simple feature is the net change over the window divided by total range.  Also, count of consecutive bars in one direction or inside-bar counts.  
  - *Volatility:*  Calculate ATR over recent bars or the standard deviation of 1m returns【11†L117-L124】【28†L309-L314】.  Also use rolling variance or high-low range.  
  - *Liquidity:*  No bid/ask available, so infer liquidity from volume: e.g. 1m **volume** vs its moving average or vs same minute of prior days.  Very low volume bars suggest a thin regime.  Alternatively, compute “volatility-of-returns” on volume (is trading flow accelerated or idle?).  
  - *Event:*  Encode time-to-next-scheduled-event as a feature.  E.g. “minutes until next known CPI release.”  This binary/time feature indicates an Event regime about to start.  
  - *Execution Quality:*  Hard with bars only – one might use bar-level proxies like spread proxy from bar width vs bar volatility.  For example, a bar whose range is huge relative to body might indicate slippage. But this is imprecise; true execution features need tick-level.  

  In summary, with 1m data use rolling statistical features: ATR, ADX, Hurst on price returns, and volume patterns.  These capture volatility and trend regimes.  

- **Using Tick + BBO + Depth Data:**  With full tick and order-book data, we can compute richer microstructure features:
  - *Spread & Depth:* Real-time bid-ask spread (ticks), and total resting volume at top N levels on each side. For example, feature = (BidDepth − AskDepth)/(BidDepth+AskDepth) for imbalance.  A large spread or imbalance signals low liquidity.  
  - *Order Flow:* Tick-by-tick signed volume (e.g. +volume for buy-initiated trades, – for sells).  Features: cumulative signed volume in last 30s, or trade count per second.  Sudden surges in trade count or volume often herald regime shifts【13†L91-L100】.  
  - *Volatility:* Instantaneous volatility can be measured by tick return dispersion over a short window, or by counting large price ticks.  
  - *Trend:* Similarly, one can apply ADX or a Kalman filter to microprice (midpoint) sampled at 1s or 5s.  Even tick data can feed microstructure-based trend filters.  
  - *Execution-Quality:* Compute realized spreads: e.g. measure difference between trade price and mid or previous best.  Track “adverse selection” by whether executions occur at bid or ask crossing.  
  - *Event:* Still use time/calendar features. High-impact releases often cause rush of orders (detectable as volume spike).  

  These features enable more precise regime detection in real time.  For instance, a **widening spread + eroding depth** flag a switch to a thin-liquidity regime, even before volatility fully materializes.  

## Unified Regime Controller Architecture

A practical architecture is a **hierarchical regime engine** that feeds a central “market state” label vector to trading logic.  For example:

1. **Time-of-Day Filter:** Identify current window (Early/Open/Midday) and load initial regime priors or strategy parameters for that block.  
2. **Market Condition Classifier:** Continuously compute volatility, trend, liquidity, and execution signals (as above).  Combine them into discrete labels or scores (e.g. “HighVol=1/0”, “Trend=Up/Down/Flat”, “Liquid=Yes/No”).  This can be done via rule-based thresholds or an ML classifier trained offline on these features.  
3. **Event Detector:** Independently mark if a scheduled event is active (possibly pre-event, during, or post-event sub-regimes).  
4. **Regime State Vector:** Assemble the multi-label state, e.g. `[Window=Open, Vol=High, Trend=Up, Liquidity=Good, Event=No, Exec=OK]`.  
5. **Strategy/Position Sizing Logic:** The unified controller uses the regime vector to **select strategies or adjust parameters**. For instance, in a “HighVol+Trending” state (likely after open or event) one might use breakout strategies with wider stops. In a “LowVol+Ranging+Thin” midday state, one might scale back size or switch to mean-reversion scalps. Execution-quality flags can widen stops or avoid market orders.

This architecture ensures all regime dimensions inform decisions.  Note that **execution-quality should be monitored continuously** – as Aron Groups emphasizes, execution often deteriorates before the price “looks” different【28†L339-L344】. The controller can preemptively reduce risk as spreads widen.

## Pitfalls and Avoiding Overfitting

Key mistakes to avoid:

- **Future Leakage:** Do *not* use any feature or label that requires future data (e.g. labeling a period as trending based on future moves). Always formulate labels on past data only.  
- **Overflexible Definitions:** Over-calibrating thresholds (e.g. tweaking ADX cutoffs to maximize past performance) risks curve-fitting.  Prefer *fixed rules* or **statistical thresholds** (e.g. quantiles) that are stable across regimes. Backtest on out-of-sample periods to validate rules.  
- **Too Many Labels:** Creating an overly granular or ad-hoc label scheme (e.g. dozens of micro-regimes) can lead to sparse data per regime and overfitting.  Stick to a parsimonious set of meaningful labels.  
- **Ignoring Label Interactions:** Treating each dimension independently in a model without accounting for their stacking can mislead (trend actions differ in high-vol vs low-vol). Our multi-label approach mitigates this by design【28†L218-L225】.  
- **Data Snooping News:** Using actual news surprise (e.g. magnitude of CPI surprise) in a label is effectively using future information. Stick to schedule/time for “event regime.”  After the fact, one could have a retrospective “big surprise” label for analysis, but not for live logic.  
- **Neglecting Execution:** A common oversight is ignoring execution conditions.  As [28] notes, regime shifts often first show up in **worsening fills/spreads**.  Not monitoring this invites slippage traps.  

In short, build regime definitions from explainable, causal indicators, and test them robustly.  A well-designed multi-dimensional regime system becomes a **state engine** for a unified controller: it routes signals and adjusts risk in accordance with current market “environment.” 

**References:** Established literature and practitioner sources describe these concepts and thresholds for ES intraday regimes【2†L375-L384】【2†L413-L420】【4†L268-L270】【7†L145-L153】【11†L61-L66】【28†L316-L318】【28†L339-L344】【31†L133-L138】【31†L190-L198】, which underpin the framework above.