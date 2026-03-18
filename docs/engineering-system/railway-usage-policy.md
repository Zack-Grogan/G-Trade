# Railway usage policy

Railway is the deployment and runtime surface for `railway/` services. Agent usage is **conservative and non-production by default**.

## Local / dev only by default

- Do not assume production deployment permissions. Prefer inspecting (logs, status, list services) over mutating (deploy, variable changes) unless the user explicitly asks to deploy or change an environment.
- Development or staging environments can be used for agent-driven deploys when the user has indicated it is safe.

## Non-production guardrails

- Do not run destructive or irreversible operations (e.g. delete production database, overwrite production env vars) without explicit user confirmation.
- Do not expose production credentials or assume the agent has production access. Document that production changes require manual or approved automation.

## What the agent may do

- **Inspect:** List services, deployments, logs, status; read variables (if MCP/CLI allows and user has granted). Use for debugging and context.
- **Deploy (when explicitly asked):** Run deploy for the linked project/service after confirming context (e.g. `railway status --json`). Prefer non-production environment unless the user specifies production.

## What the agent should not do automatically

- Change production environment variables or secrets. Trigger production deployments without explicit user request. Delete or recreate production resources.

## Railway skill and MCP

- Before any Railway operation, consult `.cursor/skills/use-railway/SKILL.md` for preflight (auth, link, context) and command patterns.
- MCP tools live under the user's Railway MCP server; check tool schemas before calling. Prefer CLI with `--json` for scriptability when possible.
