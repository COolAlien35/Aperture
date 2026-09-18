import { useState } from 'react';
import {
  X,
  Copy,
  Check,
  Cpu,
  Clock,
  Coins,
  Layers,
  ArrowUpRight,
  ArrowDownLeft,
  Calendar,
  KeyRound,
  Users,
} from 'lucide-react';
import StatusBadge from './StatusBadge.jsx';

function relTime(ts) {
  const diff = Math.floor((Date.now() - ts) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export default function SlideDrawer({ request, onClose }) {
  const [tab, setTab] = useState('overview');
  const [copiedField, setCopiedField] = useState(null);
  const open = Boolean(request);

  const copyToClipboard = (text, fieldName) => {
    navigator.clipboard?.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 1500);
  };

  const promptCost = request ? (request.promptTokens / 1e6) * (request.model.startsWith('claude') ? 3 : 5) : 0;
  const completionCost = request ? (request.completionTokens / 1e6) * (request.model.startsWith('claude') ? 15 : 15) : 0;

  return (
    <>
      <div
        className={`drawer-overlay${open ? ' open' : ''}`}
        onClick={onClose}
        role="button"
        aria-label="Close drawer"
        tabIndex={0}
        onKeyDown={e => e.key === 'Escape' && onClose()}
      />
      <div className={`slide-drawer${open ? ' open' : ''}`} role="dialog" aria-modal="true" aria-label="Request Details">
        {request && (
          <>
            <div className="drawer-header">
              <div>
                <div className="drawer-title">Trace Details</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3, fontFamily: 'var(--font-mono)' }}>
                  {request.id}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <StatusBadge status={request.status} />
                <button className="btn btn-ghost btn-icon" onClick={onClose} aria-label="Close">
                  <X size={16} />
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 20, padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-surface-1)' }}>
              <div style={{ textAlign: 'center', flex: 1 }}>
                <div style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.7px', fontWeight: 700 }}>Latency</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--status-cyan)', fontSize: 17, marginTop: 2 }}>{request.latency} ms</div>
              </div>
              <div style={{ width: 1, background: 'var(--border-subtle)' }} />
              <div style={{ textAlign: 'center', flex: 1 }}>
                <div style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.7px', fontWeight: 700 }}>Tokens</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)', fontSize: 17, marginTop: 2 }}>{request.totalTokens.toLocaleString()}</div>
              </div>
              <div style={{ width: 1, background: 'var(--border-subtle)' }} />
              <div style={{ textAlign: 'center', flex: 1 }}>
                <div style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.7px', fontWeight: 700 }}>Cost</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--brand-primary)', fontSize: 17, marginTop: 2 }}>${request.cost.toFixed(4)}</div>
              </div>
              <div style={{ width: 1, background: 'var(--border-subtle)' }} />
              <div style={{ textAlign: 'center', flex: 1 }}>
                <div style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.7px', fontWeight: 700 }}>Age</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-secondary)', fontSize: 13, marginTop: 4 }}>{relTime(request.ts)}</div>
              </div>
            </div>

            <div className="drawer-tabs">
              {['overview', 'cost', 'raw'].map(t => (
                <div
                  key={t}
                  className={`drawer-tab${tab === t ? ' active' : ''}`}
                  onClick={() => setTab(t)}
                  role="tab"
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && setTab(t)}
                >
                  {t === 'overview' ? 'Overview' : t === 'cost' ? 'Cost Attribution' : 'Raw Telemetry'}
                </div>
              ))}
            </div>

            <div className="drawer-body">
              {tab === 'overview' && (
                <>
                  <div className="drawer-field">
                    <div className="drawer-field-label">Request ID</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <code style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-primary)' }}>{request.id}</code>
                      <button className="copy-btn" onClick={() => copyToClipboard(request.id, 'id')}>
                        {copiedField === 'id' ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
                        <span>{copiedField === 'id' ? 'copied' : 'copy'}</span>
                      </button>
                    </div>
                  </div>
                  <div className="drawer-field">
                    <div className="drawer-field-label">Virtual Key</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <code style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-primary)' }}>{request.keyId}</code>
                      <button className="copy-btn" onClick={() => copyToClipboard(request.keyId, 'key')}>
                        {copiedField === 'key' ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
                        <span>{copiedField === 'key' ? 'copied' : 'copy'}</span>
                      </button>
                    </div>
                  </div>
                  <div className="drawer-field">
                    <div className="drawer-field-label">Assigned Team</div>
                    <div className="drawer-field-value"><span className="badge badge-default">{request.team}</span></div>
                  </div>
                  <div className="drawer-field">
                    <div className="drawer-field-label">Target Model</div>
                    <div className="drawer-field-value" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Cpu size={14} style={{ color: request.model.startsWith('claude') ? '#F97316' : '#10B981' }} />
                      <span style={{ fontWeight: 600 }}>{request.model}</span>
                    </div>
                  </div>
                  <div className="drawer-field">
                    <div className="drawer-field-label">Token Breakdown</div>
                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                      <span className="badge badge-cyan" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        <ArrowUpRight size={11} /> Prompt: {request.promptTokens.toLocaleString()}
                      </span>
                      <span className="badge badge-purple" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        <ArrowDownLeft size={11} /> Completion: {request.completionTokens.toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <div className="drawer-field">
                    <div className="drawer-field-label">Trace Timeline</div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      {new Date(request.ts).toISOString()}
                    </div>
                  </div>
                </>
              )}

              {tab === 'cost' && (
                <>
                  <div className="drawer-field">
                    <div className="drawer-field-label">Prompt Token Cost</div>
                    <div className="drawer-field-value mono">
                      ${promptCost.toFixed(6)}
                      <span style={{ fontSize: 11, color: 'var(--text-dim)', marginLeft: 8 }}>
                        ({request.promptTokens} tokens @ ${request.model.startsWith('claude') ? '3.00' : '5.00'} / 1M)
                      </span>
                    </div>
                  </div>
                  <div className="drawer-field">
                    <div className="drawer-field-label">Completion Token Cost</div>
                    <div className="drawer-field-value mono">
                      ${completionCost.toFixed(6)}
                      <span style={{ fontSize: 11, color: 'var(--text-dim)', marginLeft: 8 }}>
                        ({request.completionTokens} tokens @ $15.00 / 1M)
                      </span>
                    </div>
                  </div>
                  <div className="drawer-field">
                    <div className="drawer-field-label">Total Incurred Cost</div>
                    <div className="drawer-field-value mono" style={{ fontSize: 16, color: 'var(--brand-primary)', fontWeight: 700 }}>
                      ${request.cost.toFixed(6)}
                    </div>
                  </div>
                </>
              )}

              {tab === 'raw' && (
                <div style={{ background: 'var(--bg-app)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 12 }}>
                  <pre style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 11,
                    color: 'var(--text-secondary)',
                    overflowX: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                    lineHeight: 1.6,
                  }}>
                    {JSON.stringify(request, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </>
  );
}
