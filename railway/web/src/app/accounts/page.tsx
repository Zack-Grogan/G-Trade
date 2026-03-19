import { Badge, DataRow, DataTable, EmptyState, KpiCard, MiniBarChart, Panel, StatusPill, formatCurrency, formatDate, formatShort } from "@/components/dashboard";
import { PageShell } from "@/components/page-shell";
import { fetchAccountSummaries, fetchAccountTrades } from "@/lib/analytics";
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

function sideLabel(side: number | null) {
  if (side === 1) {
    return "long";
  }
  if (side === 0) {
    return "flat";
  }
  if (side === -1) {
    return "short";
  }
  return "unknown";
}

export default async function AccountsPage() {
  const signedIn = await isSignedInRequest();
  const [accountSummaries, accountTrades] = signedIn ? await Promise.all([fetchAccountSummaries(), fetchAccountTrades({ limit: 24 })]) : [[], []];

  if (!signedIn) {
    return <PageShell authenticated={false} />;
  }

  const totalTrades = accountSummaries.reduce((sum, account) => sum + account.tradeCount, 0);
  const totalPnl = accountSummaries.reduce((sum, account) => sum + account.realizedPnl, 0);
  const practiceAccounts = accountSummaries.filter((account) => account.accountMode === "practice").length;
  const liveAccounts = accountSummaries.filter((account) => account.accountMode === "live").length;
  const equityBars = accountTrades.slice(0, 8).map((trade) => trade.profitAndLoss ?? 0);
  const equityLabels = accountTrades.slice(0, 8).map((trade) => trade.accountName ?? trade.contractId ?? trade.brokerTradeId);

  return (
    <PageShell authenticated>
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-5 sm:px-6 lg:px-8">
        <Panel eyebrow="Accounts" title="Ledger">
          <div className="flex flex-wrap gap-2">
            <StatusPill label="Accounts" value={formatShort(accountSummaries.length)} tone="accent" />
            <StatusPill label="Practice" value={formatShort(practiceAccounts)} tone={practiceAccounts > 0 ? "warning" : "neutral"} />
            <StatusPill label="Live" value={formatShort(liveAccounts)} tone={liveAccounts > 0 ? "success" : "neutral"} />
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard label="Realized P/L" value={formatCurrency(totalPnl)} tone={totalPnl >= 0 ? "success" : "danger"} />
            <KpiCard label="Trades" value={formatShort(totalTrades)} />
            <KpiCard label="Latest activity" value={formatDate(accountSummaries[0]?.latestTradeAt ?? accountSummaries[0]?.latestRunSeenAt)} />
            <KpiCard label="Backfill rows" value={formatShort(accountTrades.length)} />
          </div>
        </Panel>

        <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <Panel eyebrow="Trend" title="Recent account P/L">
            {accountTrades.length ? <MiniBarChart values={equityBars} labels={equityLabels} /> : <EmptyState title="No account trades" description="Backfilled ledger rows will appear here." />}
          </Panel>

          <Panel eyebrow="Snapshot" title="Account modes">
            <div className="space-y-3">
              {accountSummaries.length === 0 ? (
                <EmptyState title="No account summaries" description="The analytics API has not populated account rows yet." />
              ) : (
                accountSummaries.slice(0, 6).map((account) => (
                  <div key={account.accountId} className="rounded-xl border border-zinc-800 bg-zinc-950/80 px-4 py-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="font-mono text-xs text-zinc-100">{account.accountName ?? account.accountId}</p>
                        <p className="text-xs text-zinc-500">{account.accountId}</p>
                      </div>
                      <Badge tone={toneForMode(account.accountMode)}>{account.accountMode ?? "unknown"}</Badge>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-3 text-sm">
                      <div>
                        <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Trades</p>
                        <p className="mt-1 text-zinc-100 tabular-nums">{formatShort(account.tradeCount)}</p>
                      </div>
                      <div>
                        <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">P/L</p>
                        <p className={`mt-1 tabular-nums ${account.realizedPnl >= 0 ? "text-emerald-300" : "text-rose-300"}`}>{formatCurrency(account.realizedPnl)}</p>
                      </div>
                      <div>
                        <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Activity</p>
                        <p className="mt-1 text-zinc-300">{formatDate(account.latestTradeAt ?? account.latestRunSeenAt)}</p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Panel>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_1.1fr]">
          <Panel eyebrow="Ledger" title="Account summary table">
            <DataTable columns={["Account", "Mode", "Trades", "P/L"]}>
              {accountSummaries.length === 0 ? (
                <div className="px-4 py-4 text-sm text-zinc-500">No account summaries.</div>
              ) : (
                accountSummaries.map((account) => (
                  <DataRow
                    key={account.accountId}
                    cells={[
                      <div key="account">
                        <p className="font-mono text-xs text-zinc-100">{account.accountName ?? account.accountId}</p>
                        <p className="text-xs text-zinc-500">{account.accountId}</p>
                      </div>,
                      <Badge key="mode" tone={toneForMode(account.accountMode)}>
                        {account.accountMode ?? "unknown"}
                      </Badge>,
                      <span key="trades" className="tabular-nums">
                        {formatShort(account.tradeCount)}
                      </span>,
                      <span key="pnl" className={`tabular-nums ${account.realizedPnl >= 0 ? "text-emerald-300" : "text-rose-300"}`}>
                        {formatCurrency(account.realizedPnl)}
                      </span>,
                    ]}
                  />
                ))
              )}
            </DataTable>
          </Panel>

          <Panel eyebrow="Broker" title="Trade ledger">
            <DataTable columns={["Account", "Side", "PnL", "Time"]}>
              {accountTrades.length === 0 ? (
                <div className="px-4 py-4 text-sm text-zinc-500">No account trades.</div>
              ) : (
                accountTrades.map((trade) => (
                  <DataRow
                    key={`${trade.accountId}-${trade.brokerTradeId}`}
                    cells={[
                      <div key="account">
                        <p className="text-sm text-zinc-100">{trade.accountName ?? trade.accountId}</p>
                        <p className="text-xs text-zinc-500">{trade.contractId ?? trade.brokerTradeId}</p>
                      </div>,
                      <Badge key="side" tone="neutral">
                        {sideLabel(trade.side)}
                      </Badge>,
                      <span key="pnl" className={(trade.profitAndLoss ?? 0) >= 0 ? "text-emerald-300 tabular-nums" : "text-rose-300 tabular-nums"}>
                        {trade.profitAndLoss === null ? "—" : formatCurrency(trade.profitAndLoss)}
                      </span>,
                      <span key="time">{formatDate(trade.occurredAt)}</span>,
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
