# Deploy and A-to-Z test

## 1. Environment

- Copy `.env.example` to `.env` and set values. See [ENV.md](ENV.md) for what’s required per service.
- **Railway:** Set `DATABASE_URL` (from Postgres), `INGEST_API_KEY`, `ANALYTICS_API_KEY`, `OPENROUTER_API_KEY`, `RLM_AI_PROVIDER`, `RLM_AI_MODEL`, `QSTASH_TOKEN`, and for RLM `RLM_REPLAY_WORKER_URL` = RLM service public URL + `/replay/worker`.

## 2. Railway deploy

- **Ingest:** Root = `railway/ingest`, start = `uvicorn app:app --host 0.0.0.0 --port $PORT`. Env: `DATABASE_URL`, `INGEST_API_KEY`.
- **Analytics:** Root = `railway/analytics`, start = `uvicorn app:app --host 0.0.0.0 --port $PORT`. Env: `DATABASE_URL`, `ANALYTICS_API_KEY`, `RLM_SERVICE_URL` = RLM service URL (e.g. `https://g-trade-rlm-xxx.up.railway.app`).
- **RLM:** Root = `railway/rlm`, start = `uvicorn app:app --host 0.0.0.0 --port $PORT` (or use `Procfile`). Env: `DATABASE_URL`, `OPENROUTER_API_KEY`, `RLM_AI_PROVIDER`, `RLM_AI_MODEL`, `QSTASH_TOKEN`, `RLM_REPLAY_WORKER_URL` (RLM public URL + `/replay/worker`). Optional: `UPSTASH_REDIS_*`, `UPSTASH_VECTOR_*`, `DAYTONA_API_KEY`.

After deploy, set `RLM_REPLAY_WORKER_URL` and `RLM_SERVICE_URL` to the RLM and analytics URLs.

## 3. A-to-Z test (E2E)

**E2E must run against Railway only.** The script exits with an error if `INGEST_URL` or `ANALYTICS_URL` are unset or point to localhost. From repo root:

```bash
export INGEST_URL=https://g-trade-ingest-production.up.railway.app
export ANALYTICS_URL=https://g-trade-analytics-production.up.railway.app
# Optional once RLM is deployed:
export RLM_URL=https://g-trade-rlm-xxx.up.railway.app
export INGEST_API_KEY=your-ingest-key
export ANALYTICS_API_KEY=your-analytics-key
python scripts/e2e_test.py
```

The script checks: health (ingest, analytics, and RLM if `RLM_URL` set), ingest state POST (if key set), analytics `/runs`, GraphQL `runs`, RLM report and hypothesis endpoints when `RLM_URL` is set.

The analytics service now also exposes `/runs/{run_id}/state_snapshots` and `/runs/{run_id}/timeline`, which the web dashboard and MCP layer use to reconstruct blockers, unresolved entries, and missed fills from the same run id.

## 4. Local CLI (es-hotzone-trader)

The `es-trade` CLI and **data bridge + outbox** live in the **es-hotzone-trader** repo (sibling or separate clone). That repo has the single local SQLite outbox and sync-to-Railway logic; G-Trade does not add a second one. To send data to Railway:

1. In that repo, set ingest URL and key (e.g. in its `.env` or config):
   - `RAILWAY_INGEST_URL` = your ingest deploy URL
   - `INGEST_API_KEY` = same key as Railway ingest service
2. Run the CLI (e.g. `es-trade start` or as documented there). The bridge will POST state/events/trades to Railway ingest.
3. After a run, use the same `run_id` in analytics/RLM or trigger replay from the RLM API.

## 5. UpStash / Daytona

- **UpStash:** Create Redis (and optionally Vector) in the UpStash dashboard; add `UPSTASH_REDIS_REST_URL`/`UPSTASH_REDIS_REST_TOKEN` (and Vector vars) to RLM env for cache and semantic search.
- **Daytona:** RLM uses `DAYTONA_API_KEY` for what-if sandbox. Set in RLM env; optional for core RLM.

---

## 6. Deployment readiness checklist

**Before first deploy:**

1. **Postgres** — In Railway project, add Postgres (or use existing). Copy `DATABASE_URL` into each service that needs it.
2. **UpStash** — In [UpStash Console](https://console.upstash.com): create QStash (used for replay worker callbacks). Optionally create Redis and Vector for RLM; add their URLs/tokens to RLM env.
3. **Env per service** (set in Railway dashboard or CLI):
   - **ingest:** `DATABASE_URL`, `INGEST_API_KEY`
   - **analytics:** `DATABASE_URL`, `ANALYTICS_API_KEY`, `RLM_SERVICE_URL` (RLM public URL)
   - **rlm:** `DATABASE_URL`, `OPENROUTER_API_KEY`, `RLM_AI_PROVIDER`, `RLM_AI_MODEL`, `QSTASH_TOKEN`, `RLM_REPLAY_WORKER_URL` (RLM public URL + `/replay/worker`). Optional: `UPSTASH_REDIS_*`, `UPSTASH_VECTOR_*`, `DAYTONA_API_KEY`
   - **mcp:** per existing MCP setup
   - **web:** `ANALYTICS_API_URL`, `ANALYTICS_API_KEY`, Clerk vars

**Deploy order (if using Railway CLI from repo root):**

1. Deploy **ingest** (so schema can run if it applies there), then **analytics** (applies schema_v2), then **rlm**, then **mcp**, then **web**.
2. After RLM is live, set **RLM_REPLAY_WORKER_URL** in RLM to the RLM service URL + `/replay/worker`, and **RLM_SERVICE_URL** in analytics to the RLM service URL.

**E2E against production:** Set `INGEST_URL`, `ANALYTICS_URL`, `RLM_URL`, `INGEST_API_KEY`, `ANALYTICS_API_KEY` to your deployed URLs and keys, then run `python scripts/e2e_test.py`.
