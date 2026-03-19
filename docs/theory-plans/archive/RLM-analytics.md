Here's the core theory of the architecture. Each layer maps directly to a step in the scientific method — and the entire system is designed to be **self-driving**: the LM doesn't just generate hypotheses, it also evaluates its own results and decides what to test next.

**The key theoretical insight** is that a standard LM call is stateless — it knows nothing between turns. RLM solves this with the **knowledge store** and the **recursive feedback loop**. Every test run is fully persisted (hypothesis, config, result, verdict, confidence score), and when the LM is called again, it reads that history as context. This is what makes it *recursive* — each generation of hypotheses is conditioned on the empirical outcomes of the prior generation.

**The three supporting pillars at the bottom** are cross-cutting concerns that plug into every layer:

The **regime context** layer matters because a hypothesis that works in a trending ES session will fail in a range-bound one. Every layer — from hypothesis formation to analysis — needs to know the current market structure. The LM should tag hypotheses with the regime they were formed under, and the analysis engine should segment results by regime.

The **meta-learner** is what separates this from a simple backtesting loop. Over many iterations, it tracks *which classes of hypotheses* survive (e.g. "breakout hypotheses in high-vol regimes have a 70% survival rate, mean-reversion hypotheses in low-vol regimes have a 30% survival rate"). The LM can then bias its hypothesis generation toward productive territories.

The **guardrails** are the scientific integrity layer. Without them, a system that generates and tests many hypotheses will find spurious edges through pure randomness — the classic p-hacking / multiple comparisons problem. The system needs Bonferroni correction or FDR control, and it needs overfitting detection (out-of-sample holdout, walk-forward validation) before any verdict gets promoted to "supported."

---

The **experiment designer** layer is where the scientific rigor lives in practice. It's responsible for defining:
- Independent variable (what's being changed — a threshold, a timing rule, a volatility filter)
- Dependent variables (what gets measured — edge per trade, Sharpe, max drawdown)
- Control variables (session time, contract, minimum volume — held constant)
- Test window (how much data, and whether it's in-sample or walk-forward)

The schema is the single most important design decision in the whole system. Every other component reads or writes to it. The key field to understand is `mutation_directive` — it's the LM's own instruction to its future self about what to test next, written at the moment it makes a verdict. This is what closes the loop between conclusion and the next generation of hypotheses.

---

Now the feedback loop mechanism:The critical theory here is that **the LM never starts fresh**. Each generation call is handed the entire lineage as context — what was claimed, how it was tested, what the verdict was, and what the system instructed itself to try next. This is why `mutation_directive` is the most important field in the schema. It's written by the LM at conclusion time, *before* it forgets everything, as a letter to its next instantiation.

The three mutation types give the system three different ways to respond to evidence. Parameter refinement exploits a promising signal. Scope expansion stress-tests a supported claim. Class pivot abandons a dead end entirely — and this is how the meta-learner's class survival scores get used: if breakout hypotheses keep getting rejected over many generations, the LM should pivot, not refine.

---

Now the statistical framework:The statistical framework is deliberately layered as a **sequential gate system** — a hypothesis must pass each layer before advancing to the next. This prevents weak signals from surviving long enough to waste compute on deep walk-forward testing.

A few design decisions worth calling out explicitly:

**Layer 1 is non-negotiable** and must be enforced at the system level, not left to the LM's discretion. By the time you've run 50 generations with 3 hypotheses each, you've run 150 tests. At α=0.05 uncorrected, roughly 7-8 of those will appear significant purely by luck. The BH-FDR method (Benjamini-Hochberg) is generally better than Bonferroni for futures trading because it controls the *rate* of false discoveries rather than the probability of *any* false discovery — which is less conservative and more appropriate when you're looking for a portfolio of edges, not a single definitive finding.

**The OOS/IS decay ratio in Layer 3** is the single most diagnostic number in the whole system. A ratio above 0.8 suggests the hypothesis is genuinely robust. A ratio between 0.6 and 0.8 is acceptable. Below 0.4 is almost always curve-fitting, regardless of how compelling the in-sample statistics look — and the LM's mutation directive should flag this explicitly so the next generation doesn't repeat the same over-parameterized structure.

**Layer 4 regime segmentation** solves a subtle problem: a hypothesis can look borderline on aggregate but be genuinely strong in one regime and a loser in another. Without segmentation, those two signals cancel out and the hypothesis gets inconclusive or rejected — but the real finding is "this is a trending-regime-only strategy." The LM needs to surface that as a scoped supported hypothesis, not a global rejection.

**Layer 5 edge decay** is what prevents the system from continuously re-confirming stale knowledge. Markets adapt. An edge that was real in 2022 may be gone by 2024. The temporal thirds test is a lightweight way to detect this — if performance in the most recent third is materially weaker than the first two thirds, the hypothesis is decaying in real time and should be flagged for re-evaluation even if its aggregate score is passing.

---

Putting all three together: the schema is the *data contract*, the feedback loop is the *control flow*, and the statistical framework is the *truth function*. None of the three work without the other two. Want to go into how the LM prompt should be structured to actually produce well-formed schemas and mutation directives?