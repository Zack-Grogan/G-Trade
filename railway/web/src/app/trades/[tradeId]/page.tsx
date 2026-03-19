import Link from "next/link";
import { notFound } from "next/navigation";

import { Badge, DataRow, DataTable, EmptyState, Panel, StatCard, formatCurrency, formatDate, formatShort } from "@/components/dashboard";
import { MarketChart, type ChartMarker, type ChartReferenceLine } from "@/components/market-chart";
import { PageShell } from "@/components/page-shell";
import { fetchTradeReview } from "@/lib/analytics";
import { isSignedInRequest } from "@/lib/session";

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function formatText(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return Math.abs(value) >= 100 ? value.toFixed(0) : value.toFixed(2);
  }
  if (typeof value === "boolean") {
    return value ? "yes" : "no";
  }
  return String(value);
}

function directionTone(direction: number | null) {
  if (direction === null) {
    return "neutral" as const;
  }
  return direction >= 0 ? "success" as const : "warning" as const;
}

export default async function TradeReviewPage({
  params,
  searchParams,
}: {
  params: Promise<{ tradeId: string }>;
  searchParams: Promise<{ view?: string }>;
}) {
  const signedIn = await isSignedInRequest();
  if (!signedIn) {
    return <PageShell authenticated={false} />;
  }

  const { tradeId } = await params;
  const { view } = await searchParams;
  const mode = (view || "narrative").toLowerCase() === "raw" ? "raw" : "narrative";
  const bundle = await fetchTradeReview(tradeId);

  if (!bundle?.trade) {
    notFound();
  }

  const trade = bundle.trade;
  const run = bundle.run;
  const analysis = bundle.analysis;
  const belief = analysis?.executorBelief ?? null;
  const diagnostics = belief ? asRecord(belief.diagnostics) : {};
  const featureSnapshot = belief ? asRecord(belief.featureSnapshot) : {};
  const signedFeatures = belief ? asRecord(belief.signedFeatures) : {};
  const marketPoints = bundle.marketTape
    .slice()
    .reverse()
    .map((row) => ({
      timestamp: row.capturedAt,
      value: row.last ?? row.bid ?? row.ask,
    }))
    .filter((point) => point.value !== null);

  const referenceLines: ChartReferenceLine[] = [
    { label: "Entry", value: analysis?.entryExit?.entryPrice ?? trade.entryPrice, tone: "success" as const },
    { label: "Exit", value: analysis?.entryExit?.exitPrice ?? trade.exitPrice, tone: "accent" as const },
    { label: "Decision", value: belief?.decisionId ? (featureSnapshot.decision_price as number | null) ?? null : null, tone: "neutral" as const },
    { label: "VWAP", value: (diagnostics.rth_vwap as number | null) ?? (diagnostics.eth_vwap as number | null) ?? null, tone: "neutral" as const },
    { label: "POC", value: diagnostics.poc as number | null, tone: "success" as const },
    { label: "VAH", value: diagnostics.vah as number | null, tone: "warning" as const },
    { label: "VAL", value: diagnostics.val as number | null, tone: "warning" as const },
  ].filter((line) => line.value !== null);

  const markers: ChartMarker[] = [];
  if (analysis?.entryExit?.entryTime && (analysis.entryExit.entryPrice ?? trade.entryPrice) !== null) {
    markers.push({
      label: "Entry",
      timestamp: analysis.entryExit.entryTime,
      value: analysis.entryExit.entryPrice ?? trade.entryPrice,
      tone: trade.direction >= 0 ? "success" : "warning",
    });
  }
  if (analysis?.entryExit?.exitTime && (analysis.entryExit.exitPrice ?? trade.exitPrice) !== null) {
    markers.push({
      label: "Exit",
      timestamp: analysis.entryExit.exitTime,
      value: analysis.entryExit.exitPrice ?? trade.exitPrice,
      tone: "accent",
    });
  }

  const projectedNotes = analysis?.executorProjection ?? [];
  const viewLinks = (
    <div className="flex flex-wrap gap-2">
      <Link
        href={`/trades/${tradeId}?view=narrative`}
        className={`inline-flex items-center rounded-full border px-3 py-2 text-sm transition ${
          mode === "narrative" ? "border-cyan-500/30 bg-cyan-500/15 text-cyan-100" : "border-zinc-800 bg-zinc-900 text-zinc-200 hover:border-cyan-500/30 hover:bg-cyan-500/10"
        }`}
      >
        Narrative
      </Link>
      <Link
        href={`/trades/${tradeId}?view=raw`}
        className={`inline-flex items-center rounded-full border px-3 py-2 text-sm transition ${
          mode === "raw" ? "border-cyan-500/30 bg-cyan-500/15 text-cyan-100" : "border-zinc-800 bg-zinc-900 text-zinc-200 hover:border-cyan-500/30 hover:bg-cyan-500/10"
        }`}
      >
        Raw evidence
      </Link>
    </div>
  );

  return (
    <PageShell authenticated>
      <main className="mx-auto max-w-7xl space-y-6 px-6 py-10 lg:px-8">
        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <Panel
            eyebrow="Trade reviewer"
            title={`Trade ${trade.tradeId ?? trade.id}`}
            description="A layered readout of what entered, what exited, what the market was doing, and what the executor believed at the time."
            action={
              <div className="flex flex-wrap items-center gap-2">
                <Link
                  href={run?.runId ? `/runs/${run.runId}` : "/runs"}
                  className="inline-flex items-center rounded-full border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-white"
                >
                  Back to run
                </Link>
                {run?.runId ? (
                  <Link
                    href={`/chart?runId=${encodeURIComponent(run.runId)}`}
                    className="inline-flex items-center rounded-full border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-white"
                  >
                    Open chart
                  </Link>
                ) : null}
                {viewLinks}
              </div>
            }
          >
            <div className="flex flex-wrap gap-2">
              <Badge tone={directionTone(trade.direction)}>{trade.direction > 0 ? "long" : trade.direction < 0 ? "short" : "flat"}</Badge>
              <Badge tone="accent">{trade.zone ?? "zone unknown"}</Badge>
              <Badge tone={trade.accountMode === "live" ? "success" : "warning"}>{trade.accountName ?? trade.accountId ?? "unknown account"}</Badge>
              <Badge tone="neutral">{trade.accountMode ?? "unknown mode"}</Badge>
              <Badge tone="neutral">{trade.strategy ?? "no strategy"}</Badge>
              <Badge tone={trade.pnl >= 0 ? "success" : "warning"}>{formatCurrency(trade.pnl)}</Badge>
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <StatCard label="Entry" value={formatCurrency(trade.entryPrice)} note={formatDate(trade.entryTime)} />
              <StatCard label="Exit" value={formatCurrency(trade.exitPrice)} note={formatDate(trade.exitTime)} />
              <StatCard label="Duration" value={formatText(analysis?.entryExit.duration ?? "—")} note="Trade window" />
              <StatCard label="Market tape" value={formatShort(bundle.marketTape.length)} note="Samples in review window" />
            </div>
          </Panel>

          <Panel eyebrow="Summary" title="Human-readable narrative" description="The same evidence rendered as a concise decision narrative.">
            <div className="space-y-3">
              <p className="rounded-2xl border border-zinc-800 bg-zinc-950/80 px-4 py-3 text-sm leading-6 text-zinc-200">
                {analysis?.summary ?? "No narrative summary is available for this trade."}
              </p>
              {projectedNotes.length ? (
                projectedNotes.map((note) => (
                  <div key={note} className="rounded-2xl border border-zinc-800 bg-zinc-950/80 px-4 py-3 text-sm leading-6 text-zinc-300">
                    {note}
                  </div>
                ))
              ) : (
                <EmptyState title="No projection notes" description="The analytics service has not produced executor projection notes for this trade yet." />
              )}
            </div>
          </Panel>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <MarketChart
            title="Trade window tape"
            subtitle="Entry and exit markers against the stored tick stream"
            points={marketPoints}
            markers={markers}
            referenceLines={referenceLines}
            height={320}
          />

          <Panel eyebrow="Belief" title="Executor belief and indicator stack" description="The decision snapshot captured at the time of the trade.">
            {belief ? (
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Badge tone={belief.allowEntries === false ? "warning" : "success"}>{belief.allowEntries === false ? "entry gated" : "entry allowed"}</Badge>
                  <Badge tone={belief.executionTradeable === false ? "warning" : "success"}>{belief.executionTradeable === false ? "not tradeable" : "tradeable"}</Badge>
                  <Badge tone="accent">{belief.dominantSide ?? "dominant side unknown"}</Badge>
                  <Badge tone="neutral">{belief.regimeState ?? "no regime"}</Badge>
                  <Badge tone="neutral">{belief.activeSession ?? "no session"}</Badge>
                </div>

                <div className="grid gap-3 text-sm text-zinc-300 sm:grid-cols-2">
                  <p>Score gap: {formatText(belief.scoreGap)}</p>
                  <p>Long score: {formatText(belief.longScore)}</p>
                  <p>Short score: {formatText(belief.shortScore)}</p>
                  <p>Regime reason: {belief.regimeReason ?? "—"}</p>
                </div>

                <DataTable columns={["Indicator", "Value", "Context"]}>
                  {(
                    [
                    ["ATR", diagnostics.atr_value ?? featureSnapshot.atr_value, "Volatility"],
                    ["RSI", diagnostics.rsi ?? featureSnapshot.rsi, "Momentum"],
                    ["RTH VWAP", diagnostics.rth_vwap ?? featureSnapshot.rth_vwap, "Session anchor"],
                    ["ETH VWAP", diagnostics.eth_vwap ?? featureSnapshot.eth_vwap, "Session anchor"],
                    ["POC", diagnostics.poc, "Volume profile"],
                    ["VAH", diagnostics.vah, "Volume profile"],
                    ["VAL", diagnostics.val, "Volume profile"],
                    ["Spread", diagnostics.spread ?? featureSnapshot.spread, "Microstructure"],
                    ["Value area position", signedFeatures.value_area_position ?? featureSnapshot.value_area_position, "Profile context"],
                    ["ATR percentile", signedFeatures.atr_percentile ?? featureSnapshot.atr_percentile, "Volatility rank"],
                    ["Price vs EMA", signedFeatures.price_vs_ema ?? featureSnapshot.price_vs_ema, "Trend context"],
                    ["Quote age", signedFeatures.quote_age_seconds ?? featureSnapshot.quote_age_seconds, "Execution freshness"],
                  ] as Array<[string, unknown, string]>
                  ).map(([label, value, context]) => (
                    <DataRow
                      key={label}
                      cells={[
                        <span key="label" className="font-medium text-zinc-100">
                          {label}
                        </span>,
                        <span key="value" className="text-zinc-200">
                          {formatText(value)}
                        </span>,
                        <span key="context" className="text-zinc-500">
                          {context}
                        </span>,
                      ]}
                    />
                  ))}
                </DataTable>
              </div>
            ) : (
              <EmptyState title="No executor snapshot" description="The trade review bundle did not include an executor snapshot." />
            )}
          </Panel>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <Panel eyebrow="Evidence" title="Raw tape and lifecycle" description="Switch to raw mode for the tape, order lifecycle, events, and timeline.">
            {mode === "raw" ? (
              <div className="space-y-4">
                <DataTable columns={["Time", "Bid", "Ask", "Last"]}>
                  {bundle.marketTape.length === 0 ? (
                    <EmptyState title="No market tape" description="No market tape rows were captured in the trade window." />
                  ) : (
                    bundle.marketTape.slice(0, 16).map((row) => (
                      <DataRow
                        key={row.id}
                        cells={[
                          <span key="time">{formatDate(row.capturedAt)}</span>,
                          <span key="bid">{formatText(row.bid)}</span>,
                          <span key="ask">{formatText(row.ask)}</span>,
                          <span key="last">{formatText(row.last)}</span>,
                        ]}
                      />
                    ))
                  )}
                </DataTable>

                <DataTable columns={["Time", "Order", "Status", "Reason"]}>
                  {bundle.orderLifecycle.length === 0 ? (
                    <EmptyState title="No order lifecycle" description="The trade did not produce an order lifecycle row in the review window." />
                  ) : (
                    bundle.orderLifecycle.slice(0, 16).map((row) => (
                      <DataRow
                        key={row.id}
                        cells={[
                          <span key="time">{formatDate(row.observedAt)}</span>,
                          <span key="order">{row.orderId ?? row.tradeId ?? "—"}</span>,
                          <span key="status">{row.status ?? "—"}</span>,
                          <span key="reason">{row.reason ?? "—"}</span>,
                        ]}
                      />
                    ))
                  )}
                </DataTable>
              </div>
            ) : (
              <div className="space-y-3">
                {bundle.timeline.length ? (
                  bundle.timeline.slice(0, 10).map((item, index) => (
                    <div key={`${item.kind}-${item.timestamp ?? index}`} className="rounded-2xl border border-zinc-800 bg-zinc-950/80 px-4 py-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone={item.kind === "trade" ? "success" : item.kind === "decision_snapshot" ? "accent" : "neutral"}>{item.kind}</Badge>
                        <span className="text-xs text-zinc-500">{formatDate(item.timestamp ?? null)}</span>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-zinc-200">
                        {String(item.reason ?? item.outcome_reason ?? item.guard_reason ?? item.action ?? item.event_type ?? "timeline entry")}
                      </p>
                    </div>
                  ))
                ) : (
                  <EmptyState title="No timeline entries" description="The review bundle did not return a merged timeline." />
                )}
              </div>
            )}
          </Panel>

          <Panel eyebrow="Audit" title="Decision and event trail" description="The executor's decision snapshots and the surrounding event stream.">
            {mode === "raw" ? (
              <div className="space-y-4">
                <DataTable columns={["Time", "Decision", "Outcome", "Gap"]}>
                  {bundle.decisionSnapshots.length === 0 ? (
                    <EmptyState title="No decision snapshots" description="The trade did not produce decision snapshots in the review window." />
                  ) : (
                    bundle.decisionSnapshots.slice(0, 12).map((row) => (
                      <DataRow
                        key={row.id}
                        cells={[
                          <span key="time">{formatDate(row.decidedAt)}</span>,
                          <span key="decision">{row.decisionId}</span>,
                          <span key="outcome">{row.outcome ?? "—"}</span>,
                          <span key="gap">{formatText(row.scoreGap)}</span>,
                        ]}
                      />
                    ))
                  )}
                </DataTable>

                <DataTable columns={["Time", "Type", "Action", "Reason"]}>
                  {bundle.events.length === 0 ? (
                    <EmptyState title="No events" description="The review bundle did not include events for this trade window." />
                  ) : (
                    bundle.events.slice(0, 12).map((row) => (
                      <DataRow
                        key={row.id}
                        cells={[
                          <span key="time">{formatDate(row.eventTimestamp)}</span>,
                          <span key="type">{row.eventType ?? "—"}</span>,
                          <span key="action">{row.action ?? "—"}</span>,
                          <span key="reason">{row.reason ?? "—"}</span>,
                        ]}
                      />
                    ))
                  )}
                </DataTable>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="rounded-2xl border border-zinc-800 bg-zinc-950/80 p-4">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-cyan-300">Market context</p>
                  <p className="mt-3 text-sm leading-6 text-zinc-300">
                    {analysis?.marketContext.stats ? `Window samples: ${analysis.marketContext.sampleCount}.` : "No market context summary available."}
                  </p>
                  {analysis?.marketNotes.length ? (
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-zinc-300">
                      {analysis.marketNotes.map((note) => (
                        <li key={note} className="rounded-xl border border-zinc-800 bg-black/20 px-3 py-2">
                          {note}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </div>
                <div className="rounded-2xl border border-zinc-800 bg-zinc-950/80 p-4">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-cyan-300">Execution notes</p>
                  <ul className="mt-3 space-y-2 text-sm leading-6 text-zinc-300">
                    {(analysis?.executionNotes ?? []).map((note) => (
                      <li key={note} className="rounded-xl border border-zinc-800 bg-black/20 px-3 py-2">
                        {note}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-2xl border border-zinc-800 bg-zinc-950/80 p-4">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-cyan-300">Narrative</p>
                  <ul className="mt-3 space-y-2 text-sm leading-6 text-zinc-300">
                    {(analysis?.narrative ?? []).map((note) => (
                      <li key={note} className="rounded-xl border border-zinc-800 bg-black/20 px-3 py-2">
                        {note}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </Panel>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <Panel eyebrow="State" title="Account and run context" description="The trade review should always show which account and run produced the evidence.">
            <div className="flex flex-wrap gap-2">
              <Badge tone={trade.accountMode === "live" ? "success" : "warning"}>{trade.accountName ?? trade.accountId ?? "unknown account"}</Badge>
              <Badge tone="neutral">{trade.accountMode ?? "unknown mode"}</Badge>
              <Badge tone="accent">{run?.symbol ?? "ES"}</Badge>
              <Badge tone="neutral">{run?.runId ?? trade.runId}</Badge>
            </div>
            <div className="mt-4 grid gap-3 text-sm text-zinc-300 sm:grid-cols-2">
              <p>Broker trade id: {trade.tradeId ?? "—"}</p>
              <p>Position id: {trade.positionId ?? "—"}</p>
              <p>Decision id: {trade.decisionId ?? "—"}</p>
              <p>Attempt id: {trade.attemptId ?? "—"}</p>
            </div>
            <pre className="mt-4 max-h-[20rem] overflow-auto rounded-2xl border border-zinc-800 bg-black/40 p-4 text-xs leading-6 text-zinc-300">
              {JSON.stringify(trade.payloadJson ?? {}, null, 2)}
            </pre>
          </Panel>

          <Panel eyebrow="Backfill" title="State and blocker context" description="Useful when the trade reviewer needs to explain why a decision changed.">
            <div className="space-y-3">
              {bundle.blockers.length ? (
                bundle.blockers.slice(0, 8).map((item, index) => (
                  <div key={`${item.kind}-${item.timestamp ?? index}`} className="rounded-2xl border border-zinc-800 bg-zinc-950/80 px-4 py-3 text-sm leading-6 text-zinc-300">
                    {String(item.reason ?? item.outcome_reason ?? item.guard_reason ?? item.action ?? item.event_type ?? "blocker")}
                  </div>
                ))
              ) : (
                <EmptyState title="No blockers" description="The reconstructed timeline does not show obvious blockers for this trade." />
              )}
              {bundle.stateSnapshots.length ? (
                <DataTable columns={["Time", "Status", "Position", "Risk"]}>
                  {bundle.stateSnapshots.slice(0, 6).map((row) => (
                    <DataRow
                      key={row.id}
                      cells={[
                        <span key="time">{formatDate(row.capturedAt)}</span>,
                        <span key="status">{row.status ?? "—"}</span>,
                        <span key="position">{formatText(row.position)}</span>,
                        <span key="risk">{row.riskState ?? "—"}</span>,
                      ]}
                    />
                  ))}
                </DataTable>
              ) : null}
            </div>
          </Panel>
        </section>
      </main>
    </PageShell>
  );
}
