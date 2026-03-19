"use client";

import { useState, useTransition, type FormEvent } from "react";

import { Badge, EmptyState } from "@/components/dashboard";

type OperatorMode = "report" | "hypothesis" | "feedback";

type OperatorAnalysisResult = {
  ok: boolean;
  mode: OperatorMode;
  prompt: string;
  title: string;
  summary: string;
  recommendation: string;
  nextActions: string[];
  supportingData: {
    runId: string | null;
    latestReportId: string | null;
    latestHypothesisId: string | null;
  };
  artifact: Record<string, unknown> | null;
  error?: string;
};

const MODE_LABELS: Record<OperatorMode, string> = {
  report: "Generate report",
  hypothesis: "Generate hypothesis",
  feedback: "Recursive feedback",
};

const QUICK_PROMPTS = [
  "Summarize the most recent run and call out bridge failures.",
  "Generate a report on the latest adverse execution path.",
  "Review the current hypothesis lineage for stale or repeated claims.",
  "Find the highest-signal blockers in the current timeline.",
];

export function OperatorChat({
  defaultRunId,
  defaultPrompt,
}: {
  defaultRunId?: string | null;
  defaultPrompt?: string;
}) {
  const [mode, setMode] = useState<OperatorMode>("report");
  const [runId, setRunId] = useState(defaultRunId ?? "");
  const [prompt, setPrompt] = useState(defaultPrompt ?? "");
  const [result, setResult] = useState<OperatorAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function submitAnalysis(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    startTransition(() => {
      void (async () => {
        try {
          const response = await fetch("/api/operator", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              mode,
              prompt,
              runId: runId.trim() || null,
              investigationQuery: prompt,
            }),
          });

          const payload = (await response.json()) as OperatorAnalysisResult & { error?: string };
          if (!response.ok) {
            setResult(payload);
            setError(payload.error ?? "Operator analysis failed.");
            return;
          }

          setResult(payload);
        } catch (requestError) {
          const message = requestError instanceof Error ? requestError.message : "Operator analysis request failed.";
          setError(message);
        }
      })();
    });
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
      <form onSubmit={submitAnalysis} className="rounded-2xl border border-zinc-800 bg-zinc-950/80 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-cyan-300">Advisory</p>
            <h3 className="mt-2 text-xl font-semibold tracking-tight text-zinc-50">RLM prompt</h3>
          </div>
          <Badge tone="neutral">Server-side</Badge>
        </div>

        <div className="mt-5 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <label className="space-y-2">
            <span className="text-xs uppercase tracking-[0.22em] text-zinc-500">Prompt</span>
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              rows={7}
              placeholder="What should RLM inspect?"
              className="min-h-[14rem] w-full rounded-xl border border-zinc-800 bg-zinc-900/90 px-4 py-3 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-cyan-500/30 focus:ring-2 focus:ring-cyan-500/10"
            />
          </label>

          <div className="space-y-3">
            <label className="block space-y-2">
              <span className="text-xs uppercase tracking-[0.22em] text-zinc-500">Run</span>
              <input
                value={runId}
                onChange={(event) => setRunId(event.target.value)}
                placeholder="Optional run id"
                className="w-full rounded-xl border border-zinc-800 bg-zinc-900/90 px-4 py-3 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-cyan-500/30 focus:ring-2 focus:ring-cyan-500/10"
              />
            </label>

            <div className="grid gap-2">
              {(Object.keys(MODE_LABELS) as OperatorMode[]).map((currentMode) => (
                <button
                  key={currentMode}
                  type="button"
                  onClick={() => setMode(currentMode)}
                  className={`rounded-xl border px-4 py-3 text-left text-sm transition ${
                    mode === currentMode
                      ? "border-cyan-500/30 bg-cyan-500/10 text-cyan-100"
                      : "border-zinc-800 bg-zinc-900/80 text-zinc-300 hover:border-zinc-700 hover:bg-zinc-800"
                  }`}
                >
                  <span className="block text-[11px] uppercase tracking-[0.22em] text-zinc-500">Mode</span>
                  <span className="mt-1 block font-medium">{MODE_LABELS[currentMode]}</span>
                </button>
              ))}
            </div>

            <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-950/80 p-4">
              <p className="text-xs uppercase tracking-[0.22em] text-zinc-500">Quick prompts</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {QUICK_PROMPTS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => setPrompt(suggestion)}
                    className="rounded-full border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-cyan-100"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={isPending || !prompt.trim()}
                className="inline-flex items-center rounded-full border border-cyan-500/30 bg-cyan-500/15 px-4 py-2 text-sm font-medium text-cyan-100 transition hover:bg-cyan-500/20 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isPending ? "Running..." : "Run"}
              </button>
            </div>

            {error ? <p className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</p> : null}
          </div>
        </div>
      </form>

      <div className="space-y-5">
        <article className="rounded-2xl border border-zinc-800 bg-zinc-950/80 p-5">
          <p className="text-[11px] uppercase tracking-[0.22em] text-cyan-300">Result</p>
          {result ? (
            <div className="mt-3 space-y-4">
              <div className="flex flex-wrap gap-2">
                <Badge tone="neutral">{result.mode}</Badge>
                <Badge tone={result.ok ? "success" : "warning"}>{result.ok ? "Done" : "Check"}</Badge>
              </div>
              <h4 className="text-lg font-semibold tracking-tight text-zinc-50">{result.title}</h4>
              <p className="text-sm leading-6 text-zinc-300">{result.summary}</p>
              <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4">
                <p className="text-xs uppercase tracking-[0.22em] text-zinc-500">Recommendation</p>
                <p className="mt-2 text-sm leading-6 text-zinc-200">{result.recommendation}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-zinc-500">Next</p>
                <ul className="mt-2 space-y-2 text-sm text-zinc-300">
                  {result.nextActions.map((item) => (
                    <li key={item} className="rounded-xl border border-zinc-800 bg-zinc-900/70 px-3 py-2">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-3">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Run</p>
                  <p className="mt-1 text-sm text-zinc-100">{result.supportingData.runId ?? "—"}</p>
                </div>
                <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-3">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Report</p>
                  <p className="mt-1 text-sm text-zinc-100">{result.supportingData.latestReportId ?? "—"}</p>
                </div>
                <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-3">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">Hypothesis</p>
                  <p className="mt-1 text-sm text-zinc-100">{result.supportingData.latestHypothesisId ?? "—"}</p>
                </div>
              </div>
            </div>
          ) : (
            <EmptyState
              title="No analysis yet"
              description="Run a prompt to generate a report bundle, hypothesis, or recursive feedback cycle. Results stay in the operator console and backend services."
            />
          )}
        </article>

        <article className="rounded-2xl border border-zinc-800 bg-zinc-950/80 p-5">
          <p className="text-[11px] uppercase tracking-[0.22em] text-cyan-300">Artifact payload</p>
          {result?.artifact ? (
            <pre className="mt-3 max-h-[24rem] overflow-auto rounded-2xl border border-zinc-800 bg-black/40 p-4 text-xs leading-6 text-zinc-300">
              {JSON.stringify(result.artifact, null, 2)}
            </pre>
          ) : (
            <p className="mt-3 text-sm text-zinc-500">No artifact payload yet.</p>
          )}
        </article>
      </div>
    </div>
  );
}
