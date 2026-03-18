---
name: RLM Analytics Platform Migration
overview: "Add Recursive Learning Module (RLM) to G-Trade Railway: hypothesis generation, conclusions, replay, benchmark, and what-if sandbox. Every third-party integration must be researched from current docs (2026), use official SDKs only, and be wired into real routes/jobs — no dead or mock code."
todos:
  - id: rlm-rules-baseline
    content: "Baseline: Follow .cursor/rules 90, 91, 92 and 00 (research, no dead code, official SDKs, never trust training data)."
    status: pending
  - id: rlm-schema-v2
    content: "Extend Postgres schema (schema_v2) with RLM tables: hypotheses, experiments, knowledge_store, trade_embeddings, replay_runs; apply from analytics or rlm service."
    status: pending
  - id: rlm-service-skeleton
    content: "Create railway/rlm FastAPI service with health, config; deployable as g-trade-rlm (same repo, Root=railway/rlm, uvicorn app:app)."
    status: pending
  - id: rlm-xai-research-wire
    content: "x.ai Grok: Research current API (api.x.ai) and SDK (e.g. langchain-xai, OpenAI-compatible). Implement grok_client using official client; wire into hypothesis generation and conclusion graph."
    status: pending
  - id: rlm-upstash-research-wire
    content: "UpStash: Research QStash (publish, callbacks), Redis, Vector SDKs (PyPI names, env vars). Use qstash>=3, upstash-redis, upstash-vector. Wire: QStash → replay worker URL; Redis/Vector only if used in a live path (e.g. similar_trades)."
    status: pending
  - id: rlm-daytona-research-wire
    content: "Daytona: Research current Python SDK (daytona_sdk, DaytonaConfig, create/code_run/delete). Wire daytona_client.run_what_if_in_sandbox into POST /replay/what-if so the endpoint actually calls the SDK."
    status: pending
  - id: rlm-semantic-search
    content: "Semantic search: Trade embeddings via Grok (or documented embedding API); store in Postgres + Upstash Vector if used. similar_trades endpoint must call embedding_service and return real results (no stub)."
    status: pending
  - id: rlm-graphql-analytics
    content: "Add GraphQL to g-trade-analytics: schema, resolvers; RLM_SERVICE_URL for similar_trades and generateHypothesis. Resolvers must call RLM HTTP client (httpx) to live RLM URL."
    status: pending
  - id: rlm-replay-migrate
    content: "Replay: list_replayable_checkpoints, trigger_replay (QStash publish to RLM_REPLAY_WORKER_URL), replay worker endpoint that runs handle_replay_request. All call sites must exist (API → worker, benchmark → handle_replay_request)."
    status: pending
  - id: rlm-meta-learner-feedback
    content: "Meta-learner and feedback loop: Persist verdicts in knowledge_store; meta_learner stats read by hypothesis graph. Advisory-only; no executor changes."
    status: pending
  - id: rlm-web-ui
    content: "Web: RLM analytics page calls ANALYTICS_API_URL (GraphQL or REST) with auth; display hypotheses, runs, conclusions. Server-side env must point at live analytics."
    status: pending
  - id: rlm-langgraph
    content: "LangGraph: Use current langgraph/langchain-xai versions; hypothesis and conclusion graphs must invoke Grok via verified client. No mock responses in production path."
    status: pending
  - id: rlm-benchmark-e2e
    content: "Benchmark and E2E: GET /benchmark/checkpoints, POST /benchmark/run (sync replay); scripts/e2e_test.py hits ingest, analytics, RLM health + endpoints. Document INGEST_URL, ANALYTICS_URL, RLM_URL, auth keys."
    status: pending
  - id: rlm-verify-no-dead-code
    content: "Verification: Grep every *_client and integration module; confirm each is imported and used in a route, worker, or CLI. Remove or wire any that are not."
    status: pending
isProject: false
---

# RLM Analytics Platform Migration — Plan (Redone)

This plan adds the Recursive Learning Module (RLM) to the G-Trade Railway stack. It is **redone** to enforce:

1. **Research first** — No relying on training data. For every third-party (UpStash, Daytona, x.ai, LangChain/LangGraph), confirm current SDK and API from official docs (as of 2026).
2. **Official SDKs only** — Use the vendor’s Python package and documented API; no hand-rolled HTTP unless the vendor only provides REST.
3. **No dead or mock code** — Every client or integration must be **imported and used** in a real code path (HTTP route, QStash worker, or CLI). If nothing calls it, delete it or add the call site.
4. **Never trust training data** — Pin latest or latest LTS versions; verify package names and import paths (e.g. `daytona_sdk` not `daytona`).

---

## 1. Scope and invariants

- **RLM is advisory-only.** It produces hypotheses, conclusions, and recommendations. It does **not** change execution config or strategy on the Mac.
- **Data flow:** Mac → Railway ingest → Postgres. RLM (and analytics) read from Postgres; RLM may call out to x.ai, UpStash, Daytona.
- **Single-operator auth** on all Railway surfaces (ingest, analytics, RLM, MCP, web).

---

## 2. Third-party integrations — research and wire matrix

Before implementing any row, **research current docs** (web search or fetch official URL). Then implement with **official SDK** and **wire** the module into the listed call site.

