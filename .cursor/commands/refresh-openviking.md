# Refresh OpenViking

1. Run `python scripts/onboard_openviking.py` from the G-Trade repo root (workspace root where docs/ and scripts/ live).
2. This regenerates `docs/generated/` and re-ingests `docs/`, `AGENTS.md`, and `README.md` into OpenViking so Cursor can query the latest content via the OpenViking MCP.
