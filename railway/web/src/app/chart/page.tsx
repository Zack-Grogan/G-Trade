import Link from "next/link";

import { Badge, DataRow, DataTable, EmptyState, Panel, formatCurrency, formatDate, formatShort } from "@/components/dashboard";
import { LiveMarketChart } from "@/components/live-market-chart";
import { LiveRefresh } from "@/components/live-refresh";
import type { ChartMarker, ChartReferenceLine } from "@/components/market-chart";
import { PageShell } from "@/components/page-shell";
import { fetchAccountSummaries, fetchAccountTrades, fetchDashboardData, fetchRunDetail, isSyntheticRunId } from "@/lib/analytics";
import { isSignedInRequest } from "@/lib/session";

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function pickIndicator(featureSnapshot: Record<string, unknown>, diagnostics: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    const candidate = diagnostics[key] ?? featureSnapshot[key];
    if (candidate !== undefined && candidate !== null && candidate !== "") {
      return candidate;
    }
  }
  return null;
}

function formatMetric(value: unknown): string {
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

export default async function ChartPage({
  searchParams,
}: {
  searchParams: Promise<{
    runId?: string;
  }>;
}) {
  const signedIn = await isSignedInRequest();
  if (!signedIn) {
    return <PageShell authenticated={false} />;
  }

  const params = await searchParams;
  const requestedRunId = (params.runId || "").trim();
  const [dashboard, accountSummaries, accountTrades] = await Promise.all([
    fetchDashboardData(),
    fetchAccountSummaries(),
    fetchAccountTrades({ limit: 16 }),
  ]);

  if (!dashboard) {
    return (
      <PageShell authenticated>
        <main className="mx-auto max-w-7xl px-6 py-10 lg:px-8">
          <Panel eyebrow="Chart" title="No analytics data yet">
            <p className="text-sm text-zinc-400">Set `ANALYTICS_API_URL` and `ANALYTICS_API_KEY` on the web service.</p>
          </Panel>
        </main>
      </PageShell>
    );
  }

  const realRuns = dashboard.runs.filter((run) => !isSyntheticRunId(run.runId));
  const selectedRunId = requestedRunId || realRuns[0]?.runId || dashboard.runs[0]?.runId || null;
  const runDetail = selectedRunId ? await fetchRunDetail(selectedRunId) : null;
  const run = runDetail?.run ?? null;
  const latestDecision = runDetail?.decisionSnapshots[0] ?? null;
  const latestSnapshot = runDetail?.stateSnapshots[0] ?? null;
  const latestTrade = runDetail?.trades[0] ?? null;
  const latestAccountSummary = accountSummaries[0] ?? null;
  const latestAccountTrade = accountTrades[0] ?? null;
  const marketSeries = runDetail?.marketTape ?? [];
  const featureSnapshot = asRecord(latestDecision?.featureSnapshot);
  const diagnostics = asRecord(featureSnapshot.diagnostics);
  const signedFeatures = asRecord(featureSnapshot.signed_features ?? featureSnapshot.signedFeatures);
  const currentPrice = asNumber(latestDecision?.currentPrice) ?? asNumber(diagnostics.current_price) ?? marketSeries[0]?.last ?? marketSeries[0]?.bid ?? marketSeries[0]?.ask ?? null;

  const pricePoints = marketSeries
    .slice()
    .reverse()
    .map((row) => ({
      timestamp: row.capturedAt,
      value: row.last ?? row.bid ?? row.ask,
    }))
    .filter((point) => point.value !== null);

  const referenceLines: ChartReferenceLine[] = [
    { label: "Decision", value: latestDecision?.decisionPrice ?? latestSnapshot?.decisionPrice ?? null, tone: "accent" as const },
    { label: "VWAP", value: asNumber(diagnostics.rth_vwap) ?? asNumber(diagnostics.eth_vwap) ?? null, tone: "neutral" as const },
    { label: "POC", value: asNumber(diagnostics.poc), tone: "success" as const },
    { label: "VAH", value: asNumber(diagnostics.vah), tone: "warning" as const },
    { label: "VAL", value: asNumber(diagnostics.val), tone: "warning" as const },
  ].filter((line) => line.value !== null);

  const markers: ChartMarker[] = [];
  if (latestTrade?.entryTime && latestTrade.entryPrice) {
    markers.push({ label: "Entry", timestamp: latestTrade.entryTime, value: latestTrade.entryPrice, tone: latestTrade.direction >= 0 ? "success" : "warning" });
  }
  if (latestTrade?.exitTime && latestTrade.exitPrice) {
    markers.push({ label: "Exit", timestamp: latestTrade.exitTime, value: latestTrade.exitPrice, tone: "accent" });
  }

  let cumulativeAccountPnl = 0;
  const accountPoints = accountTrades
    .slice()
    .reverse()
    .map((trade) => {
      cumulativeAccountPnl += trade.profitAndLoss ?? 0;
      return {
        timestamp: trade.occurredAt,
        value: cumulativeAccountPnl,
      };
    })
    .filter((point) => point.value !== null);
  const ledgerMode = marketSeries.length === 0 && accountPoints.length > 0;
  const chartPoints = ledgerMode ? accountPoints : pricePoints;
  const chartMarkers: ChartMarker[] = ledgerMode && latestAccountTrade
    ? [
        {
          label: latestAccountTrade.brokerTradeId.slice(-8) || latestAccountTrade.brokerTradeId,
          timestamp: latestAccountTrade.occurredAt,
          value: chartPoints.at(-1)?.value ?? latestAccountTrade.profitAndLoss ?? 0,
          tone: (latestAccountTrade.profitAndLoss ?? 0) >= 0 ? "success" : "warning",
        },
      ]
    : markers;
  const chartReferenceLines: ChartReferenceLine[] = ledgerMode
    ? [
        { label: "Break-even", value: 0, tone: "neutral" as const },
        { label: "Realized PnL", value: latestAccountSummary?.realizedPnl ?? null, tone: (latestAccountSummary?.realizedPnl ?? 0) >= 0 ? "success" as const : "warning" as const },
      ].filter((line) => line.value !== null)
    : referenceLines;

  const currentMetricValue = ledgerMode ? chartPoints.at(-1)?.value ?? latestAccountSummary?.realizedPnl ?? 0 : currentPrice;
  const executorProjection = [
    latestDecision?.dominantSide ? `Bias ${latestDecision.dominantSide}` : null,
    latestDecision?.allowEntries === false ? "Entries blocked" : latestDecision?.allowEntries ? "Entries allowed" : null,
    latestDecision?.executionTradeable === false ? "Not tradeable" : latestDecision?.executionTradeable ? "Tradeable" : null,
    latestDecision?.regimeState ? `Regime ${latestDecision.regimeState}` : null,
    latestDecision?.activeSession ? `Session ${latestDecision.activeSession}` : null,
    latestDecision?.scoreGap !== null && latestDecision?.scoreGap !== undefined ? `Gap ${Number(latestDecision.scoreGap).toFixed(2)}` : null,
    asNumber(diagnostics.atr_value) !== null ? `ATR ${asNumber(diagnostics.atr_value)?.toFixed(2)}` : null,
    asNumber(diagnostics.rsi) !== null ? `RSI ${asNumber(diagnostics.rsi)?.toFixed(1)}` : null,
    asNumber(diagnostics.spread) !== null ? `Spread ${asNumber(diagnostics.spread)?.toFixed(2)}` : null,
    ledgerMode ? `Ledger ${latestAccountSummary?.accountName ?? latestAccountSummary?.accountId ?? "active"}` : null,
  ].filter((item): item is string => Boolean(item));

  const indicatorRows: Array<[string, unknown]> = [
    ["Price", currentPrice],
    ["ATR", pickIndicator(featureSnapshot, diagnostics, ["atr_value", "atr", "atrValue"])],
    ["RSI", pickIndicator(featureSnapshot, diagnostics, ["rsi", "rsi_value", "rsiValue"])],
    ["RTH VWAP", pickIndicator(featureSnapshot, diagnostics, ["rth_vwap", "rthVwap"])],
    ["ETH VWAP", pickIndicator(featureSnapshot, diagnostics, ["eth_vwap", "ethVwap"])],
    ["POC", pickIndicator(featureSnapshot, diagnostics, ["poc"])],
    ["VAH", pickIndicator(featureSnapshot, diagnostics, ["vah"])],
    ["VAL", pickIndicator(featureSnapshot, diagnostics, ["val"])],
    ["EMA slope", pickIndicator(featureSnapshot, diagnostics, ["ema", "ema_slope", "emaSlope"])],
    ["Price vs EMA", pickIndicator(featureSnapshot, diagnostics, ["price_vs_ema", "priceVsEma"])],
    ["Value area", signedFeatures.value_area_position ?? featureSnapshot.value_area_position],
    ["ATR pct", signedFeatures.atr_percentile ?? featureSnapshot.atr_percentile],
    ["Quote age", signedFeatures.quote_age_seconds ?? featureSnapshot.quote_age_seconds],
    ["Spread", signedFeatures.spread_ticks ?? featureSnapshot.spread_ticks],
    ["Bias", latestDecision?.dominantSide],
    ["Gap", latestDecision?.scoreGap],
    ["Entries", latestDecision?.allowEntries],
    ["Tradeable", latestDecision?.executionTradeable],
    ["Regime", latestDecision?.regimeState],
  ];

  const chartLabel = run?.accountName ?? latestAccountSummary?.accountName ?? latestAccountSummary?.accountId ?? "Unknown account";
  const chartTitle = ledgerMode ? "Account performance chart" : "Price chart";
  const latestReviewTradeId = latestTrade?.tradeId ?? latestTrade?.id ?? latestAccountTrade?.brokerTradeId ?? latestAccountTrade?.id ?? null;

  return (
    <PageShell authenticated>
      <LiveRefresh intervalMs={15000} />
      <main className="mx-auto max-w-[1600px] space-y-5 px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div className="min-w-0">
            <p className="text-[11px] uppercase tracking-[0.24em] text-cyan-300">Chart</p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-50">Lightweight chart</h1>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={run?.accountMode === "live" ? "success" : "warning"}>{chartLabel}</Badge>
            <Badge tone="accent">{run?.accountMode ?? latestAccountSummary?.accountMode ?? "unknown mode"}</Badge>
            <Badge tone="neutral">{run?.symbol ?? "ES"}</Badge>
            <Link href="/runs" className="inline-flex items-center rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-white">
              Runs
            </Link>
            {latestReviewTradeId ? (
              <Link href={`/trades/${latestReviewTradeId}`} className="inline-flex items-center rounded-md border border-cyan-500/30 bg-cyan-500/15 px-3 py-2 text-sm text-cyan-100 transition hover:bg-cyan-500/20">
                Trade review
              </Link>
            ) : null}
          </div>
        </header>

        <section className="rounded-xl border border-zinc-800/80 bg-zinc-950 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800/80 pb-3">
            <div className="min-w-0">
              <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">{ledgerMode ? "Ledger fallback" : "Market tape"}</p>
            </div>
            <div className="flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.18em] text-zinc-500">
              <span className="rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1">{formatDate(run?.lastSeenAt ?? run?.createdAt ?? latestAccountSummary?.latestTradeAt ?? latestAccountSummary?.latestRunSeenAt)}</span>
              <span className="rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1">{ledgerMode ? "ledger fallback" : `${formatShort(marketSeries.length)} tape rows`}</span>
            </div>
          </div>

          <div className="mt-4">
            <LiveMarketChart title={chartTitle} points={chartPoints} markers={chartMarkers} referenceLines={chartReferenceLines} height={560} />
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div className="min-w-0">
              <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">{ledgerMode ? "Latest ledger PnL" : "Current price"}</p>
              <p className="mt-1 truncate text-lg font-semibold text-zinc-50 tabular-nums">
                {currentMetricValue === null ? "—" : formatCurrency(currentMetricValue)}
              </p>
            </div>
            <div className="min-w-0">
              <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Executor bias</p>
              <p className="mt-1 truncate text-lg font-semibold text-zinc-50 tabular-nums">{latestDecision?.dominantSide ?? "—"}</p>
            </div>
            <div className="min-w-0">
              <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Score gap</p>
              <p className="mt-1 truncate text-lg font-semibold text-zinc-50 tabular-nums">
                {latestDecision?.scoreGap === null || latestDecision?.scoreGap === undefined ? "—" : formatShort(Number(latestDecision.scoreGap))}
              </p>
            </div>
            <div className="min-w-0">
              <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Tradeable</p>
              <p className="mt-1 truncate text-lg font-semibold text-zinc-50 tabular-nums">{latestDecision?.executionTradeable === null || latestDecision?.executionTradeable === undefined ? "—" : latestDecision.executionTradeable ? "yes" : "no"}</p>
            </div>
          </div>

          <details className="mt-4 rounded-lg border border-zinc-800/80 bg-zinc-950 p-4">
            <summary className="cursor-pointer list-none text-[11px] uppercase tracking-[0.24em] text-zinc-400">Indicators</summary>

            <div className="mt-4 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
              <DataTable columns={["Indicator", "Value"]}>
                {indicatorRows.map(([label, value]) => (
                  <DataRow
                    key={label}
                    cells={[
                      <span key="label" className="min-w-0 truncate font-medium text-zinc-100">
                        {label}
                      </span>,
                      <span key="value" className="min-w-0 truncate tabular-nums text-zinc-200">
                        {formatMetric(value)}
                      </span>,
                    ]}
                  />
                ))}
              </DataTable>

              <div className="space-y-2">
                {executorProjection.length ? (
                  executorProjection.map((line) => (
                    <p key={line} className="rounded-md border border-zinc-800/80 bg-zinc-950 px-3 py-2 text-sm text-zinc-200">
                      {line}
                    </p>
                  ))
                ) : (
                  <EmptyState title="No projection data" description="No decision snapshot." />
                )}
              </div>
            </div>
          </details>
        </section>
      </main>
    </PageShell>
  );
}
