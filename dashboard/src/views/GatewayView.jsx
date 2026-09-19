import { useState, useEffect } from 'react';
import {
  Laptop,
  ShieldCheck,
  Zap,
  Cpu,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  FlaskConical,
  ArrowRight,
  Server,
  Activity,
  Layers,
  Radio,
  Sliders,
  Check,
} from 'lucide-react';
import ApertureLogo from '../components/ApertureLogo.jsx';
import { fetchCircuitBreaker } from '../services/api.js';

const CB_CLASS = { CLOSED: 'closed', OPEN: 'open', 'HALF-OPEN': 'half' };

const PROVIDERS = [
  {
    id: 'anthropic',
    name: 'Anthropic',
    role: 'Primary Upstream',
    model: 'claude-3-5-sonnet',
    status: 'OPERATIONAL',
    latencyP50: '680ms',
    latencyP95: '1,420ms',
    uptime: '99.98%',
    brandColor: '#F97316',
  },
  {
    id: 'openai',
    name: 'OpenAI',
    role: 'Automated Fallback',
    model: 'gpt-4o',
    status: 'STANDBY',
    latencyP50: '540ms',
    latencyP95: '1,120ms',
    uptime: '99.95%',
    brandColor: '#10B981',
  },
  {
    id: 'gemini',
    name: 'Google Gemini',
    role: 'Secondary Failover',
    model: 'gemini-1.5-flash',
    status: 'STANDBY',
    latencyP50: '320ms',
    latencyP95: '780ms',
    uptime: '99.99%',
    brandColor: '#8B5CF6',
  },
];

