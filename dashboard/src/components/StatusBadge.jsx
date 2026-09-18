export default function StatusBadge({ status }) {
  if (status === 200 || status === 'success' || status === 'active') {
    return <span className="badge badge-success">✓ {status === 200 ? '200 OK' : status === 'active' ? 'Active' : 'Success'}</span>;
  }
  if (status === 403 || status === 'blocked' || status === 'revoked') {
    return <span className="badge badge-danger">✕ {status === 403 ? 'BLOCKED' : status === 'revoked' ? 'Revoked' : 'Blocked'}</span>;
  }
  if (status === 429) {
    return <span className="badge badge-warning">⚠ 429 Rate</span>;
  }
  if (status === 500) {
    return <span className="badge badge-danger">✕ 500 Error</span>;
  }
  if (status === 'CLOSED') {
    return <span className="badge badge-success">● CLOSED</span>;
  }
  if (status === 'OPEN') {
    return <span className="badge badge-danger">● OPEN</span>;
  }
  if (status === 'HALF-OPEN') {
    return <span className="badge badge-warning">◐ HALF-OPEN</span>;
  }
  return <span className="badge badge-default">{status}</span>;
}
