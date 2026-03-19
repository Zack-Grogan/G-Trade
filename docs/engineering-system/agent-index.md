# Agent index: rules, skills, docs by concern

Single lookup for "what do I use for X?" — rule(s), skill(s), doc(s), and subagent(s) that apply.

| Concern | When to use | Rule(s) | Skill(s) | Subagent(s) | Pattern | Doc(s) |
|--------|-------------|---------|----------|--------------|---------|--------|
| Structural or architecture change | Changing module boundaries, config surface, deployment topology, or execution/data-flow | 00-core-operating-contract, 20-architecture-reading | — | software-architect, backend-architect | hybrid | docs/architecture/overview.md, docs/Current-State.md, docs/OPERATOR.md |
| Issue-driven work (branch, commit, PR) | User has a Linear or other issue; implementing a ticket; creating branch or opening PR | 40-issue-branch-pr-discipline | issue-to-pr | — | direct | linear-workflow.md, github-workflow.md, global-cursor-pack/operating-playbooks/starting-work-from-linear-issue.md |
| Exploratory work, no issue | No ticket yet; discovery or spike; formalize later | 05-development-stage-defaults, 40-issue-branch-pr-discipline | — | explore | route-first | cursor-operating-model.md, linear-workflow.md (exploratory) |
| Docs or generated index | Changing behavior/deployment/config; refreshing machine-generated maps | 10-docs-engine | — | technical-writer | hybrid | overview.md (generated docs), docs/OPERATOR.md, AGENTS.md "Documentation contract" |
| Railway deploy or ops | Deploying, inspecting, or changing Railway services | 70-railway-and-infra-guardrails | use-railway | shell, devops-automator | hybrid | railway-usage-policy.md |
| OpenViking / durable search / progress | Cross-repo or durable search; user asks for status, progress, or analysis | 60-openviking-knowledge-usage, 61-openviking-progress-and-analysis | use-openviking | openviking-analyst | route-first | openviking-integration.md |
| Safety, destructive guard, sensitive files | Any edit; special attention for env, auth, migrations, infra | 50-safety-and-non-destructive-behavior | — | security-engineer, compliance-auditor | hybrid | docs/Compliance-Boundaries.md, AGENTS.md "Safety constraints" |
| Testing | Before completing a code change | 30-testing-discipline | — | api-tester, evidence-collector, shell | route-first | AGENTS.md "Testing contract" |
| Reusing templates / global pack | Adding or editing templates or playbooks for reuse across projects | 80-reusable-template-boundary | — | — | direct | future-project-starter.md, local-vs-global.md |

Rule files: `.cursor/rules/<name>.mdc`. Skills: `.cursor/skills/<name>/`. Subagents: `mcp_task` with subagent_type. Pattern: **route-first** (dispatch subagent early), **direct** (GLM does it), **hybrid** (task-type decides). Use this index with AGENTS.md "Where to go for what" and "Subagent routing."
