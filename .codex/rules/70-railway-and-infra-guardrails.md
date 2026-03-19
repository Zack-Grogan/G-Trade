---
description: Must read use-railway skill before Railway CLI/MCP use. Deploy and test on Railway only; E2E against deployed URLs; no local stack for ingest/analytics/mcp/web/rlm.
globs: railway/**/*,scripts/e2e*.py,docs/DEPLOY_AND_TEST.md,docs/ENV.md
alwaysApply: true
---

# Railway and infra guardrails

E2E and deploy run against deployed Railway URLs to avoid local resource use and environment drift.

**When this applies:** Deploying, testing, or changing Railway services (ingest, analytics, mcp, web, rlm); E2E or deployment docs. This rule also applies when **planning or discussing** Railway operations (e.g. in chat or in a plan), not only when editing files under the globs above — follow the use-railway skill and preflight before any Railway CLI/MCP use.

**Do this:**
- **Deploy only to Railway.** Prefer deploying by pushing to the service’s GitHub repo (GitHub-triggered builds). Use Railway MCP for status, logs, and operations when available. Use Railway CLI only when MCP isn’t working or the resource/operation isn’t natively available in MCP. Do not run railway/ services locally as a substitute for deployment.
- **E2E tests run against Railway only.** The script `scripts/e2e_test.py` refuses localhost and requires Railway deploy URLs. Set `INGEST_URL`, `ANALYTICS_URL`, and optionally `RLM_URL` (and auth keys) to your **deployed** Railway URLs, then run `python scripts/e2e_test.py`. Do not start local ingest/analytics/rlm for testing.
- In docs and instructions, prefer the Railway-only flow; treat "run services locally" as legacy or emergency-only, not the default.
- Before using Railway CLI or MCP, read the **use-railway** skill (.cursor/skills/use-railway/SKILL.md) for preflight (auth, link, context), common commands, and execution rules.
- Default to non-production usage; do not assume production deployment permissions or automate production changes without explicit user direction.

**Do not:** Start uvicorn/bun dev servers for ingest, analytics, rlm, mcp, or web locally for E2E or general testing; use deployed Railway services instead.

**Full procedure:** docs/engineering-system/railway-usage-policy.md; skill: use-railway; docs/DEPLOY_AND_TEST.md.
