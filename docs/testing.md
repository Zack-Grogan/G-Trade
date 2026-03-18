# Testing

- **es-hotzone-trader:** Tests live under `es-hotzone-trader/tests/`. Run with `pytest` (from `es-hotzone-trader/` or repo root). Config: `tool.pytest.ini_options` in `es-hotzone-trader/pyproject.toml` (testpaths, asyncio_mode).
- **Railway services:** No shared test suite in repo; each service can be exercised locally for development only. Deployment and validation target Railway.
- **Docs:** Generated docs (e.g. testing map) are produced by `scripts/generate_docs_index.py` and appear under [docs/generated/](generated/).

Run relevant tests before completing code changes. See [AGENTS.md](../AGENTS.md) "Testing contract" and the rule `.cursor/rules/30-testing-discipline.mdc`.
