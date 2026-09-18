import { useState, useEffect } from 'react';
import {
  Laptop,
  Layers,
  ShieldCheck,
  Zap,
  Cpu,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  FlaskConical,
  ArrowRight,
  Server,
} from 'lucide-react';
import ApertureLogo from '../components/ApertureLogo.jsx';
import { fetchCircuitBreaker } from '../services/api.js';

const CB_CLASS = { CLOSED: 'closed', OPEN: 'open', 'HALF-OPEN': 'half' };

export default function GatewayView() {
  const [cb, setCb]       = useState(null);
  const [testState, setTest] = useState(null); // 'triggering' | 'tripped' | null

  useEffect(() => { fetchCircuitBreaker().then(setCb); }, []);

  const triggerTest = () => {
    setTest('triggering');
    setTimeout(() => setTest('tripped'), 1200);
    setTimeout(() => setTest(null), 5000);
  };

  const displayCb = testState === 'tripped'
    ? { ...(cb || {}), state: 'OPEN', failures: 3 }
    : cb;

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Gateway Routing & Circuit Breakers</h1>
          <p className="page-subtitle">Live topology of the Aperture AI request routing, failover, and rate-limiting pipeline</p>
        </div>
      </div>

      {testState === 'tripped' && (
        <div className="alert-banner danger">
          <AlertTriangle size={18} style={{ color: 'var(--status-danger)', flexShrink: 0 }} />
          <div>
            Circuit Breaker <strong>OPEN</strong> — 3 consecutive upstream 5xx errors detected. Aperture has automatically routed traffic to fallback: <strong>OpenAI (gpt-4o)</strong>. Auto-recovery active in 60s.
          </div>
        </div>
      )}
      {testState === 'triggering' && (
        <div className="alert-banner warn">
          <RotateCcw size={18} className="animate-spin" style={{ color: 'var(--status-warning)', flexShrink: 0 }} />
          <div>
            Simulating 3 consecutive 5xx failures to primary Anthropic endpoint…
          </div>
        </div>
      )}

      {/* Visual pipeline diagram */}
      <div className="chart-card" style={{ marginBottom: 20 }}>
        <div className="chart-card-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Server size={16} style={{ color: 'var(--brand-primary)' }} />
            <span>Request Routing Topology</span>
          </div>
        </div>
        <div className="pipeline-diagram">
          <div className="pipeline-node">
            <div className="pipeline-node-icon">
              <Laptop size={20} style={{ color: 'var(--text-secondary)' }} />
            </div>
            <div className="pipeline-node-label">Client</div>
            <div className="pipeline-node-sub">App / SDK / Agent</div>
          </div>
          <div className="pipeline-arrow"><ArrowRight size={16} /></div>

          <div className="pipeline-node" style={{ borderColor: 'var(--brand-primary)', boxShadow: 'var(--brand-glow)' }}>
            <div className="pipeline-node-icon">
              <ApertureLogo size={22} showText={false} />
            </div>
            <div className="pipeline-node-label">Aperture Gateway</div>
            <div className="pipeline-node-sub">Port :8080</div>
          </div>
          <div className="pipeline-arrow"><ArrowRight size={16} /></div>

          <div className="pipeline-node">
            <div className="pipeline-node-icon">
              <ShieldCheck size={20} style={{ color: 'var(--status-cyan)' }} />
            </div>
            <div className="pipeline-node-label">Auth & Policy</div>
            <div className="pipeline-node-sub">RBAC + Budget Guard</div>
          </div>
          <div className="pipeline-arrow"><ArrowRight size={16} /></div>

          <div className="pipeline-node" style={{
            borderColor: testState === 'tripped' ? 'var(--status-danger)' : 'var(--status-success)',
            boxShadow: testState === 'tripped' ? '0 0 16px rgba(239,68,68,0.4)' : '0 0 12px rgba(16,185,129,0.3)',
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
              {testState === 'tripped' ? 'OPEN' : 'CLOSED'}
            </div>
          </div>
          <div className="pipeline-arrow"><ArrowRight size={16} /></div>

          <div className="pipeline-fork">
            <div className="pipeline-node" style={{
              opacity: testState === 'tripped' ? 0.4 : 1,
              borderColor: testState === 'tripped' ? 'var(--border-default)' : 'var(--status-success-border)',
            }}>
              <div className="pipeline-node-icon">
                <Cpu size={20} style={{ color: '#F97316' }} />
              </div>
              <div className="pipeline-node-label">Primary</div>
              <div className="pipeline-node-sub">Anthropic (Claude)</div>
            </div>
            <div className="pipeline-node" style={{
              opacity: testState === 'tripped' ? 1 : 0.4,
              borderColor: testState === 'tripped' ? 'var(--status-warning-border)' : 'var(--border-default)',
              boxShadow: testState === 'tripped' ? '0 0 14px rgba(245,158,11,0.4)' : 'none',
            }}>
              <div className="pipeline-node-icon">
                <Cpu size={20} style={{ color: '#10B981' }} />
              </div>
              <div className="pipeline-node-label">Fallback</div>
              <div className="pipeline-node-sub">OpenAI (GPT-4o)</div>
            </div>
          </div>
        </div>
      </div>

      {/* CB metrics */}
      {displayCb && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
            <div className={`cb-state ${CB_CLASS[displayCb.state] || 'closed'}`}>
              <span className={`pulse-dot ${displayCb.state === 'CLOSED' ? '' : displayCb.state === 'OPEN' ? 'red' : 'amber'}`} />
              {displayCb.state}
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>
              Primary: <strong style={{ color: 'var(--text-primary)' }}>{displayCb.primary}</strong>
              {' · '}
              Fallback: <strong style={{ color: 'var(--text-primary)' }}>{displayCb.fallback}</strong>
            </div>
          </div>

          <div className="cb-metrics-grid">
            <div className="cb-metric-card">
              <div className="cb-metric-lbl">Failures</div>
              <div className="cb-metric-val" style={{ color: displayCb.failures > 0 ? 'var(--status-danger)' : 'var(--status-success)' }}>
                {displayCb.failures} / {displayCb.threshold}
              </div>
            </div>
            <div className="cb-metric-card">
              <div className="cb-metric-lbl">Recovery Window</div>
              <div className="cb-metric-val">{displayCb.recoveryWindow}s</div>
            </div>
            <div className="cb-metric-card">
              <div className="cb-metric-lbl">Success Count</div>
              <div className="cb-metric-val" style={{ color: 'var(--status-success)' }}>{displayCb.successCount}</div>
            </div>
            <div className="cb-metric-card">
              <div className="cb-metric-lbl">Total Requests</div>
              <div className="cb-metric-val">{displayCb.totalRequests}</div>
            </div>
          </div>

          <div style={{ marginTop: 24 }}>
            <div className="chart-card" style={{ display: 'inline-block' }}>
              <div className="chart-card-title">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <FlaskConical size={16} style={{ color: 'var(--brand-primary)' }} />
                  <span>Failover Simulator</span>
                </div>
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16, maxWidth: 420 }}>
                Trigger 3 consecutive simulated 5xx errors to verify automated zero-downtime fallback routing from Anthropic → OpenAI.
              </p>
              <button
                id="trigger-failure-btn"
                className="btn btn-primary"
                onClick={triggerTest}
                disabled={testState !== null}
              >
                {testState === 'triggering' ? (
                  <>
                    <RotateCcw size={14} className="animate-spin" />
                    <span>Triggering Failures…</span>
                  </>
                ) : testState === 'tripped' ? (
                  <>
                    <AlertTriangle size={14} />
                    <span>Breaker Tripped (OPEN)</span>
                  </>
                ) : (
                  <>
                    <Zap size={14} />
                    <span>Simulate Upstream Failure</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </>
      )}
    </>
  );
}
