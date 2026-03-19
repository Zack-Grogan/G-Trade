---
name: agents-orchestrator
description: Orchestrates full development pipelines by coordinating specialist subagents in phases (plan → architecture → dev-QA loop → integration). Use when the user asks for a complete spec-to-production workflow, autonomous pipeline, or multi-phase delivery with quality gates.
---

# Agents orchestrator

Orchestrates development workflows by dispatching to specialist subagents in sequence. Run at most **two subagents at a time** (see rule 03-orchestration-first). Use when the user requests a full pipeline from spec to production-ready delivery.

## When to use

- User asks for "full pipeline," "spec to production," "run the whole workflow," or "orchestrate the development."
- A project spec or task list exists (e.g. `project-specs/*-setup.md`, `project-tasks/*-tasklist.md`).
- Multi-phase delivery with quality gates is required.

## Pipeline phases

### Phase 1: Planning

- Verify spec exists (e.g. `project-specs/*-setup.md`).
- Dispatch **generalPurpose** (or equivalent) to produce a task list from the spec; save to `project-tasks/*-tasklist.md`.
- Quote exact requirements; do not add scope not in the spec.
- Verify task list exists before advancing.

### Phase 2: Architecture (optional)

- If the project needs technical foundation, dispatch **software-architect** or **backend-architect** with spec and task list.
- For frontend-heavy work, include **frontend-developer**.
- Verify deliverables (e.g. docs, structure) before dev loop.

### Phase 3: Dev–QA loop

For each task (max 2 subagents at a time):

1. **Implement** — Dispatch the right specialist (e.g. **senior-developer**, **backend-architect**, **frontend-developer**, **devops-automator**) to implement one task only. Pass task text and context.
2. **Validate** — Dispatch **evidence-collector** or **api-tester** for that task. Require PASS/FAIL with feedback.
3. **Decide** — If PASS: mark task done, next task. If FAIL: retry with same dev subagent and QA feedback (max 3 attempts per task), then escalate or block.

Do not advance to the next task until the current one passes QA.

### Phase 4: Integration

- When all tasks pass, dispatch **reality-checker** for final integration check.
- Default to "NEEDS WORK" unless evidence clearly shows production readiness.
- Produce a short completion summary.

## Quality rules

- **No shortcuts:** Every task must pass validation before moving on.
- **Evidence:** Decisions from actual subagent outputs, not assumptions.
- **Retry:** Max 3 attempts per task with QA feedback; then escalate or block.
- **Handoffs:** Give each subagent clear context and instructions (file paths, task text, acceptance criteria).

## Subagents available in this project

Use these when orchestrating (see AGENTS.md "Subagent routing" and .cursor/agents/):

| Phase / need        | Subagent                      |
|---------------------|-------------------------------|
| Planning / research | generalPurpose, explore       |
| Architecture        | software-architect, backend-architect, frontend-developer |
| Implementation      | senior-developer, backend-architect, frontend-developer, devops-automator, rapid-prototyper |
| QA / testing        | evidence-collector, api-tester, test-results-analyzer, reality-checker |
| Shell / commands    | shell                         |
| Docs                | technical-writer              |
| Security / compliance | security-engineer, compliance-auditor |

## Status reporting

Keep a brief pipeline state and report at phase boundaries:

- **Current phase** (Planning / Architecture / Dev-QA / Integration / Complete).
- **Task progress:** total, completed, current task, QA status (PASS/FAIL/IN_PROGRESS).
- **Retries:** current task attempt (1/2/3) and last QA feedback.
- **Next action:** which subagent to spawn and with what instructions.

On completion, summarize: project name, duration, final status (COMPLETED/NEEDS_WORK/BLOCKED), tasks completed, retries, and production readiness.

## Error handling

- **Spawn failure:** Retry up to 2 times; then document and escalate or fallback.
- **Task failure after 3 retries:** Mark task blocked, note reason, continue pipeline if possible; integration phase will surface remaining issues.
- **Inconclusive QA:** Treat as FAIL; do not advance without clear pass.

## Launch pattern

When the user asks for the full pipeline:

1. Confirm spec or task list location.
2. Run phases in order: Planning → (optional) Architecture → Dev-QA loop → Integration.
3. Enforce max 2 concurrent subagents; otherwise sequential.
4. Report status at each phase and a final completion summary.
