import Link from "next/link";

import { Badge, EmptyState, Panel, formatDate } from "@/components/dashboard";
import { PageShell } from "@/components/page-shell";
import { fetchReportDetail } from "@/lib/analytics";
import { isSignedInRequest } from "@/lib/session";

function listFromValue(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

export default async function ReportDetailPage({
  params,
}: {
  params: Promise<{ reportId: string }>;
}) {
  const signedIn = await isSignedInRequest();
  if (!signedIn) {
    return <PageShell authenticated={false} />;
  }

  const { reportId } = await params;
  const report = await fetchReportDetail(reportId);

  if (!report) {
    return (
      <PageShell authenticated>
        <main className="mx-auto max-w-4xl px-6 py-10 lg:px-8">
          <Panel
            eyebrow="Report"
            title="Report not found"
            action={
              <Link
                href="/advisory"
                className="inline-flex items-center rounded-full border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-white"
              >
                Advisory
              </Link>
            }
          >
            <p className="text-sm text-zinc-400">Requested report id: <span className="font-mono text-zinc-100">{reportId}</span></p>
          </Panel>
        </main>
      </PageShell>
    );
  }

  const reportJson = (report.reportJson ?? {}) as Record<string, unknown>;
  const highlights = listFromValue(reportJson.highlights);
  const risks = listFromValue(reportJson.risks);
  const nextActions = listFromValue(reportJson.next_actions ?? reportJson.nextActions);
  const hypotheses = Array.isArray(reportJson.hypotheses) ? (reportJson.hypotheses as Array<Record<string, unknown>>) : [];
  const conclusion = reportJson.conclusion as Record<string, unknown> | undefined;

  return (
    <PageShell authenticated>
      <main className="mx-auto max-w-6xl space-y-6 px-6 py-10 lg:px-8">
        <Panel
          eyebrow="Report"
          title={report.title}
          action={
            <Link
              href="/advisory"
              className="inline-flex items-center rounded-full border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-white"
            >
              Advisory
            </Link>
          }
        >
          <div className="flex flex-wrap gap-2">
            <Badge tone={report.status === "completed" ? "success" : "neutral"}>{report.status}</Badge>
            <Badge tone="accent">{report.modelProvider}</Badge>
            <Badge tone="neutral">{report.modelName}</Badge>
            <Badge tone="neutral">{report.reportType}</Badge>
          </div>
          <p className="mt-4 max-w-4xl text-sm leading-7 text-zinc-300">{report.summaryText}</p>
          <p className="mt-3 text-xs text-zinc-500">{formatDate(report.completedAt ?? report.createdAt)}</p>
        </Panel>

        <section className="grid gap-6 lg:grid-cols-3">
          <Panel eyebrow="Highlights" title="Highlights">
            {highlights.length === 0 ? (
              <EmptyState title="No highlights" description="No highlight list persisted." />
            ) : (
              <div className="space-y-3">
                {highlights.map((item) => (
                  <p key={item} className="rounded-xl border border-zinc-800 bg-zinc-950/80 px-4 py-3 text-sm leading-6 text-zinc-300">
                    {item}
                  </p>
                ))}
              </div>
            )}
          </Panel>

          <Panel eyebrow="Risks" title="Risks">
            {risks.length === 0 ? (
              <EmptyState title="No risks" description="No risk bullets persisted." />
            ) : (
              <div className="space-y-3">
                {risks.map((item) => (
                  <p key={item} className="rounded-xl border border-zinc-800 bg-zinc-950/80 px-4 py-3 text-sm leading-6 text-zinc-300">
                    {item}
                  </p>
                ))}
              </div>
            )}
          </Panel>

          <Panel eyebrow="Next steps" title="Next actions">
            {nextActions.length === 0 ? (
              <EmptyState title="No next actions" description="No next-step bullets persisted." />
            ) : (
              <div className="space-y-3">
                {nextActions.map((item) => (
                  <p key={item} className="rounded-xl border border-zinc-800 bg-zinc-950/80 px-4 py-3 text-sm leading-6 text-zinc-300">
                    {item}
                  </p>
                ))}
              </div>
            )}
          </Panel>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <Panel eyebrow="Context" title="Payload">
            <details className="rounded-2xl border border-zinc-800 bg-black/30 p-4">
              <summary className="cursor-pointer list-none text-sm text-zinc-200">Summary payload</summary>
              <pre className="mt-4 overflow-auto text-xs leading-6 text-zinc-300">{JSON.stringify(reportJson.summary ?? reportJson.analysis_snapshot ?? {}, null, 2)}</pre>
            </details>
          </Panel>

          <Panel eyebrow="Conclusion" title="Conclusion">
            <details className="rounded-2xl border border-zinc-800 bg-black/30 p-4">
              <summary className="cursor-pointer list-none text-sm text-zinc-200">Show conclusion</summary>
              <pre className="mt-4 overflow-auto text-xs leading-6 text-zinc-300">{JSON.stringify(conclusion ?? {}, null, 2)}</pre>
            </details>
          </Panel>
        </section>

        <Panel eyebrow="Hypotheses" title="Related claims">
          {hypotheses.length === 0 ? (
            <EmptyState title="No hypotheses" description="No hypothesis rows persisted." />
          ) : (
            <div className="space-y-3">
              {hypotheses.map((item, index) => (
                <article key={index} className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4">
                  <div className="flex flex-wrap gap-2">
                    <Badge tone={String(item.status ?? "unknown") === "supported" ? "success" : String(item.status ?? "unknown") === "rejected" ? "warning" : "neutral"}>
                      {String(item.status ?? "unknown")}
                    </Badge>
                    <Badge tone="accent">G{String(item.generation ?? "1")}</Badge>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-zinc-300">{String(item.claim_text ?? item.claimText ?? "")}</p>
                </article>
              ))}
            </div>
          )}
        </Panel>
      </main>
    </PageShell>
  );
}
