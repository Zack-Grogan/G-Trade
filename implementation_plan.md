# G-Trade Web UI/UX Redesign

The G-Trade operator console currently crams ~10 panels onto a single monolithic homepage, making it hard to read, use, or derive actionable insight from. This plan restructures the web app into focused, task-oriented pages with clear information hierarchy.

## Diagnosis — Current Problems

### 1. Homepage information overload
The home [page.tsx](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/app/page.tsx) (374 lines) renders **10 distinct panels** in a single scroll: operator cockpit, selected run, decision board, P&L chart, accounts table, account-trade ledger, runs table, service health, RLM artifacts, and operator chat. Every panel fights for attention.

### 2. Duplicated data across pages
- The **Reports** page is a subset of the RLM page (same data, same component)
- The **Runs** page duplicates account trades table from home
- The **Chart** page re-fetches and re-renders account summaries already shown at home
- The homepage duplicates the run table, RLM summary, and service health that all have dedicated pages

### 3. No clear information hierarchy
Every panel uses the same visual weight ([Panel](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/components/dashboard.tsx#52-79) with eyebrow + title). There's no distinction between "glance-level KPI" vs "deep-dive table" vs "action trigger". The user can't quickly scan what matters.

### 4. Overlapping page concerns
- `/rlm` shows reports, hypotheses, knowledge store, AND lineage — 4 different concerns
- `/chart` shows the chart AND a full indicator table AND account summary
- Homepage has search, run selection, AND operator chat on one page

### 5. Missing pages for key workflows
- No dedicated **Accounts** page despite the pipeline tracking multiple Topstep accounts
- No dedicated **System/Health** page — health data is buried in the homepage
- No dedicated **Trade Review** list page (only individual trade detail exists)

---

## User Review Required

> [!IMPORTANT]
> This redesign restructures the navigation from 5 pages to 6 pages, changes the URL structure, and significantly changes what appears on the homepage. The existing data pipeline and analytics API stay untouched — all changes are frontend-only.

> [!WARNING]
> The current [operator-chat.tsx](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/components/operator-chat.tsx) uses server actions via `/api/operator`. This plan moves it to a dedicated Advisory page but keeps the same backend contract. No API changes.

Key design decisions for your input:
1. **Navigation restructure** — Would you prefer the current 5-tab flat nav, or the proposed 6-tab structure with clearer groupings?
2. **Homepage scope** — The plan makes it a "pulse dashboard" with only 4-6 KPI cards + one status strip. Is that too minimal, or do you want some tables to remain?
3. **Operator Chat** — Currently buried at the bottom of the homepage. Plan moves it to a dedicated `/advisory` page with the RLM content. Good?

---

## Proposed Architecture

### Current → Proposed Navigation

| Current | Problems | Proposed |
|---------|----------|----------|
| **Console** (`/`) — 10 panels | Information overload | **Dashboard** (`/`) — Pulse KPIs only (4-6 cards + status strip) |
| **Chart** (`/chart`) — chart + full indicator dump | Too much peripheral data | **Chart** (`/chart`) — Clean chart, collapsible indicator sidebar |
| **Runs** (`/runs`) — runs + account fallback | Mixes run index with trade data | **Runs** (`/runs`) — Focused run investigation |
| **RLM** (`/rlm`) — hypotheses + reports + knowledge | Too many concerns | **Advisory** (`/advisory`) — RLM lineage + operator chat + reports unified |
| **Reports** (`/reports`) — subset of RLM | Redundant | *(merged into Advisory)* |
| *(missing)* | No account/trade focus | **Accounts** (`/accounts`) — Account performance + trade ledger |
| *(missing)* | Health buried in homepage | **System** (`/system`) — Service health, bridge status, runtime logs |

### Page Breakdown

```
/ (Dashboard)
├── Status strip: bridge alive?, last heartbeat, account mode badge
├── KPI row: Today P&L, Win rate, Active position, Score gap
├── Mini equity curve (last 8 trades sparkline)
└── Quick links to latest run, latest trade, advisory

/accounts
├── Account summary cards (per-account P&L, trade count, mode)
├── Account trade ledger table (sortable, paginated)
└── P&L bar chart

/runs
├── Search bar
├── Run table (real runs, filterable)
└── Click → /runs/[runId] for deep investigation (existing)

/chart
├── Full-width chart (existing LiveMarketChart)
├── Compact stat bar (price, bias, gap, regime)
└── Collapsible indicator panel (existing details→summary)

/advisory
├── RLM hypothesis lineage tree
├── Latest reports list
├── Knowledge store table
├── Operator chat (full width, prominent)
└── Meta learner stats

/system
├── Service health grid (analytics, bridge, runtime logs)
├── Bridge failure log
├── Latest report metadata
└── Bridge heartbeat timeline
```

---

## Proposed Changes

### Navigation & Layout

#### [MODIFY] [app-shell.tsx](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/components/app-shell.tsx)

Update `NAV_ITEMS` to the new 6-page structure:
- Console → Dashboard (keep `/`)
- Chart → Chart (keep `/chart`)
- Runs → Runs (keep `/runs`)
- RLM → Advisory (`/advisory`)
- Reports → *(remove, merged into Advisory)*
- *(add)* Accounts (`/accounts`)
- *(add)* System (`/system`)

Add nav section groupings (visually separate "Operations" from "Analysis" from "Infrastructure") using subtle dividers. Add icons via simple SVG inline or emoji for each nav item.

---

### Dashboard (Homepage)

#### [MODIFY] [page.tsx](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/app/page.tsx)

**Gut the current 374-line monolith.** Replace with a focused pulse dashboard:

- **Status strip** (1 row): Bridge status pill, account mode pill, last heartbeat time, active run indicator
- **KPI cards** (1 row, 4-5 cards): Today P&L, current position, score gap, dominant bias, win rate
- **Mini equity curve**: Reuse `MiniBarChart` with last 8 account trades
- **Quick action links**: "Latest run →", "Open chart →", "Advisory →", "Latest trade review →"
- **Remove** all tables and detailed panels from homepage (they move to dedicated pages)

This takes the page from ~374 lines to ~120 lines.

---

### Accounts & Trades Page

#### [NEW] [page.tsx](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/app/accounts/page.tsx)

New page that consolidates all account/trade data currently scattered across home and runs:

- Account summary cards (from current homepage "Accounts" panel)
- Full account-trade ledger table (from current homepage "Account-trade ledger" panel)
- P&L bar chart (from current homepage "Ledger pulse" panel)
- Per-account drill-down links

---

### Chart Page Cleanup

#### [MODIFY] [page.tsx](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/app/chart/page.tsx)

- Remove duplicate account summary data (lives on `/accounts` now)
- Keep the chart as the hero element
- Keep the compact stat bar below the chart
- Keep the collapsible `<details>` indicator panel — it's already the right pattern
- Remove the "Account summary" stat card from the 4-card stat row — replace with a more chart-relevant metric

---

### Runs Page

#### [MODIFY] [page.tsx](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/app/runs/page.tsx)

- Remove the account-trade fallback section (that data lives on `/accounts`)
- Keep the run table with search
- Add run status filter pills (running / stopped / all)
- Keep linking to `/runs/[runId]` for deep investigation

---

### Advisory Page (RLM + Operator Chat)

#### [NEW] [page.tsx](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/app/advisory/page.tsx)

Merge the current `/rlm` page and the `OperatorChat` component into one focused advisory workspace:

- **Top section**: Operator chat (prominent, full width) — moved from the bottom of the homepage
- **Middle section**: RLM hypothesis lineage tree + latest reports (2-column)
- **Bottom section**: Knowledge store table + meta learner stats

#### [MODIFY] [page.tsx](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/app/rlm/page.tsx)

Replace with a redirect to `/advisory` so existing bookmarks/links don't break.

#### [MODIFY] [page.tsx](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/app/reports/page.tsx)

Replace with a redirect to `/advisory` so existing bookmarks/links don't break.

---

### System Health Page

#### [NEW] [page.tsx](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/app/system/page.tsx)

New page that consolidates infrastructure health data currently buried in the homepage:

- Service health grid (analytics status, bridge status, runtime log count)
- Bridge failure log
- Latest bridge heartbeat details
- Latest report metadata card

---

### Design System Improvements

#### [MODIFY] [dashboard.tsx](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/components/dashboard.tsx)

- Add a `KpiCard` component variant of `StatCard` with a subtle glow/gradient for important metrics
- Add a `StatusPill` component for inline status indicators (bridge alive, account mode)
- Add `danger` tone to `Badge` for error states
- Add hover micro-animations to `Panel` borders

#### [MODIFY] [globals.css](file:///Users/zgrogan/Repos/G-Trade/railway/web/src/app/globals.css)

- Add CSS custom properties for the color palette (currently all inline Tailwind)
- Add subtle glow keyframe animation for the KPI cards
- Add smooth transition for panel hover effects

---

## What stays unchanged

- `src/lib/analytics.ts` — all data fetching stays as-is
- `src/lib/operator.ts` — operator API client stays as-is
- `src/lib/session.ts` — auth stays as-is
- `src/app/api/operator/` — server action stays as-is
- `src/app/runs/[runId]/` — run detail page stays as-is
- `src/app/trades/[tradeId]/` — trade detail page stays as-is
- `src/app/reports/[reportId]/` — report detail page stays as-is (linked from advisory)
- `src/components/live-market-chart.tsx` — chart component stays as-is
- `src/components/market-chart.tsx` — chart component stays as-is
- `src/components/live-refresh.tsx` — stays as-is
- All railway backend services (analytics, ingest, mcp, rlm) — **no changes**

---

## Verification Plan

### Build Verification
```bash
cd /Users/zgrogan/Repos/G-Trade/railway/web && bun run build
```
Must complete without errors. This validates all TypeScript, imports, and Next.js page generation.

### Browser Verification
After build passes, run dev server and verify each page loads correctly:
```bash
cd /Users/zgrogan/Repos/G-Trade/railway/web && bun run dev
```
Then visually verify each page in the browser:
1. `/` — Dashboard loads with KPI cards and status strip
2. `/accounts` — Account summary cards and trade ledger render
3. `/runs` — Run table renders with search
4. `/chart` — Chart renders with stat bar
5. `/advisory` — Operator chat and RLM lineage render
6. `/system` — Service health grid renders
7. `/rlm` — Redirects to `/advisory`
8. `/reports` — Redirects to `/advisory`

### Manual Verification (User)
After deploying to Railway, verify on the live URL:
1. Clerk auth works on all new pages
2. All data populates from the analytics API
3. Navigation between pages feels clean and fast
4. No broken links to run/trade/report detail pages
5. Operator chat still functions on the advisory page
