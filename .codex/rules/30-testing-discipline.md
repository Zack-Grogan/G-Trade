---
description: Run relevant tests before completing code changes; do not remove tests without a documented reason. Dispatch to api-tester, evidence-collector, test-results-analyzer, or shell as appropriate.
alwaysApply: false
---

# Testing discipline

**When this applies:** Before completing a code change that touches application or service code.

**Do this:**
- Run the relevant tests (e.g. pytest from es-hotzone-trader, or the test surface for the area changed).
- Do not remove or disable tests unless there is an explicit, documented reason (e.g. behavior obsolete). Prefer fixing or updating tests to match intended behavior.

**Subagent dispatch (max 2 at a time):**

| When | Subagent | Use for |
|------|----------|---------|
| API / endpoint testing | **api-tester** | API validation, performance testing, quality assurance. |
| QA with evidence | **evidence-collector** | QA requiring visual proof; screenshots. |
| Test result analysis | **test-results-analyzer** | Evaluating test results, metrics, actionable insights. |
| Running test commands | **shell** | Execute pytest, lint, or other test commands. |

**Full procedure:** AGENTS.md "Testing contract."
