# Linear setup for G-Trade

How to create a Linear project for this repo and use it with Cursor. No secrets in repo; API keys and MCP config stay in your environment or Cursor settings.

**Important:** This repo’s Linear project is **G-Trade** only. Do not create issues or documents in other workspace projects (e.g. grogan.trade UCML); they are separate products.

## 1. Create workspace and project

1. Create or use a Linear workspace.
2. Create a project for this repo: name **G-Trade**, team GDG. (Branch prefix for issues is **GDG**, e.g. `fix/GDG-211-name`.) Do not use another project in the workspace for G-Trade work.
3. Note the **Team** (or project) ID if you will run the optional backfill script — find it in Linear settings or the API.

## 2. Add Linear MCP in Cursor

- In Cursor, enable the Linear MCP server and add your Linear API key in Cursor settings (or in your MCP config). Do not put the key in the repo.
- Reference: [global-cursor-pack/mcp/README.md](global-cursor-pack/mcp/README.md). Linear is not listed in `.cursor/mcp.json` by default; add it in Cursor's MCP configuration with your API key.

## 3. Branch / commit / PR conventions

- **Branch:** When an issue exists, use the team/issue key: `fix/GDG-211-description` or `feat/GDG-212-feature-name`.
- **Commits:** Reference the issue in the message (e.g. "Fix bridge retry GDG-211").
- **PR:** Use the repo PR template; link the Linear issue in the body.

See [linear-workflow.md](linear-workflow.md) and [github-workflow.md](github-workflow.md).

## 4. Backfill issues

Open work from [Tasks.md](../Tasks.md) and the plan is listed in [linear-backfill-issues.md](linear-backfill-issues.md). Create those issues in your Linear project (manually or via the optional script below).

**Optional script:** With `LINEAR_API_KEY` and `LINEAR_TEAM_ID` set in your environment, run from G-Trade repo root:

```bash
python scripts/linear_backfill.py
```

To assign backfilled issues to the G-Trade project, set `LINEAR_PROJECT_ID` to the G-Trade project ID (from Linear project settings or API, e.g. via `list_projects`) when running the script.

Run locally only; never commit API keys. The script reads [linear-backfill-issues.json](linear-backfill-issues.json) and creates the issues in Linear.
