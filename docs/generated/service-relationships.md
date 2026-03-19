# Service relationships (generated)

```
Mac (G-Trade)
  CLI → engine → execution, market (Topstep)
  engine → observability (SQLite)
  Flask console ← observability, logs, broker truth, trade review
  legacy bridge/outbox retained for historical recovery only
```

Active runtime is local-only: execution, broker connectivity, observability, and operator tooling stay on the Mac.
