#!/usr/bin/env python3
"""
Generate machine-friendly docs index artifacts under docs/generated/.

Safe and idempotent: no app runtime, no network, no mutation of source code.
Only writes under docs/generated/*.md. Run from repo root.

Usage:
  python scripts/generate_docs_index.py

Outputs:
  docs/generated/dependency-map.md
  docs/generated/module-map.md
  docs/generated/routes-map.md
  docs/generated/config-matrix.md
  docs/generated/testing-map.md
  docs/generated/entrypoints.md
  docs/generated/change-impact-map.md
  docs/generated/service-relationships.md
"""

from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATED = REPO_ROOT / "docs" / "generated"
ES_APP = REPO_ROOT / "es-hotzone-trader"
RAILWAY = REPO_ROOT / "railway"


def ensure_dir():
    GENERATED.mkdir(parents=True, exist_ok=True)


def load_pyproject():
    p = ES_APP / "pyproject.toml"
    if not p.exists():
        return {}
    text = p.read_text()
    deps = []
    for line in text.splitlines():
        if line.strip().startswith('"') or line.strip().startswith("'"):
            m = re.match(r'^\s*["\']([^"\']+)["\']', line)
            if m:
                deps.append(m.group(1))
    scripts = {}
    in_scripts = False
    for line in text.splitlines():
        if "[project.scripts]" in line:
            in_scripts = True
            continue
        if in_scripts and "=" in line and not line.strip().startswith("["):
            k, v = line.split("=", 1)
            scripts[k.strip()] = v.strip().strip('"')
        elif in_scripts and line.strip().startswith("["):
            break
    return {"dependencies": deps, "scripts": scripts}


def list_python_packages(root: Path, prefix: str) -> list[str]:
    out = []
    for d in sorted(root.iterdir()):
        if d.is_dir() and not d.name.startswith("_"):
            if (d / "__init__.py").exists():
                out.append(f"{prefix}{d.name}")
    return out


def write_dependency_map():
    data = load_pyproject()
    deps = data.get("dependencies", [])
    lines = ["# Dependency map (generated)", "", "## es-hotzone-trader (runtime)", ""]
    for d in deps:
        lines.append(f"- {d}")
    lines.append("")
    lines.append("## railway/ingest, analytics, mcp")
    lines.append("- fastapi, uvicorn, psycopg2, httpx (see railway/*/requirements.txt)")
    lines.append("")
    lines.append("## railway/web")
    lines.append("- next, react (see railway/web/package.json)")
    (GENERATED / "dependency-map.md").write_text("\n".join(lines))


