import { useState, useEffect } from 'react';
import {
  Sparkles,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  ArrowRight,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { fetchTeamSummary } from '../services/api.js';

/**
 * Fintech-style plain-language narrative template engine.
 * Generates clear, non-technical executive sentences without jargon.
 */
function generateNarrative(data) {
  if (!data) return '';

  const {
    team_name,
    total_spend_usd,
    budget_usd,
    pct_budget_used,
    top_model,
    top_model_pct,
    trend_direction,
    trend_pct,
    daily_burn_usd,
    projected_month_end_usd,
    projected_pct_of_budget,
  } = data;

  const spendStr = `$${total_spend_usd.toFixed(2)}`;
  const budgetStr = `$${budget_usd.toFixed(0)}`;
  const trendStr = `${trend_pct}%`;

  if (pct_budget_used >= 90 || projected_pct_of_budget >= 100) {
    return (
      <>
        <strong>{team_name}</strong> spent <span className="highlight-val">{spendStr}</span> this month (
        <span className="highlight-danger">{pct_budget_used.toFixed(0)}% of {budgetStr} quota</span>), with{' '}
        <span className="highlight-val">{top_model_pct}%</span> concentrated on <strong>{top_model}</strong>,{' '}
        <span className="highlight-warn">trending to exceed quota in ~18 hours</span> at {trendStr} acceleration.
      </>
    );
  }

  if (trend_direction === 'down') {
    return (
      <>
        <strong>{team_name}</strong> spent <span className="highlight-val">{spendStr}</span> this month (
        {pct_budget_used.toFixed(0)}% of {budgetStr} quota), with <span className="highlight-val">{top_model_pct}%</span> on{' '}
        <strong>{top_model}</strong>, <span className="highlight-success">down {trendStr}</span> from last period as caching and prompt compression lowered costs.
      </>
    );
  }

  return (
    <>
      <strong>{team_name}</strong> spent <span className="highlight-val">{spendStr}</span> this month (
      {pct_budget_used.toFixed(0)}% of {budgetStr} quota), with <span className="highlight-val">{top_model_pct}%</span> on{' '}
      <strong>{top_model}</strong>, <span className="highlight-val">up {trendStr}</span> from last period at a stable run rate of ${daily_burn_usd.toFixed(2)}/day.
    </>
  );
}

export default function PlainLanguageSummary({ activeTeam = 'engineering', onTeamChange, onRequestIncrease }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchTeamSummary(activeTeam).then(data => {
      setSummary(data);
      setLoading(false);
    });
  }, [activeTeam]);

  const teams = [
    { id: 'engineering', label: 'Engineering' },
    { id: 'product', label: 'Product' },
    { id: 'marketing', label: 'Marketing' },
  ];

  const isWarning = summary?.pct_budget_used >= 85 || summary?.projected_pct_of_budget >= 100;

  return (
    <div className="plain-summary-card" style={{
      background: 'linear-gradient(145deg, rgba(28, 32, 42, 0.9) 0%, rgba(17, 19, 24, 0.95) 100%)',
      border: isWarning ? '1px solid rgba(245, 158, 11, 0.35)' : '1px solid var(--border-active)',
      borderRadius: 'var(--radius-xl)',
      padding: '24px 28px',
      marginBottom: 24,
      boxShadow: isWarning ? '0 12px 36px rgba(245, 158, 11, 0.12)' : '0 12px 32px rgba(0, 0, 0, 0.5)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Background ambient gradient */}
      <div style={{
        position: 'absolute',
        top: -60,
        right: -60,
        width: 180,
        height: 180,
        borderRadius: '50%',
        background: isWarning ? 'radial-gradient(circle, rgba(245, 158, 11, 0.15) 0%, transparent 70%)' : 'radial-gradient(circle, rgba(249, 115, 22, 0.12) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      {/* Header bar: badge + team selector tabs */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '4px 10px',
            borderRadius: 99,
            background: 'rgba(249, 115, 22, 0.15)',
            border: '1px solid rgba(249, 115, 22, 0.3)',
            color: 'var(--brand-primary)',
            fontSize: 11.5,
            fontWeight: 700,
            letterSpacing: '0.4px',
            textTransform: 'uppercase',
          }}>
            <Sparkles size={12} />
            <span>Fintech Executive Spend Narrative</span>
          </div>

          <span style={{ fontSize: 11.5, color: 'var(--text-dim)' }}>
            Plain-language translation for finance & leadership
          </span>
        </div>

        {/* Team switcher pills */}
        <div className="time-filter-group" style={{ background: 'var(--bg-surface-2)' }}>
          {teams.map(t => (
            <button
              key={t.id}
              type="button"
              className={`time-filter-btn ${activeTeam === t.id ? 'active' : ''}`}
              onClick={() => onTeamChange && onTeamChange(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Primary Narrative Hero Sentence */}
      <div style={{
        fontSize: 19,
        lineHeight: 1.5,
        color: 'var(--text-primary)',
        fontWeight: 450,
        letterSpacing: '-0.2px',
        marginBottom: 18,
      }}>
        {loading ? (
          <span style={{ color: 'var(--text-muted)' }}>Synthesizing financial telemetry…</span>
        ) : (
          generateNarrative(summary)
        )}
      </div>

      {/* Three Executive Key Takeaways */}
      {summary && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 12,
          paddingTop: 16,
          borderTop: '1px solid var(--border-subtle)',
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
            <Zap size={14} style={{ color: 'var(--brand-primary)', marginTop: 2, flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-dim)' }}>
                Primary Cost Driver
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 1 }}>
                <strong>{summary.top_model}</strong> ({summary.top_model_pct}% of tokens)
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
            <TrendingUp size={14} style={{ color: isWarning ? 'var(--status-warning)' : 'var(--status-cyan)', marginTop: 2, flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-dim)' }}>
                Current Trajectory
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 1 }}>
                ${summary.daily_burn_usd.toFixed(2)}/day &rarr; ~${summary.projected_month_end_usd.toFixed(2)} month-end
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
            <ShieldCheck size={14} style={{ color: 'var(--status-success)', marginTop: 2, flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-dim)' }}>
                Guardrail Status
              </div>
              <div style={{ fontSize: 12.5, color: isWarning ? 'var(--status-warning)' : 'var(--status-success)', marginTop: 1, fontWeight: 500 }}>
                {isWarning ? 'Kill-switch trigger imminent' : 'Healthy (Under allocation)'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
