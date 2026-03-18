# MCP example configs (do not put secrets here)

Example structures for MCP server config. **Real URLs and tokens go in Cursor user/workspace config, not in the repo.**

- **GitHub:** Enable GitHub MCP in Cursor; add token in Cursor settings. See provider docs for scopes.
- **Linear:** Enable Linear MCP; add API key in Cursor settings.
- **Railway:** Enable Railway MCP; auth via Railway CLI or token per Railway docs.
- **OpenViking:** For local use, stdio is typical: use `openviking-mcp.example.json` (command + env for `OPENVIKING_CONFIG_FILE`). For HTTP, use the `openviking` entry in `cursor-mcp.example.json` and point it at your OpenViking server URL.

Copy the `.example.json` patterns into your Cursor MCP config file and replace placeholders. Never commit filled config.
