# Upstash Rate Limit

Use the official `@upstash/ratelimit` SDK with an Upstash Redis instance. Supports fixed-window and sliding-window algorithms.

## Install

```bash
npm install @upstash/ratelimit @upstash/redis
```

## Setup

```typescript
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const redis = Redis.fromEnv();
const ratelimit = new Ratelimit({
  redis,
  limiter: Ratelimit.fixedWindow(10, "10 s"),  // 10 requests per 10s
  // or: Ratelimit.slidingWindow(10, "10 s"),
});
```

## Use

```typescript
const { success, limit, remaining, reset } = await ratelimit.limit(identifier);
if (!success) {
  return new Response("Too Many Requests", { status: 429 });
}
```

Use a stable `identifier` per user or IP (e.g. `userId`, `ip`). For multi-region, prefer fixed window. Do not implement custom rate limiting against Redis when this SDK exists.
