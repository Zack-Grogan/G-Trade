# Module map

This directory holds module-level documentation. The codebase is organized as:

- **es-hotzone-trader/src/** — CLI, engine, execution, market, observability, bridge, server, strategies, indicators, config. See [es-hotzone-trader/README.md](../../es-hotzone-trader/README.md) and [architecture/overview.md](../architecture/overview.md).
- **railway/** — One service per directory (ingest, analytics, mcp, web); each has a README and app entry point. See [railway/ingest/README.md](../../railway/ingest/README.md), [railway/analytics/README.md](../../railway/analytics/README.md), [railway/mcp/README.md](../../railway/mcp/README.md), [railway/web/README.md](../../railway/web/README.md).

Generated module and dependency maps are produced by `scripts/generate_docs_index.py` and live under [docs/generated/](../generated/).
