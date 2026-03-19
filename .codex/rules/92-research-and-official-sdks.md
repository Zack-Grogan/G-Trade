---
description: Research first; use official SDKs and current APIs. Never trust training data for package names, versions, or API shape.
globs: railway/**/*
alwaysApply: false
---

# Research and official SDKs only

**When this applies:** Any integration with an external service, API, or framework (QStash, UpStash Redis/Vector, Daytona, x.ai, LangChain, etc.).

**Do this:**
- **Use the official SDK or documented API.** Prefer the vendor's Python/JS SDK over hand-rolled HTTP unless the docs explicitly show only REST. Check PyPI/npm for the canonical package name and use the **latest or latest LTS** version in requirements.
- **Verify from current docs.** Before implementing, open the official docs (or run a targeted web search for "[Service] Python SDK publish" / "API reference 2025"). Confirm method names, env vars, and response shapes. Do not rely on training data for "how QStash works" or "how Daytona SDK is imported." APIs and package names change; training data is often outdated.
- **Pin versions in requirements.** After choosing the correct package, add it to `requirements.txt` or `package.json` with a version range that targets latest stable (e.g. `qstash>=3.0.0`, `daytona-sdk>=0.1.0`). Resolve dependency conflicts by dropping or replacing conflicting deps (e.g. if `upstash-workflow` requires `qstash<3`, remove or replace it rather than downgrading the primary SDK).

**Do not:**
- Invent import paths (e.g. `from daytona import Daytona` when the real SDK is `from daytona_sdk import Daytona, DaytonaConfig`).
- Use deprecated or undocumented APIs because "it used to work."
- Add integration code without confirming the current SDK/docs first.

**Full procedure:** 1) Search or fetch official docs. 2) Install the official package. 3) Implement using the documented API. 4) Wire the client into a real route/job/CLI (see no-dead-code rule).
