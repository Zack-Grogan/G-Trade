# Change impact map (generated)

High-impact areas (touching these may require docs/runbook/compliance updates):

- src/engine/ — trading logic, reconciliation
- src/execution/ — order execution
- src/market/ — Topstep client
- src/server/ — local Flask console and health/debug surfaces
- src/bridge/ — legacy bridge code retained for historical recovery only
- config/default.yaml — config surface
- docs/OPERATOR.md, docs/Compliance-Boundaries.md, docs/runbooks/

See AGENTS.md 'What requires docs updates' and 'What requires approval before editing'.
