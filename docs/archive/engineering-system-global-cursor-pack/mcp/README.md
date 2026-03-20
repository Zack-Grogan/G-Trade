# MCP example configs (do not put secrets here)

Example structures for MCP server config. **Real URLs and tokens go in Cursor user/workspace config, not in the repo.**

- **GitHub:** Enable GitHub MCP in Cursor; add token in Cursor settings. See provider docs for scopes.
- **Linear:** Enable Linear MCP; add API key in Cursor settings.
- **Optional infra provider:** Add only if the project actively uses that provider; keep auth in local user config, never in the repo.

Copy the `.example.json` patterns into your Cursor MCP config file and replace placeholders. Never commit filled config.
