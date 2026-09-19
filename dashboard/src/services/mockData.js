// ============================================================
// Mock / seed data — realistic Aperture telemetry
// ============================================================

export const mockRequests = [
  { id: 'req-8f2a3b1c', keyId: 'sk-gw-eng-001', team: 'engineering', model: 'claude-sonnet-4-6', promptTokens: 120, completionTokens: 80, totalTokens: 200, cost: 0.0024, status: 200, latency: 218, ts: Date.now() - 45000 },
  { id: 'req-31c0d4e5', keyId: 'sk-gw-prod-002', team: 'product', model: 'gpt-4o', promptTokens: 90, completionTokens: 50, totalTokens: 140, cost: 0.0018, status: 200, latency: 312, ts: Date.now() - 90000 },
  { id: 'req-99ba7f2e', keyId: 'sk-gw-dev-003', team: 'marketing', model: 'gpt-4o', promptTokens: 0, completionTokens: 0, totalTokens: 0, cost: 0.0000, status: 403, latency: 4, ts: Date.now() - 130000 },
  { id: 'req-a12c8e90', keyId: 'sk-gw-eng-001', team: 'engineering', model: 'claude-sonnet-4-6', promptTokens: 310, completionTokens: 190, totalTokens: 500, cost: 0.0060, status: 200, latency: 450, ts: Date.now() - 200000 },
  { id: 'req-b4f921da', keyId: 'sk-gw-prod-004', team: 'product', model: 'gpt-4o-mini', promptTokens: 200, completionTokens: 100, totalTokens: 300, cost: 0.0006, status: 200, latency: 198, ts: Date.now() - 310000 },
  { id: 'req-c7e03b1f', keyId: 'sk-gw-eng-001', team: 'engineering', model: 'claude-sonnet-4-6', promptTokens: 450, completionTokens: 280, totalTokens: 730, cost: 0.0088, status: 200, latency: 620, ts: Date.now() - 420000 },
  { id: 'req-d9201cfa', keyId: 'sk-gw-dev-005', team: 'marketing', model: 'gpt-4o', promptTokens: 150, completionTokens: 95, totalTokens: 245, cost: 0.0032, status: 200, latency: 267, ts: Date.now() - 540000 },
  { id: 'req-e0b4a8c3', keyId: 'sk-gw-prod-002', team: 'product', model: 'gpt-4o-mini', promptTokens: 0, completionTokens: 0, totalTokens: 0, cost: 0.0000, status: 403, latency: 3, ts: Date.now() - 700000 },
  { id: 'req-f3c19d2e', keyId: 'sk-gw-eng-001', team: 'engineering', model: 'claude-sonnet-4-6', promptTokens: 280, completionTokens: 160, totalTokens: 440, cost: 0.0052, status: 200, latency: 390, ts: Date.now() - 820000 },
  { id: 'req-07a3e8b9', keyId: 'sk-gw-prod-004', team: 'product', model: 'gpt-4o', promptTokens: 110, completionTokens: 70, totalTokens: 180, cost: 0.0022, status: 200, latency: 230, ts: Date.now() - 960000 },
];

export const mockKeys = [
  { id: 'sk-gw-eng-001', name: 'Engineering — Primary', team: 'engineering', role: 'admin', budget: 100.00, spent: 8.40, active: true, created: '2025-08-01' },
  { id: 'sk-gw-prod-002', name: 'Product — Beta Testing', team: 'product', role: 'team_lead', budget: 50.00, spent: 3.95, active: true, created: '2025-08-05' },
  { id: 'sk-gw-dev-003', name: 'Marketing — Campaigns', team: 'marketing', role: 'developer', budget: 25.00, spent: 0.15, active: false, created: '2025-08-10' },
  { id: 'sk-gw-prod-004', name: 'Product — Analytics', team: 'product', role: 'developer', budget: 50.00, spent: 0.80, active: true, created: '2025-08-12' },
  { id: 'sk-gw-dev-005', name: 'Marketing — Social', team: 'marketing', role: 'developer', budget: 25.00, spent: 0.11, active: true, created: '2025-08-14' },
];

export const mockTeams = [
  { id: 'engineering', name: 'Engineering', budget: 100.00, spent: 8.40, blocked: 0, keyCount: 1 },
  { id: 'product',     name: 'Product',     budget: 50.00,  spent: 3.95, blocked: 2, keyCount: 2 },
  { id: 'marketing',   name: 'Marketing',   budget: 25.00,  spent: 0.26, blocked: 1, keyCount: 2 },
];

// 24-hour time-series (hourly)
export const mockTimeSeries = Array.from({ length: 24 }, (_, i) => ({
  hour: `${String(i).padStart(2, '0')}:00`,
  spend: +(Math.random() * 0.9 + 0.05).toFixed(4),
  requests: Math.floor(Math.random() * 8 + 1),
}));

export const mockModelBreakdown = [
  { model: 'claude-sonnet-4-6', pct: 64, spend: 7.94, color: '#F97316' },
  { model: 'gpt-4o',            pct: 28, spend: 3.47, color: '#06B6D4' },
  { model: 'gpt-4o-mini',       pct: 8,  spend: 0.99, color: '#8B5CF6' },
];

