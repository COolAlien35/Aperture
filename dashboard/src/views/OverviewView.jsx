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
  Zap,
  ArrowUpRight,
  TrendingDown,
  ShieldAlert,
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

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--bg-surface-3)', border: '1px solid var(--border-active)',
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
      boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
    }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: 6 }}>{label}</div>
      {payload.map(p => (
        <div key={p.dataKey} style={{ color: p.color, fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
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

  const load = useCallback(async () => {
    setRefreshing(true);
    try {
      const [k, t, m, l] = await Promise.all([
        fetchKPIs(),
        fetchTimeSeries(timeFilter),
        fetchModelBreakdown(),
        fetchRequests({ limit: 10 }),
      ]);
      setKpi(k); setTs(t); setModels(m); setLogs(l);
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
      <div className="page-header">
        <div>
          <h1 className="page-title">Analytics Overview</h1>
          <p className="page-subtitle">Real-time AI spend, token consumption, and routing telemetry across all teams</p>
        </div>
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

      {/* KPI Row */}
      <div className="metric-grid">
        <MetricCard
          id="kpi-spend"
          label="Total Spend"
          icon={DollarSign}
          value={kpi ? `$${kpi.totalSpend.toFixed(4)}` : '—'}
          valueClass="orange"
          sub="+$0.0016 last req"
          delta="+2.4%"
          deltaType="up"
        />
        <MetricCard
          id="kpi-tokens"
          label="Total Tokens"
          icon={Cpu}
          value={kpi ? fmtSI(kpi.totalTokens) : '—'}
          valueClass="cyan"
          sub={`Prompt: ${kpi ? fmtSI(kpi.promptTokens) : '—'} · Compl: ${kpi ? fmtSI(kpi.completionTokens) : '—'}`}
        />
        <MetricCard
          id="kpi-requests"
          label="Total Requests"
          icon={Activity}
          value={kpi ? kpi.totalRequests : '—'}
          valueClass="purple"
          sub={`${kpi?.successRequests || 0} successful`}
          sub2={<span style={{ color: 'var(--status-danger)' }}>{kpi?.blockedRequests || 0} blocked by budget</span>}
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
          label="Circuit State"
          icon={CheckCircle2}
          value="CLOSED"
          valueClass="green"
          sub="Anthropic · Primary"
          sub2="0 fallback triggers"
        />
      </div>

      {/* Charts Row */}
      <div className="charts-grid">
        {/* Spend & Requests time-series */}
        <div className="chart-card">
          <div className="chart-card-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <BarChart3 size={16} style={{ color: 'var(--brand-primary)' }} />
              <span>Spend & Request Volume</span>
            </div>
            <span className="badge badge-orange" style={{ marginLeft: 'auto', fontSize: 10 }}>Hourly Aggregation</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={ts} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#F97316" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#F97316" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="reqGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#06B6D4" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#06B6D4" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="hour" tick={{ fill: 'var(--text-dim)', fontSize: 10 }} tickLine={false} axisLine={false} interval={3} />
              <YAxis tick={{ fill: 'var(--text-dim)', fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="spend" stroke="#F97316" strokeWidth={2} fill="url(#spendGrad)" dot={false} activeDot={{ r: 4, fill: '#F97316' }} />
              <Area type="monotone" dataKey="requests" stroke="#06B6D4" strokeWidth={1.5} fill="url(#reqGrad)" dot={false} activeDot={{ r: 3, fill: '#06B6D4' }} />
            </AreaChart>
          </ResponsiveContainer>
          <div className="chart-legend">
            <div className="legend-item"><div className="legend-dot" style={{ background: '#F97316' }} />Spend ($ USD)</div>
            <div className="legend-item"><div className="legend-dot" style={{ background: '#06B6D4' }} />Request Volume</div>
          </div>
        </div>

        {/* Model donut + team gauges */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Donut */}
          <div className="chart-card" style={{ flex: 1 }}>
            <div className="chart-card-title">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <PieIcon size={16} style={{ color: 'var(--status-cyan)' }} />
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

          {/* Team gauges */}
          <div className="chart-card">
            <div className="chart-card-title">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Users size={16} style={{ color: 'var(--status-purple)' }} />
                <span>Team Budgets</span>
              </div>
            </div>
            {teams.map(t => {
              const gaugeClass = t.pct >= 100 ? 'red' : t.pct >= 80 ? 'amber' : 'green';
              return (
                <div key={t.name} className="team-gauge">
                  <div className="team-gauge-header">
                    <span className="team-gauge-name">{t.name}</span>
                    <span className="team-gauge-spend">${t.spent.toFixed(2)} / ${t.budget.toFixed(2)}</span>
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
            <span>Live Usage Telemetry</span>
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>Streamed via Kafka & DynamoDB</span>
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
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {logs.map(r => (
                <tr key={r.id} onClick={() => setSelected(r)}>
                  <td><StatusBadge status={r.status} /></td>
                  <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{relTime(r.ts)}</td>
                  <td>
                    <span className="mono truncate">{r.id}</span>
                  </td>
                  <td><span className="mono truncate">{r.keyId}</span></td>
                  <td><span className="badge badge-default">{r.team}</span></td>
                  <td style={{ fontSize: 12 }}>{r.model}</td>
                  <td className="mono">{r.totalTokens.toLocaleString()}</td>
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
