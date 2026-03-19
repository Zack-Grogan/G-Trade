import { Badge, DataRow, DataTable, EmptyState, KpiCard, Panel, StatusPill, formatDate, formatShort } from "@/components/dashboard";
import { PageShell } from "@/components/page-shell";
import { fetchBridgeFailures, fetchDashboardData, fetchServiceHealth } from "@/lib/analytics";
import { isSignedInRequest } from "@/lib/session";

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function toneForStatus(status: string | null) {
  const normalized = (status ?? "").toLowerCase();
  if (normalized.includes("ok") || normalized.includes("healthy") || normalized.includes("running") || normalized.includes("success")) {
    return "success" as const;
  }
  if (normalized.includes("error") || normalized.includes("fail") || normalized.includes("down")) {
    return "danger" as const;
  }
  return "warning" as const;
}

export default async function SystemPage() {
  const signedIn = await isSignedInRequest();
  const [dashboard, serviceHealth, bridgeFailures] = signedIn
    ? await Promise.all([fetchDashboardData(), fetchServiceHealth(), fetchBridgeFailures()])
    : [null, null, []];

  if (!signedIn) {
    return <PageShell authenticated={false} />;
  }

  if (!serviceHealth) {
    return (
      <PageShell authenticated>
        <main className="mx-auto max-w-7xl px-6 py-10 lg:px-8">
          <Panel eyebrow="System" title="No health data yet">
            <p className="text-sm text-zinc-400">Set `ANALYTICS_API_URL` and `ANALYTICS_API_KEY` on the web service.</p>
          </Panel>
        </main>
      </PageShell>
    );
  }

  const analyticsPool = asRecord(serviceHealth.analytics?.pool);
  const bridge = asRecord(serviceHealth.bridge);
  const latestReport = dashboard?.reports[0] ?? null;
  const analyticsStatus = serviceHealth.analytics?.status ?? "unknown";
  const bridgeStatus = asString(bridge.bridge_status ?? bridge.bridgeStatus) ?? "unknown";
  const queueDepth = asNumber(bridge.queue_depth ?? bridge.queueDepth);
  const latestHeartbeat = asString(bridge.last_success_at ?? bridge.lastSuccessAt) ?? serviceHealth.runtimeLogs?.latestLoggedAt ?? null;
  const latestReportAt = asString(latestReport?.completedAt ?? latestReport?.createdAt ?? serviceHealth.reports?.latestCreatedAt) ?? null;
  const runtimeLogs = serviceHealth.runtimeLogs?.count ?? 0;
  const reportCount = serviceHealth.reports?.count ?? 0;

  return (
    <PageShell authenticated>
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-5 sm:px-6 lg:px-8">
        <Panel eyebrow="System" title="Health">
          <div className="flex flex-wrap gap-2">
            <StatusPill label="Analytics" value={analyticsStatus} tone={toneForStatus(analyticsStatus)} />
            <StatusPill label="Bridge" value={bridgeStatus} tone={toneForStatus(bridgeStatus)} />
            <StatusPill label="Runtime logs" value={formatShort(runtimeLogs)} tone={runtimeLogs > 0 ? "success" : "warning"} />
            <StatusPill label="Reports" value={formatShort(reportCount)} tone={reportCount > 0 ? "accent" : "neutral"} />
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard label="Queue depth" value={queueDepth === null ? "—" : formatShort(queueDepth)} tone={queueDepth && queueDepth > 0 ? "warning" : "success"} />
            <KpiCard label="Latest heartbeat" value={formatDate(latestHeartbeat)} />
            <KpiCard label="Latest report" value={formatDate(latestReportAt)} />
            <KpiCard label="Bridge errors" value={formatShort(bridgeFailures.length)} tone={bridgeFailures.length ? "danger" : "success"} />
          </div>
        </Panel>

        <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <Panel eyebrow="Analytics" title="Pool state">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              <KpiCard label="Min conn" value={String(analyticsPool.pool_minconn ?? "—")} />
              <KpiCard label="Max conn" value={String(analyticsPool.pool_maxconn ?? "—")} />
              <KpiCard label="Available" value={String(analyticsPool.pool_available ?? "—")} />
              <KpiCard label="Borrowed" value={String(analyticsPool.pool_borrowed ?? "—")} />
              <KpiCard label="Closed" value={String(analyticsPool.pool_closed ?? "—")} />
            </div>
          </Panel>

          <Panel eyebrow="Bridge" title="Failure log">
            <DataTable columns={["Time", "Status", "Queue", "Error"]}>
              {bridgeFailures.length === 0 ? (
                <EmptyState title="No bridge failures" description="The bridge has not reported an active failure." />
              ) : (
                bridgeFailures.slice(0, 6).map((failure) => (
                  <DataRow
                    key={failure.id}
                    cells={[
                      <span key="time">{formatDate(failure.observedAt)}</span>,
                      <Badge key="status" tone={toneForStatus(failure.bridgeStatus)}>
                        {failure.bridgeStatus ?? "unknown"}
                      </Badge>,
                      <span key="queue" className="tabular-nums">
                        {failure.queueDepth === null ? "—" : formatShort(failure.queueDepth)}
                      </span>,
                      <span key="error" className="truncate">
                        {failure.lastError ?? "—"}
                      </span>,
                    ]}
                  />
                ))
              )}
            </DataTable>
          </Panel>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <Panel eyebrow="Reports" title="Latest report metadata">
            {latestReport ? (
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  <Badge tone="accent">{latestReport.status}</Badge>
                  <Badge tone="neutral">{latestReport.reportType}</Badge>
                  <Badge tone="neutral">{latestReport.modelProvider}</Badge>
                </div>
                <p className="text-sm font-medium text-zinc-100">{latestReport.title}</p>
                <p className="text-sm text-zinc-400">{latestReport.modelName}</p>
                <p className="text-xs text-zinc-500">{formatDate(latestReport.completedAt ?? latestReport.createdAt)}</p>
              </div>
            ) : (
              <EmptyState title="No reports yet" description="Report bundles appear here once RLM persists them." />
            )}
          </Panel>

          <Panel eyebrow="Heartbeat" title="Bridge status">
            <div className="space-y-3 text-sm text-zinc-300">
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 px-4 py-3">
                <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Run</p>
                <p className="mt-1 font-mono text-zinc-100">{asString(bridge.run_id ?? bridge.runId) ?? "—"}</p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 px-4 py-3">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Last flush</p>
                  <p className="mt-1 text-zinc-100">{formatDate(asString(bridge.last_flush_at ?? bridge.lastFlushAt))}</p>
                </div>
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 px-4 py-3">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Last success</p>
                  <p className="mt-1 text-zinc-100">{formatDate(asString(bridge.last_success_at ?? bridge.lastSuccessAt))}</p>
                </div>
              </div>
            </div>
          </Panel>
        </section>
      </main>
    </PageShell>
  );
}
