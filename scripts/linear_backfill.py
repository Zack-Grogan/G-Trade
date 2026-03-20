#!/usr/bin/env python3
"""Create Linear issues from docs/engineering-system/linear-backfill-issues.json.

Run locally with your API key. Never commit LINEAR_API_KEY.

Usage (from repo root):
  export LINEAR_API_KEY=lin_api_...
  export LINEAR_TEAM_ID=<team-id>   # required; find in Linear Settings > Team or via API
  export LINEAR_PROJECT_ID=<project-id>   # optional; assign issues to G-Trade project (see docs/engineering-system/linear-setup.md)
  python scripts/linear_backfill.py

Requires: pip install requests (or use stdlib urllib).
"""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ISSUES_JSON = REPO_ROOT / "docs" / "engineering-system" / "linear-backfill-issues.json"
LINEAR_GRAPHQL = "https://api.linear.app/graphql"


def main():
    api_key = os.environ.get("LINEAR_API_KEY")
    team_id = os.environ.get("LINEAR_TEAM_ID")
    project_id = os.environ.get("LINEAR_PROJECT_ID")
    if not api_key:
        print("Error: set LINEAR_API_KEY in the environment.", file=sys.stderr)
        sys.exit(1)
    if not team_id:
        print(
            "Error: set LINEAR_TEAM_ID in the environment (find in Linear Settings > Team).",
            file=sys.stderr,
        )
        sys.exit(1)

    if not ISSUES_JSON.is_file():
        print(f"Error: {ISSUES_JSON} not found.", file=sys.stderr)
        sys.exit(1)

    with open(ISSUES_JSON) as f:
        issues = json.load(f)

    try:
        import requests
    except ImportError:
        print("Error: pip install requests", file=sys.stderr)
        sys.exit(1)

    # Personal API key: use as-is (no "Bearer " prefix). OAuth: use "Bearer <token>".
    headers = {
        "Authorization": api_key if api_key.startswith("Bearer ") else api_key,
        "Content-Type": "application/json",
    }

    for item in issues:
        title = item.get("title", "").strip()
        if not title:
            continue
        description = item.get("description", "") or ""

        mutation = """
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            issue { id identifier url }
            success
          }
        }
        """
        input_obj = {
            "teamId": team_id,
            "title": title,
            "description": description,
        }
        if project_id:
            input_obj["projectId"] = project_id
        variables = {"input": input_obj}
        payload = {"query": mutation, "variables": variables}

        resp = requests.post(LINEAR_GRAPHQL, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"Failed to create '{title}': {resp.status_code} {resp.text}", file=sys.stderr)
            continue
        data = resp.json()
        if "errors" in data and data["errors"]:
            print(f"GraphQL errors for '{title}': {data['errors']}", file=sys.stderr)
            continue
        issue = (data.get("data") or {}).get("issueCreate", {}).get("issue")
        if issue:
            print(
                f"Created: {issue.get('identifier', issue.get('id'))} — {title} ({issue.get('url', '')})"
            )
        else:
            print(f"No issue returned for '{title}'", file=sys.stderr)

    print("Done.")


if __name__ == "__main__":
    main()
