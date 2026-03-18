# Engineering system overview

This section describes the AI operating layer: how Cursor, Linear, GitHub, Railway, and OpenViking fit together, and how docs and generated artifacts are maintained.

## Roles

- **Cursor** — Live coding surface and execution engine. Rules in `.cursor/rules/` and the AGENTS.md contract govern behavior.
- **Linear** — Work and issue/planning source of truth (when used). See [linear-workflow.md](linear-workflow.md). Setup and backfill: [linear-setup.md](linear-setup.md); see also [runbooks/Project-onboarding-Linear-and-OpenViking.md](../runbooks/Project-onboarding-Linear-and-OpenViking.md).
- **GitHub** — Code truth, branches, PRs, review workflow. See [github-workflow.md](github-workflow.md).
- **Railway** — Runtime/deployment; agent usage is conservative and non-production by default. See [railway-usage-policy.md](railway-usage-policy.md).
- **OpenViking** — Durable repository knowledge and documentation index behind MCP; not an app runtime dependency. See [openviking-integration.md](openviking-integration.md). First-time ingest: run `python scripts/onboard_openviking.py` from repo root; see [runbooks/Project-onboarding-Linear-and-OpenViking.md](../runbooks/Project-onboarding-Linear-and-OpenViking.md).
- **Repo docs** — Human-maintained source of truth. **Generated docs** — Machine-maintained index/maps produced by `scripts/generate_docs_index.py` under `docs/generated/`.

## Local vs global

What lives in the repo vs in user/team config: [local-vs-global.md](local-vs-global.md).

## Cursor operating model

How Cursor is expected to behave (issue-driven vs exploratory, docs updates, safety): [cursor-operating-model.md](cursor-operating-model.md).

## Generated docs

The script `scripts/generate_docs_index.py` is idempotent and safe. It writes under `docs/generated/`:

- dependency-map.md, module-map.md, routes-map.md, config-matrix.md, testing-map.md, entrypoints.md, change-impact-map.md, service-relationships.md

Do not hand-edit files in `docs/generated/`; re-run the script to refresh. Authored docs in `docs/` remain authoritative.

## Agent index

By-concern lookup for rules, skills, and docs: [agent-index.md](agent-index.md).

## Reusable pack and future projects

Templates and global setup live under [global-cursor-pack/](global-cursor-pack/). How to reuse this setup for new repos: [future-project-starter.md](future-project-starter.md).
