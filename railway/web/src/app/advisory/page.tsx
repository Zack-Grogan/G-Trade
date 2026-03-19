import Link from "next/link";

import { Badge, DataRow, DataTable, EmptyState, Panel, StatCard, formatDate, formatShort } from "@/components/dashboard";
import { OperatorChat } from "@/components/operator-chat";
import { PageShell } from "@/components/page-shell";
import { fetchRlmLibrary } from "@/lib/analytics";
import { isSignedInRequest } from "@/lib/session";

type LineageNode = {
  id: string;
  label: string;
  status: string;
  generation: number;
  regimeContext: string | null;
  children: LineageNode[];
};

function buildLineage(nodes: Array<{ hypothesisId: string; parentHypothesisId: string | null; claimText: string; status: string; generation: number; regimeContext: string | null }>) {
  const lookup = new Map<string, LineageNode>();
  const roots: LineageNode[] = [];

  for (const item of nodes) {
    lookup.set(item.hypothesisId, {
      id: item.hypothesisId,
      label: item.claimText,
      status: item.status,
      generation: item.generation,
      regimeContext: item.regimeContext,
      children: [],
    });
  }

  for (const item of nodes) {
    const node = lookup.get(item.hypothesisId);
    if (!node) continue;
    if (item.parentHypothesisId && lookup.has(item.parentHypothesisId)) {
      lookup.get(item.parentHypothesisId)!.children.push(node);
    } else {
      roots.push(node);
    }
  }

  return roots.sort((left, right) => right.generation - left.generation || left.id.localeCompare(right.id));
}

