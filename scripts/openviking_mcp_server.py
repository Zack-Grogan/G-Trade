#!/usr/bin/env python3
"""OpenViking MCP Server - exposes find, read, glob, abstract, overview, grep to Cursor via stdio.

Uses OPENVIKING_DATA_PATH (default ./viking_data) and OPENVIKING_CONFIG_FILE for config.
Requires: pip install openviking mcp
"""

import os
import sys
import json
import logging

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

from mcp.server.fastmcp import FastMCP

try:
    import openviking as ov
except ImportError:
    print("Error: openviking not found. Run: pip install openviking mcp", file=sys.stderr)
    sys.exit(1)

mcp = FastMCP("OpenViking")
_client = None


def get_client():
    global _client
    if _client is None:
        data_path = os.environ.get("OPENVIKING_DATA_PATH", os.path.expanduser("~/.openviking/workspace"))
        _client = ov.SyncOpenViking(path=data_path)
        _client.initialize()
    return _client


@mcp.tool()
def openviking_find(query: str, limit: int = 10) -> str:
    """Semantic search over OpenViking knowledge base.

    Args:
        query: Search query
        limit: Max results (default 10)

    Returns:
        JSON list of {uri, score, preview}
    """
    try:
        client = get_client()
        results = client.find(query, target_uri="viking://", limit=limit)
        items = getattr(results, "resources", results) if results else []
        if not isinstance(items, list):
            items = list(items) if items else []
        formatted = []
        for r in items[:limit]:
            uri = getattr(r, "uri", str(r))
            score = getattr(r, "score", 0.0)
            try:
                preview = (client.read(uri) or "")[:500]
            except Exception:
                preview = "Error reading"
            formatted.append({"uri": uri, "score": round(float(score), 4), "preview": preview})
        return json.dumps(formatted, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def openviking_read(uri: str) -> str:
    """Read full content at a viking:// URI.

    Args:
        uri: Resource URI (e.g. viking://resources/g-trade/docs/README.md)

    Returns:
        Resource content
    """
    try:
        return get_client().read(uri) or ""
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def openviking_glob(pattern: str) -> str:
    """Match files by glob pattern under viking://.

    Args:
        pattern: Glob pattern (e.g. **/*.md)

    Returns:
        JSON list of matching URIs
    """
    try:
        results = get_client().glob(pattern, uri="viking://")
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def openviking_abstract(uri: str) -> str:
    """Get L0 abstract for a viking:// URI.

    Args:
        uri: Resource URI

    Returns:
        Short abstract
    """
    try:
        return get_client().abstract(uri) or ""
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def openviking_overview(uri: str) -> str:
    """Get L1 overview for a viking:// URI.

    Args:
        uri: Resource URI

    Returns:
        Overview content
    """
    try:
        return get_client().overview(uri) or ""
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def openviking_grep(pattern: str, case_insensitive: bool = False) -> str:
    """Full-text search under viking://.

    Args:
        pattern: Search pattern
        case_insensitive: Ignore case (default False)

    Returns:
        JSON search results
    """
    try:
        results = get_client().grep("viking://", pattern, case_insensitive=case_insensitive)
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="stdio")
