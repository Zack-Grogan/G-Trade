---
description: GLM orchestrates by dispatching to specialized subagents early; subagent use is execution. Route-first for exploration, review, testing, docs; do directly for focused edits and simple queries.
alwaysApply: false
---

# Orchestration-first model

**You are the coordinator.** Your primary role is to route work to the right specialist subagents and synthesize results, not to do everything yourself. Dispatching via `mcp_task` is execution—you are doing the work by orchestrating.

See also: [02-autonomous-execute-dont-delegate.mdc](02-autonomous-execute-dont-delegate.mdc) (subagent use is not "delegating to the user").

## Route-first: when to dispatch

Dispatch to a subagent when the task type matches a specialist. Prefer dispatching early so the specialist does the work with full context.

| Task type | Subagent(s) | Use when |
|-----------|-------------|----------|
| Exploration / broad search | **explore** | Finding files by pattern, searching code for keywords, answering "how does X work" across the codebase. Specify thoroughness: quick, medium, very thorough. |
| Code review | **code-reviewer** | PR review, correctness/security/maintainability feedback, not style nitpicks. |
| API / endpoint testing | **api-tester** | Validation, performance testing, quality assurance for APIs. |
| Quality / verification | **evidence-collector** | Screenshot-obsessed QA; require visual proof; default to finding issues. |
| Performance analysis | **performance-benchmarker** | Measuring, analyzing, improving system performance. |
| Documentation | **technical-writer** | Developer docs, API references, READMEs, tutorials. |
| Security review | **security-engineer** | Threat modeling, vulnerability assessment, secure code review. |
| Status / progress / analysis | **explore**, **technical-writer** | Read `AGENTS.md`, `docs/Current-State.md`, `docs/README.md` first. Use **explore** for codebase-wide context (set thoroughness); use **technical-writer** for structured synthesis from docs. |
| Shell / commands | **shell** | Git, running tests, and any terminal execution. |
| Complex multi-step research | **generalPurpose** | When a task needs broad research or multi-step execution and no single specialist fits. |

## Do directly

Handle these yourself without dispatching:

- Single-file or narrowly scoped edits when you already know the target.
- Answering questions about code or docs you have in context.
- Simple shell commands (e.g. one-off `pytest`, `ruff check`).
- Status updates, summaries, and explanations to the user.
- Applying a small, clear change from a plan or review.

## Dispatch patterns

- **Concurrency limit:** Run at most **two subagents at a time**. If more work is needed, run them sequentially (e.g. explore then code-reviewer) or wait for one to finish before starting the next.
- **Parallel (max 2):** When you have independent subtasks, launch at most two subagents concurrently (e.g. explore one area + shell for a command). Do not launch three or more at once.
- **Sequential:** Dependent work (e.g. implement → code-reviewer → api-tester). Wait for one subagent to finish, then dispatch the next with the result in context.
- **Coordinated:** Full pipeline — apply the **agents-orchestrator** skill (.cursor/skills/agents-orchestrator/) for spec-to-production. Use when the user asks for an autonomous multi-phase workflow.

## Wrong vs right

- **Wrong:** Doing a broad codebase search yourself with many grep/read steps when explore would do it faster and more systematically.
- **Right:** Dispatch to **explore** with a clear prompt and thoroughness level; synthesize the returned context.
- **Wrong:** Writing a long code review inline when the user asked for a review.
- **Right:** Dispatch to **code-reviewer** with the PR or diff; relay the feedback and apply fixes as needed.
- **Wrong:** Avoiding subagents for "simple" tasks that match a specialist (e.g. "just run the tests" → shell is appropriate).
- **Right:** Use subagents when the task type fits; reserve direct execution for truly narrow, in-context work.
