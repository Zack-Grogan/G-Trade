# Railway services: what’s actually built

Honest assessment of what’s in `railway/` (and what gets deployed from the g-trade-* repos).

## Ingest (`railway/ingest` → g-trade-ingest)

**Fully built.** Single FastAPI app in `app.py`:

- `POST /ingest/state`, `/ingest/events`, `/ingest/trades` — contract matches the Mac bridge.
- Bearer auth via `INGEST_API_KEY`.
- `schema.sql` applied on startup (runs, events, state_snapshots, completed_trades).
- No `main.py`; app is `app:app`. Railway was defaulting to `main:app` and crashing; start command was overridden to `uvicorn app:app --host 0.0.0.0 --port $PORT`.

**Verdict:** Production-ready for the current contract. No placeholder behavior.

---

## Analytics (`railway/analytics` → g-trade-analytics)

**Fully built.** Single FastAPI app in `app.py`:

- Read-only: `GET /runs`, `/runs/{id}`, `/runs/{id}/events`, `/runs/{id}/trades`, `/analytics/summary`, `/health`.
- Bearer auth via `ANALYTICS_API_KEY`.
- Same `app:app`; start command overridden like ingest.

**Verdict:** Production-ready. No placeholder behavior.

---

## MCP (`railway/mcp` → g-trade-mcp)

**Fully built.** Single FastAPI app in `app.py`:

- `POST /mcp` — JSON-RPC (initialize, tools/list, tools/call, resources/list, resources/read).
- Tools: `list_runs`, `query_events`, `get_performance_summary`, `get_runtime_summary`, `get_run_context` — all proxy to the analytics API.
- Bearer auth via `ANALYTICS_API_KEY` (or MCP_AUTH_TOKEN if the server is updated to accept it).
- **Gap:** Requires `ANALYTICS_API_URL` to be set (e.g. `https://${{g-trade-analytics.RAILWAY_PUBLIC_DOMAIN}}` or the analytics service public URL). Without it, tool calls return empty.

**Verdict:** App is complete; deployment needs `ANALYTICS_API_URL` wired.

---

## Web (`railway/web` → g-trade-web)

**Updated: Clerk auth, Next 16, Bun.**

- **Structure:** Next.js 16 App Router: `src/app/page.tsx`, `src/app/layout.tsx`, `next.config.js` (standalone), `package.json` with `next build` / `next start`. Not “manually coded” in a broken way.
- **Content:** One page: “G-Trade” and a line saying to configure ANALYTICS_API_URL. No components that call the analytics API, no runs/events/trades UI, no auth wiring.
- **Deploy failure:** Railway blocked deploy due to Next.js 14.2.0 CVEs; upgrade to `next@14.2.35` (or later patched 14.x) is required. That’s a dependency fix, not a structural rewrite.

**Verdict:** Correct Next.js setup, but the app is a placeholder. A “real” dashboard would add pages that call the analytics API (with ANALYTICS_API_KEY) and render runs, events, and trades. **Next.js** was upgraded to `14.2.35` in this repo’s `railway/web/package.json` to fix the Railway security gate; if g-trade-web is deployed from a separate GitHub repo, apply the same upgrade there and push.

---

## Summary

| Service   | Code state        | Deploy / config notes                                      |
|----------|--------------------|------------------------------------------------------------|
| ingest   | Full app           | Start command fixed to `uvicorn app:app`; keys set         |
| analytics| Full app           | Start command fixed; keys set                              |
| mcp      | Full app           | Set `ANALYTICS_API_URL` to analytics public (or private) URL |
| web      | Placeholder UI     | Upgrade Next to 14.2.35+; then expand to real dashboard    |

So: ingest, analytics, and mcp are real, deployable apps. Web is a valid but minimal Next app; the “build up” (deploy, keys, start commands) is for those three. Web is currently “almost nothing” in terms of UI; fixing Next and then building out the dashboard would make it a full app.
