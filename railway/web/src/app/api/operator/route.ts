import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

import type { OperatorAnalysisInput } from "@/lib/operator";
import { runOperatorAnalysis } from "@/lib/operator";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let body: Partial<OperatorAnalysisInput> | null = null;
  try {
    body = (await request.json()) as Partial<OperatorAnalysisInput>;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (!body?.prompt || !body.mode) {
    return NextResponse.json({ error: "prompt and mode are required" }, { status: 400 });
  }

  const result = await runOperatorAnalysis({
    prompt: body.prompt,
    mode: body.mode,
    runId: body.runId ?? null,
    investigationQuery: body.investigationQuery ?? null,
  });

  return NextResponse.json(result, { status: result.ok ? 200 : 503 });
}
