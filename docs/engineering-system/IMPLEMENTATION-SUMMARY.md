# AI Operating Layer — Implementation Summary

Summary of what was added or changed for the AI engineering operating layer. Do not edit the plan file; this doc is the post-implementation reference.

---

## 1. Repo audit (concise)

- **Workspace:** Composite; git in `es-hotzone-trader/` only. Stacks: Python 3.11 (app + railway ingest/analytics/mcp), Next.js (railway/web). Entry: `es-trade` CLI, `railway/*/app.py`. Commands: pytest, ruff, black, npm run dev/build/start. Docs: docs/ (architecture, operator, compliance, runbooks, research, state, tasks). CI: none. Cursor: .cursor/rules (now 10 files), .cursor/plans, .cursor/agents, .cursor/skills, .cursor/mcp.json. No formal issue/branch/PR convention before this pass. Railway and docs strongly present. No prior docs-generation script.
- **Classification:** Local = AGENTS, rules, docs, script, PR/issue templates, ignore files. Global = MCP auth, hooks install, Linear/GitHub/Railway admin. Hybrid = global-cursor-pack templates; install is manual.

---

## 2. Local vs global decision summary

| Item | Location | Reason |
|------|----------|--------|
| AGENTS.md | Commit to repo | Repo operating contract. |
| .cursor/rules/* | Commit to repo | Repo behavior control. |
| docs/ (skeleton, engineering-system, generated) | Commit to repo | Authored and generated docs. |
| scripts/generate_docs_index.py | Commit to repo | Idempotent doc index generator. |
| .cursorignore / .cursorindexingignore | Commit to repo | Reduce noise; not security. |
| .github/ (PR template, issue templates) | Commit to repo | Repo workflow. |
| global-cursor-pack/ (templates, hooks, mcp examples, playbooks) | Commit to repo | Reusable content; install is manual. |
| MCP credentials, API keys | Global user config | Never in repo. |
| Hooks execution | Global user/team | Install to path Cursor or shell uses. |
| Linear/GitHub/Railway admin | Manual external | Admin UI. |

---

## 3. File tree of added/changed artifacts

```
docs/
  architecture/
    overview.md                    # NEW (canonical architecture)
  modules/
    README.md                      # NEW
  decisions/
    README.md                      # NEW
  testing.md                       # NEW
  onboarding.md                    # NEW
  generated/                       # NEW (script output)
    README.md
    dependency-map.md
    module-map.md
    routes-map.md
    config-matrix.md
    testing-map.md
    entrypoints.md
    change-impact-map.md
    service-relationships.md
  engineering-system/              # NEW
    overview.md
    local-vs-global.md
    cursor-operating-model.md
    linear-workflow.md
    github-workflow.md
    railway-usage-policy.md
    openviking-integration.md
    future-project-starter.md
    repo-audit-and-boundaries.md
    IMPLEMENTATION-SUMMARY.md      # This file
    global-cursor-pack/
      global-setup-guide.md
      hooks/
        README.md
        destructive-guard.example.sh
        protected-branch.example.sh
      mcp/
        README.md
        cursor-mcp.example.json
      templates/
        AGENTS-template.md
        rules-starter-README.md
        docs-tree-starter.md
        docs-generation-spec.md
        local-vs-global-checklist.md
      operating-playbooks/
        README.md
        starting-work-from-linear-issue.md
        exploratory-development.md
        deciding-local-vs-global.md
docs/README.md                    # UPDATED (links to architecture/, engineering-system/)
docs/Architecture-Overview.md     # UPDATED (canonical path note)

.cursor/rules/
  00-core-operating-contract.mdc   # NEW
  05-development-stage-defaults.mdc
  10-docs-engine.mdc
  20-architecture-reading.mdc
  30-testing-discipline.mdc
  40-issue-branch-pr-discipline.mdc
  50-safety-and-non-destructive-behavior.mdc
  60-openviking-knowledge-usage.mdc
  70-railway-and-infra-guardrails.mdc
  80-reusable-template-boundary.mdc
  railway-deploy-and-tooling.mdc  # REMOVED (folded into 70)

.github/
  pull_request_template.md         # NEW
  ISSUE_TEMPLATE/
    config.yml
    bug.md
    feature.md

scripts/
  generate_docs_index.py           # NEW

AGENTS.md                         # UPDATED (full operating contract)
.cursorindexingignore             # NEW (or UPDATED)
```

Note: `.cursorignore` was not written (write permission denied in this environment). Add it manually at repo root with the same patterns as in .cursorindexingignore if desired; see "Manual steps" below.

---

## 4. Purpose of each added/changed file

| File | Purpose |
|------|---------|
| docs/architecture/overview.md | Canonical architecture doc (lowercase path); what runs where, data flow, config. |
| docs/modules/README.md | Module map index; links to code and generated maps. |
| docs/decisions/README.md | Placeholder for ADRs or notable decisions. |
| docs/testing.md | How to run tests; pointer to AGENTS and rule. |
| docs/onboarding.md | First-read path and link to engineering-system. |
| docs/generated/* | Machine-friendly indexes; produced by script only. |
| docs/engineering-system/*.md | Roles, local vs global, Cursor model, Linear/GitHub/Railway/OpenViking contracts, future-project reuse. |
| docs/engineering-system/global-cursor-pack/* | Reusable templates, hook examples, MCP examples, playbooks; install is global/manual. |
| .cursor/rules/00–80 | Behavior control: contract, exploratory vs issue-driven, docs, architecture, tests, issue/PR, safety, OpenViking, Railway, templates. |
| .github/pull_request_template.md | PR body template; issue link, testing, docs checklist. |
| .github/ISSUE_TEMPLATE/* | Bug and feature issue templates. |
| scripts/generate_docs_index.py | Idempotent generator for docs/generated/. |
| AGENTS.md | Full repo operating contract (purpose, layout, entry points, commands, docs/testing/issue/safety contracts, OpenViking, approval-required). |
| .cursorindexingignore | Reduce indexing of logs, caches, node_modules, etc. |

---

## 5. Manual steps (outside the repo)

- **MCP:** Add and enable GitHub, Linear, Railway, OpenViking MCP servers in Cursor; set URLs and tokens in Cursor config (never in repo). Use `docs/engineering-system/global-cursor-pack/mcp/` as reference.
- **.cursorignore:** If missing at repo root, create it with the same patterns as .cursorindexingignore (logs/, *.log, __pycache__/, .pytest_cache/, node_modules/, etc.) and a comment that it is not a security control.
- **Hooks:** If using destructive-guard or protected-branch hooks, copy from global-cursor-pack/hooks/ to your hook path and wire to git or Cursor per global-setup-guide.md.
- **Linear/GitHub/Railway:** Create or link workspaces, set branch protection, review policies, and Railway project access in each service’s admin UI.
- **OpenViking:** If used, configure service URL and auth; document refresh cadence. No app runtime dependency.

---

## 6. Optional next upgrades

- Add a `scripts/init-ai-operating-layer.sh` (or similar) that creates AGENTS.md, .cursor/rules, docs skeleton, and .github templates in a new repo from global-cursor-pack templates.
- Add CI (e.g. GitHub Actions) that runs pytest and optionally `scripts/generate_docs_index.py` on push/PR; document in docs rather than forcing a workflow.
- Expand operating-playbooks (e.g. opening-a-pr.md, validating-before-merge.md) with repo-specific checklists.
- Ingest docs/generated/ or key docs into OpenViking and document the ingestion process.

---

## 7. Risky or deferred items

- **.cursorignore:** Write was denied in this environment; add manually at repo root if desired.
- **Production Railway:** No automation or agent-triggered production deploys; all usage remains conservative and non-production by default.
- **Linear/GitHub integration:** No assumption that Linear or GitHub MCP are configured; workflows are documented for when they are.

---

## 8. Future-project reuse checklist

- [ ] Copy or adapt AGENTS.md from global-cursor-pack/templates/AGENTS-template.md.
- [ ] Copy .cursor/rules (00–80) and adjust repo-specific paths (e.g. plan file name).
- [ ] Create docs tree from global-cursor-pack/templates/docs-tree-starter.md.
- [ ] Add scripts/generate_docs_index.py (or port from this repo) per docs-generation-spec.md.
- [ ] Add .github/pull_request_template.md and ISSUE_TEMPLATE/.
- [ ] Add .cursorignore and .cursorindexingignore with project-appropriate patterns.
- [ ] Use local-vs-global-checklist.md when adding new config or automation.
- [ ] Follow global-setup-guide.md for MCP and hooks install in user/team config.

---

## 9. How to work with this system daily

- **Start:** Read AGENTS.md when making structural or behavioral changes. Use docs/README.md and docs/architecture/overview.md for architecture.
- **With an issue:** Follow linear-workflow.md and github-workflow.md; reference issue in branch/commit/PR; use PR template.
- **Exploratory:** Work without an issue; document findings; propose creating an issue when formalizing.
- **Before merging:** Run tests; update docs if behavior or config changed; use the PR template and checklists.
- **Docs:** Treat docs/ as authority; refresh docs/generated/ with `python scripts/generate_docs_index.py` when structure or deps change.
- **Railway:** Use skill and MCP/CLI for deploy and logs; keep usage non-production by default. See railway-usage-policy.md.
- **OpenViking:** Use for durable search when helpful; prefer repo docs first. See openviking-integration.md.
