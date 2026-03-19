---
description: OpenViking is durable repo knowledge via MCP; prefer repo docs first; use OpenViking when cross-repo or durable search helps.
alwaysApply: false
---

# OpenViking knowledge usage

**When this applies:** Cross-repo or durable search; or user asks for status, progress, or analysis that benefits from indexed knowledge.

**Do this:**
- Prefer repo docs (docs/) and generated maps (docs/generated/) first. Use OpenViking via MCP when the task benefits from cross-repo or durable search.
- Apply the **use-openviking** skill (.cursor/skills/use-openviking/). Do not replace Cursor's native repo understanding; use OpenViking to augment.
- OpenViking is not an app runtime dependency; the repo does not depend on it at runtime.

**Full procedure:** docs/engineering-system/openviking-integration.md; skill: use-openviking.
