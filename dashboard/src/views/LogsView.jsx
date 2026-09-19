import { useState, useEffect, useCallback } from 'react';
import {
  Search,
  RefreshCw,
  Activity,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ChevronDown,
  SlidersHorizontal,
  Download,
  Columns,
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge.jsx';
import SlideDrawer from '../components/SlideDrawer.jsx';
import { fetchRequests } from '../services/api.js';

function relTime(ts) {
  const diff = Math.floor((Date.now() - ts) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function absTime(ts) {
  return new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
}

const MODEL_DOT = { 'claude-3-5-sonnet': '#F97316', 'claude-3-haiku': '#FB923C', 'gpt-4o': '#10B981', 'gpt-4o-mini': '#06B6D4', 'gemini-1.5-flash': '#8B5CF6' };

export default function LogsView() {
  const [logs, setLogs]         = useState([]);
  const [search, setSearch]     = useState('');
  const [team, setTeam]         = useState('all');
  const [statusF, setStatusF]   = useState('all');
  const [selected, setSelected] = useState(null);
  const [loading, setLoading]   = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchRequests({ limit: 50 });
      setLogs(data);
    } finally {
      setTimeout(() => setLoading(false), 350);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 20000);
    return () => clearInterval(id);
  }, [load]);

  const filtered = logs.filter(r => {
    const q = search.toLowerCase();
    const matchQ = !q || r.id.toLowerCase().includes(q) || r.keyId.toLowerCase().includes(q) || r.model.toLowerCase().includes(q) || r.team.toLowerCase().includes(q);
    const matchTeam = team === 'all' || r.team === team;
    const matchStatus = statusF === 'all' || (statusF === 'success' && r.status === 200) || (statusF === 'blocked' && r.status === 403) || (statusF === 'slow' && r.latency > 1500);
    return matchQ && matchTeam && matchStatus;
  });

  const totalTokens = filtered.reduce((s, r) => s + r.totalTokens, 0);
  const totalCost   = filtered.reduce((s, r) => s + r.cost, 0);
  const avgLatency  = filtered.length ? Math.round(filtered.reduce((s, r) => s + r.latency, 0) / filtered.length) : 0;
  const successRate = filtered.length ? ((filtered.filter(r => r.status === 200).length / filtered.length) * 100).toFixed(1) : '—';

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Request Logs</h1>
          <p className="page-subtitle">Full observability stream — click any row to inspect trace, headers, tokens, and payload</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary btn-sm" style={{ gap: 5 }}>
            <Download size={13} />
            <span>Export CSV</span>
          </button>
          <button
            id="logs-refresh"
            className="btn btn-secondary btn-sm"
            onClick={load}
            disabled={loading}
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>{loading ? 'Loading…' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Summary strip */}
      <div className="stats-info-row">
        <div className="stat-info-item">
          <div className="stat-info-label">Requests Shown</div>
          <div className="stat-info-value">{filtered.length}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Total Tokens</div>
          <div className="stat-info-value" style={{ color: 'var(--status-cyan)' }}>{totalTokens.toLocaleString()}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Total Cost</div>
          <div className="stat-info-value" style={{ color: 'var(--brand-primary)' }}>${totalCost.toFixed(4)}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Avg Latency</div>
          <div className="stat-info-value" style={{ color: avgLatency > 1500 ? 'var(--status-warning)' : 'inherit' }}>{avgLatency}ms</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Success Rate</div>
          <div className="stat-info-value" style={{ color: parseFloat(successRate) >= 95 ? 'var(--status-success)' : 'var(--status-warning)' }}>{successRate}%</div>
        </div>
      </div>

      <div className="table-panel">
        {/* Filter bar */}
        <div className="filter-bar">
          <div className="search-wrap" style={{ maxWidth: 360 }}>
            <Search size={14} className="search-icon" />
            <input
              id="logs-search"
              type="text"
              className="search-input"
              placeholder="Search request_id, model, team, key…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          <select
            id="team-filter"
            className="form-select"
            style={{ width: 'auto', padding: '6px 12px', fontSize: 12 }}
            value={team}
            onChange={e => setTeam(e.target.value)}
          >
            <option value="all">All Teams</option>
            <option value="engineering">Engineering</option>
            <option value="product">Product</option>
            <option value="marketing">Marketing</option>
          </select>

          <select
            id="status-filter"
            className="form-select"
            style={{ width: 'auto', padding: '6px 12px', fontSize: 12 }}
            value={statusF}
            onChange={e => setStatusF(e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="success">200 OK</option>
            <option value="blocked">403 Blocked</option>
            <option value="slow">Slow (&gt;1500ms)</option>
          </select>

          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="pulse-dot" style={{ display: 'inline-block' }} />
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Live · auto-refresh 20s</span>
          </div>
        </div>

        {/* Table */}
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Status</th>
                <th>Time</th>
                <th>Request ID</th>
                <th>Virtual Key</th>
                <th>Team</th>
                <th>Model</th>
                <th>Latency</th>
                <th>Tokens</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(r => (
                <tr key={r.id} onClick={() => setSelected(r)}>
                  <td><StatusBadge status={r.status} /></td>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{absTime(r.ts)}</span>
                      <span style={{ color: 'var(--text-dim)', fontSize: 10.5 }}>{relTime(r.ts)}</span>
                    </div>
                  </td>
                  <td>
                    <span className="mono truncate" style={{ maxWidth: 120, color: 'var(--text-secondary)' }}>{r.id}</span>
                  </td>
                  <td>
                    <span className="mono truncate" style={{ maxWidth: 120, color: 'var(--text-muted)' }}>{r.keyId}</span>
                  </td>
                  <td>
                    <span className="badge badge-default">{r.team}</span>
                  </td>
                  <td style={{ fontSize: 12 }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: MODEL_DOT[r.model] || '#6B7280', flexShrink: 0 }} />
                      <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{r.model}</span>
                    </span>
                  </td>
                  <td>
                    <span className="mono" style={{ color: r.latency > 1500 ? 'var(--status-warning)' : r.latency > 800 ? 'var(--text-secondary)' : 'var(--status-success)', fontWeight: r.latency > 1500 ? 600 : 400 }}>
                      {r.latency}ms
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <span className="mono" style={{ fontSize: 12 }}>{r.totalTokens.toLocaleString()}</span>
                      <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>↑{r.promptTokens} ↓{r.completionTokens}</span>
                    </div>
                  </td>
                  <td>
                    <span className="mono" style={{ color: r.cost > 0 ? 'var(--brand-primary)' : 'var(--text-dim)', fontWeight: 600 }}>
                      ${r.cost.toFixed(4)}
                    </span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '48px 20px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                      <Activity size={28} style={{ color: 'var(--text-dim)' }} />
                      <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>No matching traces found</span>
                      <span style={{ color: 'var(--text-dim)', fontSize: 12 }}>Try adjusting your search or filters</span>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <SlideDrawer request={selected} onClose={() => setSelected(null)} />
    </>
  );
}
