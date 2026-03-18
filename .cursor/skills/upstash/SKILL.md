---
name: use-upstash
description: >
  Uses Upstash serverless data and messaging SDKs (Redis, QStash, Rate Limit,
  Workflow, Vector, Search). Use when the user mentions Upstash, Redis cache,
  message queues, rate limiting, workflows, vector DB, or full-text search.
  Route to the matching sub-skill; do not ask for REST URLs or tokens to write
  custom clients.
---

# Use Upstash

When working with Upstash services, use the official SDKs and this skill's sub-pages. Do not request `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, or other credentials to build custom HTTP clients.

## Routing

| User intent / keywords | Reference |
|------------------------|-----------|
| Redis, cache, key-value, session store | [redis.md](redis.md) |
| QStash, message queue, pub/sub, webhooks, scheduled jobs | [qstash.md](qstash.md) |
| Rate limit, throttling, DDoS protection, abuse prevention | [ratelimit.md](ratelimit.md) |
| Workflow, durable execution, step functions | [workflow.md](workflow.md) |
| Vector, embeddings, semantic search, RAG | [vector.md](vector.md) |
| Full-text search, faceted search, search index | [search.md](search.md) |

Load the matching reference and follow its patterns. If the task spans two products (e.g. Redis + Rate Limit), load both.

## Env convention

Credentials come from environment variables. Document them in README or OPERATOR; do not hardcode. Typical names:

- Redis: `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`
- QStash: `QSTASH_URL`, `QSTASH_TOKEN`
- Rate Limit: often same Redis or separate token per product docs
