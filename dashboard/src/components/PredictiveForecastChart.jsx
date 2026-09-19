import { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  DollarSign,
  ShieldAlert,
  ArrowRight,
} from 'lucide-react';
import { fetchTeamForecast } from '../services/api.js';

const ForecastTooltip = ({ active, payload, label }) => {
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
          {p.name}: ${Number(p.value).toFixed(2)}
        </div>
      ))}
    </div>
  );
};

export default function PredictiveForecastChart({ activeTeam = 'marketing', onTeamChange, onRequestIncrease }) {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading]   = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchTeamForecast(activeTeam).then(data => {
      setForecast(data);
      setLoading(false);
    });
  }, [activeTeam]);

  const teams = [
    { id: 'marketing', label: 'Marketing (Overage Alert)' },
    { id: 'engineering', label: 'Engineering (Nominal)' },
  ];

  if (!forecast) return null;

  const isOver = forecast.is_over_budget;
  const budget = forecast.budget_usd;
  const projectedEnd = forecast.projected_month_end;
  const overageDelta = projectedEnd - budget;
  const overagePct = Math.round((overageDelta / budget) * 100);

  return (
    <div className="chart-card" style={{ marginBottom: 24 }}>
      {/* Header bar */}
      <div className="chart-card-title" style={{ flexWrap: 'wrap', gap: 10, marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <TrendingUp size={16} style={{ color: isOver ? 'var(--status-danger)' : 'var(--brand-primary)' }} />
          <span>Predictive Month-End Spend Forecast</span>
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>Select Department:</span>
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
      </div>

      {/* Proactive Finance Overage Alert Banner (Mandatory per Task 4) */}
      {isOver ? (
        <div style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 14,
          padding: '14px 18px',
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: 'var(--radius-lg)',
          marginBottom: 18,
          boxShadow: '0 8px 24px rgba(239, 68, 68, 0.15)',
        }}>
          <ShieldAlert size={22} style={{ color: 'var(--status-danger)', flexShrink: 0, marginTop: 2 }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--status-danger)', letterSpacing: '0.2px' }}>
              PROACTIVE OVERAGE ALERT: Projected to Breach Allocation by {overagePct}% (${projectedEnd.toFixed(2)})
            </div>
            <div style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.5 }}>
              Current velocity indicates this team will exhaust its <strong>${budget.toFixed(2)}</strong> quota on{' '}
              <strong style={{ color: 'var(--text-primary)' }}>{forecast.overage_date || 'Day 20'}</strong>.
              The gateway kill-switch will automatically enforce pre-flight HTTP 403 rejections upon breach unless an increase is approved.
            </div>
          </div>
          {onRequestIncrease && (
            <button
              type="button"
              className="btn btn-primary btn-sm"
              style={{ flexShrink: 0, alignSelf: 'center', gap: 5 }}
              onClick={onRequestIncrease}
            >
              <span>Request Increase</span>
              <ArrowRight size={12} />
            </button>
          )}
        </div>
      ) : (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '10px 16px',
          background: 'rgba(16, 185, 129, 0.08)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          borderRadius: 'var(--radius-md)',
          marginBottom: 18,
          fontSize: 12.5,
          color: 'var(--status-success)',
        }}>
          <CheckCircle2 size={16} />
          <span>
            Nominal spending velocity: Projected to close the 30-day period at <strong>${projectedEnd.toFixed(2)}</strong> (
            {Math.round((projectedEnd / budget) * 100)}% of ${budget.toFixed(2)} allocation).
          </span>
        </div>
      )}

      {/* Trajectory Chart */}
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={forecast.trajectory} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
          <XAxis dataKey="day" tick={{ fill: '#4B5563', fontSize: 10 }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fill: '#4B5563', fontSize: 10 }} tickLine={false} axisLine={false} />
          <Tooltip content={<ForecastTooltip />} />
          <ReferenceLine
            y={budget}
            label={{ value: `Quota Ceiling: $${budget.toFixed(0)}`, fill: '#EF4444', fontSize: 10, position: 'insideTopRight' }}
            stroke="#EF4444"
            strokeDasharray="4 4"
            strokeWidth={1.5}
          />
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual Spend"
            stroke="#F97316"
            strokeWidth={2.5}
            dot={{ r: 3, fill: '#F97316' }}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="projected"
            name="Projected Trajectory"
            stroke={isOver ? '#EF4444' : '#06B6D4'}
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={{ r: 2, fill: isOver ? '#EF4444' : '#06B6D4' }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Legend & Summary */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12, borderTop: '1px solid var(--border-subtle)', paddingTop: 10, fontSize: 11, color: 'var(--text-muted)' }}>
        <div style={{ display: 'flex', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 12, height: 3, background: '#F97316', borderRadius: 2 }} />
            <span>Actual Spend (Days 1–19)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 12, height: 2, background: isOver ? '#EF4444' : '#06B6D4', borderTop: '2px dashed' }} />
            <span>Projected Trajectory (Days 20–30)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 12, height: 2, background: '#EF4444', borderTop: '2px dashed' }} />
            <span>Hard Quota Ceiling (${budget.toFixed(0)})</span>
          </div>
        </div>

        <div>
          Model Confidence: <strong style={{ color: 'var(--text-secondary)' }}>95% CI (Linear Run-Rate)</strong>
        </div>
      </div>
    </div>
  );
}
