---
description: When the user asks for project status, progress, or deep analysis, use OpenViking skill and optionally the openviking-analyst subagent.
alwaysApply: false
---

# OpenViking progress and analysis

**When this applies:** User asks for project status, progress reports, impact analysis, or to act as a "progress monster" or "analytical machine."

**Do this:**
- Apply the **use-openviking** skill. Dispatch the **openviking-analyst** subagent for structured synthesis when the task benefits from it.
- Output: executive summary, key findings with evidence (doc or viking:// URI), and actionable recommendations. Prefer repo docs first; use OpenViking for cross-repo or durable context.

**Full procedure:** docs/engineering-system/openviking-integration.md; skill: use-openviking.
