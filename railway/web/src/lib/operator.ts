import type { AnalyticsSummary, DashboardData, RunDetail } from "@/lib/analytics";
import { fetchDashboardData, fetchRlmLibrary, fetchRunDetail, fetchSearchResults } from "@/lib/analytics";

export type OperatorMode = "report" | "hypothesis" | "feedback";

export type OperatorSnapshot = {
  summary: AnalyticsSummary | null;
  dashboard: DashboardData | null;
  search: Awaited<ReturnType<typeof fetchSearchResults>>;
  selectedRun: RunDetail | null;
  rlmLibrary: Awaited<ReturnType<typeof fetchRlmLibrary>>;
};

export type OperatorAnalysisInput = {
  prompt: string;
  mode: OperatorMode;
  runId?: string | null;
  investigationQuery?: string | null;
};

export type OperatorAnalysisResult = {
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

const RLM_URL = (process.env.RLM_SERVICE_URL || "").trim().replace(/\/$/, "");
const RLM_TOKEN = (process.env.RLM_AUTH_TOKEN || "").trim();

function readString(value: Record<string, unknown> | null, ...keys: string[]): string | null {
  if (!value) {
    return null;
  }

  for (const key of keys) {
    const candidate = value[key];
    if (typeof candidate === "string" && candidate.trim()) {
      return candidate;
    }
  }

  return null;
}

function readValue(value: Record<string, unknown> | null, ...keys: string[]): unknown {
  if (!value) {
    return null;
  }

  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(value, key)) {
      return value[key];
    }
  }

  return null;
}

async function postJson<T>(url: string, body: Record<string, unknown>, token: string): Promise<T | null> {
  if (!url || !token) {
    return null;
  }

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as T;
  } catch {
    return null;
  }
}

function buildContextText(snapshot: OperatorSnapshot): string {
  const dashboard = snapshot.dashboard;
  const selectedRun = snapshot.selectedRun;
  const latestReport = snapshot.rlmLibrary?.reports?.[0] ?? null;
  const latestHypothesis = snapshot.rlmLibrary?.hypotheses?.[0] ?? null;

  return [
    "G-Trade operator context:",
    dashboard
      ? `Summary: ${dashboard.summary.run_count} runs, ${dashboard.summary.event_count} events, ${dashboard.summary.trade_count} trades, ${dashboard.summary.report_count} reports.`
      : "Summary unavailable.",
    selectedRun?.run
      ? `Selected run ${selectedRun.run.runId} has ${selectedRun.events.length} events, ${selectedRun.trades.length} trades, ${selectedRun.decisionSnapshots.length} decision snapshots, and ${selectedRun.bridgeHealth.length} bridge health rows.`
      : "No selected run.",
    latestReport ? `Latest report: ${latestReport.title} (${latestReport.modelName})` : "No reports yet.",
    latestHypothesis ? `Latest hypothesis: ${latestHypothesis.claimText}` : "No hypotheses yet.",
  ].join("\n");
}

export async function fetchOperatorSnapshot(searchQuery?: string | null, runId?: string | null): Promise<OperatorSnapshot> {
  const [dashboard, rlmLibrary, search, selectedRun] = await Promise.all([
    fetchDashboardData(),
    fetchRlmLibrary(),
    fetchSearchResults(searchQuery ?? ""),
    runId ? fetchRunDetail(runId) : Promise.resolve(null),
  ]);

  const resolvedRunId = runId ?? dashboard?.runs?.[0]?.runId ?? null;
  const fallbackRun = !selectedRun && resolvedRunId ? await fetchRunDetail(resolvedRunId) : selectedRun;

  return {
    summary: dashboard?.summary ?? null,
    dashboard,
    search,
    selectedRun: fallbackRun,
    rlmLibrary,
  };
}