export const mockCircuitBreaker = {
  state: 'CLOSED',
  primary: 'Anthropic (claude-sonnet-4-6)',
  fallback: 'OpenAI (gpt-4o)',
  failures: 0,
  threshold: 3,
  recoveryWindow: 60,
  successCount: 57,
  totalRequests: 62,
};

// KPI aggregates
export const mockKPIs = {
  totalSpend: 12.36,
  totalTokens: 14280,
  promptTokens: 8450,
  completionTokens: 5830,
  totalRequests: 62,
  successRequests: 57,
  blockedRequests: 5,
  avgLatency: 240,
  p95Latency: 410,
};

// ============================================================
// Phase 2 — Person B: Plain-language summary & forecast contracts
// ============================================================

export const mockTeamSummaries = {
  engineering: {
    team_id: 'engineering',
    team_name: 'Engineering',
    period: 'September 2026',
    total_spend_usd: 8.40,
    budget_usd: 100.00,
    pct_budget_used: 8.4,
    top_model: 'Claude 3.5 Sonnet',
    top_model_pct: 66,
    trend_direction: 'up',
    trend_pct: 14.2,
    daily_burn_usd: 0.44,
    projected_month_end_usd: 13.20,
    projected_pct_of_budget: 13.2,
    sentiment: 'nominal',
    highlight_sentence: 'Engineering spent $8.40 this month (8% of quota), with 66% on Claude 3.5 Sonnet, up 14% from last period.',
  },
  product: {
    team_id: 'product',
    team_name: 'Product',
    period: 'September 2026',
    total_spend_usd: 3.95,
    budget_usd: 50.00,
    pct_budget_used: 7.9,
    top_model: 'GPT-4o',
    top_model_pct: 71,
    trend_direction: 'down',
    trend_pct: 5.1,
    daily_burn_usd: 0.21,
    projected_month_end_usd: 6.30,
    projected_pct_of_budget: 12.6,
    sentiment: 'favorable',
    highlight_sentence: 'Product spent $3.95 this month, 71% on GPT-4o, down 5% from last period as caching adoption grew.',
  },
  marketing: {
    team_id: 'marketing',
    team_name: 'Marketing',
    period: 'September 2026',
    total_spend_usd: 24.80,
    budget_usd: 25.00,
    pct_budget_used: 99.2,
    top_model: 'GPT-4o',
    top_model_pct: 88,
    trend_direction: 'up',
    trend_pct: 142.5,
    daily_burn_usd: 1.30,
    projected_month_end_usd: 39.00,
    projected_pct_of_budget: 156.0,
    sentiment: 'warning',
    highlight_sentence: 'Marketing spent $24.80 this month (99% of quota) and is trending to exceed its $25 limit in the next 18 hours.',
  },
};

export const mockBudgetRequests = [
  {
    id: 'req-bg-9921',
    team_id: 'marketing',
    team_name: 'Marketing',
    requested_by: 'sarah.mkt@aperture.io',
    current_budget_usd: 25.00,
    requested_budget_usd: 60.00,
    reason: 'Q4 Product Hunt launch copy generation and automated multi-channel social campaign experiments.',
    status: 'pending',
    timestamp: new Date(Date.now() - 3600000 * 3).toISOString(),
  },
  {
    id: 'req-bg-8814',
    team_id: 'engineering',
    team_name: 'Engineering',
    requested_by: 'alex.dev@aperture.io',
    current_budget_usd: 100.00,
    requested_budget_usd: 150.00,
    reason: 'Running Claude Code benchmark sweeps across 4 microservice repositories to correlate PR velocity.',
    status: 'pending',
    timestamp: new Date(Date.now() - 3600000 * 14).toISOString(),
  },
  {
    id: 'req-bg-7702',
    team_id: 'product',
    team_name: 'Product',
    requested_by: 'elena.pm@aperture.io',
    current_budget_usd: 35.00,
    requested_budget_usd: 50.00,
    reason: 'Beta customer feedback synthesis and automated transcript tagging for v2 roadmap planning.',
    status: 'approved',
    reviewed_by: 'Soham Banerjee (Admin)',
    timestamp: new Date(Date.now() - 86400000 * 2).toISOString(),
  },
];

