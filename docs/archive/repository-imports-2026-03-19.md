# Repository import record — 2026-03-19

This document records the nested repository origins that were imported into the root `G-Trade` monorepo on 2026-03-19.

## Import map

| Path in monorepo | Previous repo | Remote URL | Imported branch | Imported commit |
|---|---|---|---|---|
| `es-hotzone-trader/` | `es-hotzone-trader` | `https://github.com/Zack-Grogan/es-hotzone-trader.git` | `main` | `1f001083faef7fca7e251ebc1984fed8c524be99` |
| `railway/ingest/` | `g-trade-ingest` | `https://github.com/Zack-Grogan/g-trade-ingest.git` | `main` | `c87407c18e3b15f8e35cdc342fbaeda64c76c2ec` |
| `railway/analytics/` | `g-trade-analytics` | `https://github.com/Zack-Grogan/g-trade-analytics.git` | `main` | `66df08fcab5eb3c3a892759062e7749d64311aad` |
| `railway/mcp/` | `g-trade-mcp` | `https://github.com/Zack-Grogan/g-trade-mcp.git` | `main` | `4295087fe625a74137fcd895a22507fde652ad3a` |
| `railway/web/` | `g-trade-web` | `https://github.com/Zack-Grogan/g-trade-web.git` | `main` | `c413d54a7f8707baf8449b3e38bfee7c5d967eab` |

## Notes

- The root `G-Trade` repository becomes the canonical source of truth after this import.
- The previous GitHub repositories remain historical references, but nested `.git` directories were removed from the workspace so the root repo owns the working tree.
- Railway services remain present after the import commit as legacy code pending the separate Railway sunset pass.
