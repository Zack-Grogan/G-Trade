# Upstash Search

Use the official `@upstash/search` SDK for full-text and semantic search over an index.

## Install

```bash
npm install @upstash/search
```

## Client and index

```typescript
import { Search } from "@upstash/search";

const client = new Search({
  url: process.env.UPSTASH_SEARCH_REST_URL!,
  token: process.env.UPSTASH_SEARCH_REST_TOKEN!,
});
const index = client.index("movies");
```

## Search

```typescript
const results = await index.search({
  query: "space opera",
  limit: 10,
  filter: { genre: "sci-fi" },
});
```

## Index operations

- `index.upsert([{ id, data, metadata }])` — add/update documents
- `index.fetch({ ids })` — fetch by ID
- `index.delete({ ids })` — delete by ID

Use env for URL and token; document in README. Do not build a custom search REST client.
