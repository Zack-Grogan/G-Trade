# Upstash Redis

Use the official `@upstash/redis` SDK. Serverless-friendly (HTTP/REST); no persistent connection.

## Install

```bash
npm install @upstash/redis
```

## Client

```typescript
import { Redis } from "@upstash/redis";

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});
// Or: Redis.fromEnv()
```

## Common operations

- **Strings:** `redis.set('key', 'value')`, `redis.get('key')`
- **Lists:** `redis.lpush('list', 'item')`, `redis.lrange('list', 0, -1)`
- **Hashes:** `redis.hset('hash', { field: 'value' })`, `redis.hget('hash', 'field')`
- **Sets:** `redis.sadd('set', 'member')`, `redis.smembers('set')`
- **Sorted sets:** `redis.zadd('scores', { score: 1, member: 'id' })`, `redis.zrange('scores', 0, -1)`
- **TTL:** `redis.set('key', 'value', { ex: 3600 })` or `redis.expire('key', 3600)`

Use env vars for URL and token; document in README. Do not implement a custom REST client.
