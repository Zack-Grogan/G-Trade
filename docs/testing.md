# Testing

- **Trader runtime:** Tests live under `tests/`. Run with `pytest` from the repo root. Config: `tool.pytest.ini_options` in `pyproject.toml` (testpaths, asyncio_mode).
- **Docs:** Generated docs (e.g. testing map) are produced by `scripts/generate_docs_index.py` and appear under [docs/generated/](generated/).

Run relevant tests before completing code changes. See [AGENTS.md](../AGENTS.md) "Testing contract" and the rule `.cursor/rules/30-testing-discipline.mdc`.
