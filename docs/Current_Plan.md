# Current state and plan reference

There is no active migration plan now. The repo is in steady state as a **local trader monorepo**.

## Current system

- **Operator interfaces:** CLI and local Flask console
- **Execution:** trading engine, order executor, and Topstep API stay on the Mac
- **Durability:** SQLite is the only required source of truth
- **Cloud:** retired from the active operator path; historical notes remain archived

## Where to look

- [docs/README.md](README.md)
- [Architecture-Overview.md](Architecture-Overview.md)
- [OPERATOR.md](OPERATOR.md)
- [Current-State.md](Current-State.md)
- [Tasks.md](Tasks.md)
- [archive/railway-sunset/README.md](archive/railway-sunset/README.md)
