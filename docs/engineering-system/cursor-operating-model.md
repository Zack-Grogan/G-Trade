# Cursor operating model

How Cursor (and agents in it) should behave in this repo.

## Behavior control

- **Rules** (`.cursor/rules/*.mdc`) guide behavior: read AGENTS.md first, update docs when relevant, run tests, prefer issue-aware workflow when an issue exists, avoid destructive or risky actions by default.
- **AGENTS.md** is the repository operating contract. Structural or behavioral changes must follow it.

## Development loops

**When a Linear (or other) issue exists:** Read issue and relevant docs → plan narrowly → implement → run verification → update docs → prepare PR; reference issue in branch/commit/PR. See [linear-workflow.md](linear-workflow.md) and [github-workflow.md](github-workflow.md).

**When no issue exists:** Treat as development-stage exploration. Do not invent an issue. Implement narrowly; document findings; propose formalizing into an issue or plan after the pass. Still update docs and produce PR-ready summary if code changed.

**Triage/debugging:** Collect context → locate modules and docs → distinguish facts from hypotheses → document findings → recommend issue conversion if warranted. Keep changes narrow and reversible.

## Docs and safety

- Authored docs are authority; generated docs are refreshable indexes. When behavior or deployment changes, update the relevant doc.
- Do not add secrets. Do not force production automation. Flag edits to sensitive files (env, auth, migrations, infra). See .cursor/rules/50-safety-and-non-destructive-behavior.mdc.

## OpenViking and local operation

- Use OpenViking for durable knowledge when it helps; prefer repo docs first. Do not make the app depend on OpenViking at runtime.
- The active product is local-first. Use the CLI, Flask console, and local docs as the primary operator surfaces; treat archived Railway notes as historical only.
