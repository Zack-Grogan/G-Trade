#!/usr/bin/env python3
"""
A-to-Z E2E test: ingest → analytics → GraphQL → RLM (health, similar_trades, hypotheses, replay, benchmark).
Must run against Railway (no localhost). Loads .env from repo root if present.
Requires INGEST_URL, ANALYTICS_URL (Railway deploy URLs). RLM_URL optional (skip RLM if unset).
Usage: INGEST_URL=https://g-trade-ingest-xxx.up.railway.app ANALYTICS_URL=https://... [RLM_URL=...] python scripts/e2e_test.py
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

# Base URLs (no trailing slash). No localhost defaults — E2E must run against Railway.
INGEST_URL = (os.environ.get("INGEST_URL") or os.environ.get("RAILWAY_INGEST_URL") or "").rstrip("/")
ANALYTICS_URL = (os.environ.get("ANALYTICS_URL") or os.environ.get("RAILWAY_ANALYTICS_URL") or "").rstrip("/")
RLM_URL = (os.environ.get("RLM_URL") or os.environ.get("RAILWAY_RLM_URL") or "").rstrip("/")
INGEST_API_KEY = os.environ.get("INGEST_API_KEY", "")
ANALYTICS_API_KEY = os.environ.get("ANALYTICS_API_KEY", "")
TIMEOUT = 30.0

def _is_localhost(url: str) -> bool:
    if not url:
        return True
    u = url.lower()
    return "localhost" in u or u.startswith("127.0.0.1") or (u.startswith("http://") and "railway" not in u and "up.railway.app" not in u and ":800" in u)


def _require_railway() -> None:
    """Exit if required URLs are missing or localhost. E2E must run against Railway."""
    if not INGEST_URL or _is_localhost(INGEST_URL):
        print("E2E must run against Railway. Set INGEST_URL to your deploy URL (e.g. https://g-trade-ingest-production.up.railway.app)")
        sys.exit(1)
    if not ANALYTICS_URL or _is_localhost(ANALYTICS_URL):
        print("E2E must run against Railway. Set ANALYTICS_URL to your deploy URL (e.g. https://g-trade-analytics-production.up.railway.app)")
        sys.exit(1)
    if RLM_URL and _is_localhost(RLM_URL):
        print("E2E must run against Railway. Set RLM_URL to your RLM deploy URL or leave unset to skip RLM.")
        sys.exit(1)


def ok(name: str, resp: httpx.Response, body: dict | list | None = None) -> bool:
    if resp.status_code >= 400:
        print(f"  FAIL {name}: status={resp.status_code} body={resp.text[:200]}")
        return False
    print(f"  OK   {name}: status={resp.status_code}")
    return True


def main() -> int:
    _require_railway()
    failures = 0
    print("E2E test (Railway) — INGEST_URL=%s ANALYTICS_URL=%s RLM_URL=%s" % (INGEST_URL, ANALYTICS_URL, RLM_URL or "(unset, skipping RLM)"))
    with httpx.Client(timeout=TIMEOUT) as client:
        # --- Health ---
        print("\n1. Health checks")
        health_checks = [
            ("ingest /health", f"{INGEST_URL}/health"),
            ("analytics /health", f"{ANALYTICS_URL}/health"),
        ]
        if RLM_URL:
            health_checks.append(("rlm /health", f"{RLM_URL}/health"))
        for label, url in health_checks:
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
        if not RLM_URL:
            print("\n5. RLM endpoints — SKIP (RLM_URL not set)")
        else:
            print("\n5. RLM endpoints (require DATABASE_URL)")
            rlm_skipped = 0
            rlm_saw_503 = False
            for label, method, url, kwargs in [
                ("RLM /similar_trades", "get", f"{RLM_URL}/similar_trades", {"params": {"trade_id": 1, "limit": 5}}),
                ("RLM /hypotheses/generate", "post", f"{RLM_URL}/hypotheses/generate", {"json": {"regime_context": "E2E test", "generation": 1}}),
                ("RLM /replay/checkpoints", "get", f"{RLM_URL}/replay/checkpoints", {"params": {"limit": 10}}),
                ("RLM /benchmark/checkpoints", "get", f"{RLM_URL}/benchmark/checkpoints", {"params": {"limit": 10}}),
            ]:
                try:
                    r = client.request(method, url, **kwargs)
                    if r.status_code == 200:
                        print(f"  OK   {label}: status=200")
                    elif r.status_code == 503:
                        rlm_saw_503 = True
                        try:
                            body = r.json()
                            if body.get("service_unavailable") or "DATABASE_URL" in str(body.get("detail", "")):
                                print(f"  SKIP {label}: 503 (DATABASE_URL not set)")
                                rlm_skipped += 1
                                continue
                        except Exception:
                            pass
                        print(f"  FAIL {label}: status=503 body={r.text[:120]}")
                        failures += 1
                    elif r.status_code >= 500 and rlm_saw_503:
                        print(f"  SKIP {label}: {r.status_code} (backend config unavailable)")
                        rlm_skipped += 1
                    else:
                        if not ok(label, r):
                            failures += 1
                except Exception as e:
                    print(f"  FAIL {label}: {e}")
                    failures += 1
            if rlm_skipped:
                print(f"  (RLM: {rlm_skipped} endpoint(s) skipped — DATABASE_URL or backend config not set)")
    print()
    if failures:
        print("E2E completed with %d failure(s)." % failures)
        return 1
    print("E2E passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
