type GraphQLResponse<T> = {
  data?: T;
  errors?: Array<{ message: string }>;
};

export type AnalyticsSummary = {
  run_count: number;
  event_count: number;
  state_snapshot_count: number;
  blocker_count: number;
  trade_count: number;
  total_pnl: number;
  report_count: number;
  bridge_failure_count: number;
  latest_report_at: string | null;
  latest_bridge_failure_at: string | null;
  latest_state_at: string | null;
  latest_trade_at: string | null;
  latest_run_seen_at: string | null;
};

export type RunRow = {
  runId: string;
  createdAt: string;
  lastSeenAt: string | null;
  processId: number | null;
  dataMode: string | null;
  symbol: string | null;
  accountId: string | null;
  accountName: string | null;
  accountMode: string | null;
  accountIsPractice: boolean | null;
  status: string | null;
  zone: string | null;
  zoneState: string | null;
  position: number | null;
  positionPnl: number | null;
  dailyPnl: number | null;
  riskState: string | null;
  lastEntryBlockReason: string | null;
  payloadJson: Record<string, unknown> | null;
};

export type EventRow = {
  id: number;
  runId: string;
  eventTimestamp: string;
  insertedAt: string;
  category: string | null;
  eventType: string | null;
  source: string | null;
  symbol: string | null;
  zone: string | null;
  action: string | null;
  reason: string | null;
  orderId: string | null;
  riskState: string | null;
  contracts: number | null;
  orderStatus: string | null;
  guardReason: string | null;
  decisionSide: string | null;
  decisionPrice: number | null;
  expectedFillPrice: number | null;
  entryGuardJson: Record<string, unknown> | null;
  unresolvedEntryJson: Record<string, unknown> | null;
  executionJson: Record<string, unknown> | null;
  payloadJson: Record<string, unknown> | null;
};

export type MarketTapeRow = {
  id: number;
  runId: string;
  capturedAt: string;
  insertedAt: string;
  processId: number | null;
  symbol: string | null;
  contractId: string | null;
  bid: number | null;
  ask: number | null;
  last: number | null;
  volume: number | null;
  bidSize: number | null;
  askSize: number | null;
  lastSize: number | null;
  volumeIsCumulative: boolean | null;
  quoteIsSynthetic: boolean | null;
  tradeSide: number | null;
  latencyMs: number | null;
  source: string | null;
  sequence: number | null;
  payloadJson: Record<string, unknown> | null;
};

export type TradeRow = {
  id: number;
  runId: string;
  insertedAt: string | null;
  entryTime: string | null;
  exitTime: string | null;
  direction: number;
  contracts: number;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  zone: string | null;
  strategy: string | null;
  regime: string | null;
  eventTagsJson: unknown | null;
  source: string | null;
  backfilled: boolean | null;
  tradeId: string | null;
  positionId: string | null;
  decisionId: string | null;
  attemptId: string | null;
  accountId: string | null;
  accountName: string | null;
  accountMode: string | null;
  accountIsPractice: boolean | null;
  payloadJson: Record<string, unknown> | null;
};

export type StateSnapshotRow = {
  id: number;
  runId: string;
  capturedAt: string;
  status: string | null;
  dataMode: string | null;
  symbol: string | null;
  zone: string | null;
  zoneState: string | null;
  position: number | null;
  positionPnl: number | null;
  dailyPnl: number | null;
  riskState: string | null;
  accountId: string | null;
  accountName: string | null;
  accountMode: string | null;
  accountIsPractice: boolean | null;
  lastSignalJson: Record<string, unknown> | null;
  lastEntryReason: string | null;
  lastEntryBlockReason: string | null;
  decisionPrice: number | null;
  entryGuardJson: Record<string, unknown> | null;
  unresolvedEntryJson: Record<string, unknown> | null;
  executionJson: Record<string, unknown> | null;
  heartbeatJson: Record<string, unknown> | null;
  lifecycleJson: Record<string, unknown> | null;
  observabilityJson: Record<string, unknown> | null;
  payloadJson: Record<string, unknown> | null;
};

export type DecisionSnapshotRow = {
  id: number;
  runId: string;
  decidedAt: string;
  insertedAt: string;
  decisionId: string;
  attemptId: string | null;
  processId: number | null;
  symbol: string | null;
  zone: string | null;
  action: string | null;
  reason: string | null;
  outcome: string | null;
  outcomeReason: string | null;
  longScore: number | null;
  shortScore: number | null;
  flatBias: number | null;
  scoreGap: number | null;
  dominantSide: string | null;
  currentPrice: number | null;
  allowEntries: boolean | null;
  executionTradeable: boolean | null;
  contracts: number | null;
  orderType: string | null;
  limitPrice: number | null;
  decisionPrice: number | null;
  side: string | null;
  stopLoss: number | null;
  takeProfit: number | null;
  maxHoldMinutes: number | null;
  regimeState: string | null;
  regimeReason: string | null;
  activeSession: string | null;
  activeVetoes: unknown[];
  featureSnapshot: Record<string, unknown> | null;
  entryGuard: Record<string, unknown> | null;
  unresolvedEntry: Record<string, unknown> | null;
  eventContext: Record<string, unknown> | null;
  orderFlow: Record<string, unknown> | null;
  payloadJson: Record<string, unknown> | null;
};

