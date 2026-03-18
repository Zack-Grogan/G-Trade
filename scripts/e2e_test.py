#!/usr/bin/env python3
"""
A-to-Z E2E test: ingest → analytics → GraphQL → RLM (health, similar_trades, hypotheses, replay, benchmark).
Loads .env from repo root if present. Requires INGEST_URL, ANALYTICS_URL, RLM_URL (and auth keys for full test).
Usage: from repo root, run:  python scripts/e2e_test.py
       Or with explicit env: INGEST_URL=... ANALYTICS_URL=... RLM_URL=... python scripts/e2e_test.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Load .env from repo root (simple key=value, no quotes stripping for values with =)
_repo_root = Path(__file__).resolve().parent.parent
_env_file = _repo_root / ".env"
if _env_file.exists():
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if k and v not in (None, ""):
                    os.environ.setdefault(k, v)

try:
    import httpx
except ImportError:
    print("pip install httpx then re-run")
    sys.exit(1)

# Base URLs (no trailing slash)
INGEST_URL = (os.environ.get("INGEST_URL") or os.environ.get("RAILWAY_INGEST_URL") or "http://localhost:8000").rstrip("/")
ANALYTICS_URL = (os.environ.get("ANALYTICS_URL") or os.environ.get("RAILWAY_ANALYTICS_URL") or "http://localhost:8001").rstrip("/")
RLM_URL = (os.environ.get("RLM_URL") or os.environ.get("RAILWAY_RLM_URL") or "http://localhost:8003").rstrip("/")
INGEST_API_KEY = os.environ.get("INGEST_API_KEY", "")
ANALYTICS_API_KEY = os.environ.get("ANALYTICS_API_KEY", "")
TIMEOUT = 30.0


def ok(name: str, resp: httpx.Response, body: dict | list | None = None) -> bool:
    if resp.status_code >= 400:
        print(f"  FAIL {name}: status={resp.status_code} body={resp.text[:200]}")
        return False
    print(f"  OK   {name}: status={resp.status_code}")
    return True


def main() -> int:
    failures = 0
    print("E2E test — using INGEST_URL=%s ANALYTICS_URL=%s RLM_URL=%s" % (INGEST_URL, ANALYTICS_URL, RLM_URL))
    with httpx.Client(timeout=TIMEOUT) as client:
        # --- Health ---
        print("\n1. Health checks")
        for label, url in [
            ("ingest /health", f"{INGEST_URL}/health"),
            ("analytics /health", f"{ANALYTICS_URL}/health"),
            ("rlm /health", f"{RLM_URL}/health"),
        ]:
            try:
                r = client.get(url)
                if not ok(label, r):
                    failures += 1
            except Exception as e:
                print(f"  FAIL {label}: {e}")
                failures += 1

        # --- Ingest (optional: needs INGEST_API_KEY) ---
        print("\n2. Ingest (optional)")
        if INGEST_API_KEY:
            try:
                r = client.post(
                    f"{INGEST_URL}/ingest/state",
                    json={"run_id": "e2e-test-run", "process_id": 0, "data_mode": "live", "symbols": ["ES"]},
                    headers={"Authorization": f"Bearer {INGEST_API_KEY}"},
                )
                if not ok("ingest /ingest/state", r):
                    failures += 1
            except Exception as e:
                print(f"  FAIL ingest /ingest/state: {e}")
                failures += 1
        else:
            print("  SKIP ingest (INGEST_API_KEY not set)")

        # --- Analytics REST (optional: needs ANALYTICS_API_KEY) ---
        print("\n3. Analytics REST")
        if ANALYTICS_API_KEY:
            try:
                r = client.get(
                    f"{ANALYTICS_URL}/runs",
                    params={"limit": 5},
                    headers={"Authorization": f"Bearer {ANALYTICS_API_KEY}"},
                )
                if not ok("analytics /runs", r):
                    failures += 1
            except Exception as e:
                print(f"  FAIL analytics /runs: {e}")
                failures += 1
        else:
            print("  SKIP analytics REST (ANALYTICS_API_KEY not set)")

        # --- GraphQL (optional) ---
        print("\n4. GraphQL")
        if ANALYTICS_API_KEY:
            try:
                r = client.post(
                    f"{ANALYTICS_URL}/graphql",
                    json={"query": "query { runs(limit: 2) { run_id created_at } }"},
                    headers={"Authorization": f"Bearer {ANALYTICS_API_KEY}", "Content-Type": "application/json"},
                )
                if not ok("GraphQL runs", r):
                    failures += 1
                else:
                    data = r.json()
                    if "errors" in data and data["errors"]:
                        print(f"  WARN GraphQL errors: {data['errors']}")
            except Exception as e:
                print(f"  FAIL GraphQL: {e}")
                failures += 1
        else:
            print("  SKIP GraphQL (ANALYTICS_API_KEY not set)")

        # --- RLM: similar_trades, hypotheses/generate, replay/checkpoints, benchmark/checkpoints ---
        print("\n5. RLM endpoints")
        try:
            r = client.get(f"{RLM_URL}/similar_trades", params={"trade_id": 1, "limit": 5})
            if not ok("RLM /similar_trades", r):
                failures += 1
        except Exception as e:
            print(f"  FAIL RLM /similar_trades: {e}")
            failures += 1

        try:
            r = client.post(
                f"{RLM_URL}/hypotheses/generate",
                json={"regime_context": "E2E test", "generation": 1},
            )
            if not ok("RLM /hypotheses/generate", r):
                failures += 1
        except Exception as e:
            print(f"  FAIL RLM /hypotheses/generate: {e}")
            failures += 1

        try:
            r = client.get(f"{RLM_URL}/replay/checkpoints", params={"limit": 10})
            if not ok("RLM /replay/checkpoints", r):
                failures += 1
        except Exception as e:
            print(f"  FAIL RLM /replay/checkpoints: {e}")
            failures += 1

        try:
            r = client.get(f"{RLM_URL}/benchmark/checkpoints", params={"limit": 10})
            if not ok("RLM /benchmark/checkpoints", r):
                failures += 1
        except Exception as e:
            print(f"  FAIL RLM /benchmark/checkpoints: {e}")
            failures += 1
    print()
    if failures:
        print("E2E completed with %d failure(s)." % failures)
        return 1
    print("E2E passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
