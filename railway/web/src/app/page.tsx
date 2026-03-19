import Link from "next/link";

import { EmptyState, KpiCard, MiniBarChart, Panel, StatusPill, formatCurrency, formatDate, formatShort } from "@/components/dashboard";
import { PageShell } from "@/components/page-shell";
import {
  fetchAccountSummaries,
  fetchAccountTrades,
  fetchBridgeFailures,
  fetchDashboardData,
  fetchRunDetail,
  fetchServiceHealth,
  isSyntheticRunId,
} from "@/lib/analytics";
import { isSignedInRequest } from "@/lib/session";

function toneForMode(mode: string | null) {
  if (mode === "practice") {
    return "warning" as const;
  }
  if (mode === "live") {
    return "success" as const;
  }
  return "neutral" as const;
}

function toneForBridge(status: string | null) {
  const normalized = (status ?? "").toLowerCase();
  if (normalized.includes("error") || normalized.includes("fail") || normalized.includes("down")) {
    return "danger" as const;
  }
  if (normalized.includes("ok") || normalized.includes("healthy") || normalized.includes("running") || normalized.includes("success")) {
    return "success" as const;
  }
  return "warning" as const;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function positionLabel(position: number | null | undefined) {
  if (position === null || position === undefined || position === 0) {
    return "flat";
  }
  return position > 0 ? `long ${formatShort(position)}` : `short ${formatShort(Math.abs(position))}`;
}

function winRate(trades: Array<{ profitAndLoss: number | null }>) {
  if (!trades.length) {
    return 0;
  }
  const winners = trades.filter((trade) => (trade.profitAndLoss ?? 0) > 0).length;
  return Math.round((winners / trades.length) * 100);
}

function quickLink({
  href,
  label,
}: {
  href: string;
  label: string;
}) {
  return (
    <Link
      href={href}
      className="inline-flex items-center justify-between rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-zinc-200 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-white"
    >
      <span>{label}</span>
      <span className="text-zinc-500">→</span>
    </Link>
  );
}

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{
    q?: string;
    runId?: string;
  }>;
}) {
  const signedIn = await isSignedInRequest();
  const params = await searchParams;
  const requestedRunId = (params.runId || "").trim();

  if (!signedIn) {
    return <PageShell authenticated={false} />;
  }

  const [dashboard, accountSummaries, accountTrades, bridgeFailures, serviceHealth] = await Promise.all([
    fetchDashboardData(),
    fetchAccountSummaries(),
    fetchAccountTrades({ limit: 12 }),
    fetchBridgeFailures(),
    fetchServiceHealth(),
  ]);

  if (!dashboard) {
    return (
      <PageShell authenticated>
        <main className="mx-auto max-w-7xl px-6 py-10 lg:px-8">
          <Panel eyebrow="Dashboard" title="No analytics data yet">
            <p className="text-sm text-zinc-400">Set `ANALYTICS_API_URL` and `ANALYTICS_API_KEY` on the web service.</p>
          </Panel>
        </main>
      </PageShell>
    );
  }

  const realRuns = dashboard.runs.filter((run) => !isSyntheticRunId(run.runId));
  const selectedRunId = requestedRunId || realRuns[0]?.runId || dashboard.runs[0]?.runId || null;
  const activeRun = selectedRunId ? await fetchRunDetail(selectedRunId) : null;
  const latestDecision = activeRun?.decisionSnapshots[0] ?? null;
  const latestAccountSummary = accountSummaries[0] ?? null;
  const latestRunTrade = activeRun?.trades[0] ?? null;
  const latestAccountTrade = accountTrades[0] ?? null;
  const bridgeSnapshot = asRecord(serviceHealth?.bridge);
  const bridgeStatus = asString(bridgeSnapshot.bridge_status ?? bridgeSnapshot.bridgeStatus) ?? bridgeFailures[0]?.bridgeStatus ?? "unknown";
  const bridgeQueueDepth = asNumber(bridgeSnapshot.queue_depth ?? bridgeSnapshot.queueDepth) ?? bridgeFailures[0]?.queueDepth ?? null;
  const lastHeartbeat =
    asString(bridgeSnapshot.last_success_at ?? bridgeSnapshot.lastSuccessAt) ??
    serviceHealth?.runtimeLogs?.latestLoggedAt ??
    dashboard.summary.latest_run_seen_at;
  const currentPnl = activeRun?.run?.dailyPnl ?? latestAccountSummary?.realizedPnl ?? dashboard.summary.total_pnl ?? 0;
  const currentPosition = activeRun?.run?.position ?? null;
  const scoreGap = latestDecision?.scoreGap ?? null;
  const dominantBias = latestDecision?.dominantSide ?? (scoreGap === null ? "flat" : scoreGap > 0 ? "long" : "short");
  const accountTradeBars = accountTrades.slice(0, 8).map((trade) => trade.profitAndLoss ?? 0);
  const accountTradeLabels = accountTrades.slice(0, 8).map((trade) => trade.accountName ?? trade.contractId ?? trade.brokerTradeId);
  const winRateValue = winRate(accountTrades);
  const latestTradeReviewId = latestRunTrade?.tradeId ?? latestRunTrade?.id ?? latestAccountTrade?.id ?? null;

  return (
    <PageShell authenticated>
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-5 sm:px-6 lg:px-8">
        <Panel eyebrow="Dashboard" title="Live pulse">
          <div className="flex flex-wrap gap-2">
            <StatusPill label="Bridge" value={bridgeStatus} tone={toneForBridge(bridgeStatus)} />
            <StatusPill label="Account" value={latestAccountSummary?.accountMode ?? "unknown"} tone={toneForMode(latestAccountSummary?.accountMode)} />
            <StatusPill label="Run" value={selectedRunId ?? "none"} tone={selectedRunId ? "accent" : "neutral"} />
            <StatusPill label="Heartbeat" value={formatDate(lastHeartbeat)} tone={bridgeStatus.toLowerCase().includes("error") ? "danger" : "neutral"} />
            {bridgeQueueDepth !== null ? <StatusPill label="Queue" value={formatShort(bridgeQueueDepth)} tone={bridgeQueueDepth > 0 ? "warning" : "success"} /> : null}
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <KpiCard label="Today P/L" value={formatCurrency(currentPnl)} tone={currentPnl >= 0 ? "success" : "danger"} />
            <KpiCard label="Position" value={positionLabel(currentPosition)} tone={currentPosition ? "accent" : "neutral"} />
            <KpiCard label="Score gap" value={scoreGap === null ? "—" : formatShort(scoreGap)} tone={scoreGap === null ? "neutral" : scoreGap >= 0 ? "success" : "warning"} />
            <KpiCard label="Bias" value={dominantBias ?? "flat"} tone={dominantBias === "long" ? "success" : dominantBias === "short" ? "warning" : "neutral"} />
            <KpiCard label="Win rate" value={`${formatShort(winRateValue)}%`} tone={winRateValue >= 50 ? "success" : "warning"} />
          </div>
        </Panel>

        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <Panel eyebrow="Equity" title="Recent account P/L">
            {accountTrades.length ? (
              <MiniBarChart values={accountTradeBars} labels={accountTradeLabels} />
            ) : (
              <EmptyState title="No account trades" description="Ledger backfill has not populated yet." />
            )}
          </Panel>

          <Panel eyebrow="Shortcuts" title="Open surfaces">
            <div className="grid gap-3 sm:grid-cols-2">
              {quickLink({ href: "/chart", label: "Chart" })}
              {quickLink({ href: "/accounts", label: "Accounts" })}
              {quickLink({ href: "/advisory", label: "Advisory" })}
              {quickLink({ href: "/system", label: "System" })}
              {latestTradeReviewId ? quickLink({ href: `/trades/${latestTradeReviewId}`, label: "Latest trade review" }) : null}
              {selectedRunId ? quickLink({ href: `/runs/${selectedRunId}`, label: "Latest run" }) : null}
            </div>

            <div className="mt-6 rounded-xl border border-zinc-800 bg-zinc-950 p-4">
              <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Current run</p>
              <p className="mt-2 font-mono text-sm text-zinc-100">{selectedRunId ?? "No run selected"}</p>
              <p className="mt-1 text-sm text-zinc-500">
                {latestDecision?.dominantSide ? `Bias ${latestDecision.dominantSide}` : "No decision snapshot"}
              </p>
            </div>
          </Panel>
        </section>
      </main>
    </PageShell>
  );
}
