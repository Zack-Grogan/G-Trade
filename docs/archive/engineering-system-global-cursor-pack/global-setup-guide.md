# Global Cursor setup guide

What belongs in **global** Cursor (or user/team) config vs **repo** config. Apply these steps manually; this repo only provides templates and instructions.

## In the repo (commit)

- AGENTS.md, .cursor/rules/*, docs tree, scripts/generate_docs_index.py, .github templates, .cursorindexingignore.
- Templates under this global-cursor-pack/ are committed for reuse; they are not active until you install or copy them to global config.

## In global user config (not in repo)

- **Cursor MCP servers:** Add and enable MCP servers (GitHub, Linear, and any optional infra provider) in Cursor settings. Use the example configs in `mcp/` as reference; put real URLs and tokens in Cursor's MCP config (e.g. user-level or workspace-level), never in the repo.
- **Credentials:** API keys, Bearer tokens, and Linear/GitHub auth. Store in env or Cursor secrets; never commit.
- **Hooks:** If you use Cursor hooks or a shell hook that runs before/after Cursor actions, install the scripts from `hooks/` to a path Cursor or your shell uses (see hooks/README in this pack).

## In global team config

- Linear workspace, GitHub org/repo settings, and any provider-specific access. Branch protection and review policies. Configure in the respective services' admin UI.

## Install steps (manual)

1. **MCP:** Copy `mcp/*.example.json` patterns into Cursor MCP config. Fill in URLs and auth per service docs. Do not commit filled config.
2. **Hooks:** If your team uses hooks, copy `hooks/*` to your hook directory and set execute bit. Document the path in team docs.
3. **New repo:** Use `templates/` and `future-project-starter.md` (in parent directory) to bootstrap a new repo. Run or adapt an init script if you create one.

## Paths (typical)

- **Cursor config (Mac):** `~/Library/Application Support/Cursor/User/` or workspace `.cursor/` for MCP.
- **Cursor MCP config file:** Often `.cursor/mcp.json` in workspace or in Cursor application settings.
- **Hooks:** Depends on how you run them (e.g. Cursor task, pre-commit, or custom script). See hooks/README.
