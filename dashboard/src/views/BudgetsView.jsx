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
} from 'lucide-react';
import { fetchTeams } from '../services/api.js';

export default function BudgetsView() {
  const [teams, setTeams] = useState([]);

  useEffect(() => {
    fetchTeams().then(setTeams);
  }, []);

  const totalBudget = teams.reduce((a, t) => a + t.budget, 0);
  const totalSpent  = teams.reduce((a, t) => a + t.spent, 0);
  const totalBlocked = teams.reduce((a, t) => a + t.blocked, 0);

  const gaugeColor = (pct) => {
    if (pct >= 100) return 'red';
    if (pct >= 80) return 'amber';
    return 'green';
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Team Budgets & Kill-Switches</h1>
          <p className="page-subtitle">Monitor spend against departmental quotas with gateway-enforced budget circuit breakers</p>
        </div>
      </div>

      {/* Kill-switch alert */}
      {totalBlocked > 0 && (
        <div className="alert-banner warn">
          <ShieldAlert size={18} style={{ color: 'var(--status-warning)', flexShrink: 0 }} />
          <div>
            <strong>{totalBlocked} requests blocked</strong> at the Aperture gateway — upstream LLM API calls were terminated pre-flight, saving an estimated ${(totalBlocked * 0.015).toFixed(4)}.
          </div>
        </div>
      )}

      {/* Org-level metric row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 24 }}>
        <div className="metric-card">
          <div className="metric-label">
            <DollarSign size={14} className="metric-icon" />
            <span>Total Org Budget</span>
          </div>
          <div className="metric-value orange" style={{ fontFamily: 'var(--font-mono)' }}>${totalBudget.toFixed(2)}</div>
          <div className="metric-sub">{teams.length} teams allocated</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">
            <Zap size={14} className="metric-icon" />
            <span>Total Org Spend</span>
          </div>
          <div className="metric-value" style={{ fontFamily: 'var(--font-mono)' }}>${totalSpent.toFixed(4)}</div>
          <div className="metric-sub">
            <span className="metric-delta up">{((totalSpent / totalBudget) * 100).toFixed(1)}% used</span>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">
            <ShieldCheck size={14} className="metric-icon" />
            <span>Blocked Requests</span>
          </div>
          <div className="metric-value" style={{ color: totalBlocked > 0 ? 'var(--status-danger)' : 'var(--status-success)', fontFamily: 'var(--font-mono)' }}>
            {totalBlocked}
          </div>
          <div className="metric-sub">Gateway kill-switch enforced</div>
        </div>
      </div>

      {/* Team cards */}
      <div className="budget-grid">
        {teams.map(t => {
          const pct = Math.min(Math.round((t.spent / t.budget) * 100), 100);
          const colorClass = gaugeColor(pct);

          return (
            <div key={t.id} className="budget-card">
              <div className="budget-card-header">
                <div>
                  <div className="budget-team-name">
                    <Users size={14} style={{ color: 'var(--text-muted)' }} />
                    <span>{t.name}</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
                    Quota: ${t.budget.toFixed(2)} / month
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 16, color: 'var(--text-primary)' }}>
                    ${t.spent.toFixed(2)}
                  </div>
                  <span className={`badge badge-${colorClass === 'red' ? 'danger' : colorClass === 'amber' ? 'orange' : 'green'}`} style={{ fontSize: 10 }}>
                    {pct}% consumed
                  </span>
                </div>
              </div>

              {/* Progress bar */}
              <div className="gauge-track" style={{ height: 8, marginTop: 14 }}>
                <div className={`gauge-fill ${colorClass}`} style={{ width: `${pct}%` }} />
              </div>

              {/* Kill-switch row */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--border-subtle)', fontSize: 12 }}>
                <span style={{ color: 'var(--text-muted)' }}>Auto Kill-Switch:</span>
                <span style={{ color: t.killSwitch ? 'var(--status-success)' : 'var(--text-dim)', fontWeight: 600 }}>
                  {t.killSwitch ? '● ARMED (100%)' : '○ DISABLED'}
                </span>
              </div>

              {t.blocked > 0 && (
                <div style={{ marginTop: 8, fontSize: 11.5, color: 'var(--status-danger)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <AlertTriangle size={13} />
                  <span>{t.blocked} requests blocked due to budget exhaustion</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </>
  );
}
