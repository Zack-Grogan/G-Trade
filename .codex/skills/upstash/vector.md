# Upstash Vector

Use the official `@upstash/vector` SDK for vector storage and similarity search (embeddings, RAG).

## Install

```bash
npm install @upstash/vector
```

## Client and index

```typescript
import { Index } from "@upstash/vector";

const index = new Index({
  url: process.env.UPSTASH_VECTOR_REST_URL!,
  token: process.env.UPSTASH_VECTOR_REST_TOKEN!,
});
```

## Upsert

```typescript
await index.upsert({
  id: "doc-1",
  vector: [0.1, 0.2, ...],
  metadata: { title: "Example", genre: "docs" },
});
```

## Query

```typescript
const results = await index.query({
  vector: [...],
  topK: 5,
  includeMetadata: true,
});
```

Use `data` for auto-embedding when supported. Keep URL and token in env; document in README. Do not implement a custom vector REST client.