export async function runOperatorAnalysis(input: OperatorAnalysisInput): Promise<OperatorAnalysisResult> {
  const prompt = input.prompt.trim();
  if (!prompt) {
    return {
      ok: false,
      mode: input.mode,
      prompt: input.prompt,
      title: "No prompt provided",
      summary: "Operator analysis requires a prompt.",
      recommendation: "Enter a concrete investigation question or report request.",
      nextActions: [],
      supportingData: {
        runId: input.runId ?? null,
        latestReportId: null,
        latestHypothesisId: null,
      },
      artifact: null,
      error: "Prompt is required.",
    };
  }

  const snapshot = await fetchOperatorSnapshot(input.investigationQuery ?? prompt, input.runId ?? null);
  const contextText = buildContextText(snapshot);
  const latestReport = snapshot.rlmLibrary?.reports?.[0] ?? null;
  const latestHypothesis = snapshot.rlmLibrary?.hypotheses?.[0] ?? null;
  const investigationPrompt = `${contextText}\n\nOperator prompt:\n${prompt}`;

  if (input.mode === "report") {
    if (!RLM_URL || !RLM_TOKEN) {
      return {
        ok: false,
        mode: input.mode,
        prompt,
        title: "RLM report generation unavailable",
        summary: "Set `RLM_SERVICE_URL` and `RLM_AUTH_TOKEN` on the web service to trigger report generation from this console.",
        recommendation: "Use the operator library and investigation views until the RLM service token is configured.",
        nextActions: ["Inspect recent runs", "Open the RLM library", "Collect bridge health evidence"],
        supportingData: {
          runId: input.runId ?? snapshot.selectedRun?.run?.runId ?? null,
          latestReportId: latestReport?.reportId ?? null,
          latestHypothesisId: latestHypothesis?.hypothesisId ?? null,
        },
        artifact: null,
        error: "RLM service not configured.",
      };
    }

    const report = await postJson<Record<string, unknown>>(`${RLM_URL}/reports/generate`, {
      regime_context: investigationPrompt,
      generation: 1,
      report_type: "operator_chat",
      lookback: 8,
    }, RLM_TOKEN);

    if (!report) {
      return {
        ok: false,
        mode: input.mode,
        prompt,
        title: "Report generation failed",
        summary: "The RLM service did not return a report bundle.",
        recommendation: "Inspect the RLM service and try again with a narrower prompt.",
        nextActions: ["Review the latest run", "Check the RLM service health", "Try a hypothesis request"],
        supportingData: {
          runId: input.runId ?? snapshot.selectedRun?.run?.runId ?? null,
          latestReportId: latestReport?.reportId ?? null,
          latestHypothesisId: latestHypothesis?.hypothesisId ?? null,
        },
        artifact: null,
        error: "Report generation did not return data.",
      };
    }

    return {
      ok: true,
      mode: input.mode,
      prompt,
      title: String(readString(report, "title") ?? readString(readValue(report, "report") as Record<string, unknown> | null, "title") ?? "Operator report"),
      summary: String(readString(report, "summary_text", "summaryText") ?? "Report generated successfully."),
      recommendation: String(readString(report, "summary_text", "summaryText") ?? "Review the generated report bundle."),
      nextActions: [
        "Open the generated report",
        "Cross-check the latest run detail",
        "Confirm bridge health for the selected run",
      ],
      supportingData: {
        runId: input.runId ?? snapshot.selectedRun?.run?.runId ?? null,
        latestReportId: String(readString(report, "report_id", "reportId") ?? latestReport?.reportId ?? ""),
        latestHypothesisId: latestHypothesis?.hypothesisId ?? null,
      },
      artifact: report,
    };
  }

  if (input.mode === "feedback") {
    const feedback = await postJson<Record<string, unknown>>(`${RLM_URL}/feedback/cycle`, {
      regime_context: investigationPrompt,
      generation: 1,
      parent_hypothesis_id: latestHypothesis?.hypothesisId ?? input.runId ?? null,
    }, RLM_TOKEN);

    if (feedback) {
      return {
        ok: true,
        mode: input.mode,
        prompt,
        title: "Feedback cycle completed",
        summary: "The RLM service produced a recursive feedback pass.",
        recommendation: "Review the new hypotheses and decide whether to promote or reject the resulting claims.",
        nextActions: ["Inspect hypotheses", "Review the latest report", "Compare against prior runs"],
        supportingData: {
          runId: input.runId ?? snapshot.selectedRun?.run?.runId ?? null,
          latestReportId: latestReport?.reportId ?? null,
          latestHypothesisId: latestHypothesis?.hypothesisId ?? null,
        },
        artifact: feedback,
      };
    }
  }

  const hypothesis = await postJson<Record<string, unknown>>(`${RLM_URL}/hypotheses/generate`, {
    regime_context: investigationPrompt,
    prior_conclusions_summary: contextText,
    generation: 1,
    parent_hypothesis_id: latestHypothesis?.hypothesisId ?? input.runId ?? null,
  }, RLM_TOKEN);

  if (!hypothesis) {
    return {
      ok: false,
      mode: input.mode,
      prompt,
      title: "Hypothesis generation failed",
      summary: "The RLM service did not return a hypothesis bundle.",
      recommendation: "Check the RLM service and retry with a narrower question.",
      nextActions: ["Review the latest run", "Open the RLM library", "Generate a report instead"],
      supportingData: {
        runId: input.runId ?? snapshot.selectedRun?.run?.runId ?? null,
        latestReportId: latestReport?.reportId ?? null,
        latestHypothesisId: latestHypothesis?.hypothesisId ?? null,
      },
      artifact: null,
      error: "Hypothesis generation did not return data.",
    };
  }

  const hypotheses = Array.isArray(hypothesis.hypotheses) ? (hypothesis.hypotheses as Array<Record<string, unknown>>) : [];
  const primary = hypotheses[0] ?? (hypothesis.hypothesis as Record<string, unknown> | undefined) ?? null;

  return {
    ok: true,
    mode: input.mode,
    prompt,
    title: String(primary?.claim_text ?? primary?.claimText ?? "Hypothesis generated"),
    summary: String(primary?.regime_context ?? primary?.regimeContext ?? "RLM produced a hypothesis."),
    recommendation: "Use the hypothesis as the starting point for a run review, then validate against the run timeline and bridge health.",
    nextActions: ["Open the latest run", "Inspect the RLM lineage", "Compare against earlier reports"],
    supportingData: {
      runId: input.runId ?? snapshot.selectedRun?.run?.runId ?? null,
      latestReportId: latestReport?.reportId ?? null,
      latestHypothesisId: String(primary?.hypothesis_id ?? primary?.hypothesisId ?? latestHypothesis?.hypothesisId ?? ""),
    },
    artifact: hypothesis,
  };
}