export const mockForecastData = {
  engineering: {
    team_id: 'engineering',
    budget_usd: 100.00,
    current_spent: 8.40,
    days_elapsed: 19,
    days_in_month: 30,
    projected_month_end: 13.20,
    is_over_budget: false,
    trajectory: [
      { day: 'Day 1', actual: 0.40, projected: 0.40, budgetLine: 100 },
      { day: 'Day 5', actual: 2.10, projected: 2.10, budgetLine: 100 },
      { day: 'Day 10', actual: 4.30, projected: 4.30, budgetLine: 100 },
      { day: 'Day 15', actual: 6.80, projected: 6.80, budgetLine: 100 },
      { day: 'Day 19', actual: 8.40, projected: 8.40, budgetLine: 100 },
      { day: 'Day 23', actual: null, projected: 10.30, budgetLine: 100 },
      { day: 'Day 27', actual: null, projected: 12.10, budgetLine: 100 },
      { day: 'Day 30', actual: null, projected: 13.20, budgetLine: 100 },
    ],
  },
  marketing: {
    team_id: 'marketing',
    budget_usd: 25.00,
    current_spent: 24.80,
    days_elapsed: 19,
    days_in_month: 30,
    projected_month_end: 39.20,
    is_over_budget: true,
    overage_date: 'Sept 20, 2026',
    trajectory: [
      { day: 'Day 1', actual: 1.20, projected: 1.20, budgetLine: 25 },
      { day: 'Day 5', actual: 5.80, projected: 5.80, budgetLine: 25 },
      { day: 'Day 10', actual: 12.40, projected: 12.40, budgetLine: 25 },
      { day: 'Day 15', actual: 19.10, projected: 19.10, budgetLine: 25 },
      { day: 'Day 19', actual: 24.80, projected: 24.80, budgetLine: 25 },
      { day: 'Day 23', actual: null, projected: 30.10, budgetLine: 25 },
      { day: 'Day 27', actual: null, projected: 35.40, budgetLine: 25 },
      { day: 'Day 30', actual: null, projected: 39.20, budgetLine: 25 },
    ],
  },
};

// ============================================================
// Phase 2 — Person A: Git Activity & Cost-per-PR Outcome
// ============================================================

export const mockPRCorrelations = [
  {
    id: 'pr-148',
    repo_id: 'Aperture/core-engine',
    pr_number: 148,
    pr_title: 'feat(cache): semantic response caching with cosine similarity lookup',
    pr_url: 'https://github.com/COolAlien35/Aperture/pull/148',
    author: 'sohambanerjee',
    author_avatar: 'https://avatars.githubusercontent.com/u/1024025?v=4',
    total_ai_cost_usd: 1.4820,
    time_to_merge_hours: 4.5,
    files_changed: 7,
    session_count: 5,
    top_model: 'Claude 3.5 Sonnet',
    created_at: '2026-09-18T14:20:00Z',
    merged_at: '2026-09-18T18:50:00Z',
    status: 'merged',
  },
  {
    id: 'pr-144',
    repo_id: 'Aperture/gateway-proxy',
    pr_number: 144,
    pr_title: 'fix(circuit): graceful fallback transition on upstream Anthropic 529',
    pr_url: 'https://github.com/COolAlien35/Aperture/pull/144',
    author: 'person-b-eng',
    author_avatar: 'https://avatars.githubusercontent.com/u/2048050?v=4',
    total_ai_cost_usd: 0.9410,
    time_to_merge_hours: 2.1,
    files_changed: 4,
    session_count: 3,
    top_model: 'Claude 3.5 Sonnet',
    created_at: '2026-09-17T11:10:00Z',
    merged_at: '2026-09-17T13:16:00Z',
    status: 'merged',
  },
  {
    id: 'pr-141',
    repo_id: 'Aperture/dashboard-ui',
    pr_number: 141,
    pr_title: 'feat(ui): split-screen auth carousel and telemetry drawer inspector',
    pr_url: 'https://github.com/COolAlien35/Aperture/pull/141',
    author: 'sohambanerjee',
    author_avatar: 'https://avatars.githubusercontent.com/u/1024025?v=4',
    total_ai_cost_usd: 0.7250,
    time_to_merge_hours: 3.8,
    files_changed: 6,
    session_count: 4,
    top_model: 'Claude 3.5 Sonnet',
    created_at: '2026-09-16T09:40:00Z',
    merged_at: '2026-09-16T13:28:00Z',
    status: 'merged',
  },
  {
    id: 'pr-139',
    repo_id: 'Aperture/data-pipeline',
    pr_number: 139,
    pr_title: 'perf(kafka): batch consumer commits with conditional DynamoDB idempotency',
    pr_url: 'https://github.com/COolAlien35/Aperture/pull/139',
    author: 'person-c-data',
    author_avatar: 'https://avatars.githubusercontent.com/u/3072075?v=4',
    total_ai_cost_usd: 0.4320,
    time_to_merge_hours: 1.8,
    files_changed: 3,
    session_count: 2,
    top_model: 'Claude 3.5 Sonnet',
    created_at: '2026-09-15T16:00:00Z',
    merged_at: '2026-09-15T17:48:00Z',
    status: 'merged',
  },
  {
    id: 'pr-136',
    repo_id: 'Aperture/core-engine',
    pr_number: 136,
    pr_title: 'test(reconciliation): verify token credit return on mid-stream disconnect',
    pr_url: 'https://github.com/COolAlien35/Aperture/pull/136',
    author: 'person-a-sec',
    author_avatar: 'https://avatars.githubusercontent.com/u/4096100?v=4',
    total_ai_cost_usd: 0.1890,
    time_to_merge_hours: 0.9,
    files_changed: 2,
    session_count: 1,
    top_model: 'GPT-4o-mini',
    created_at: '2026-09-15T10:15:00Z',
    merged_at: '2026-09-15T11:09:00Z',
    status: 'merged',
  },
];

