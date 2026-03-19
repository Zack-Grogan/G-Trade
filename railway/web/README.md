# g-trade-web

Internal operator console for the G-Trade Railway project. The app is Clerk-authenticated and read-only from an execution standpoint: it investigates runs, bridge health, and persisted AI artifacts, but it does not control the trader.

The current UI uses a sidebar-first admin shell with compact top-bar search, route-aware navigation, collapsible desktop navigation, and task-focused views for Dashboard, Chart, Runs, Accounts, Advisory, System, and trade review. When unauthenticated, the app shows only the login screen. The design is intentionally minimal and data-dense so the live account ledger, market chart, and bridge diagnostics stay readable.

For Clerk-gated behavior, the live Railway deployment is the source of truth. Use local `bun run dev` or `bun run start` for build and smoke checks, but validate final visibility, navigation, and login-only behavior on the deployed Railway URL after each push. The production web domain is [`grogan.trade`](https://grogan.trade).

## Surfaces

- `GET /` - operator console for run/bridge/log investigation and advisory chat
- `GET /chart` - market analysis dashboard with stored indicator overlays and executor projections
- `GET /runs` - latest run index
- `GET /accounts` - account summaries and broker trade ledger
- `GET /system` - bridge, runtime, and service health
- `GET /runs/[runId]` - run detail with timeline, bridge health, and order lifecycle
- `GET /trades/[tradeId]` - layered trade reviewer with tape, lifecycle, and rationale
- `GET /rlm` - advisory lineage explorer
- `GET /reports` - persisted report index
- `GET /reports/[reportId]` - persisted report detail
- `POST /api/operator` - server-side advisory analysis trigger for the chat UI

## Env

- `ANALYTICS_API_URL`
- `ANALYTICS_API_KEY`
- `RLM_SERVICE_URL` for direct report / hypothesis generation from the chat UI
- `RLM_AUTH_TOKEN` for the RLM service when direct generation is enabled

All backend access stays on the server. No service tokens are exposed to the browser.

Keyboard shortcut:

- `Cmd+K` / `Ctrl+K` focuses the global search field in the shell.

## Build

```bash
bun run build
bun run lint
```
