# Service relationships (generated)

```
Mac (G-Trade)
  CLI → engine → execution, market (Topstep)
  engine → observability (SQLite)
  CLI ← observability (SQLite), runtime state
  retired bridge/outbox history archived only
```

Active runtime is local-only: execution, broker connectivity, observability, and operator tooling stay on the Mac.