function LineageTree({ node, depth = 0 }: { node: LineageNode; depth?: number }) {
  return (
    <div className={`rounded-xl border border-zinc-800 bg-zinc-950/80 p-4 ${depth > 0 ? "ml-4" : ""}`}>
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={node.status === "supported" ? "success" : node.status === "rejected" ? "warning" : "neutral"}>{node.status}</Badge>
        <Badge tone="accent">G{node.generation}</Badge>
      </div>
      <p className="mt-3 text-sm leading-6 text-zinc-200">{node.label}</p>
      {node.regimeContext ? <p className="mt-2 text-xs text-zinc-500">{node.regimeContext}</p> : null}
      {node.children.length ? (
        <div className="mt-4 space-y-3 border-l border-zinc-800 pl-4">
          {node.children.map((child) => (
            <LineageTree key={child.id} node={child} depth={depth + 1} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

export default async function AdvisoryPage() {
  const signedIn = await isSignedInRequest();
  const data = signedIn ? await fetchRlmLibrary() : null;

  if (!signedIn) {
    return <PageShell authenticated={false} />;
  }

  const hypotheses = data?.hypotheses ?? [];
  const knowledgeStore = data?.knowledgeStore ?? [];
  const reports = data?.reports ?? [];
  const metaLearnerStats = data?.metaLearnerStats ?? null;
  const metaLearnerRate = metaLearnerStats
    ? metaLearnerStats.survivalCount + metaLearnerStats.rejectionCount > 0
      ? metaLearnerStats.survivalCount / (metaLearnerStats.survivalCount + metaLearnerStats.rejectionCount)
      : 0
    : null;
  const lineage = buildLineage(
    hypotheses.map((item) => ({
      hypothesisId: item.hypothesisId,
      parentHypothesisId: item.parentHypothesisId,
      claimText: item.claimText,
      status: item.status,
      generation: item.generation,
      regimeContext: item.regimeContext,
    })),
  );

  return (
    <PageShell authenticated>
      <main className="mx-auto max-w-7xl space-y-6 px-6 py-10 lg:px-8">
        <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <Panel
            eyebrow="Advisory"
            title="RLM workspace"
            action={
              <Link
                href="/"
                className="inline-flex items-center rounded-full border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-white"
              >
                Console
              </Link>
            }
          >
            <div className="flex flex-wrap gap-2">
              <Badge tone="neutral">Advisory only</Badge>
              <Badge tone="accent">Graph-first</Badge>
              <Badge tone="success">Server-side chat</Badge>
            </div>
          </Panel>

          <div className="grid gap-4 sm:grid-cols-2">
            <StatCard label="Hypotheses" value={formatShort(hypotheses.length)} />
            <StatCard label="Reports" value={formatShort(reports.length)} />
            <StatCard label="Knowledge entries" value={formatShort(knowledgeStore.length)} />
            <StatCard
              label="Meta learner"
              value={`${metaLearnerStats?.survivalCount ?? 0}/${metaLearnerStats?.rejectionCount ?? 0}`}
            />
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <OperatorChat defaultRunId={null} />

          <Panel eyebrow="Advisory index" title="Latest reports">
            <div className="space-y-3">
              {reports.length === 0 ? (
                <EmptyState title="No reports yet" description="Persisted bundles will appear here." />
              ) : (
                reports.slice(0, 5).map((report) => (
                  <article key={report.reportId} className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-[11px] uppercase tracking-[0.22em] text-cyan-300">{report.modelProvider}</p>
                        <Link href={`/reports/${report.reportId}`} className="mt-2 block truncate text-base font-semibold text-zinc-50 transition hover:text-cyan-300">
                          {report.title}
                        </Link>
                      </div>
                      <Badge tone={report.status === "completed" ? "success" : "neutral"}>{report.status}</Badge>
                    </div>
                    <p className="mt-3 line-clamp-3 text-sm leading-6 text-zinc-400">{report.summaryText}</p>
                    <p className="mt-3 text-xs text-zinc-500">
                      {formatDate(report.completedAt ?? report.createdAt)} · {report.modelName}
                    </p>
                  </article>
                ))
              )}
            </div>
          </Panel>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <Panel eyebrow="Lineage" title="Hypothesis tree">
            <div className="space-y-4">
              {lineage.length === 0 ? (
                <EmptyState title="No hypotheses yet" description="No hypothesis nodes persisted." />
              ) : (
                lineage.map((node) => <LineageTree key={node.id} node={node} />)
              )}
            </div>
          </Panel>

          <Panel eyebrow="Research" title="Knowledge store">
            <DataTable columns={["Verdict", "Confidence", "Directive", "Created"]}>
              {knowledgeStore.length === 0 ? (
                <EmptyState title="No knowledge entries" description="No knowledge rows yet." />
              ) : (
                knowledgeStore.slice(0, 6).map((entry) => (
                  <DataRow
                    key={entry.id}
                    cells={[
                      <Badge key="verdict" tone={entry.verdict === "supported" ? "success" : entry.verdict === "rejected" ? "warning" : "neutral"}>
                        {entry.verdict}
                      </Badge>,
                      <span key="confidence">{entry.confidenceScore ?? "—"}</span>,
                      <span key="directive" className="truncate">
                        {entry.mutationDirective ?? "—"}
                      </span>,
                      <span key="created">{formatDate(entry.createdAt)}</span>,
                    ]}
                  />
                ))
              )}
            </DataTable>
          </Panel>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <Panel eyebrow="Artifact summary" title="Latest hypotheses">
            <div className="space-y-3">
              {hypotheses.length === 0 ? (
                <EmptyState title="No hypotheses" description="No hypothesis rows yet." />
              ) : (
                hypotheses.slice(0, 5).map((item) => (
                  <article key={item.id} className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4">
                    <div className="flex items-center justify-between gap-2">
                      <Badge tone={item.status === "supported" ? "success" : item.status === "rejected" ? "warning" : "neutral"}>{item.status}</Badge>
                      <span className="text-xs text-zinc-500">G{item.generation}</span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-zinc-300">{item.claimText}</p>
                    <p className="mt-2 text-xs text-zinc-500">{formatDate(item.createdAt)}</p>
                  </article>
                ))
              )}
            </div>
          </Panel>

          <Panel eyebrow="Meta" title="Meta learner">
            {metaLearnerStats ? (
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Survival</p>
                  <p className="mt-2 text-2xl font-semibold text-zinc-50">{formatShort(metaLearnerStats.survivalCount)}</p>
                </div>
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Rejection</p>
                  <p className="mt-2 text-2xl font-semibold text-zinc-50">{formatShort(metaLearnerStats.rejectionCount)}</p>
                </div>
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Survival rate</p>
                  <p className="mt-2 text-2xl font-semibold text-zinc-50">{metaLearnerRate === null ? "—" : metaLearnerRate.toFixed(2)}</p>
                </div>
              </div>
            ) : (
              <EmptyState title="No meta learner stats" description="Meta learner stats will appear after advisory history accumulates." />
            )}
          </Panel>
        </section>
      </main>
    </PageShell>
  );
}
