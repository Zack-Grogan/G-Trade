---
name: use-openviking
description: >
  Queries OpenViking via MCP for semantic search, L0/L1 summaries, and directory-style
  context over durable repo knowledge. Use when the task benefits from cross-repo or
  durable search, project status or progress reports, analytical deep dives, or
  project-wide / multi-doc analysis. Apply after checking repo docs and docs/generated/
  first; OpenViking augments, does not replace, Cursor's native repo understanding.
---

# Use OpenViking

## When to use OpenViking

Per [docs/engineering-system/openviking-integration.md](../../docs/engineering-system/openviking-integration.md):

- **After** reading repo docs (`docs/`, AGENTS.md) and generated maps (`docs/generated/`).
- **For:** cross-repo context, durable semantic search, progress/status reports, analytical summaries, or when the user asks for project-wide or multi-doc analysis (e.g. "progress monster," "analytical machine").

Do not use OpenViking as a substitute for reading the repo. Use it to augment when the above cases apply.

## MCP tools

OpenViking is exposed to Cursor via MCP. Use these tools when the OpenViking MCP server is configured:

| Tool | Use for |
|------|--------|
| `openviking_find` | Semantic search over the indexed context. Primary way to discover relevant docs or passages. |
| `openviking_read` | Read full content (L2) by `viking://` URI when you need full text. |
| `openviking_glob` | Pattern-based match (e.g. by path or name) to narrow scope. |
| `openviking_abstract` | L0 summary (~100 tokens) for quick relevance check. |
| `openviking_overview` | L1 overview (~2k tokens) for structure and key points before pulling L2. |

**Workflow:** Prefer `find` to locate candidates; use `overview` or `abstract` to triage; call `read` only when you need full content.

## URI convention

Resources live under `viking://resources/<repo-or-project>/...`. For this repo, use a consistent prefix such as `viking://resources/g-trade/...` so URIs stay predictable after ingest. Document the chosen prefix in team or MCP adapter docs.

## Progress and analytics

When the user asks for status, impact, or "progress monster" style output:

1. Use `openviking_find` and/or `openviking_overview` to gather relevant context.
2. **For structured synthesis, dispatch the openviking-analyst subagent** with the query and gathered context.
3. Output format:
   - **Executive summary** — one paragraph.
   - **Key findings** — with evidence (doc or URI).
   - **Recommendations** — actionable next steps.

Do not duplicate the full ingest/refresh playbook here; see [reference.md](reference.md) and the integration doc for ingest and refresh.

## Refresh

The OpenViking index is refreshed manually or after `scripts/generate_docs_index.py` or a merge. Do not assume real-time sync; treat it as an index on a refresh cadence.

## Additional resources

- Ingest, refresh, and what to ingest: [reference.md](reference.md) and [docs/engineering-system/openviking-integration.md](../../docs/engineering-system/openviking-integration.md).
