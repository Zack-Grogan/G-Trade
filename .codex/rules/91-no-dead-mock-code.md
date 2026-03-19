---
description: No dead, stub, or mock code. Every module must be imported and used in a real code path; delete or wire it.
globs: railway/**/*
alwaysApply: false
---

# No dead / mock / stub code

**When this applies:** Adding or refactoring any module, client, or "integration" that talks to an external service or implements a feature.

**Do this:**
- **Wire before ship.** If you add `foo_client.py` or a function `run_what_if_in_sandbox`, ensure some **caller** imports and uses it in a real path: e.g. an HTTP handler, a background job, or a CLI command. Grep for the module or function name; if nothing references it, add the call site or remove the code.
- **No "for later" stubs.** Avoid "TODO: wire this" or "we'll use this when we add X." Either implement the call site now or don't add the module.
- **Mocks only in tests.** Test doubles (mocks, fakes) are allowed only inside test files or test helpers, never in production code paths as the only "usage."

**Do not:**
- Add a client or helper that is never imported.
- Add an endpoint that returns hardcoded or placeholder data without calling the real service or SDK.
- Leave a BaaS/SDK integration in the codebase with no route, job, or command that invokes it.

**Check before PR:** For every new file under `railway/` or any `*_client.py`, confirm there is at least one `import` or call in a live code path (app route, worker, CLI).
