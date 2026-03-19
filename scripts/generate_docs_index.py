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
ES_APP = REPO_ROOT


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
    lines = ["# Dependency map (generated)", "", "## G-Trade runtime", ""]
    for d in deps:
        lines.append(f"- {d}")
    lines.append("")
    lines.append("## Local operator stack")
    lines.append("- click, flask, sqlite3, requests, websockets, pandas, numpy")
    lines.append("- Topstep integration runs locally via src/market")
    (GENERATED / "dependency-map.md").write_text("\n".join(lines))


def write_module_map():
    src = ES_APP / "src"
    modules = []
    if src.exists():
        for d in sorted(src.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                modules.append(f"src.{d.name}")
    lines = ["# Module map (generated)", "", "## src", ""]
    for m in modules:
        lines.append(f"- {m}")
    (GENERATED / "module-map.md").write_text("\n".join(lines))


def write_routes_map():
    lines = [
        "# Routes / endpoints map (generated)",
        "",
        "## Local service",
        "- GET /health",
        "- GET /debug (state snapshot)",
        "- GET / (Flask console)",
        "- GET /chart",
        "- GET /trades",
        "- GET /logs",
        "- GET /system",
        "",
    ]
    (GENERATED / "routes-map.md").write_text("\n".join(lines))


def write_config_matrix():
    yaml_path = ES_APP / "config" / "default.yaml"
    lines = ["# Config matrix (generated)", "", "Top-level keys in config/default.yaml:", ""]
    if yaml_path.exists():
        text = yaml_path.read_text()
        for line in text.splitlines():
            m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:", line)
            if m:
                lines.append(f"- {m.group(1)}")
    lines.append("")
    lines.append("Env / overrides: broker auth, account selection, and local port overrides. See docs/ENV.md and docs/OPERATOR.md.")
    (GENERATED / "config-matrix.md").write_text("\n".join(lines))


def write_testing_map():
    tests_dir = ES_APP / "tests"
    lines = ["# Testing map (generated)", "", "## tests", ""]
    if tests_dir.exists():
        for f in sorted(tests_dir.glob("test_*.py")):
            lines.append(f"- {f.name}")
    lines.append("")
    lines.append("Run: `pytest` from the repo root. Config: pyproject.toml [tool.pytest.ini_options].")
    (GENERATED / "testing-map.md").write_text("\n".join(lines))


def write_entrypoints():
    data = load_pyproject()
    scripts = data.get("scripts", {})
    lines = ["# Entrypoints (generated)", "", "## G-Trade", ""]
    for name, ref in scripts.items():
        lines.append(f"- **{name}** → {ref}")
    (GENERATED / "entrypoints.md").write_text("\n".join(lines))


def write_change_impact_map():
    lines = [
        "# Change impact map (generated)",
        "",
        "High-impact areas (touching these may require docs/runbook/compliance updates):",
        "",
        "- src/engine/ — trading logic, reconciliation",
        "- src/execution/ — order execution",
        "- src/market/ — Topstep client",
        "- src/server/ — local Flask console and health/debug surfaces",
        "- src/bridge/ — legacy bridge code retained for historical recovery only",
        "- config/default.yaml — config surface",
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
        "Mac (G-Trade)",
        "  CLI → engine → execution, market (Topstep)",
        "  engine → observability (SQLite)",
        "  Flask console ← observability, logs, broker truth, trade review",
        "  legacy bridge/outbox retained for historical recovery only",
        "```",
        "",
        "Active runtime is local-only: execution, broker connectivity, observability, and operator tooling stay on the Mac.",
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
