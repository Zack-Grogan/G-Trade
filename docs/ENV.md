# Environment variables

Reference for all services. Copy from `.env.example` and set values.

| Variable | Where used | Required | You have (.env) |
|----------|------------|----------|-----------------|
| `DATABASE_URL` | ingest, analytics, rlm | Yes (Railway) | Set in Railway |
| `GTRADE_INTERNAL_API_TOKEN` | bridge, ingest, analytics, rlm | Yes | Add if missing |
| `ANALYTICS_API_KEY` | analytics (REST + GraphQL auth), web server, mcp outbound | Yes | Add if missing |
| `MCP_AUTH_TOKEN` | mcp inbound auth | Yes | Add if missing |
| `RLM_SERVICE_URL` | analytics query helpers, web operator chat, mcp RLM tools | Yes for RLM-linked features | Set to RLM deploy URL |
| `RLM_AUTH_TOKEN` | analytics/web/mcp optional auth when calling RLM | No | Add if RLM is bearer-protected |
| `OPENROUTER_API_KEY` | rlm (batch report model) | Yes for reports | ✓ |
| `RLM_AI_PROVIDER` | rlm (model provider) | No | Defaults to `openrouter` |
| `RLM_AI_MODEL` | rlm (model name) | No | Defaults to `openai/gpt-5.4-mini` |
| `RLM_AI_TEMPERATURE` | rlm (report synthesis) | No | Defaults to `0` |
| `QSTASH_TOKEN` | rlm (replay worker) | Yes for async replay | ✓ |
| `QSTASH_URL` | rlm (optional) | No | Optional |
| `RLM_REPLAY_WORKER_URL` | rlm (QStash callback) | Yes for trigger replay | Set to RLM deploy URL + `/replay/worker` |
| `UPSTASH_REDIS_REST_URL` | rlm (cache) | No | Create in UpStash if needed |
| `UPSTASH_REDIS_REST_TOKEN` | rlm | No | — |
| `DAYTONA_API_KEY` | rlm (what-if) | No (optional) | ✓ |
| `CLERK_*` | web | Yes for auth | ✓ |
| `ANALYTICS_API_URL` | web operator console, mcp outbound | Yes | Set to analytics deploy URL |

**Local outbox:** The durable outbox and sync-to-Railway logic live in **es-hotzone-trader** (`src/bridge/outbox.py`, `railway_bridge.py`). There is no separate local SQLite in G-Trade.

**Vector store:** The critical similarity path is now Postgres-backed (`pgvector` target). Upstash Vector is no longer part of the required env contract for core RLM retrieval.

**Railway:** Set `DATABASE_URL`, `GTRADE_INTERNAL_API_TOKEN`, `ANALYTICS_API_KEY`, `MCP_AUTH_TOKEN`, `RLM_SERVICE_URL`, optional `RLM_AUTH_TOKEN`, `OPENROUTER_API_KEY`, `RLM_AI_PROVIDER`, `RLM_AI_MODEL`, `QSTASH_TOKEN`, `RLM_REPLAY_WORKER_URL` (and optionally Redis) in each service’s env. For RLM, `RLM_REPLAY_WORKER_URL` must be the **public** URL of the RLM service + `/replay/worker` (e.g. `https://g-trade-rlm-xxx.up.railway.app/replay/worker`).

**Local CLI (es-hotzone-trader):** Set `observability.railway_ingest_url` and `observability.internal_api_token` (or env `GTRADE_INTERNAL_API_TOKEN`) so the Mac app can send state/events/trades/runtime logs to Railway. Legacy ingest-key auth is no longer accepted by the Railway ingest service.