export type OrderLifecycleRow = {
  id: number;
  runId: string;
  observedAt: string;
  insertedAt: string;
  decisionId: string | null;
  attemptId: string | null;
  orderId: string | null;
  positionId: string | null;
  tradeId: string | null;
  processId: number | null;
  symbol: string | null;
  eventType: string | null;
  status: string | null;
  side: string | null;
  role: string | null;
  isProtective: boolean | null;
  orderType: string | null;
  quantity: number | null;
  contracts: number | null;
  limitPrice: number | null;
  stopPrice: number | null;
  expectedFillPrice: number | null;
  filledPrice: number | null;
  filledQuantity: number | null;
  remainingQuantity: number | null;
  zone: string | null;
  reason: string | null;
  lifecycleState: string | null;
  payloadJson: Record<string, unknown> | null;
};

export type BridgeHealthRow = {
  id: number;
  runId: string | null;
  observedAt: string;
  insertedAt: string;
  bridgeStatus: string | null;
  queueDepth: number | null;
  lastFlushAt: string | null;
  lastSuccessAt: string | null;
  lastError: string | null;
  payloadJson: Record<string, unknown> | null;
};

export type TimelineEntry = {
  kind: "event" | "state_snapshot" | "decision_snapshot" | "order_lifecycle" | "bridge_health" | "trade";
  timestamp: string | null;
  runId: string;
  [key: string]: unknown;
};

export type HypothesisRow = {
  id: number;
  hypothesisId: string;
  generation: number;
  parentHypothesisId: string | null;
  claimText: string;
  regimeContext: string | null;
  status: string;
  createdAt: string;
  updatedAt: string;
};

export type KnowledgeRow = {
  id: number;
  hypothesisId: string;
  verdict: string;
  confidenceScore: number | null;
  mutationDirective: string | null;
  regimeTags: Record<string, unknown> | null;
  survivalCount: number;
  rejectionCount: number;
  createdAt: string;
};

export type ReportRow = {
  id: number;
  reportId: string;
  title: string;
  reportType: string;
  modelProvider: string;
  modelName: string;
  status: string;
  summaryText: string;
  reportJson: Record<string, unknown> | null;
  createdAt: string;
  completedAt: string | null;
};

export type MetaLearnerStats = {
  survivalCount: number;
  rejectionCount: number;
  stats: Record<string, unknown>;
};

export type DashboardData = {
  summary: AnalyticsSummary;
  runs: RunRow[];
  trades: TradeRow[];
  hypotheses: HypothesisRow[];
  knowledgeStore: KnowledgeRow[];
  reports: ReportRow[];
  metaLearnerStats: MetaLearnerStats | null;
};

export type AccountSummaryRow = {
  accountId: string;
  accountName: string | null;
  accountMode: string | null;
  accountIsPractice: boolean | null;
  runCount: number;
  tradeCount: number;
  realizedPnl: number;
  latestTradeAt: string | null;
  latestRunSeenAt: string | null;
};

export type AccountTradeRow = {
  id: number;
  runId: string | null;
  insertedAt: string | null;
  occurredAt: string;
  accountId: string;
  accountName: string | null;
  accountMode: string | null;
  accountIsPractice: boolean | null;
  brokerTradeId: string;
  brokerOrderId: string | null;
  contractId: string | null;
  side: number | null;
  size: number | null;
  price: number | null;
  profitAndLoss: number | null;
  fees: number | null;
  voided: boolean | null;
  source: string | null;
  payloadJson: Record<string, unknown> | null;
};

export type BridgeFailureRow = {
  id: number;
  runId: string | null;
  observedAt: string;
  bridgeStatus: string | null;
  queueDepth: number | null;
  lastFlushAt: string | null;
  lastSuccessAt: string | null;
  lastError: string | null;
  payloadJson: Record<string, unknown> | null;
};

export type ServiceHealthSnapshot = {
  analytics: { status: string; pool: Record<string, unknown> } | null;
  bridge: Record<string, unknown> | null;
  runtimeLogs: { count: number; latestLoggedAt: string | null } | null;
  reports: { count: number; latestCreatedAt: string | null } | null;
};

export type RunDetail = {
  run: RunRow | null;
  events: EventRow[];
  marketTape: MarketTapeRow[];
  trades: TradeRow[];
  stateSnapshots: StateSnapshotRow[];
  decisionSnapshots: DecisionSnapshotRow[];
  orderLifecycle: OrderLifecycleRow[];
  bridgeHealth: BridgeHealthRow[];
  timeline: TimelineEntry[];
  blockers: TimelineEntry[];
};

export type ReportDetail = ReportRow | null;

export type TradeReviewAnalysis = {
  summary: string;
  marketContext: {
    sampleCount: number;
    firstTimestamp: string | null;
    lastTimestamp: string | null;
    firstPrice: number | null;
    lastPrice: number | null;
    stats: Record<string, unknown>;
  };
  entryExit: {
    direction: string;
    entryTime: string | null;
    exitTime: string | null;
    duration: string | null;
    entryPrice: number | null;
    exitPrice: number | null;
    pnl: number | null;
  };
  executorBelief: {
    decisionId: string | null;
    dominantSide: string | null;
    scoreGap: number | null;
    longScore: number | null;
    shortScore: number | null;
    allowEntries: boolean | null;
    executionTradeable: boolean | null;
    regimeState: string | null;
    regimeReason: string | null;
    activeSession: string | null;
    featureSnapshot: Record<string, unknown> | null;
    signedFeatures: Record<string, unknown>;
    diagnostics: Record<string, unknown>;
    longFeatures: Record<string, unknown>;
    shortFeatures: Record<string, unknown>;
    flatFeatures: Record<string, unknown>;
  };
  narrative: string[];
  marketNotes: string[];
  executionNotes: string[];
  executorProjection: string[];
};

