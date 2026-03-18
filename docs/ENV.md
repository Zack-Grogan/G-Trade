# Environment variables

Reference for all services. Copy from `.env.example` and set values.

| Variable | Where used | Required | You have (.env) |
|----------|------------|----------|-----------------|
| `DATABASE_URL` | ingest, analytics, rlm | Yes (Railway) | Set in Railway |
| `INGEST_API_KEY` | ingest (auth), bridge/CLI | Yes | Add if missing |
| `ANALYTICS_API_KEY` | analytics (auth), web server | Yes | Add if missing |
| `X_AI_API_KEY` | rlm (Grok) | Yes | ✓ |
| `QSTASH_TOKEN` | rlm (replay worker) | Yes for async replay | ✓ |
| `QSTASH_URL` | rlm (optional) | No | Optional |
| `RLM_REPLAY_WORKER_URL` | rlm (QStash callback) | Yes for trigger replay | Set to RLM deploy URL + `/replay/worker` |
| `UPSTASH_REDIS_REST_URL` | rlm (cache) | No | Create in UpStash if needed |
| `UPSTASH_REDIS_REST_TOKEN` | rlm | No | — |
| `UPSTASH_VECTOR_REST_URL` | rlm (semantic search) | No | — |
| `UPSTASH_VECTOR_REST_TOKEN` | rlm | No | — |
| `DAYTONA_API_KEY` | rlm (what-if) | No (optional) | ✓ |
| `CLERK_*` | web | Yes for auth | ✓ |
| `ANALYTICS_API_URL` | web (RLM page) | Yes | Set to analytics deploy URL |
| `RAILWAY_INGEST_URL` | bridge (es-hotzone-trader) | Yes for bridge | Set to ingest deploy URL |

**Local outbox:** The durable outbox and sync-to-Railway logic live in **es-hotzone-trader** (`src/bridge/outbox.py`, `railway_bridge.py`). There is no separate local SQLite in G-Trade.

**Railway:** Set `DATABASE_URL`, `INGEST_API_KEY`, `ANALYTICS_API_KEY`, `X_AI_API_KEY`, `QSTASH_TOKEN`, `RLM_REPLAY_WORKER_URL` (and optionally Redis/Vector) in each service’s env. For RLM, `RLM_REPLAY_WORKER_URL` must be the **public** URL of the RLM service + `/replay/worker` (e.g. `https://g-trade-rlm-xxx.up.railway.app/replay/worker`).

**Local CLI (es-hotzone-trader):** Set `RAILWAY_INGEST_URL` and `INGEST_API_KEY` (or bridge config) so the Mac app can send state/events/trades to Railway.
