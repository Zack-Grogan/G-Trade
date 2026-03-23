"""Tenant namespace helpers for runtime paths and identifiers."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Optional

DEFAULT_TENANT_ID = "default"


def normalize_tenant_id(value: Optional[str]) -> str:
    """Return a filesystem-safe tenant identifier."""
    raw = str(value or "").strip().lower()
    if not raw:
        return DEFAULT_TENANT_ID
    normalized = re.sub(r"[^a-z0-9._-]+", "-", raw).strip("._-")
    return normalized or DEFAULT_TENANT_ID


def is_default_tenant(value: Optional[str]) -> bool:
    return normalize_tenant_id(value) == DEFAULT_TENANT_ID


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def resolve_tenant_scoped_path(
    path: str | Path,
    *,
    tenant_id: Optional[str] = None,
    root: Optional[Path] = None,
) -> Path:
    """Resolve a tenant-aware path while preserving the legacy default layout."""
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved

    base_root = root or project_root()
    slug = normalize_tenant_id(tenant_id)
    if slug == DEFAULT_TENANT_ID:
        return base_root / resolved

    parent = resolved.parent
    if str(parent) in {".", ""}:
        return base_root / "tenants" / slug / resolved.name
    return base_root / parent / "tenants" / slug / resolved.name
