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
