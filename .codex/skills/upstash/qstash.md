# Upstash QStash

Use the official `@upstash/qstash` SDK for serverless message queue, webhooks, and scheduled jobs.

## Install

```bash
npm install @upstash/qstash
```

## Client

```typescript
import { Client } from "@upstash/qstash";

const client = new Client({ token: process.env.QSTASH_TOKEN! });
```

## Publish (HTTP callback)

```typescript
await client.publishJSON({
  url: "https://your-api.com/webhook",
  body: { event: "order.created" },
  headers: { "X-Custom": "value" },
  delay: "5m",        // optional
  retries: 3,
  callback: "https://your-api.com/callback",  // optional
});
```

## Schedules (cron)

```typescript
await client.schedules.create({
  destination: "https://your-api.com/cron",
  cron: "0 * * * *",  // every hour
});
```

Use `QSTASH_TOKEN` from env; document in README. Do not build a custom HTTP client for QStash.
