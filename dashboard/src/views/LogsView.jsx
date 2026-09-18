import { useState, useEffect, useCallback } from 'react';
import {
  Search,
  RefreshCw,
  Filter,
  ArrowUpDown,
  Calendar,
  Layers,
  CheckCircle2,
  XCircle,
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

export default function LogsView() {
  const [logs, setLogs]       = useState([]);
  const [search, setSearch]   = useState('');
  const [team, setTeam]       = useState('all');
  const [status, setStatus]   = useState('all');
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchRequests();
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
    const matchQ = !q || r.id.toLowerCase().includes(q) || r.keyId.toLowerCase().includes(q) || r.model.toLowerCase().includes(q);
    const matchTeam = team === 'all' || r.team === team;
    const matchStatus = status === 'all'
      || (status === 'success' && r.status === 200)
      || (status === 'blocked' && r.status === 403);
    return matchQ && matchTeam && matchStatus;
  });

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Request Logs & Traces</h1>
          <p className="page-subtitle">Full observability stream from DynamoDB telemetry — click any trace row to inspect headers, payloads, and tokens</p>
        </div>
        <button
          id="logs-refresh"
          className="btn btn-secondary btn-sm"
          onClick={load}
          disabled={loading}
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>{loading ? 'Refreshing…' : 'Refresh'}</span>
        </button>
      </div>

      <div className="table-panel">
        <div className="filter-bar">
          <div className="search-wrap">
            <Search size={14} className="search-icon" />
            <input
              id="logs-search"
              type="text"
              className="search-input"
              placeholder="Search by request_id, key_id, or model…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          <div className="filter-controls" style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
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
              value={status}
              onChange={e => setStatus(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="success">200 OK</option>
              <option value="blocked">403 Blocked</option>
            </select>
          </div>

          <div style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-muted)' }}>
            Showing {filtered.length} traces
          </div>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Status</th>
                <th>Timestamp</th>
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
                <tr key={r.id} onClick={() => setSelected(r)} style={{ cursor: 'pointer' }}>
                  <td><StatusBadge status={r.status} /></td>
                  <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{relTime(r.ts)}</td>
                  <td>
                    <span className="mono truncate">{r.id}</span>
                  </td>
                  <td><span className="mono truncate">{r.keyId}</span></td>
                  <td><span className="badge badge-default">{r.team}</span></td>
                  <td style={{ fontSize: 12 }}>{r.model}</td>
                  <td className="mono" style={{ color: r.latency > 1500 ? 'var(--status-warning)' : 'inherit' }}>
                    {r.latency}ms
                  </td>
                  <td className="mono">{r.totalTokens.toLocaleString()}</td>
                  <td className="mono" style={{ color: r.cost > 0 ? 'var(--brand-primary)' : 'var(--text-dim)' }}>
                    ${r.cost.toFixed(4)}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                    No matching traces found for the active search and filters.
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
