export default function MetricCard({
  id,
  label,
  value,
  sub,
  sub2,
  valueClass,
  icon: Icon,
  labelIcon,
  delta,
  deltaType,
}) {
  return (
    <div className="metric-card" id={id || undefined}>
      <div className="metric-label">
        {Icon ? (
          <Icon size={14} className="metric-icon" />
        ) : labelIcon ? (
          <span className="metric-icon">{labelIcon}</span>
        ) : null}
        <span>{label}</span>
      </div>
      <div className={`metric-value ${valueClass || ''}`}>{value}</div>
      <div className="metric-sub">
        {delta !== undefined && (
          <span className={`metric-delta ${deltaType || 'up'}`}>{delta}</span>
        )}
        {sub && <span>{sub}</span>}
      </div>
      {sub2 && <div className="metric-sub" style={{ marginTop: 2 }}>{sub2}</div>}
    </div>
  );
}
