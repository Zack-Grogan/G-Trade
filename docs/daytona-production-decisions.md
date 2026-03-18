# Daytona Production Decision Records & Acceptance Criteria

## Decision: Single sandbox provider (Daytona only)

- **Context:** What-if RLM runs and replay experiments need isolated, durable sandbox compute. Options considered: Upstash Box, Modal, Daytona.
- **Decision:** Use **Daytona only** for sandbox. No fallback to Box or Modal.
- **Rationale:** Single code path; avoid threshold/quotas confusion; cost and behavior are predictable.

## Runtime sizing (acceptance criteria)

| Criterion | Target | Notes |
|-----------|--------|--------|
| **CPU per sandbox** | ≥ 2 cores | Enough for replay + light RLM logic. |
| **Memory per sandbox** | ≥ 4 GiB | Replay state and small datasets in memory. |
| **Disk per sandbox** | ≥ 10 GiB | Logs, artifacts, optional clone. |
| **Max run time** | 300 s (default) | Configurable per job; what-if runs can request longer. |
| **Concurrent sandboxes** | TBD by quota | Document actual Daytona org/concurrent limit and size RLM queue accordingly. |

## Quotas and limits (acceptance criteria)

- **Daily/monthly sandbox runs:** Document Daytona plan limits; alert when approaching threshold.
- **Auto-stop:** Sandbox must auto-stop after idle (e.g. 15–30 min) to avoid runaway cost.
- **Auto-delete:** Stopped sandboxes auto-delete after interval (e.g. 1 h) unless archived for inspection.
- **Network:** Sandboxes used for what-if replay do not need outbound to Topstep/ProjectX; allow outbound only to Railway (ingest/analytics) if needed for reporting.

## Sign-off

- [ ] Daytona org/account created; API key (DAYTONA_API_KEY) stored in secrets.
- [ ] Runtime sizing (CPU/memory/disk) verified for one what-if replay run.
- [ ] Quotas and auto-stop/auto-delete configured and documented.
- [ ] RLM what-if endpoint (`POST /replay/what-if`) tested with Daytona SDK.