| Integration | Research (current docs) | Official SDK / API | Call site (must exist) |
|-------------|-------------------------|--------------------|-------------------------|
| **x.ai Grok** | api.x.ai, OpenAI-compatible; embedding if used | langchain-xai and/or httpx to api.x.ai | grok_client used by hypothesis_graph, conclusion_graph, embedding_service |
| **QStash** | UpStash QStash docs: publish, callbacks, Python SDK | qstash (PyPI); QStash token env | replay_api.trigger_replay → publish to RLM_REPLAY_WORKER_URL |
| **UpStash Redis** | Optional cache/rate limit | upstash-redis, from_env() | Only if a live path uses redis_get/redis_set (e.g. memory_graph); else omit |
| **UpStash Vector** | Index API, Python SDK | upstash-vector, from_env() | embedding_service vector_upsert/vector_query used by similar_trades |
| **Daytona** | Daytona SDK docs: create, code_run, delete | daytona_sdk (Daytona, DaytonaConfig) | daytona_client.run_what_if_in_sandbox called from POST /replay/what-if |
| **LangGraph / LangChain** | LangGraph + LangChain x.ai integration | langgraph, langchain-core, langchain-xai | hypothesis_graph, conclusion_graph import and invoke; no mock in prod |

**Dependency rule:** Resolve conflicts (e.g. qstash 3 vs upstash-workflow requiring qstash<3) by dropping or replacing the conflicting dependency, not by downgrading the primary SDK we rely on.

---

## 3. Services and code paths

### 3.1 g-trade-rlm (railway/rlm)

- **Purpose:** Hypothesis generation, conclusions, replay worker, benchmark, similar_trades, what-if sandbox.
- **Endpoints (all must call real logic, no stubs):**
  - `GET /health` — live
  - `GET /config` — non-secret config
  - `POST /feedback/cycle` — workflow_orchestrator.run_one_feedback_cycle
  - `POST /hypotheses/generate` — graphs.invoke_hypothesis_graph (Grok)
  - `GET /benchmark/checkpoints` — replay_api.list_replayable_checkpoints
  - `POST /benchmark/run` — benchmark.run_full_benchmark (sync replay)
  - `GET /replay/checkpoints` — replay_api.list_replayable_checkpoints
  - `POST /replay/trigger` — replay_api.trigger_replay (QStash publish)
  - `POST /replay/what-if` — **must call** daytona_client.run_what_if_in_sandbox
  - `POST /replay/worker` — replay_worker.handle_replay_request (QStash callback)
  - `GET /similar_trades` — embedding_service.find_similar_trades (Grok + Vector/DB)
- **Env:** DATABASE_URL, X_AI_API_KEY, QSTASH_TOKEN, RLM_REPLAY_WORKER_URL; optional UPSTASH_REDIS_*, UPSTASH_VECTOR_*, DAYTONA_API_KEY.
- **No dead code:** Every *_client and helper is imported in app.py or in a module that app.py uses.

### 3.2 g-trade-analytics

- **Purpose:** Read-only API + GraphQL over Postgres; GraphQL resolvers call RLM for similar_trades and generateHypothesis.
- **RLM_SERVICE_URL** must point at g-trade-rlm. Resolvers use httpx to call RLM; no mock.

### 3.3 Web (g-trade-web)

- **RLM page** calls analytics (GraphQL or REST) with server-side ANALYTICS_API_URL and ANALYTICS_API_KEY; displays hypotheses, runs, conclusions.

---

## 4. Phased execution (research → implement → wire)

1. **Baseline rules** — Confirm .cursor/rules 90, 91, 92 and 00 are in place; all work follows them.
2. **Schema** — Add RLM tables (hypotheses, experiments, knowledge_store, trade_embeddings, replay_runs) in schema_v2; apply on analytics or rlm startup.
3. **RLM service** — Create railway/rlm with FastAPI, health/config; deployable as g-trade-rlm.
4. **x.ai Grok** — Research current API/SDK; implement grok_client; wire into hypothesis and conclusion graphs and embedding_service.
5. **UpStash** — Research QStash 3, Redis, Vector; implement upstash_client; wire QStash to replay trigger and worker; Redis/Vector only where a live path uses them.
6. **Daytona** — Research current Python SDK; implement daytona_client with official package; **wire** run_what_if_in_sandbox into POST /replay/what-if.
7. **Semantic search** — similar_trades endpoint uses embedding_service (Grok + Postgres/Vector); no stub response.
8. **GraphQL** — Analytics GraphQL resolvers call RLM via RLM_SERVICE_URL (httpx).
9. **Replay and benchmark** — trigger_replay → QStash → worker; benchmark/run → sync handle_replay_request; list checkpoints from Postgres.
10. **Meta-learner and feedback** — Persist verdicts; hypothesis graph reads meta stats; advisory only.
11. **Web RLM page** — Real API calls to analytics; no placeholder data.
12. **E2E and verification** — scripts/e2e_test.py; grep for every *_client and integration to ensure each has a call site; remove or wire.

---

## 5. Verification checklist (no dead code)

Before considering RLM migration complete:

- [ ] Every file under railway/rlm that ends in `_client.py` or provides an external integration is **imported** somewhere in a code path that handles a request or job.
- [ ] POST /replay/what-if **calls** daytona_client.run_what_if_in_sandbox (and Daytona SDK is the official one, researched from current docs).
- [ ] QStash publish uses the official qstash package and RLM_REPLAY_WORKER_URL; worker endpoint runs handle_replay_request.
- [ ] similar_trades returns data from embedding_service (and optionally Vector); not a hardcoded empty list or stub.
- [ ] Hypothesis and conclusion graphs use a real Grok client (researched API/SDK), not mock or training-data assumptions.
- [ ] requirements.txt (or equivalent) pins latest or LTS versions for qstash, daytona-sdk, upstash-redis, upstash-vector, langchain-xai, langgraph; no deprecated or guessed package names.

---

## 6. References

- RLM theory: docs/theory-plans/RLM-analytics.md
- Env and deploy: docs/ENV.md, docs/DEPLOY_AND_TEST.md
- Rules: .cursor/rules/90-third-party-baas-research.mdc, 91-no-dead-mock-code.mdc, 92-research-and-official-sdks.mdc, 00-core-operating-contract.mdc
