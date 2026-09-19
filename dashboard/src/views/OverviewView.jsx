import { useState, useEffect, useCallback } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart as RechartsPie, Pie, Cell,
} from 'recharts';
import {
  DollarSign,
  Cpu,
  Activity,
  Clock,
  CheckCircle2,
  BarChart3,
  PieChart as PieIcon,
  Users,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Sparkles,
  ArrowUpRight,
} from 'lucide-react';
import MetricCard from '../components/MetricCard.jsx';
import StatusBadge from '../components/StatusBadge.jsx';
import SlideDrawer from '../components/SlideDrawer.jsx';
import { fetchKPIs, fetchTimeSeries, fetchModelBreakdown, fetchRequests } from '../services/api.js';

const MODEL_COLORS = ['#F97316', '#06B6D4', '#8B5CF6', '#10B981'];

function fmtSI(n) {
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'k';
  return String(n);
}

function relTime(ts) {
  const diff = Math.floor((Date.now() - ts) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: '#1C202A',
      border: '1px solid #323849',
      borderRadius: 8,
      padding: '10px 14px',
      fontSize: 12,
      boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
    }}>
      <div style={{ color: '#6B7280', marginBottom: 6, fontSize: 11 }}>{label}</div>
      {payload.map(p => (
        <div key={p.dataKey} style={{ color: p.color, fontFamily: "'JetBrains Mono', monospace", fontWeight: 600, fontSize: 12 }}>
          {p.dataKey === 'spend' ? `$${Number(p.value).toFixed(4)}` : `${p.value} req`}
        </div>
      ))}
    </div>
  );
};

