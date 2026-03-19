---
name: status
description: Project status via openviking-analyst subagent. Returns executive summary, key findings, and recommendations.
---

# Status

1. **Dispatch analyst** - Launch openviking-analyst subagent:
   ```
   Task: openviking-analyst
   Prompt: Provide project status for G-Trade.
         Include:
         - Executive summary (one paragraph)
         - Key findings with evidence (doc paths or viking:// URIs)
         - Actionable recommendations
   ```

2. **Synthesize** - Return structured status report.

For deep analysis, apply use-openviking skill first to gather context via MCP.
