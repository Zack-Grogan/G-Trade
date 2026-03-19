---
name: deploy
description: Deploy to Railway; prefer GitHub push, fallback to Railway CLI when MCP unavailable.
---

# Deploy

1. **Prefer GitHub** - Deploy by pushing to the service's GitHub repo (GitHub-triggered builds). Use Railway MCP for status and logs when available.

2. **Fallback to CLI** - Use Railway CLI only when MCP isn't working or the operation isn't natively available:
   - Preflight: `railway whoami --json`, `railway status --json`
   - Deploy: `railway up --service <service> -m "<summary>"`
   - Verify: `railway service status --all --json`, `railway logs --service <service> --lines 50`

3. **Single build path** - When using CLI for a deploy, do not push to GitHub in the same iteration until the deploy is verified.

4. **Report** - Summarize result with URL and status.

For complex deploys, consider dispatching **devops-automator** subagent (max 2 at a time).
