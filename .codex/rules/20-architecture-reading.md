---
description: Before structural or architecture-touching changes, read the architecture and current-state docs. Dispatch to software-architect, backend-architect, or frontend-developer for architecture design/review.
alwaysApply: false
---

# Architecture reading

**When this applies:** Changing module boundaries, config surface, deployment topology, or execution/data-flow paths.

**Do this:**
- Read docs/architecture/overview.md (or docs/Architecture-Overview.md), docs/Current-State.md, and AGENTS.md "Architecture rules" and "What to touch / What not to do."
- Do not move execution or broker logic to Railway; do not add unauthenticated endpoints.
- Preserve one-way data flow (Mac → Railway) and local execution invariants.

**Subagent dispatch (max 2 at a time):**

| When | Subagent | Use for |
|------|----------|---------|
| Architecture design/review | **software-architect** | System design, domain-driven design, architectural patterns. |
| Backend architecture | **backend-architect** | Scalable system design, database architecture, API development. |
| Frontend architecture | **frontend-developer** | Modern web technologies, React/Vue/Angular, UI implementation. |

**Full procedure:** docs/architecture/overview.md, docs/Current-State.md, AGENTS.md.
