#!/usr/bin/env python3
"""First-time or refresh ingest of G-Trade into OpenViking.

Uses OPENVIKING_DATA_PATH (default ~/.openviking/workspace) and OPENVIKING_CONFIG_FILE.
Runs generate_docs_index.py, then add_resource for docs/ and key repo files.
Exclusions: .env, secrets, binaries — only docs/ and listed paths are ingested.

Usage (from repo root):
  python scripts/onboard_openviking.py

Requires: pip install openviking
"""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main():
    os.chdir(REPO_ROOT)

    # Refresh generated docs so docs/generated/ is up to date
    print("Running generate_docs_index.py...")
    r = subprocess.run(
        [sys.executable, "scripts/generate_docs_index.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(r.stderr or r.stdout, file=sys.stderr)
        sys.exit(1)
    print(r.stdout or "Generated docs index under docs/generated/")

    try:
        import openviking as ov
    except ImportError:
        print("Error: openviking not found. Run: pip install openviking", file=sys.stderr)
        sys.exit(1)

    data_path = os.environ.get(
        "OPENVIKING_DATA_PATH",
        os.path.expanduser("~/.openviking/workspace"),
    )
    data_path = os.path.abspath(os.path.expanduser(data_path))
    if not os.path.isdir(data_path):
        os.makedirs(data_path, exist_ok=True)
        print(f"Created workspace dir: {data_path}")

    client = ov.SyncOpenViking(path=data_path)
    client.initialize()

    root_uris = []
    # Ingest docs/ (authored + generated)
    docs_path = REPO_ROOT / "docs"
    if docs_path.is_dir():
        path_str = str(docs_path)
        print(f"Adding resource: {path_str}")
        result = client.add_resource(path=path_str)
        if result and isinstance(result, dict):
            ru = result.get("root_uri", "")
            if ru:
                root_uris.append(ru)
                print(f"  root_uri: {ru}")
        elif result and getattr(result, "root_uri", None):
            root_uris.append(result.root_uri)
            print(f"  root_uri: {result.root_uri}")

    # Key repo-level files
    for name in ["AGENTS.md", "README.md"]:
        p = REPO_ROOT / name
        if p.is_file():
            path_str = str(p)
            print(f"Adding resource: {path_str}")
            result = client.add_resource(path=path_str)
            if result and isinstance(result, dict):
                ru = result.get("root_uri", "")
                if ru:
                    root_uris.append(ru)
                    print(f"  root_uri: {ru}")
            elif result and getattr(result, "root_uri", None):
                root_uris.append(result.root_uri)
                print(f"  root_uri: {result.root_uri}")

    print("\nDone. Root URIs for querying (viking://):")
    for u in root_uris:
        print(f"  {u}")
    if not root_uris:
        print("  (none captured; check add_resource return value)")


if __name__ == "__main__":
    main()
