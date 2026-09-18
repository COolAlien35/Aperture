// Gateway & DynamoDB API client
// Falls back to mock data when gateway is unreachable

import {
  mockRequests, mockKeys, mockTeams,
  mockTimeSeries, mockModelBreakdown, mockCircuitBreaker, mockKPIs,
} from './mockData.js';

const BASE = '/api';
const timeout = (ms) => new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), ms));

async function safeFetch(url, opts = {}) {
  try {
    const res = await Promise.race([fetch(url, opts), timeout(3000)]);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchKPIs() {
  const data = await safeFetch(`${BASE}/metrics/summary`);
  return data || mockKPIs;
}

export async function fetchTimeSeries(period = '24h') {
  const data = await safeFetch(`${BASE}/metrics/timeseries?period=${period}`);
  return data || mockTimeSeries;
}

export async function fetchModelBreakdown() {
  const data = await safeFetch(`${BASE}/metrics/models`);
  return data || mockModelBreakdown;
}

export async function fetchRequests(params = {}) {
  const qs = new URLSearchParams(params).toString();
  const data = await safeFetch(`${BASE}/logs?${qs}`);
  return data || mockRequests;
}

export async function fetchKeys() {
  const data = await safeFetch(`${BASE}/keys`);
  return data || mockKeys;
}

export async function fetchTeams() {
  const data = await safeFetch(`${BASE}/teams`);
  return data || mockTeams;
}

export async function fetchCircuitBreaker() {
  const data = await safeFetch(`${BASE}/gateway/circuit`);
  return data || mockCircuitBreaker;
}

export async function checkServiceHealth() {
  const checks = await Promise.allSettled([
    Promise.race([fetch(`${BASE}/health`), timeout(1500)]),
    Promise.race([fetch(`${BASE}/kafka/health`), timeout(1500)]),
    Promise.race([fetch(`${BASE}/dynamodb/health`), timeout(1500)]),
  ]);
  return {
    gateway:  checks[0].status === 'fulfilled' && checks[0].value?.ok,
    kafka:    checks[1].status === 'fulfilled' && checks[1].value?.ok,
    dynamodb: checks[2].status === 'fulfilled' && checks[2].value?.ok,
  };
}

export async function createKey(payload) {
  const data = await safeFetch(`${BASE}/keys`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return data;
}
