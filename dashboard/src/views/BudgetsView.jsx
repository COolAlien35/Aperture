import { useState, useEffect } from 'react';
import {
  DollarSign,
  Zap,
  ShieldCheck,
  ShieldAlert,
  Users,
  AlertTriangle,
  ArrowUpRight,
  Lock,
  Plus,
  Sliders,
  Bell,
  CheckCircle2,
  Edit2,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import Modal from '../components/Modal.jsx';
import PlainLanguageSummary from '../components/PlainLanguageSummary.jsx';
import PredictiveForecastChart from '../components/PredictiveForecastChart.jsx';
import BudgetApprovalQueue from '../components/BudgetApprovalQueue.jsx';
import { fetchTeams } from '../services/api.js';

export default function BudgetsView() {
  const [teams, setTeams]                 = useState([]);
  const [showAdjustModal, setAdjustModal] = useState(false);
  const [selectedTeam, setSelectedTeam]   = useState(null);
  const [newBudgetVal, setNewBudgetVal]   = useState('');
  const [activeNarrativeTeam, setActiveNarrative] = useState('engineering');
  const [forecastTeam, setForecastTeam]   = useState('marketing');

  useEffect(() => {
    fetchTeams().then(data => {
      // Enrich with extra model spend distribution and alert policy
      const enriched = data.map(t => ({
        ...t,
        keysCount: t.name === 'Engineering' ? 4 : t.name === 'Product' ? 2 : 1,
        alertSlack: true,
        resetPeriod: 'Monthly (1st of month)',
        modelBreakdown: t.name === 'Engineering'
          ? [{ name: 'Claude 3.5 Sonnet', spend: 5.60 }, { name: 'GPT-4o', spend: 2.80 }]
          : t.name === 'Product'
          ? [{ name: 'GPT-4o-mini', spend: 2.70 }, { name: 'Claude 3.5 Haiku', spend: 1.25 }]
          : [{ name: 'GPT-4o', spend: 24.80 }],
      }));
      setTeams(enriched);
    });
  }, []);

  const totalBudget = teams.reduce((a, t) => a + t.budget, 0);
  const totalSpent  = teams.reduce((a, t) => a + t.spent, 0);
  const totalBlocked = teams.reduce((a, t) => a + t.blocked, 0);
  const remainingBudget = Math.max(totalBudget - totalSpent, 0);

  const gaugeColor = (pct) => {
    if (pct >= 100) return 'red';
    if (pct >= 80) return 'amber';
    return 'green';
  };

  const toggleKillSwitch = (teamId) => {
    setTeams(prev => prev.map(t => t.id === teamId ? { ...t, killSwitch: !t.killSwitch } : t));
  };

  const openAdjust = (t) => {
    setSelectedTeam(t);
    setNewBudgetVal(String(t.budget));
    setAdjustModal(true);
  };

  const saveAdjust = () => {
    if (!selectedTeam) return;
    const parsed = parseFloat(newBudgetVal);
    if (!isNaN(parsed) && parsed > 0) {
      setTeams(prev => prev.map(t => t.id === selectedTeam.id ? { ...t, budget: parsed } : t));
    }
    setAdjustModal(false);
  };

  // Called when an admin approves a budget request in BudgetApprovalQueue!
  const handleBudgetApproved = (teamId, newLimit) => {
    setTeams(prev => prev.map(t => t.id === teamId ? { ...t, budget: newLimit } : t));
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Budgets & Spend Guardrails</h1>
          <p className="page-subtitle">Departmental quota caps, plain-language financial narratives, predictive forecasts, and approval loops</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => {
            const newTeam = {
              id: `team-${Math.random().toString(36).slice(2, 6)}`,
              name: 'Customer Support',
              budget: 50.00,
              spent: 0,
              blocked: 0,
              killSwitch: true,
              keysCount: 1,
              alertSlack: true,
              resetPeriod: 'Monthly (1st of month)',
              modelBreakdown: [{ name: 'GPT-4o-mini', spend: 0 }],
            };
            setTeams(prev => [...prev, newTeam]);
          }}
        >
          <Plus size={15} />
          <span>New Department Quota</span>
        </button>
      </div>

      {/* Kill-switch active warning alert banner */}
      {totalBlocked > 0 && (
        <div className="alert-banner warn">
          <ShieldAlert size={18} style={{ color: 'var(--status-warning)', flexShrink: 0 }} />
          <div>
            <strong>Budget Guard Active: {totalBlocked} upstream requests blocked</strong> at the Aperture gateway. Pre-flight quota check prevented credit overruns, saving approximately ${(totalBlocked * 0.018).toFixed(4)} in unbudgeted LLM API costs.
          </div>
        </div>
      )}

      {/* Top Stats Strip */}
      <div className="stats-info-row">
        <div className="stat-info-item">
          <div className="stat-info-label">Total Org Budget</div>
          <div className="stat-info-value" style={{ color: 'var(--status-cyan)' }}>${totalBudget.toFixed(2)}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Total Spend (MTD)</div>
          <div className="stat-info-value" style={{ color: 'var(--brand-primary)' }}>${totalSpent.toFixed(4)}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Remaining Pool</div>
          <div className="stat-info-value" style={{ color: 'var(--status-success)' }}>${remainingBudget.toFixed(2)}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Pre-Flight Blocked</div>
          <div className="stat-info-value" style={{ color: totalBlocked > 0 ? 'var(--status-danger)' : 'var(--text-primary)' }}>
            {totalBlocked} reqs
          </div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Guardrail Mode</div>
          <div className="stat-info-value" style={{ fontSize: 13, fontFamily: 'var(--font-sans)', color: 'var(--status-success)' }}>
            Hard-Stop (403)
          </div>
        </div>
      </div>

      {/* Plain-Language Narrative Component (Task 1) */}
      <PlainLanguageSummary
        activeTeam={activeNarrativeTeam}
        onTeamChange={setActiveNarrative}
      />

      {/* Predictive Forecast Chart (Task 4) */}
      <PredictiveForecastChart
        activeTeam={forecastTeam}
        onTeamChange={setForecastTeam}
      />

      {/* Team Budget Cards Grid */}
      <div className="section-header">
        <div className="section-title">
          <Users size={14} style={{ color: 'var(--brand-primary)' }} />
          <span>Departmental Quota Allocations</span>
        </div>
      </div>

      <div className="budget-grid">
        {teams.map(t => {
          const pct = Math.min(Math.round((t.spent / (t.budget || 1)) * 100), 100);
          const colorClass = gaugeColor(pct);

          return (
            <div key={t.id} className="budget-card">
              <div className="budget-card-header">
                <div>
                  <div className="budget-team-name">
                    <div style={{
                      width: 24,
                      height: 24,
                      borderRadius: 6,
                      background: 'rgba(249, 115, 22, 0.12)',
                      border: '1px solid rgba(249, 115, 22, 0.25)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--brand-primary)',
                      flexShrink: 0,
                    }}>
                      <Users size={13} />
                    </div>
                    <span>{t.name}</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
                    {t.keysCount} active virtual key{t.keysCount !== 1 ? 's' : ''} · {t.resetPeriod}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    style={{ padding: '3px 8px', fontSize: 11 }}
                    onClick={() => openAdjust(t)}
                    title="Edit monthly quota"
                  >
                    <Edit2 size={11} />
                    <span>Adjust</span>
                  </button>
                </div>
              </div>

              {/* Big Spend Figure */}
              <div style={{ marginTop: 8, marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 26, color: 'var(--text-primary)', letterSpacing: '-0.5px' }}>
                    ${t.spent.toFixed(2)}
                  </span>
                  <span style={{ fontSize: 13, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    / ${t.budget.toFixed(2)}
                  </span>
                  <span
                    className={`badge badge-${colorClass === 'red' ? 'danger' : colorClass === 'amber' ? 'warning' : 'success'}`}
                    style={{ marginLeft: 'auto', fontSize: 11 }}
                  >
                    {pct}%
                  </span>
                </div>
              </div>

              {/* Progress bar with thresholds */}
              <div className="gauge-track" style={{ height: 6, position: 'relative' }}>
                <div className={`gauge-fill ${colorClass}`} style={{ width: `${pct}%` }} />
              </div>

              {/* Threshold indicator row */}
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-dim)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
                <span>$0</span>
                <span>50%</span>
                <span style={{ color: 'var(--status-warning)' }}>80% Alert</span>
                <span style={{ color: 'var(--status-danger)' }}>100% Stop</span>
              </div>

              {/* Model spend mini-breakdown */}
              {t.modelBreakdown && t.modelBreakdown.length > 0 && (
                <div style={{
                  marginTop: 14,
                  padding: '10px 12px',
                  background: 'var(--bg-surface-2)',
                  borderRadius: 8,
                  border: '1px solid var(--border-subtle)',
                }}>
                  <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '0.6px', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: 6 }}>
                    Spend by Model
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {t.modelBreakdown.map(m => (
                      <div key={m.name} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11.5 }}>
                        <span style={{ color: 'var(--text-secondary)' }}>{m.name}</span>
                        <span className="mono" style={{ color: 'var(--text-primary)' }}>${m.spend.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Kill-switch control row */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginTop: 14,
                paddingTop: 12,
                borderTop: '1px solid var(--border-subtle)',
                fontSize: 12,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Bell size={12} style={{ color: 'var(--text-dim)' }} />
                  <span style={{ color: 'var(--text-muted)' }}>Pre-Flight Kill-Switch</span>
                </div>
                <button
                  type="button"
                  onClick={() => toggleKillSwitch(t.id)}
                  className={`status-pill ${t.killSwitch ? 'healthy' : 'warning'}`}
                  style={{ cursor: 'pointer', userSelect: 'none', padding: '2px 8px', fontSize: 11 }}
                  title="Click to toggle budget kill-switch"
                >
                  <span className={`pulse-dot ${t.killSwitch ? '' : 'amber'}`} />
                  <span>{t.killSwitch ? 'ARMED' : 'OFF'}</span>
                </button>
              </div>

              {/* Blocked info */}
              {t.blocked > 0 && (
                <div style={{
                  marginTop: 10,
                  padding: '8px 10px',
                  borderRadius: 6,
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  fontSize: 11.5,
                  color: 'var(--status-danger)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}>
                  <AlertTriangle size={13} style={{ flexShrink: 0 }} />
                  <span>{t.blocked} requests blocked due to quota breach</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Budget Request / Approval Workflow Queue (Task 2) */}
      <BudgetApprovalQueue
        teams={teams}
        onBudgetUpdated={handleBudgetApproved}
      />

      {/* Adjust Budget Modal */}
      {showAdjustModal && selectedTeam && (
        <Modal title={`Adjust Budget: ${selectedTeam.name}`} onClose={() => setAdjustModal(false)}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="form-group">
              <label className="form-label" htmlFor="adjust-budget-input">Monthly Quota ($ USD)</label>
              <input
                id="adjust-budget-input"
                type="number"
                step="5"
                className="form-input"
                value={newBudgetVal}
                onChange={e => setNewBudgetVal(e.target.value)}
              />
            </div>

            <div style={{
              padding: '12px 14px',
              background: 'var(--bg-surface-2)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 8,
              fontSize: 12,
              color: 'var(--text-secondary)',
            }}>
              Current MTD spend is <strong style={{ color: 'var(--brand-primary)' }}>${selectedTeam.spent.toFixed(2)}</strong>.
              Setting a quota below this value will immediately arm the kill-switch and return HTTP 403 to inbound requests with matching keys.
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 12 }}>
              <button type="button" className="btn btn-ghost" onClick={() => setAdjustModal(false)}>Cancel</button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={saveAdjust}
              >
                Save Quota
              </button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
