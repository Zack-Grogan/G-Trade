# Upstash Workflow

Use the official `@upstash/workflow` SDK for durable, reliable serverless workflows with automatic retries and state.

## Install

```bash
npm install @upstash/workflow
```

## Define a workflow (Next.js example)

```typescript
import { serve } from "@upstash/workflow/nextjs";

export const { POST } = serve<string>(async (context) => {
  const input = context.requestPayload;

  const result1 = await context.run("step-1", async () => {
    return someWork(input);
  });

  await context.run("step-2", async () => {
    return someOtherWork(result1);
  });
});
```

## Step types

- `context.run(id, fn)` — execute a function (result persisted)
- `context.sleep(duration)` — wait for a duration
- `context.sleepUntil(timestamp)` — wait until a time
- `context.waitForEvent(name)` / `context.notify(name, payload)` — event-based continuation

Run steps sequentially with `await` or in parallel with `Promise.all()`. Use env for workflow credentials; do not build a custom durable runner.
