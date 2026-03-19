# Route by task

1. Read **AGENTS.md** section "Where to go for what (routing by task)" and, if needed, **docs/engineering-system/agent-index.md**.
2. Identify which task type matches the current request (issue-driven work, Railway, OpenViking, docs, safety, architecture, exploratory, templates).
3. **Subagent dispatch:** Check the agent-index **Subagent(s)** and **Pattern** columns. If the concern is route-first or hybrid and a subagent is listed, consider dispatching via `mcp_task`. Examples: broad codebase search → **explore** (set thoroughness); PR or diff review → **code-reviewer**; status/progress/analysis → **openviking-analyst**; API testing → **api-tester**; shell commands → **shell**. See AGENTS.md "Subagent routing" and rule 03-orchestration-first.
4. Apply the listed Rule(s) and Skill(s), and follow the Doc(s) for full procedure.
5. Proceed with the work using that rule/skill/doc set (and subagent results if dispatched).
