---
description: For any third-party framework, BaaS, or external service — research how it works right now; never assume from training data.
globs: "**/*"
alwaysApply: false
---

# Third-party / BaaS / frameworks — research first

**When this applies:** Adding or changing integration with any third-party: SDK, BaaS (UpStash, Daytona, Neon, Redis, etc.), API, or framework (LangChain, FastAPI, etc.).

**Do this:**
- **Research before coding.** Use web search or official docs (fetch URLs) to confirm current behavior as of **today** (e.g. March 2026). Do not rely on training data for API shapes, package names, or env vars.
- **Identify the official surface:** Official docs URL, SDK package name (PyPI/npm), and the **latest stable or LTS** version. Prefer latest LTS over "latest" when the project offers it.
- **Understand our setup and beyond:** Document what we need for our setup and at least one "we could also do X" so the integration is extensible, not a one-off stub.
- **Wire it.** Every client or adapter must be **imported and used** somewhere in a real code path (e.g. an HTTP route, a worker, or a CLI command). No "we might use this later" files that nothing calls.

**Do not:**
- Guess package names (`daytona` vs `daytona_sdk`), import paths, or env var names from memory.
- Add a new dependency or client module without adding a call site that actually uses it in a user- or system-visible flow.

**Full procedure:** Before writing integration code, run a quick search or doc fetch for "[Service] Python SDK 2025" or "[Service] official documentation"; then implement against the current API and wire the module into at least one real endpoint or job.