export default function OverviewView({ timeFilter }) {
  const [kpi, setKpi]       = useState(null);
  const [ts, setTs]         = useState([]);
  const [models, setModels] = useState([]);
  const [logs, setLogs]     = useState([]);
  const [selected, setSelected] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState(new Date());

  const load = useCallback(async () => {
    setRefreshing(true);
    try {
      const [k, t, m, l] = await Promise.all([
        fetchKPIs(),
        fetchTimeSeries(timeFilter),
        fetchModelBreakdown(),
        fetchRequests({ limit: 12 }),
      ]);
      setKpi(k); setTs(t); setModels(m); setLogs(l);
      setLastRefreshed(new Date());
    } finally {
      setTimeout(() => setRefreshing(false), 400);
    }
  }, [timeFilter]);

  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, [load]);

  const teams = [
    { name: 'Engineering', spent: 8.40, budget: 100.00, pct: 8 },
    { name: 'Product',     spent: 3.95, budget: 50.00,  pct: 8 },
    { name: 'Marketing',   spent: 0.26, budget: 25.00,  pct: 1 },
  ];

  return (
    <>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Analytics Overview</h1>
          <p className="page-subtitle">Real-time AI spend, latency, and routing telemetry across all teams and models</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
            Updated {lastRefreshed.toLocaleTimeString()}
          </span>
          <button
            id="overview-refresh"
            className="btn btn-secondary btn-sm"
            onClick={load}
            disabled={refreshing}
          >
            <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
            <span>{refreshing ? 'Refreshing…' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Quick stats info bar — Portkey-style compact secondary row */}
      <div className="stats-info-row">
        <div className="stat-info-item">
          <div className="stat-info-label">Period</div>
          <div className="stat-info-value" style={{ fontFamily: 'var(--font-sans)', fontSize: 13 }}>{timeFilter === '24H' ? 'Last 24 Hours' : timeFilter === '7D' ? 'Last 7 Days' : timeFilter === '30D' ? 'Last 30 Days' : 'All Time'}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Org Budget Used</div>
          <div className="stat-info-value" style={{ color: 'var(--status-success)' }}>7.5%</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Avg. Cost / Req</div>
          <div className="stat-info-value">$0.0021</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Cache Hit Rate</div>
          <div className="stat-info-value" style={{ color: 'var(--status-cyan)' }}>— %</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Error Rate</div>
          <div className="stat-info-value" style={{ color: kpi?.blockedRequests > 0 ? 'var(--status-danger)' : 'var(--status-success)' }}>
            {kpi ? `${((kpi.blockedRequests / Math.max(kpi.totalRequests, 1)) * 100).toFixed(1)}%` : '—'}
          </div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Active Models</div>
          <div className="stat-info-value">{models.length || '—'}</div>
        </div>
      </div>

      {/* KPI Row */}
      <div className="metric-grid">
        <MetricCard
          id="kpi-spend"
          label="Total Spend"
          icon={DollarSign}
          value={kpi ? `$${kpi.totalSpend.toFixed(4)}` : '—'}
          valueClass="orange"
          sub="+$0.0016 last request"
          delta="+2.4%"
          deltaType="up"
        />
        <MetricCard
          id="kpi-tokens"
          label="Token Consumption"
          icon={Cpu}
          value={kpi ? fmtSI(kpi.totalTokens) : '—'}
          valueClass="cyan"
          sub={`↑ ${kpi ? fmtSI(kpi.promptTokens) : '—'} prompt  ·  ↓ ${kpi ? fmtSI(kpi.completionTokens) : '—'} completion`}
        />
        <MetricCard
          id="kpi-requests"
          label="Total Requests"
          icon={Activity}
          value={kpi ? kpi.totalRequests : '—'}
          valueClass="purple"
          sub={`${kpi?.successRequests || 0} successful`}
          sub2={<span style={{ color: 'var(--status-danger)', fontSize: 11 }}>{kpi?.blockedRequests || 0} blocked by budget guard</span>}
        />
        <MetricCard
          id="kpi-latency"
          label="Avg Latency"
          icon={Clock}
          value={kpi ? `${kpi.avgLatency} ms` : '—'}
          sub={`P95: ${kpi?.p95Latency || '—'} ms`}
          delta="↓ -12ms"
          deltaType="up"
        />
        <MetricCard
          id="kpi-circuit"
          label="Circuit Breaker"
          icon={CheckCircle2}
          value="CLOSED"
          valueClass="green"
          sub="Anthropic → Primary"
          sub2="0 fallback triggers today"
        />
      </div>

      {/* Charts Row */}
      <div className="charts-grid">
        {/* Time-series area chart */}
        <div className="chart-card">
          <div className="chart-card-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <BarChart3 size={15} style={{ color: 'var(--brand-primary)' }} />
              <span>Spend & Request Volume</span>
            </div>
            <span className="badge badge-orange" style={{ marginLeft: 'auto', fontSize: 10 }}>Hourly</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={ts} margin={{ top: 8, right: 4, left: -22, bottom: 0 }}>
              <defs>
                <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#F97316" stopOpacity={0.45} />
                  <stop offset="100%" stopColor="#F97316" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="reqGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#06B6D4" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#06B6D4" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="hour" tick={{ fill: '#4B5563', fontSize: 10 }} tickLine={false} axisLine={false} interval={3} />
              <YAxis tick={{ fill: '#4B5563', fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip content={<ChartTooltip />} />
              <Area type="monotone" dataKey="spend" stroke="#F97316" strokeWidth={2} fill="url(#spendGrad)" dot={false} activeDot={{ r: 4, fill: '#F97316', strokeWidth: 0 }} />
              <Area type="monotone" dataKey="requests" stroke="#06B6D4" strokeWidth={1.5} fill="url(#reqGrad)" dot={false} activeDot={{ r: 3, fill: '#06B6D4', strokeWidth: 0 }} />
            </AreaChart>
          </ResponsiveContainer>
          <div className="chart-legend">
            <div className="legend-item"><div className="legend-dot" style={{ background: '#F97316' }} />Spend (USD)</div>
            <div className="legend-item"><div className="legend-dot" style={{ background: '#06B6D4' }} />Requests</div>
          </div>
        </div>

        {/* Right column: donut + gauges */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="chart-card" style={{ flex: 1 }}>
            <div className="chart-card-title">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <PieIcon size={15} style={{ color: 'var(--status-cyan)' }} />
                <span>Cost by Model</span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <ResponsiveContainer width={100} height={100}>
                <RechartsPie>
                  <Pie data={models} dataKey="pct" innerRadius={28} outerRadius={46} strokeWidth={0}>
                    {models.map((m, i) => <Cell key={m.model} fill={MODEL_COLORS[i % MODEL_COLORS.length]} />)}
                  </Pie>
                </RechartsPie>
              </ResponsiveContainer>
              <div className="donut-legend" style={{ flex: 1 }}>
                {models.map((m, i) => (
                  <div key={m.model} className="donut-legend-row">
                    <div className="legend-dot" style={{ background: MODEL_COLORS[i], width: 8, height: 8, borderRadius: '50%', flexShrink: 0 }} />
                    <span style={{ fontSize: 11, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.model}</span>
                    <span className="donut-legend-pct">{m.pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="chart-card">
            <div className="chart-card-title">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Users size={15} style={{ color: 'var(--status-purple)' }} />
                <span>Team Budget Gauges</span>
              </div>
            </div>
            {teams.map(t => {
              const gaugeClass = t.pct >= 100 ? 'red' : t.pct >= 80 ? 'amber' : 'green';
              return (
                <div key={t.name} className="team-gauge">
                  <div className="team-gauge-header">
                    <span className="team-gauge-name">{t.name}</span>
                    <span className="team-gauge-spend">${t.spent.toFixed(2)} <span style={{ color: 'var(--text-dim)' }}>/ ${t.budget.toFixed(0)}</span></span>
                  </div>
                  <div className="gauge-track">
                    <div className={`gauge-fill ${gaugeClass}`} style={{ width: `${Math.min(t.pct, 100)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Live request feed */}
      <div className="table-panel">
        <div className="table-panel-header">
          <div className="table-panel-title">
            <span className="pulse-dot" style={{ display: 'inline-block' }} />
            <span>Live Telemetry Stream</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>Kafka → DynamoDB · auto-refresh 30s</span>
          </div>
        </div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Status</th>
                <th>Time</th>
                <th>Request ID</th>
                <th>Key</th>
                <th>Team</th>
                <th>Model</th>
                <th>Tokens</th>
                <th>Latency</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {logs.map(r => (
                <tr key={r.id} onClick={() => setSelected(r)}>
                  <td><StatusBadge status={r.status} /></td>
                  <td style={{ color: 'var(--text-muted)', fontSize: 11.5 }}>{relTime(r.ts)}</td>
                  <td><span className="mono truncate" style={{ maxWidth: 110 }}>{r.id}</span></td>
                  <td><span className="mono truncate" style={{ maxWidth: 100 }}>{r.keyId}</span></td>
                  <td><span className="badge badge-default">{r.team}</span></td>
                  <td style={{ fontSize: 12 }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: r.model.startsWith('claude') ? '#F97316' : '#10B981', flexShrink: 0 }} />
                      {r.model}
                    </span>
                  </td>
                  <td className="mono">{r.totalTokens.toLocaleString()}</td>
                  <td className="mono" style={{ color: r.latency > 1500 ? 'var(--status-warning)' : 'var(--text-secondary)' }}>
                    {r.latency}ms
                  </td>
                  <td className="mono" style={{ color: r.cost > 0 ? 'var(--brand-primary)' : 'var(--text-dim)' }}>
                    ${r.cost.toFixed(4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <SlideDrawer request={selected} onClose={() => setSelected(null)} />
    </>
  );
}
