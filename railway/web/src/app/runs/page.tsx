import Link from "next/link";

import { Badge, DataRow, DataTable, EmptyState, Panel, KpiCard, formatDate, formatShort } from "@/components/dashboard";
import { PageShell } from "@/components/page-shell";
import { fetchDashboardData, isSyntheticRunId } from "@/lib/analytics";
import { isSignedInRequest } from "@/lib/session";

function modeTone(mode: string | null) {
  if (mode === "practice") {
    return "warning" as const;
  }
  if (mode === "live") {
    return "success" as const;
  }
  return "neutral" as const;
}

function matchesQuery(run: { runId: string; accountName: string | null; accountId: string | null; symbol: string | null; status: string | null }, query: string) {
  if (!query) {
    return true;
  }

  const haystack = [run.runId, run.accountName, run.accountId, run.symbol, run.status].filter(Boolean).join(" ").toLowerCase();
  return haystack.includes(query.toLowerCase());
}

export default async function RunsPage({
  searchParams,
}: {
  searchParams: Promise<{
    q?: string;
  }>;
}) {
  const signedIn = await isSignedInRequest();
  const params = await searchParams;
  const query = (params.q || "").trim();
  const data = signedIn ? await fetchDashboardData() : null;

  if (!signedIn) {
    return <PageShell authenticated={false} />;
  }

  if (!data) {
    return (
      <PageShell authenticated>
        <main className="mx-auto max-w-6xl px-6 py-10 lg:px-8">
          <Panel eyebrow="Runs" title="No run data yet">
            <p className="text-sm text-zinc-400">Set `ANALYTICS_API_URL` and `ANALYTICS_API_KEY`.</p>
          </Panel>
        </main>
      </PageShell>
    );
  }

  const realRuns = data.runs.filter((run) => !isSyntheticRunId(run.runId));
  const syntheticRuns = data.runs.length - realRuns.length;
  const filteredRuns = realRuns.filter((run) => matchesQuery(run, query));
  const latestRun = filteredRuns[0] ?? realRuns[0] ?? null;

  return (
    <PageShell authenticated>
      <main className="mx-auto max-w-6xl space-y-6 px-6 py-10 lg:px-8">
        <Panel
          eyebrow="Runs"
          title="Run index"
          action={
            <Link
              href="/"
              className="inline-flex items-center rounded-full border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-white"
            >
              Console
            </Link>
          }
        >
          <div className="grid gap-4 sm:grid-cols-3">
            <KpiCard label="Visible" value={formatShort(realRuns.length)} />
            <KpiCard label="Hidden" value={formatShort(syntheticRuns)} tone={syntheticRuns > 0 ? "warning" : "neutral"} />
            <KpiCard label="Selected" value={latestRun?.runId ?? "none"} tone={latestRun ? "accent" : "neutral"} />
          </div>

          <form className="mt-5">
            <label className="block space-y-2">
              <span className="text-xs uppercase tracking-[0.22em] text-zinc-500">Search</span>
              <input
                name="q"
                defaultValue={query}
                placeholder="Run id, account, symbol, status"
                className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-cyan-500/30 focus:ring-2 focus:ring-cyan-500/10"
              />
            </label>
          </form>

          <div className="mt-4">
            {filteredRuns.length === 0 ? (
              <EmptyState title="No matching runs" description="Try a broader search or clear the filter." />
            ) : (
              <DataTable columns={["Run", "Account", "Mode", "Last seen"]}>
                {filteredRuns.slice(0, 12).map((run) => (
                  <DataRow
                    key={run.runId}
                    cells={[
                      <Link key="run" href={`/runs/${run.runId}`} className="font-mono text-xs text-zinc-100 transition hover:text-cyan-300">
                        {run.runId}
                      </Link>,
                      <div key="account">
                        <p>{run.accountName ?? "Unknown account"}</p>
                        <p className="text-xs text-zinc-500">{run.accountId ?? "—"}</p>
                      </div>,
                      <Badge key="mode" tone={modeTone(run.accountMode)}>
                        {run.accountMode ?? "unknown"}
                      </Badge>,
                      <span key="created">{formatDate(run.lastSeenAt ?? run.createdAt)}</span>,
                    ]}
                  />
                ))}
              </DataTable>
            )}
          </div>
        </Panel>
      </main>
    </PageShell>
  );
}
