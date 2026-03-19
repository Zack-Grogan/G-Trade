---
description: Must read AGENTS.md first for structural or behavioral changes. Repository operating contract; follow before changing code or config.
alwaysApply: true
---

# Core operating contract

When making structural or behavioral changes, read AGENTS.md and the doc it points to for that area before changing code or config.

**When this applies:** Structural or behavioral change to modules, config surface, deployment topology, or safety-relevant behavior.

**Do this:**
- Read AGENTS.md and the doc it points to for that area (architecture, OPERATOR, Compliance-Boundaries as relevant).
- Do not redesign product architecture or rewrite business logic unless explicitly required.
- Preserve existing conventions unless there is a documented reason to evolve them.
- When uncertain, create neutral scaffolding or TODO markers rather than risky assumptions.
- **Never trust training data** for third-party APIs, SDKs, or versions. Package names, versions, and API shapes change; training data is often stale. Verify against current official docs or latest/latest LTS releases (e.g. March 2026). Use web search or doc fetch before implementing integrations.

Before editing the plan file, broad refactors, or compliance/safety-critical paths, check AGENTS.md "What requires approval before editing" and obtain approval.

**Full procedure:** AGENTS.md, docs/architecture/overview.md.