export default function GatewayView() {
  const [cb, setCb]             = useState(null);
  const [testState, setTest]     = useState(null); // 'triggering' | 'tripped' | null
  const [activeStrategy, setStrategy] = useState('fallback');

  useEffect(() => {
    fetchCircuitBreaker().then(setCb);
  }, []);

  const triggerTest = () => {
    setTest('triggering');
    setTimeout(() => setTest('tripped'), 1400);
    setTimeout(() => setTest(null), 7000);
  };

  const displayCb = testState === 'tripped'
    ? { ...(cb || {}), state: 'OPEN', failures: 3 }
    : cb;

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">AI Gateway & Routing Topology</h1>
          <p className="page-subtitle">Real-time load balancing, automated upstream failover, and zero-downtime circuit breaking</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            id="trigger-failure-btn"
            className={`btn ${testState === 'tripped' ? 'btn-secondary' : 'btn-primary'}`}
            onClick={triggerTest}
            disabled={testState !== null}
          >
            {testState === 'triggering' ? (
              <>
                <RotateCcw size={14} className="animate-spin" />
                <span>Simulating 5xx Failures…</span>
              </>
            ) : testState === 'tripped' ? (
              <>
                <AlertTriangle size={14} style={{ color: 'var(--status-danger)' }} />
                <span>Failover Active (OpenAI)</span>
              </>
            ) : (
              <>
                <FlaskConical size={14} />
                <span>Simulate Primary Outage</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Outage banner when tripped */}
      {testState === 'tripped' && (
        <div className="alert-banner danger">
          <AlertTriangle size={18} style={{ color: 'var(--status-danger)', flexShrink: 0 }} />
          <div>
            <strong>Circuit Breaker Tripped (State: OPEN)</strong> — 3 consecutive upstream 5xx errors recorded from Anthropic. Aperture Gateway has automatically redirected traffic to <strong>OpenAI (gpt-4o)</strong> with zero dropped requests. Auto-health probe active in 60s.
          </div>
        </div>
      )}

      {/* Top Stats Strip */}
      <div className="stats-info-row">
        <div className="stat-info-item">
          <div className="stat-info-label">Active Strategy</div>
          <div className="stat-info-value" style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--brand-primary)' }}>
            Dynamic Failover
          </div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Primary Gateway Node</div>
          <div className="stat-info-value" style={{ color: 'var(--status-success)' }}>localhost:8080</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Current Route</div>
          <div className="stat-info-value" style={{ color: testState === 'tripped' ? 'var(--status-warning)' : 'var(--brand-primary)' }}>
            {testState === 'tripped' ? 'OpenAI (GPT-4o)' : 'Anthropic (Claude)'}
          </div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Circuit State</div>
          <div className="stat-info-value" style={{ color: testState === 'tripped' ? 'var(--status-danger)' : 'var(--status-success)' }}>
            {testState === 'tripped' ? 'OPEN (TRIPPED)' : 'CLOSED (HEALTHY)'}
          </div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Max Retries</div>
          <div className="stat-info-value">3 attempts</div>
        </div>
      </div>

      {/* Visual Pipeline Topology */}
      <div className="chart-card" style={{ marginBottom: 20 }}>
        <div className="chart-card-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Server size={16} style={{ color: 'var(--brand-primary)' }} />
            <span>End-to-End Pipeline Topology</span>
          </div>
          <span className="badge badge-default" style={{ marginLeft: 'auto', fontSize: 10 }}>
            Zero-Downtime Architecture
          </span>
        </div>

        <div className="pipeline-diagram">
          {/* Client node */}
          <div className="pipeline-node">
            <div className="pipeline-node-icon">
              <Laptop size={20} style={{ color: 'var(--text-secondary)' }} />
            </div>
            <div className="pipeline-node-label">Client App / SDK</div>
            <div className="pipeline-node-sub">OpenAI / Anthropic SDK</div>
          </div>

          <div className="pipeline-arrow"><ArrowRight size={16} /></div>

          {/* Aperture Gateway */}
          <div className="pipeline-node" style={{ borderColor: 'var(--brand-primary)', boxShadow: 'var(--brand-glow)' }}>
            <div className="pipeline-node-icon">
              <ApertureLogo size={22} showText={false} />
            </div>
            <div className="pipeline-node-label">Aperture Gateway</div>
            <div className="pipeline-node-sub">Reverse Proxy :8080</div>
          </div>

          <div className="pipeline-arrow"><ArrowRight size={16} /></div>

          {/* Auth & Guardrails */}
          <div className="pipeline-node">
            <div className="pipeline-node-icon">
              <ShieldCheck size={20} style={{ color: 'var(--status-cyan)' }} />
            </div>
            <div className="pipeline-node-label">Auth & Budgets</div>
            <div className="pipeline-node-sub">Pre-Flight Quota Check</div>
          </div>

          <div className="pipeline-arrow"><ArrowRight size={16} /></div>

          {/* Circuit Breaker Node */}
          <div className="pipeline-node" style={{
            borderColor: testState === 'tripped' ? 'var(--status-danger)' : 'var(--status-success)',
            boxShadow: testState === 'tripped' ? '0 0 16px rgba(239,68,68,0.4)' : '0 0 12px rgba(16,185,129,0.25)',
          }}>
            <div className="pipeline-node-icon">
              {testState === 'tripped' ? (
                <AlertTriangle size={20} style={{ color: 'var(--status-danger)' }} />
              ) : (
                <CheckCircle2 size={20} style={{ color: 'var(--status-success)' }} />
              )}
            </div>
            <div className="pipeline-node-label">Circuit Breaker</div>
            <div className="pipeline-node-sub" style={{ color: testState === 'tripped' ? 'var(--status-danger)' : 'var(--status-success)', fontWeight: 600 }}>
              {testState === 'tripped' ? 'OPEN (Tripped)' : 'CLOSED (Nominal)'}
            </div>
          </div>

          <div className="pipeline-arrow"><ArrowRight size={16} /></div>

          {/* Upstream Providers Fork */}
          <div className="pipeline-fork">
            <div className="pipeline-node" style={{
              opacity: testState === 'tripped' ? 0.35 : 1,
              borderColor: testState === 'tripped' ? 'var(--border-default)' : 'var(--status-success-border)',
              boxShadow: testState === 'tripped' ? 'none' : '0 0 12px rgba(16,185,129,0.2)',
            }}>
              <div className="pipeline-node-icon">
                <Cpu size={20} style={{ color: '#F97316' }} />
              </div>
              <div className="pipeline-node-label">Primary Target</div>
              <div className="pipeline-node-sub">Anthropic (Claude 3.5)</div>
            </div>

            <div className="pipeline-node" style={{
              opacity: testState === 'tripped' ? 1 : 0.4,
              borderColor: testState === 'tripped' ? 'var(--status-warning-border)' : 'var(--border-default)',
              boxShadow: testState === 'tripped' ? '0 0 16px rgba(245,158,11,0.4)' : 'none',
            }}>
              <div className="pipeline-node-icon">
                <Cpu size={20} style={{ color: '#10B981' }} />
              </div>
              <div className="pipeline-node-label">Fallback Target</div>
              <div className="pipeline-node-sub">OpenAI (GPT-4o)</div>
            </div>
          </div>
        </div>
      </div>

      {/* Upstream Provider Health Table */}
      <div className="table-panel" style={{ marginBottom: 24 }}>
        <div className="table-panel-header">
          <div className="table-panel-title">
            <Activity size={14} style={{ color: 'var(--brand-primary)' }} />
            <span>Upstream Provider Health & Telemetry</span>
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
            Probes active every 15s
          </span>
        </div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Provider</th>
                <th>Routing Role</th>
                <th>Default Model</th>
                <th>P50 Latency</th>
                <th>P95 Latency</th>
                <th>Uptime SLA</th>
                <th>Live Status</th>
              </tr>
            </thead>
            <tbody>
              {PROVIDERS.map(p => {
                const isTrippedPrimary = p.id === 'anthropic' && testState === 'tripped';
                const isTrippedFallback = p.id === 'openai' && testState === 'tripped';

                return (
                  <tr key={p.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ width: 8, height: 8, borderRadius: '50%', background: p.brandColor, flexShrink: 0 }} />
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{p.name}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${p.id === 'anthropic' ? 'badge-orange' : 'badge-default'}`}>
                        {p.role}
                      </span>
                    </td>
                    <td><span className="mono" style={{ fontSize: 12 }}>{p.model}</span></td>
                    <td className="mono">{p.latencyP50}</td>
                    <td className="mono">{p.latencyP95}</td>
                    <td className="mono" style={{ color: 'var(--status-success)' }}>{p.uptime}</td>
                    <td>
                      {isTrippedPrimary ? (
                        <span className="status-pill danger">
                          <span className="pulse-dot red" />
                          <span>5xx DEGRADED</span>
                        </span>
                      ) : isTrippedFallback ? (
                        <span className="status-pill warning">
                          <span className="pulse-dot amber" />
                          <span>ACTIVE FALLBACK</span>
                        </span>
                      ) : (
                        <span className="status-pill healthy">
                          <span className="pulse-dot" />
                          <span>OPERATIONAL</span>
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Circuit Breaker Live Diagnostics */}
      {displayCb && (
        <div className="chart-card">
          <div className="chart-card-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Zap size={16} style={{ color: 'var(--status-warning)' }} />
              <span>Circuit Breaker State Machine Diagnostics</span>
            </div>
            <div className={`cb-state ${CB_CLASS[displayCb.state] || 'closed'}`} style={{ marginLeft: 'auto', padding: '3px 10px', fontSize: 11 }}>
              <span className={`pulse-dot ${displayCb.state === 'CLOSED' ? '' : displayCb.state === 'OPEN' ? 'red' : 'amber'}`} />
              <span>{displayCb.state}</span>
            </div>
          </div>

          <div className="cb-metrics-grid" style={{ marginTop: 12 }}>
            <div className="cb-metric-card">
              <div className="cb-metric-lbl">Failure Threshold</div>
              <div className="cb-metric-val" style={{ color: displayCb.failures > 0 ? 'var(--status-danger)' : 'var(--status-success)' }}>
                {displayCb.failures} / {displayCb.threshold}
              </div>
            </div>
            <div className="cb-metric-card">
              <div className="cb-metric-lbl">Recovery Probe Window</div>
              <div className="cb-metric-val">{displayCb.recoveryWindow}s</div>
            </div>
            <div className="cb-metric-card">
              <div className="cb-metric-lbl">Consecutive Successes</div>
              <div className="cb-metric-val" style={{ color: 'var(--status-success)' }}>{displayCb.successCount}</div>
            </div>
            <div className="cb-metric-card">
              <div className="cb-metric-lbl">Total Monitored Requests</div>
              <div className="cb-metric-val">{displayCb.totalRequests}</div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
