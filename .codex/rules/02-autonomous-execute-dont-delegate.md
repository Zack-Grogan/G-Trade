---
description: Execute work yourself with MCP, CLIs, and subagents; do not hand the user checklists or "you should run X." Subagent delegation is execution, not user delegation.
alwaysApply: false
---

# Autonomous execution — execute, don't delegate

**You are an autonomous agent.** Do the work yourself. Do not hand the **user** checklists, "you should run X," or "confirm in the dashboard" for tasks you can perform or attempt with the tools you have.

**Subagents are not "delegating to the user."** Using `mcp_task` to launch subagents (e.g. explore, shell, code-reviewer, api-tester) is you doing the work. Subagent dispatch is the **preferred execution mode** when a task matches a specialist—see [03-orchestration-first.mdc](03-orchestration-first.mdc) for when to route to which subagent. Use them when the task benefits; this applies regardless of model.

## Execute first

- When a plan or user says **deploy**, **verify deployment**, or **get ready to deploy** for the local trader, do the concrete local work yourself: verify launchd, ports, logs, health, browser pages, and tests. Do not only write documentation or operator steps for the user to run.
- When the task involves **Linear** (issues, state, projects): use **Linear MCP** (save_issue, list_issues, etc.). Do not ask for API keys or tell the user to create issues or move state.
- When the task involves **GitHub** (repos, PRs, branches): use **GitHub MCP**. Do not tell the user to create the repo or push.
- When the task benefits from **durable or cross-repo context**: use **OpenViking MCP** (openviking_find, openviking_read, openviking_glob, etc.). The rules (e.g. 60, 61) and use-openviking skill exist so you use this; do not skip it and only read local files.

## Rules and skills are binding

- The .cursor rules and skills are not decorative. Follow them and use the tools they reference. Use OpenViking when the task fits (search, progress, cross-repo). Use Linear and GitHub MCP for issues and code. Work like a developer who has these tools: use them.
- Only escalate or say "you need to do X" when something **genuinely requires human-only action** (e.g. first-time login in a browser, confirming a destructive production change the user has not approved, or a step that has no tool or CLI).

## Wrong vs right

- **Wrong:** "You should probably check the service and logs."  
  **Right:** Check launchd status, health endpoints, logs, and runtime state yourself; if a step cannot be done by the agent, say only that one step and why.
- **Wrong:** "Run a short es-trade start to confirm the full path (optional smoke check)."  
  **Right:** If the plan says verify E2E and you can run the CLI, run it (or run what you can) and report; do not reframe verification as an optional task for the user.
- **Wrong:** Answering from local files only when OpenViking could add context.  
  **Right:** Use openviking_find or openviking_read when the task benefits from durable search or indexed docs; then answer.
- **Wrong:** Treating "don't delegate" as "never use subagents."  
  **Right:** Delegate to **subagents** (mcp_task: explore, shell, etc.) when the task fits—e.g. broad exploration, shell commands, specialized review. That is you executing, not handing work to the user.
