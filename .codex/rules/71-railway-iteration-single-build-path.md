---
description: Prefer GitHub push for deploys; use Railway CLI only when MCP is unavailable or the operation isn't natively available.
globs: railway/**/*
alwaysApply: false
---

# Railway deploy preference and single build path

**When this applies:** Deploying or fixing a failing/flaky Railway service (build, start, runtime).

**Rule:** Prefer deploying by pushing to the service’s GitHub repo (GitHub-triggered builds). Use Railway MCP when the operation is available. Use Railway CLI only when MCP isn’t working or the resource/operation isn’t natively available in MCP.

When you do use the CLI: use one build path. Pushing to GitHub and running `railway up` both trigger builds; doing both in the same session causes conflicting deployments. So if you fall back to CLI for a deploy, do not also push to GitHub until that deploy is verified (or vice versa: if you’re iterating by pushing to GitHub, don’t run `railway up` in the same iteration).

**Do this:**
- **Default:** Deploy by pushing to the relevant GitHub repo. Use Railway MCP for status, logs, variables, etc. when available.
- **Fallback to CLI:** Use Railway CLI (`railway up`, `railway logs`, `railway service status`, etc.) only when MCP isn’t working or the operation isn’t exposed in MCP.
- **When using CLI for a deploy:** From the service directory, `railway up --service <service> -m "<summary>"`. Verify with `railway logs --service <service>` and `railway service status --all --json`. Do not push to the same service’s GitHub repo in the same iteration until the fix is confirmed.
- **After any fix is verified:** Push to GitHub if you used CLI for the fix, then document (Linear, OPERATOR.md, etc.) as needed.

**Wrong:** Using Railway CLI for every deploy when GitHub/MCP are available. Or mixing a GitHub push and `railway up` in the same debugging session.
**Right:** Prefer GitHub push (and MCP for ops); use CLI only when MCP isn’t working or the resource isn’t natively available; use one build path per iteration when you do use CLI.