export type TradeReviewBundle = {
  trade: TradeRow | null;
  run: RunRow | null;
  marketTape: MarketTapeRow[];
  decisionSnapshots: DecisionSnapshotRow[];
  stateSnapshots: StateSnapshotRow[];
  orderLifecycle: OrderLifecycleRow[];
  events: EventRow[];
  timeline: TimelineEntry[];
  blockers: TimelineEntry[];
  analysis: TradeReviewAnalysis | null;
};

const ANALYTICS_URL = process.env.ANALYTICS_API_URL || "";
const ANALYTICS_KEY = process.env.ANALYTICS_API_KEY || "";

type JsonRecord = Record<string, unknown>;

function analyticsFetchInit() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${ANALYTICS_KEY}`,
  };
}

async function queryAnalytics<T>(query: string, variables?: Record<string, unknown>): Promise<T | null> {
  if (!ANALYTICS_URL || !ANALYTICS_KEY) {
    return null;
  }

  try {
    const response = await fetch(`${ANALYTICS_URL.replace(/\/$/, "")}/graphql`, {
      method: "POST",
      headers: analyticsFetchInit(),
      body: JSON.stringify({ query, variables }),
      next: { revalidate: 30 },
    });

    if (!response.ok) {
      return null;
    }

    const payload = (await response.json()) as GraphQLResponse<T>;
    if (payload.errors?.length) {
      return null;
    }

    return payload.data ?? null;
  } catch {
    return null;
  }
}

async function fetchAnalyticsJson<T>(path: string, params?: Record<string, string | number | null | undefined>): Promise<T | null> {
  if (!ANALYTICS_URL || !ANALYTICS_KEY) {
    return null;
  }

  try {
    const url = new URL(`${ANALYTICS_URL.replace(/\/$/, "")}${path}`);
    for (const [key, value] of Object.entries(params ?? {})) {
      if (value !== null && value !== undefined && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }

    const response = await fetch(url.toString(), {
      headers: analyticsFetchInit(),
      next: { revalidate: 30 },
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as T;
  } catch {
    return null;
  }
}

function asRecord(value: unknown): JsonRecord {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as JsonRecord;
  }

  return {};
}

function stringOrEmpty(value: unknown): string {
  return typeof value === "string" ? value : value == null ? "" : String(value);
}

function stringOrNull(value: unknown): string | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  return typeof value === "string" ? value : String(value);
}

function numberOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function numberOrZero(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function booleanOrNull(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function recordOrNull(value: unknown): JsonRecord | null {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as JsonRecord) : null;
}

function arrayOrEmpty(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function timelineKind(value: unknown): TimelineEntry["kind"] {
  switch (typeof value === "string" ? value : "event") {
    case "state_snapshot":
    case "decision_snapshot":
    case "order_lifecycle":
    case "bridge_health":
    case "trade":
    case "event":
      return value as TimelineEntry["kind"];
    default:
      return "event";
  }
}

function normalizeRunRow(run: unknown): RunRow {
  const record = asRecord(run);
  return {
    runId: stringOrEmpty(record.run_id ?? record.runId),
    createdAt: stringOrEmpty(record.created_at ?? record.createdAt),
    lastSeenAt: stringOrNull(record.last_seen_at ?? record.lastSeenAt),
    processId: numberOrNull(record.process_id ?? record.processId),
    dataMode: stringOrNull(record.data_mode ?? record.dataMode),
    symbol: stringOrNull(record.symbol),
    accountId: stringOrNull(record.account_id ?? record.accountId),
    accountName: stringOrNull(record.account_name ?? record.accountName),
    accountMode: stringOrNull(record.account_mode ?? record.accountMode),
    accountIsPractice: booleanOrNull(record.account_is_practice ?? record.accountIsPractice),
    status: stringOrNull(record.status),
    zone: stringOrNull(record.zone),
    zoneState: stringOrNull(record.zone_state ?? record.zoneState),
    position: numberOrNull(record.position),
    positionPnl: numberOrNull(record.position_pnl ?? record.positionPnl),
    dailyPnl: numberOrNull(record.daily_pnl ?? record.dailyPnl),
    riskState: stringOrNull(record.risk_state ?? record.riskState),
    lastEntryBlockReason: stringOrNull(record.last_entry_block_reason ?? record.lastEntryBlockReason),
    payloadJson: recordOrNull(record.payload_json ?? record.payloadJson),
  };
}

function normalizeEventRow(event: unknown): EventRow {
  const record = asRecord(event);
  return {
    id: numberOrZero(record.id),
    runId: stringOrEmpty(record.run_id ?? record.runId),
    eventTimestamp: stringOrEmpty(record.event_timestamp ?? record.eventTimestamp),
    insertedAt: stringOrEmpty(record.inserted_at ?? record.insertedAt),
    category: stringOrNull(record.category),
    eventType: stringOrNull(record.event_type ?? record.eventType),
    source: stringOrNull(record.source),
    symbol: stringOrNull(record.symbol),
    zone: stringOrNull(record.zone),
    action: stringOrNull(record.action),
    reason: stringOrNull(record.reason),
    orderId: stringOrNull(record.order_id ?? record.orderId),
    riskState: stringOrNull(record.risk_state ?? record.riskState),
    contracts: numberOrNull(record.contracts),
    orderStatus: stringOrNull(record.order_status ?? record.orderStatus),
    guardReason: stringOrNull(record.guard_reason ?? record.guardReason),
    decisionSide: stringOrNull(record.decision_side ?? record.decisionSide),
    decisionPrice: numberOrNull(record.decision_price ?? record.decisionPrice),
    expectedFillPrice: numberOrNull(record.expected_fill_price ?? record.expectedFillPrice),
    entryGuardJson: recordOrNull(record.entry_guard_json ?? record.entryGuardJson),
    unresolvedEntryJson: recordOrNull(record.unresolved_entry_json ?? record.unresolvedEntryJson),
    executionJson: recordOrNull(record.execution_json ?? record.executionJson),
    payloadJson: recordOrNull(record.payload_json ?? record.payloadJson),
  };
}

function normalizeMarketTapeRow(row: unknown): MarketTapeRow {
  const record = asRecord(row);
  return {
    id: numberOrZero(record.id),
    runId: stringOrEmpty(record.run_id ?? record.runId),
    capturedAt: stringOrEmpty(record.captured_at ?? record.capturedAt),
    insertedAt: stringOrEmpty(record.inserted_at ?? record.insertedAt),
    processId: numberOrNull(record.process_id ?? record.processId),
    symbol: stringOrNull(record.symbol),
    contractId: stringOrNull(record.contract_id ?? record.contractId),
    bid: numberOrNull(record.bid),
    ask: numberOrNull(record.ask),
    last: numberOrNull(record.last),
    volume: numberOrNull(record.volume),
    bidSize: numberOrNull(record.bid_size ?? record.bidSize),
    askSize: numberOrNull(record.ask_size ?? record.askSize),
    lastSize: numberOrNull(record.last_size ?? record.lastSize),
    volumeIsCumulative: booleanOrNull(record.volume_is_cumulative ?? record.volumeIsCumulative),
    quoteIsSynthetic: booleanOrNull(record.quote_is_synthetic ?? record.quoteIsSynthetic),
    tradeSide: numberOrNull(record.trade_side ?? record.tradeSide),
    latencyMs: numberOrNull(record.latency_ms ?? record.latencyMs),
    source: stringOrNull(record.source),
    sequence: numberOrNull(record.sequence),
    payloadJson: recordOrNull(record.payload_json ?? record.payloadJson),
  };
}

function normalizeTradeRow(trade: unknown): TradeRow {
  const record = asRecord(trade);
  return {
    id: numberOrZero(record.id),
    runId: stringOrEmpty(record.run_id ?? record.runId),
    insertedAt: stringOrNull(record.inserted_at ?? record.insertedAt),
    entryTime: stringOrNull(record.entry_time ?? record.entryTime),
    exitTime: stringOrNull(record.exit_time ?? record.exitTime),
    direction: numberOrZero(record.direction),
    contracts: numberOrZero(record.contracts),
    entryPrice: numberOrZero(record.entry_price ?? record.entryPrice),
    exitPrice: numberOrZero(record.exit_price ?? record.exitPrice),
    pnl: numberOrZero(record.pnl),
    zone: stringOrNull(record.zone),
    strategy: stringOrNull(record.strategy),
    regime: stringOrNull(record.regime),
    eventTagsJson: recordOrNull(record.event_tags_json ?? record.eventTagsJson),
    source: stringOrNull(record.source),
    backfilled: booleanOrNull(record.backfilled),
    tradeId: stringOrNull(record.trade_id ?? record.tradeId),
    positionId: stringOrNull(record.position_id ?? record.positionId),
    decisionId: stringOrNull(record.decision_id ?? record.decisionId),
    attemptId: stringOrNull(record.attempt_id ?? record.attemptId),
    accountId: stringOrNull(record.account_id ?? record.accountId),
    accountName: stringOrNull(record.account_name ?? record.accountName),
    accountMode: stringOrNull(record.account_mode ?? record.accountMode),
    accountIsPractice: booleanOrNull(record.account_is_practice ?? record.accountIsPractice),
    payloadJson: recordOrNull(record.payload_json ?? record.payloadJson),
  };
}

function normalizeStateSnapshotRow(snapshot: unknown): StateSnapshotRow {
  const record = asRecord(snapshot);
  return {
    id: numberOrZero(record.id),
    runId: stringOrEmpty(record.run_id ?? record.runId),
    capturedAt: stringOrEmpty(record.captured_at ?? record.capturedAt),
    status: stringOrNull(record.status),
    dataMode: stringOrNull(record.data_mode ?? record.dataMode),
    symbol: stringOrNull(record.symbol),
    zone: stringOrNull(record.zone),
    zoneState: stringOrNull(record.zone_state ?? record.zoneState),
    position: numberOrNull(record.position),
    positionPnl: numberOrNull(record.position_pnl ?? record.positionPnl),
    dailyPnl: numberOrNull(record.daily_pnl ?? record.dailyPnl),
    riskState: stringOrNull(record.risk_state ?? record.riskState),
    accountId: stringOrNull(record.account_id ?? record.accountId),
    accountName: stringOrNull(record.account_name ?? record.accountName),
    accountMode: stringOrNull(record.account_mode ?? record.accountMode),
    accountIsPractice: booleanOrNull(record.account_is_practice ?? record.accountIsPractice),
    lastSignalJson: recordOrNull(record.last_signal_json ?? record.lastSignalJson),
    lastEntryReason: stringOrNull(record.last_entry_reason ?? record.lastEntryReason),
    lastEntryBlockReason: stringOrNull(record.last_entry_block_reason ?? record.lastEntryBlockReason),
    decisionPrice: numberOrNull(record.decision_price ?? record.decisionPrice),
    entryGuardJson: recordOrNull(record.entry_guard_json ?? record.entryGuardJson),
    unresolvedEntryJson: recordOrNull(record.unresolved_entry_json ?? record.unresolvedEntryJson),
    executionJson: recordOrNull(record.execution_json ?? record.executionJson),
    heartbeatJson: recordOrNull(record.heartbeat_json ?? record.heartbeatJson),
    lifecycleJson: recordOrNull(record.lifecycle_json ?? record.lifecycleJson),
    observabilityJson: recordOrNull(record.observability_json ?? record.observabilityJson),
    payloadJson: recordOrNull(record.payload_json ?? record.payloadJson),
  };
}

function normalizeDecisionSnapshotRow(snapshot: unknown): DecisionSnapshotRow {
  const record = asRecord(snapshot);
  return {
    id: numberOrZero(record.id),
    runId: stringOrEmpty(record.run_id ?? record.runId),
    decidedAt: stringOrEmpty(record.decided_at ?? record.decidedAt),
    insertedAt: stringOrEmpty(record.inserted_at ?? record.insertedAt),
    decisionId: stringOrEmpty(record.decision_id ?? record.decisionId),
    attemptId: stringOrNull(record.attempt_id ?? record.attemptId),
    processId: numberOrNull(record.process_id ?? record.processId),
    symbol: stringOrNull(record.symbol),
    zone: stringOrNull(record.zone),
    action: stringOrNull(record.action),
    reason: stringOrNull(record.reason),
    outcome: stringOrNull(record.outcome),
    outcomeReason: stringOrNull(record.outcome_reason ?? record.outcomeReason),
    longScore: numberOrNull(record.long_score ?? record.longScore),
    shortScore: numberOrNull(record.short_score ?? record.shortScore),
    flatBias: numberOrNull(record.flat_bias ?? record.flatBias),
    scoreGap: numberOrNull(record.score_gap ?? record.scoreGap),
    dominantSide: stringOrNull(record.dominant_side ?? record.dominantSide),
    currentPrice: numberOrNull(record.current_price ?? record.currentPrice),
    allowEntries: booleanOrNull(record.allow_entries ?? record.allowEntries),
    executionTradeable: booleanOrNull(record.execution_tradeable ?? record.executionTradeable),
    contracts: numberOrNull(record.contracts),
    orderType: stringOrNull(record.order_type ?? record.orderType),
    limitPrice: numberOrNull(record.limit_price ?? record.limitPrice),
    decisionPrice: numberOrNull(record.decision_price ?? record.decisionPrice),
    side: stringOrNull(record.side),
    stopLoss: numberOrNull(record.stop_loss ?? record.stopLoss),
    takeProfit: numberOrNull(record.take_profit ?? record.takeProfit),
    maxHoldMinutes: numberOrNull(record.max_hold_minutes ?? record.maxHoldMinutes),
    regimeState: stringOrNull(record.regime_state ?? record.regimeState),
    regimeReason: stringOrNull(record.regime_reason ?? record.regimeReason),
    activeSession: stringOrNull(record.active_session ?? record.activeSession),
    activeVetoes: arrayOrEmpty(record.active_vetoes_json ?? record.active_vetoes ?? record.activeVetoes),
    featureSnapshot: recordOrNull(record.feature_snapshot_json ?? record.feature_snapshot ?? record.featureSnapshot),
    entryGuard: recordOrNull(record.entry_guard_json ?? record.entry_guard ?? record.entryGuard),
    unresolvedEntry: recordOrNull(record.unresolved_entry_json ?? record.unresolved_entry ?? record.unresolvedEntry),
    eventContext: recordOrNull(record.event_context_json ?? record.event_context ?? record.eventContext),
    orderFlow: recordOrNull(record.order_flow_json ?? record.order_flow ?? record.orderFlow),
    payloadJson: recordOrNull(record.payload_json ?? record.payloadJson),
  };
}

function normalizeOrderLifecycleRow(row: unknown): OrderLifecycleRow {
  const record = asRecord(row);
  return {
    id: numberOrZero(record.id),
    runId: stringOrEmpty(record.run_id ?? record.runId),
    observedAt: stringOrEmpty(record.observed_at ?? record.observedAt),
    insertedAt: stringOrEmpty(record.inserted_at ?? record.insertedAt),
    decisionId: stringOrNull(record.decision_id ?? record.decisionId),
    attemptId: stringOrNull(record.attempt_id ?? record.attemptId),
    orderId: stringOrNull(record.order_id ?? record.orderId),
    positionId: stringOrNull(record.position_id ?? record.positionId),
    tradeId: stringOrNull(record.trade_id ?? record.tradeId),
    processId: numberOrNull(record.process_id ?? record.processId),
    symbol: stringOrNull(record.symbol),
    eventType: stringOrNull(record.event_type ?? record.eventType),
    status: stringOrNull(record.status),
    side: stringOrNull(record.side),
    role: stringOrNull(record.role),
    isProtective: booleanOrNull(record.is_protective ?? record.isProtective),
    orderType: stringOrNull(record.order_type ?? record.orderType),
    quantity: numberOrNull(record.quantity),
    contracts: numberOrNull(record.contracts),
    limitPrice: numberOrNull(record.limit_price ?? record.limitPrice),
    stopPrice: numberOrNull(record.stop_price ?? record.stopPrice),
    expectedFillPrice: numberOrNull(record.expected_fill_price ?? record.expectedFillPrice),
    filledPrice: numberOrNull(record.filled_price ?? record.filledPrice),
    filledQuantity: numberOrNull(record.filled_quantity ?? record.filledQuantity),
    remainingQuantity: numberOrNull(record.remaining_quantity ?? record.remainingQuantity),
    zone: stringOrNull(record.zone),
    reason: stringOrNull(record.reason),
    lifecycleState: stringOrNull(record.lifecycle_state ?? record.lifecycleState),
    payloadJson: recordOrNull(record.payload_json ?? record.payloadJson),
  };
}

function normalizeBridgeHealthRow(row: unknown): BridgeHealthRow {
  const record = asRecord(row);
  return {
    id: numberOrZero(record.id),
    runId: stringOrNull(record.run_id ?? record.runId),
    observedAt: stringOrEmpty(record.observed_at ?? record.observedAt),
    insertedAt: stringOrEmpty(record.inserted_at ?? record.insertedAt),
    bridgeStatus: stringOrNull(record.bridge_status ?? record.bridgeStatus),
    queueDepth: numberOrNull(record.queue_depth ?? record.queueDepth),
    lastFlushAt: stringOrNull(record.last_flush_at ?? record.lastFlushAt),
    lastSuccessAt: stringOrNull(record.last_success_at ?? record.lastSuccessAt),
    lastError: stringOrNull(record.last_error ?? record.lastError),
    payloadJson: recordOrNull(record.payload_json ?? record.payloadJson),
  };
}

function normalizeAccountSummaryRow(row: unknown): AccountSummaryRow {
  const record = asRecord(row);
  return {
    accountId: stringOrEmpty(record.account_id ?? record.accountId),
    accountName: stringOrNull(record.account_name ?? record.accountName),
    accountMode: stringOrNull(record.account_mode ?? record.accountMode),
    accountIsPractice: booleanOrNull(record.account_is_practice ?? record.accountIsPractice),
    runCount: numberOrZero(record.run_count ?? record.runCount),
    tradeCount: numberOrZero(record.trade_count ?? record.tradeCount),
    realizedPnl: numberOrZero(record.realized_pnl ?? record.realizedPnl),
    latestTradeAt: stringOrNull(record.latest_trade_at ?? record.latestTradeAt),
    latestRunSeenAt: stringOrNull(record.latest_run_seen_at ?? record.latestRunSeenAt),
  };
}

function normalizeAccountTradeRow(row: unknown): AccountTradeRow {
  const record = asRecord(row);
  return {
    id: numberOrZero(record.id),
    runId: stringOrNull(record.run_id ?? record.runId),
    insertedAt: stringOrNull(record.inserted_at ?? record.insertedAt),
    occurredAt: stringOrEmpty(record.occurred_at ?? record.occurredAt),
    accountId: stringOrEmpty(record.account_id ?? record.accountId),
    accountName: stringOrNull(record.account_name ?? record.accountName),
    accountMode: stringOrNull(record.account_mode ?? record.accountMode),
    accountIsPractice: booleanOrNull(record.account_is_practice ?? record.accountIsPractice),
    brokerTradeId: stringOrEmpty(record.broker_trade_id ?? record.brokerTradeId),
    brokerOrderId: stringOrNull(record.broker_order_id ?? record.brokerOrderId),
    contractId: stringOrNull(record.contract_id ?? record.contractId),
    side: numberOrNull(record.side),
    size: numberOrNull(record.size),
    price: numberOrNull(record.price),
    profitAndLoss: numberOrNull(record.profit_and_loss ?? record.profitAndLoss),
    fees: numberOrNull(record.fees),
    voided: booleanOrNull(record.voided),
    source: stringOrNull(record.source),
    payloadJson: recordOrNull(record.payload_json ?? record.payloadJson),
  };
}

function normalizeBridgeFailureRow(row: unknown): BridgeFailureRow {
  const record = asRecord(row);
  return {
    id: numberOrZero(record.id),
    runId: stringOrNull(record.run_id ?? record.runId),
    observedAt: stringOrEmpty(record.observed_at ?? record.observedAt),
    bridgeStatus: stringOrNull(record.bridge_status ?? record.bridgeStatus),
    queueDepth: numberOrNull(record.queue_depth ?? record.queueDepth),
    lastFlushAt: stringOrNull(record.last_flush_at ?? record.lastFlushAt),
    lastSuccessAt: stringOrNull(record.last_success_at ?? record.lastSuccessAt),
    lastError: stringOrNull(record.last_error ?? record.lastError),
    payloadJson: recordOrNull(record.payload_json ?? record.payloadJson),
  };
}

function normalizeTimelineEntry(entry: unknown): TimelineEntry {
  const record = asRecord(entry);
  return {
    ...record,
    kind: timelineKind(record.kind),
    timestamp: stringOrNull(record.timestamp),
    runId: stringOrEmpty(record.run_id ?? record.runId),
  };
}

export async function fetchAnalyticsSummary(): Promise<AnalyticsSummary | null> {
  if (!ANALYTICS_URL || !ANALYTICS_KEY) {
    return null;
  }

  try {
    const response = await fetch(`${ANALYTICS_URL.replace(/\/$/, "")}/analytics/summary`, {
      headers: analyticsFetchInit(),
      next: { revalidate: 30 },
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as AnalyticsSummary;
  } catch {
    return null;
  }
}

export async function fetchDashboardData(): Promise<DashboardData | null> {
  const query = `
    query Dashboard($limit: Int!, $reportLimit: Int!) {
      runs(limit: $limit) {
        runId
        createdAt
        lastSeenAt
        processId
        dataMode
        symbol
        accountId
        accountName
        accountMode
        accountIsPractice
        payloadJson
      }
      trades(limit: $limit) {
        id
        runId
        insertedAt
        entryTime
        exitTime
        direction
        contracts
        entryPrice
        exitPrice
        pnl
        zone
        strategy
        regime
        source
        backfilled
        tradeId
        positionId
        decisionId
        attemptId
        accountId
        accountName
        accountMode
        accountIsPractice
        payloadJson
      }
      hypotheses(limit: $limit) {
        id
        hypothesisId
        generation
        parentHypothesisId
        claimText
        regimeContext
        status
        createdAt
        updatedAt
      }
      knowledgeStore(limit: $limit) {
        id
        hypothesisId
        verdict
        confidenceScore
        mutationDirective
        survivalCount
        rejectionCount
        createdAt
      }
      reports(limit: $reportLimit) {
        id
        reportId
        title
        reportType
        modelProvider
        modelName
        status
        summaryText
        reportJson
        createdAt
        completedAt
      }
      metaLearnerStats {
        survivalCount
        rejectionCount
        stats
      }
    }
  `;

  const data = await queryAnalytics<{
    runs: RunRow[];
    trades: TradeRow[];
    hypotheses: HypothesisRow[];
    knowledgeStore: KnowledgeRow[];
    reports: ReportRow[];
    metaLearnerStats: MetaLearnerStats | null;
  }>(query, { limit: 8, reportLimit: 5 });

  const summary = await fetchAnalyticsSummary();
  if (!data || !summary) {
    return null;
  }

  return {
    summary,
    runs: data.runs ?? [],
    trades: data.trades ?? [],
    hypotheses: data.hypotheses ?? [],
    knowledgeStore: data.knowledgeStore ?? [],
    reports: data.reports ?? [],
    metaLearnerStats: data.metaLearnerStats ?? null,
  };
}

export async function fetchRunDetail(runId: string): Promise<RunDetail | null> {
  const [run, events, marketTape, trades, snapshots, decisions, lifecycles, bridgeHealth, timeline] = await Promise.all([
    fetchAnalyticsJson<Record<string, unknown>>(`/runs/${runId}`),
    fetchAnalyticsJson<{ events: Record<string, unknown>[] }>(`/runs/${runId}/events`, { limit: 100 }),
    fetchAnalyticsJson<{ marketTape: Record<string, unknown>[] }>(`/runs/${runId}/market_tape`, { limit: 200 }),
    fetchAnalyticsJson<{ trades: Record<string, unknown>[] }>(`/runs/${runId}/trades`, { limit: 100 }),
    fetchAnalyticsJson<{ stateSnapshots: Record<string, unknown>[] }>(`/runs/${runId}/state_snapshots`, { limit: 50 }),
    fetchAnalyticsJson<{ decisionSnapshots: Record<string, unknown>[] }>(`/runs/${runId}/decision_snapshots`, { limit: 50 }),
    fetchAnalyticsJson<{ orderLifecycle: Record<string, unknown>[] }>(`/runs/${runId}/order_lifecycle`, { limit: 50 }),
    fetchAnalyticsJson<{ bridgeHealth: Record<string, unknown>[] }>(`/runs/${runId}/bridge_health`, { limit: 50 }),
    fetchAnalyticsJson<{ timeline: Record<string, unknown>[]; blockers: Record<string, unknown>[] }>(`/runs/${runId}/timeline`, {
      limit: 300,
    }),
  ]);

  if (!run && !events && !marketTape && !trades && !snapshots && !decisions && !lifecycles && !bridgeHealth && !timeline) {
    return null;
  }

  return {
    run: run ? normalizeRunRow(run) : null,
    events: (events?.events ?? []).map(normalizeEventRow),
    marketTape: (marketTape?.marketTape ?? []).map(normalizeMarketTapeRow),
    trades: (trades?.trades ?? []).map(normalizeTradeRow),
    stateSnapshots: (snapshots?.stateSnapshots ?? []).map(normalizeStateSnapshotRow),
    decisionSnapshots: (decisions?.decisionSnapshots ?? []).map(normalizeDecisionSnapshotRow),
    orderLifecycle: (lifecycles?.orderLifecycle ?? []).map(normalizeOrderLifecycleRow),
    bridgeHealth: (bridgeHealth?.bridgeHealth ?? []).map(normalizeBridgeHealthRow),
    timeline: (timeline?.timeline ?? []).map(normalizeTimelineEntry),
    blockers: (timeline?.blockers ?? []).map(normalizeTimelineEntry),
  };
}

export async function fetchTradeReview(tradeId: string | number): Promise<TradeReviewBundle | null> {
  const payload = await fetchAnalyticsJson<{
    trade: Record<string, unknown> | null;
    run: Record<string, unknown> | null;
    marketTape: Record<string, unknown>[];
    decisionSnapshots: Record<string, unknown>[];
    stateSnapshots: Record<string, unknown>[];
    orderLifecycle: Record<string, unknown>[];
    events: Record<string, unknown>[];
    timeline: Record<string, unknown>[];
    blockers: Record<string, unknown>[];
    analysis: Record<string, unknown> | null;
  }>(`/trades/${tradeId}`, { limit: 300 });

  if (!payload) {
    return null;
  }

  return {
    trade: payload.trade ? normalizeTradeRow(payload.trade) : null,
    run: payload.run ? normalizeRunRow(payload.run) : null,
    marketTape: (payload.marketTape ?? []).map(normalizeMarketTapeRow),
    decisionSnapshots: (payload.decisionSnapshots ?? []).map(normalizeDecisionSnapshotRow),
    stateSnapshots: (payload.stateSnapshots ?? []).map(normalizeStateSnapshotRow),
    orderLifecycle: (payload.orderLifecycle ?? []).map(normalizeOrderLifecycleRow),
    events: (payload.events ?? []).map(normalizeEventRow),
    timeline: (payload.timeline ?? []).map(normalizeTimelineEntry),
    blockers: (payload.blockers ?? []).map(normalizeTimelineEntry),
    analysis: payload.analysis
      ? {
          summary: stringOrEmpty(payload.analysis.summary),
          marketContext: asRecord(payload.analysis.marketContext) as TradeReviewAnalysis["marketContext"],
          entryExit: asRecord(payload.analysis.entryExit) as TradeReviewAnalysis["entryExit"],
          executorBelief: asRecord(payload.analysis.executorBelief) as TradeReviewAnalysis["executorBelief"],
          narrative: Array.isArray(payload.analysis.narrative) ? payload.analysis.narrative.map(stringOrEmpty) : [],
          marketNotes: Array.isArray(payload.analysis.marketNotes) ? payload.analysis.marketNotes.map(stringOrEmpty) : [],
          executionNotes: Array.isArray(payload.analysis.executionNotes) ? payload.analysis.executionNotes.map(stringOrEmpty) : [],
          executorProjection: Array.isArray(payload.analysis.executorProjection) ? payload.analysis.executorProjection.map(stringOrEmpty) : [],
        }
      : null,
  };
}

export async function fetchReportDetail(reportId: string): Promise<ReportDetail> {
  const query = `
    query ReportDetail($reportId: String!) {
      report(reportId: $reportId) {
        id
        reportId
        title
        reportType
        modelProvider
        modelName
        status
        summaryText
        reportJson
        createdAt
        completedAt
      }
    }
  `;

  const data = await queryAnalytics<{ report: ReportRow | null }>(query, { reportId });
  return data?.report ?? null;
}

export async function fetchRlmLibrary(): Promise<{
  hypotheses: HypothesisRow[];
  knowledgeStore: KnowledgeRow[];
  reports: ReportRow[];
  metaLearnerStats: MetaLearnerStats | null;
} | null> {
  const query = `
    query RlmLibrary($limit: Int!) {
      hypotheses(limit: $limit) {
        id
        hypothesisId
        generation
        parentHypothesisId
        claimText
        regimeContext
        status
        createdAt
        updatedAt
      }
      knowledgeStore(limit: $limit) {
        id
        hypothesisId
        verdict
        confidenceScore
        mutationDirective
        survivalCount
        rejectionCount
        createdAt
      }
      reports(limit: $limit) {
        id
        reportId
        title
        reportType
        modelProvider
        modelName
        status
        summaryText
        reportJson
        createdAt
        completedAt
      }
      metaLearnerStats {
        survivalCount
        rejectionCount
        stats
      }
    }
  `;

  return queryAnalytics<{
    hypotheses: HypothesisRow[];
    knowledgeStore: KnowledgeRow[];
    reports: ReportRow[];
    metaLearnerStats: MetaLearnerStats | null;
  }>(query, { limit: 10 });
}

export async function fetchSearchResults(query: string): Promise<{
  runs: RunRow[];
  events: EventRow[];
} | null> {
  const cleaned = query.trim();
  if (!cleaned) {
    return null;
  }

  const [runs, events] = await Promise.all([
    fetchAnalyticsJson<{ runs: Record<string, unknown>[] }>("/search/runs", { q: cleaned, limit: 12 }),
    fetchAnalyticsJson<{ events: Record<string, unknown>[] }>("/search/events", { q: cleaned, limit: 20 }),
  ]);

  return {
    runs: (runs?.runs ?? []).map(normalizeRunRow),
    events: (events?.events ?? []).map(normalizeEventRow),
  };
}

export async function fetchAccountSummaries(): Promise<AccountSummaryRow[]> {
  const payload = await fetchAnalyticsJson<{ accounts: Record<string, unknown>[] }>("/accounts", { limit: 20 });
  return (payload?.accounts ?? []).map(normalizeAccountSummaryRow);
}

export async function fetchAccountTrades(params?: {
  accountId?: string | null;
  runId?: string | null;
  limit?: number;
}): Promise<AccountTradeRow[]> {
  const payload = await fetchAnalyticsJson<{ accountTrades: Record<string, unknown>[] }>("/account-trades", {
    account_id: params?.accountId ?? undefined,
    run_id: params?.runId ?? undefined,
    limit: params?.limit ?? 50,
  });
  return (payload?.accountTrades ?? []).map(normalizeAccountTradeRow);
}

export async function fetchBridgeFailures(runId?: string | null): Promise<BridgeFailureRow[]> {
  const payload = await fetchAnalyticsJson<{ failures: Record<string, unknown>[] }>("/bridge/failures", {
    run_id: runId ?? undefined,
    limit: 20,
  });
  return (payload?.failures ?? []).map(normalizeBridgeFailureRow);
}

export async function fetchServiceHealth(): Promise<ServiceHealthSnapshot | null> {
  const payload = await fetchAnalyticsJson<Record<string, unknown>>("/service-health");
  if (!payload) {
    return null;
  }
  return {
    analytics: recordOrNull(payload.analytics) as { status: string; pool: Record<string, unknown> } | null,
    bridge: recordOrNull(payload.bridge),
    runtimeLogs: payload.runtime_logs
      ? {
          count: numberOrZero(asRecord(payload.runtime_logs).count),
          latestLoggedAt: stringOrNull(asRecord(payload.runtime_logs).latest_logged_at),
        }
      : null,
    reports: payload.reports
      ? {
          count: numberOrZero(asRecord(payload.reports).count),
          latestCreatedAt: stringOrNull(asRecord(payload.reports).latest_created_at),
        }
      : null,
  };
}

export function isSyntheticRunId(runId: string): boolean {
  const normalized = runId.trim().toLowerCase();
  return normalized.startsWith("reality-check-") || normalized.startsWith("e2e-test-") || normalized.startsWith("test-run-");
}
