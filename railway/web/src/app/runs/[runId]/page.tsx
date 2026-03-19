import Link from "next/link";
import { notFound } from "next/navigation";

import { Badge, DataRow, DataTable, EmptyState, MiniBarChart, Panel, formatCurrency, formatDate, formatShort } from "@/components/dashboard";
import { PageShell } from "@/components/page-shell";
import { fetchRunDetail } from "@/lib/analytics";
import { isSignedInRequest } from "@/lib/session";

function asText(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  return String(value);
}

function describeTimelineEntry(entry: Record<string, unknown>) {
  if (entry.kind === "state_snapshot") {
    const position = entry.position ?? entry.position_pnl ?? "—";
    const riskState = entry.risk_state ?? entry.riskState ?? "—";
    return `state ${entry.status ?? "unknown"} · pos ${position} · risk ${riskState}`;
  }
  if (entry.kind === "decision_snapshot") {
    return `${entry.outcome ?? "decision"} · ${entry.reason ?? entry.outcome_reason ?? "no reason"}`;
  }
  if (entry.kind === "order_lifecycle") {
    return `${entry.event_type ?? entry.eventType ?? "order"} · ${entry.status ?? "unknown"} · ${entry.reason ?? "no reason"}`;
  }
  if (entry.kind === "bridge_health") {
    return `bridge ${entry.bridge_status ?? "unknown"} · queue ${entry.queue_depth ?? "—"} · ${entry.last_error ?? "no error"}`;
  }
  if (entry.kind === "trade") {
    return `trade pnl ${asText(entry.pnl)} · ${asText(entry.zone)} · ${asText(entry.strategy)}`;
  }
  return [entry.event_type ?? entry.eventType ?? "event", entry.category ?? "unknown", entry.action ?? entry.reason ?? "—"].join(" · ");
}

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ runId: string }>;
}) {
  const signedIn = await isSignedInRequest();
  if (!signedIn) {
    return <PageShell authenticated={false} />;
  }

  const { runId } = await params;
  const data = await fetchRunDetail(runId);

  if (!data?.run) {
    notFound();
  }

  const tradeValues = data.trades.slice(0, 8).map((trade) => trade.pnl);
  const tradeLabels = data.trades.slice(0, 8).map((trade) => trade.id.toString());
  const latestSnapshot = data.stateSnapshots[0] ?? null;
  const latestDecision = data.decisionSnapshots[0] ?? null;
  const latestLifecycle = data.orderLifecycle[0] ?? null;
  const latestBridge = data.bridgeHealth[0] ?? null;

  return (
    <PageShell authenticated>
      <main className="mx-auto max-w-6xl space-y-6 px-6 py-10 lg:px-8">
      <Panel
        eyebrow="Run detail"
        title={data.run.runId}
        action={
          <div className="flex flex-wrap gap-2">
            <Link
              href="/"
              className="inline-flex items-center rounded-full border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-white"
            >
              Back to console
            </Link>
            <Link
              href={`/chart?runId=${encodeURIComponent(data.run.runId)}`}
              className="inline-flex items-center rounded-full border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-white"
            >
              Open chart
            </Link>
            <Link
              href="/accounts"
              className="inline-flex items-center rounded-full border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-white"
            >
              Accounts
            </Link>
            {data.trades[0] ? (
              <Link
                href={`/trades/${data.trades[0].tradeId ?? data.trades[0].id}`}
                className="inline-flex items-center rounded-full border border-cyan-500/30 bg-cyan-500/15 px-3 py-2 text-sm text-cyan-100 transition hover:bg-cyan-500/20"
              >
                Latest trade review
              </Link>
            ) : null}
          </div>
        }
      >
        <div className="flex flex-wrap gap-2">
          <Badge tone="neutral">{data.run.dataMode ?? "unknown"}</Badge>
          <Badge tone="accent">{data.run.symbol ?? "n/a"}</Badge>
          {data.run.accountName ? <Badge tone={data.run.accountMode === "practice" ? "warning" : "success"}>{data.run.accountName}</Badge> : null}
          {data.run.accountMode ? <Badge tone={data.run.accountMode === "practice" ? "warning" : "success"}>{data.run.accountMode}</Badge> : null}
          <Badge tone="success">{formatDate(data.run.createdAt)}</Badge>
        </div>
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <Panel eyebrow="Run facts" title="Metadata">
            <p className="text-sm text-zinc-300">Process: {asText(data.run.processId)}</p>
            <p className="mt-2 text-sm text-zinc-300">Mode: {asText(data.run.dataMode)}</p>
            <p className="mt-2 text-sm text-zinc-300">Symbol: {asText(data.run.symbol)}</p>
            <p className="mt-2 text-sm text-zinc-300">Account: {asText(data.run.accountName ?? data.run.accountId)}</p>
          </Panel>
          <Panel eyebrow="Trades" title="Closed trades">
            <p className="text-2xl font-semibold text-zinc-50">{formatShort(data.trades.length)}</p>
            <p className="mt-2 text-sm text-zinc-400">{formatCurrency(data.trades.reduce((sum, trade) => sum + trade.pnl, 0))}</p>
          </Panel>
          <Panel eyebrow="Events" title="Event count">
            <p className="text-2xl font-semibold text-zinc-50">{formatShort(data.events.length)}</p>
            <p className="mt-2 text-sm text-zinc-400">{formatShort(data.blockers.length)} blockers.</p>
          </Panel>
        </div>
      </Panel>

      <section className="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel eyebrow="Signal strip" title="Trade P&L">
          <MiniBarChart values={tradeValues} labels={tradeLabels} />
        </Panel>

        <Panel eyebrow="Payload" title="Payload JSON">
          <pre className="max-h-[24rem] overflow-auto rounded-2xl border border-zinc-800 bg-black/40 p-4 text-xs leading-6 text-zinc-300">
            {JSON.stringify(data.run.payloadJson ?? {}, null, 2)}
          </pre>
        </Panel>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-2">
        <Panel eyebrow="Current state" title="Latest snapshot">
          {latestSnapshot ? (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Badge tone="accent">{latestSnapshot.status ?? "unknown"}</Badge>
                <Badge tone="neutral">{latestSnapshot.zone ?? "no zone"}</Badge>
                <Badge tone="success">{latestSnapshot.riskState ?? "risk unknown"}</Badge>
              </div>
              <div className="grid gap-3 text-sm text-zinc-300 sm:grid-cols-2">
                <p>Position: {asText(latestSnapshot.position)}</p>
                <p>PnL: {formatCurrency(latestSnapshot.positionPnl ?? 0)}</p>
                <p>Daily PnL: {formatCurrency(latestSnapshot.dailyPnl ?? 0)}</p>
                <p>Last block: {asText(latestSnapshot.lastEntryBlockReason)}</p>
              </div>
              <pre className="max-h-[18rem] overflow-auto rounded-2xl border border-zinc-800 bg-black/40 p-4 text-xs leading-6 text-zinc-300">
                {JSON.stringify(latestSnapshot.payloadJson ?? {}, null, 2)}
              </pre>
            </div>
          ) : (
            <EmptyState title="No state snapshots" description="No trader snapshot yet." />
          )}
        </Panel>

        <Panel eyebrow="Decision trace" title="Latest decision">
          {latestDecision ? (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Badge tone={latestDecision.outcome === "order_submitted" ? "success" : latestDecision.outcome === "blocked" ? "warning" : "neutral"}>
                  {latestDecision.outcome ?? "unknown"}
                </Badge>
                <Badge tone="accent">{latestDecision.decisionId.slice(-8) || `D${latestDecision.id}`}</Badge>
                <Badge tone="neutral">{latestDecision.regimeState ?? "no regime"}</Badge>
              </div>
              <div className="grid gap-3 text-sm text-zinc-300 sm:grid-cols-2">
                <p>Decision: {asText(latestDecision.decisionId)}</p>
                <p>Reason: {asText(latestDecision.reason ?? latestDecision.outcomeReason)}</p>
                <p>Score gap: {asText(latestDecision.scoreGap)}</p>
                <p>Dominant side: {asText(latestDecision.dominantSide)}</p>
              </div>
              <pre className="max-h-[18rem] overflow-auto rounded-2xl border border-zinc-800 bg-black/40 p-4 text-xs leading-6 text-zinc-300">
                {JSON.stringify(latestDecision.payloadJson ?? {}, null, 2)}
              </pre>
            </div>
          ) : (
            <EmptyState title="No decision snapshots" description="No decision snapshot yet." />
          )}
        </Panel>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-2">
        <Panel eyebrow="Bridge health" title="Bridge diagnostics">
          {latestBridge ? (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Badge tone={latestBridge.bridgeStatus === "running" ? "success" : "warning"}>{latestBridge.bridgeStatus ?? "unknown"}</Badge>
                <Badge tone="neutral">Queue {asText(latestBridge.queueDepth)}</Badge>
                <Badge tone="accent">{formatDate(latestBridge.observedAt)}</Badge>
              </div>
              <div className="grid gap-3 text-sm text-zinc-300 sm:grid-cols-2">
                <p>Last flush: {formatDate(latestBridge.lastFlushAt)}</p>
                <p>Last success: {formatDate(latestBridge.lastSuccessAt)}</p>
              </div>
              <p className="rounded-2xl border border-zinc-800 bg-zinc-900/80 px-4 py-3 text-sm text-zinc-200">
                {latestBridge.lastError ?? "No bridge error recorded."}
              </p>
            </div>
          ) : (
            <EmptyState title="No bridge diagnostics" description="No bridge rows yet." />
          )}
        </Panel>

        <Panel eyebrow="Order lifecycle" title="Order events">
          {latestLifecycle ? (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Badge tone="neutral">{latestLifecycle.eventType ?? "unknown"}</Badge>
                <Badge tone={latestLifecycle.isProtective ? "warning" : "accent"}>{latestLifecycle.role ?? "role unknown"}</Badge>
                <Badge tone="success">{formatDate(latestLifecycle.observedAt)}</Badge>
              </div>
              <div className="grid gap-3 text-sm text-zinc-300 sm:grid-cols-2">
                <p>Order: {asText(latestLifecycle.orderId)}</p>
                <p>Status: {asText(latestLifecycle.status)}</p>
                <p>Reason: {asText(latestLifecycle.reason)}</p>
                <p>Protective: {latestLifecycle.isProtective === null ? "—" : latestLifecycle.isProtective ? "yes" : "no"}</p>
              </div>
              <pre className="max-h-[18rem] overflow-auto rounded-2xl border border-zinc-800 bg-black/40 p-4 text-xs leading-6 text-zinc-300">
                {JSON.stringify(latestLifecycle.payloadJson ?? {}, null, 2)}
              </pre>
            </div>
          ) : (
              <EmptyState title="No order lifecycle rows" description="No order evidence yet." />
            )}
          </Panel>
      </section>

      <section className="mt-6">
        <Panel eyebrow="Timeline" title="Run timeline">
          <DataTable columns={["Kind", "Time", "Detail", "Reason"]}>
            {data.timeline.length === 0 ? (
              <EmptyState title="No timeline entries" description="No timeline rows yet." />
            ) : (
              data.timeline.slice(0, 12).map((entry, index) => (
                <DataRow
                  key={`${entry.kind}-${entry.timestamp ?? index}`}
                  cells={[
                    <Badge key="kind" tone={entry.kind === "trade" ? "success" : entry.kind === "state_snapshot" ? "accent" : "neutral"}>
                      {entry.kind}
                    </Badge>,
                    <span key="time">{asText(entry.timestamp)}</span>,
                    <span key="detail" className="truncate">
                      {describeTimelineEntry(entry)}
                    </span>,
                    <span key="reason" className="truncate">
                      {asText((entry.reason as string | undefined) ?? (entry.guard_reason as string | undefined) ?? (entry.guardReason as string | undefined) ?? (entry.outcome_reason as string | undefined))}
                    </span>,
                  ]}
                />
              ))
            )}
          </DataTable>
        </Panel>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-2">
        <Panel eyebrow="Trades" title="Closed trades">
          <DataTable columns={["PnL", "Zone", "Strategy", "Exit"]}>
            {data.trades.length === 0 ? (
              <EmptyState title="No trades" description="No closed trades yet." />
            ) : (
              data.trades.slice(0, 8).map((trade) => (
                <DataRow
                  key={trade.id}
                  cells={[
                    <Link key="pnl" href={`/trades/${trade.tradeId ?? trade.id}`} className={trade.pnl >= 0 ? "text-emerald-300 transition hover:text-emerald-200" : "text-rose-300 transition hover:text-rose-200"}>
                      {formatCurrency(trade.pnl)}
                    </Link>,
                    <span key="zone">{trade.zone ?? "—"}</span>,
                    <span key="strategy">{trade.strategy ?? "—"}</span>,
                    <span key="exit">{formatDate(trade.exitTime ?? trade.entryTime)}</span>,
                  ]}
                />
              ))
            )}
          </DataTable>
        </Panel>
      </section>

      <section className="mt-6">
        <Panel eyebrow="Events" title="Latest telemetry">
          <DataTable columns={["Type", "Category", "Symbol", "Time"]}>
            {data.events.length === 0 ? (
              <EmptyState title="No events" description="No event rows yet." />
            ) : (
              data.events.slice(0, 8).map((event) => (
                <DataRow
                  key={event.id}
                  cells={[
                    <span key="type">{event.eventType ?? "—"}</span>,
                    <span key="category">{event.category ?? "—"}</span>,
                    <span key="symbol">{event.symbol ?? "—"}</span>,
                    <span key="time">{formatDate(event.eventTimestamp)}</span>,
                  ]}
                />
              ))
            )}
          </DataTable>
        </Panel>
      </section>
      </main>
    </PageShell>
  );
}