def write_module_map():
    src = ES_APP / "src"
    modules = []
    if src.exists():
        for d in sorted(src.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                modules.append(f"es-hotzone-trader.src.{d.name}")
    lines = ["# Module map (generated)", "", "## es-hotzone-trader/src", ""]
    for m in modules:
        lines.append(f"- {m}")
    lines.append("")
    lines.append("## railway services")
    for name in ["ingest", "analytics", "mcp", "web"]:
        p = RAILWAY / name
        if p.exists():
            lines.append(f"- railway/{name} (app entry: app.py or Next.js)")
    (GENERATED / "module-map.md").write_text("\n".join(lines))


def write_routes_map():
    lines = [
        "# Routes / endpoints map (generated)",
        "",
        "## railway/ingest",
        "- POST /ingest/state",
        "- POST /ingest/events",
        "- POST /ingest/trades",
        "- GET /health",
        "",
        "## railway/analytics",
        "- GET /runs",
        "- GET /runs/{run_id}",
        "- GET /runs/{run_id}/events",
        "- GET /runs/{run_id}/trades",
        "- GET /analytics/summary",
        "- GET /health",
        "",
        "## railway/mcp",
        "- POST /mcp (JSON-RPC)",
        "- GET /mcp (metadata)",
        "- GET /health",
        "",
        "## railway/web",
        "- Next.js app; calls analytics API only.",
        "",
        "## es-hotzone-trader (local debug server)",
        "- GET /health",
        "- GET /debug (state snapshot)",
        "",
    ]
    (GENERATED / "routes-map.md").write_text("\n".join(lines))


def write_config_matrix():
    yaml_path = ES_APP / "config" / "default.yaml"
    lines = ["# Config matrix (generated)", "", "Top-level keys in es-hotzone-trader/config/default.yaml:", ""]
    if yaml_path.exists():
        text = yaml_path.read_text()
        for line in text.splitlines():
            m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:", line)
            if m:
                lines.append(f"- {m.group(1)}")
    lines.append("")
    lines.append("Env / overrides: RAILWAY_INGEST_API_KEY, DATABASE_URL, INGEST_API_KEY, ANALYTICS_API_KEY, etc. (see OPERATOR.md and railway READMEs).")
    (GENERATED / "config-matrix.md").write_text("\n".join(lines))


def write_testing_map():
    tests_dir = ES_APP / "tests"
    lines = ["# Testing map (generated)", "", "## es-hotzone-trader/tests", ""]
    if tests_dir.exists():
        for f in sorted(tests_dir.glob("test_*.py")):
            lines.append(f"- {f.name}")
    lines.append("")
    lines.append("Run: `pytest` from es-hotzone-trader/ or repo root. Config: pyproject.toml [tool.pytest.ini_options].")
    (GENERATED / "testing-map.md").write_text("\n".join(lines))


def write_entrypoints():
    data = load_pyproject()
    scripts = data.get("scripts", {})
    lines = ["# Entrypoints (generated)", "", "## es-hotzone-trader", ""]
    for name, ref in scripts.items():
        lines.append(f"- **{name}** → {ref}")
    lines.append("")
    lines.append("## railway")
    lines.append("- ingest: railway/ingest/app.py (uvicorn)")
    lines.append("- analytics: railway/analytics/app.py (uvicorn)")
    lines.append("- mcp: railway/mcp/app.py (uvicorn)")
    lines.append("- web: railway/web (npm run dev / next start)")
    (GENERATED / "entrypoints.md").write_text("\n".join(lines))


def write_change_impact_map():
    lines = [
        "# Change impact map (generated)",
        "",
        "High-impact areas (touching these may require docs/runbook/compliance updates):",
        "",
        "- es-hotzone-trader/src/engine/ — trading logic, reconciliation",
        "- es-hotzone-trader/src/execution/ — order execution",
        "- es-hotzone-trader/src/market/ — Topstep client",
        "- es-hotzone-trader/src/bridge/ — telemetry to Railway",
        "- es-hotzone-trader/config/default.yaml — config surface",
        "- railway/ingest/app.py — ingest API and schema",
        "- docs/OPERATOR.md, docs/Compliance-Boundaries.md, docs/runbooks/",
        "",
        "See AGENTS.md 'What requires docs updates' and 'What requires approval before editing'.",
        "",
    ]
    (GENERATED / "change-impact-map.md").write_text("\n".join(lines))


def write_service_relationships():
    lines = [
        "# Service relationships (generated)",
        "",
        "```",
        "Mac (es-hotzone-trader)",
        "  CLI → engine → execution, market (Topstep)",
        "  engine → observability (SQLite)",
        "  bridge ← debug server, observability → outbox → HTTPS → Railway ingest",
        "",
        "Railway",
        "  ingest → Postgres",
        "  analytics ← Postgres (read-only)",
        "  mcp ← analytics API (read-only)",
        "  web ← analytics API (read-only)",
        "  Cursor/IDE → mcp (MCP)",
        "```",
        "",
        "Data flow: Mac → Railway only. No execution or broker on Railway.",
        "",
    ]
    (GENERATED / "service-relationships.md").write_text("\n".join(lines))


def main():
    ensure_dir()
    write_dependency_map()
    write_module_map()
    write_routes_map()
    write_config_matrix()
    write_testing_map()
    write_entrypoints()
    write_change_impact_map()
    write_service_relationships()
    print("Generated docs index under docs/generated/")


if __name__ == "__main__":
    main()
