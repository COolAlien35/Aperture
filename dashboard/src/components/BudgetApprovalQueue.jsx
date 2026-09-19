import { useState, useEffect } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowUpRight,
  Plus,
  Send,
  User,
  MessageSquare,
  AlertCircle,
  Filter,
} from 'lucide-react';
import Modal from './Modal.jsx';
import { fetchBudgetRequests, submitBudgetRequest, reviewBudgetRequest } from '../services/api.js';

export default function BudgetApprovalQueue({ teams = [], onBudgetUpdated }) {
  const [requests, setRequests]           = useState([]);
  const [filter, setFilter]               = useState('pending'); // 'all' | 'pending' | 'approved' | 'denied'
  const [showRequestModal, setReqModal]   = useState(false);
  const [submitting, setSubmitting]       = useState(false);
  const [reviewingId, setReviewingId]     = useState(null);

  // Form state
  const [formTeam, setFormTeam]           = useState('engineering');
  const [formRequestedBudget, setFormReq] = useState('');
  const [formReason, setFormReason]       = useState('');
  const [formEmail, setFormEmail]         = useState('alex.dev@aperture.io');

  useEffect(() => {
    fetchBudgetRequests().then(setRequests);
  }, []);

  const activeTeamObj = teams.find(t => t.id === formTeam) || teams[0];
  const currentBudget = activeTeamObj ? activeTeamObj.budget : 100.00;

  const handleSubmitRequest = async (e) => {
    e.preventDefault();
    if (!formReason.trim() || !formRequestedBudget) return;

    setSubmitting(true);
    try {
      const payload = {
        team_id: formTeam,
        team_name: activeTeamObj?.name || formTeam,
        requested_by: formEmail,
        current_budget_usd: currentBudget,
        requested_budget_usd: parseFloat(formRequestedBudget),
        reason: formReason.trim(),
        status: 'pending',
        timestamp: new Date().toISOString(),
      };

      const result = await submitBudgetRequest(payload);
      setRequests(prev => [result, ...prev]);
      setReqModal(false);
      setFormReason('');
      setFormReq('');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReview = async (req, action) => {
    setReviewingId(req.id);
    try {
      await reviewBudgetRequest(req.id, action);
      setRequests(prev => prev.map(r => r.id === req.id ? { ...r, status: action === 'approve' ? 'approved' : 'denied', reviewed_by: 'Current User (Admin)' } : r));

      // If approved, notify parent to immediately update live team budget allocation!
      if (action === 'approve' && onBudgetUpdated) {
        onBudgetUpdated(req.team_id, req.requested_budget_usd);
      }
    } finally {
      setReviewingId(null);
    }
  };

  const filteredRequests = requests.filter(r => {
    if (filter === 'all') return true;
    return r.status === filter;
  });

  const pendingCount = requests.filter(r => r.status === 'pending').length;

  return (
    <div className="table-panel" style={{ marginTop: 24 }}>
      {/* Header */}
      <div className="table-panel-header" style={{ flexWrap: 'wrap', gap: 12 }}>
        <div className="table-panel-title">
          <Clock size={15} style={{ color: 'var(--brand-primary)' }} />
          <span>Budget Approval Workflow & Requests</span>
          {pendingCount > 0 && (
            <span className="badge badge-warning" style={{ fontSize: 10.5, marginLeft: 6 }}>
              {pendingCount} Pending Review
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Status filter pills */}
          <div className="time-filter-group" style={{ background: 'var(--bg-surface-2)' }}>
            <button
              type="button"
              className={`time-filter-btn ${filter === 'pending' ? 'active' : ''}`}
              onClick={() => setFilter('pending')}
            >
              Pending ({pendingCount})
            </button>
            <button
              type="button"
              className={`time-filter-btn ${filter === 'approved' ? 'active' : ''}`}
              onClick={() => setFilter('approved')}
            >
              Approved
            </button>
            <button
              type="button"
              className={`time-filter-btn ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              All Requests
            </button>
          </div>

          <button
            type="button"
            className="btn btn-secondary btn-sm"
            style={{ gap: 5 }}
            onClick={() => setReqModal(true)}
          >
            <Plus size={13} />
            <span>Request Budget Increase</span>
          </button>
        </div>
      </div>

      {/* Requests table */}
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Status</th>
              <th>Department / Team</th>
              <th>Requested By</th>
              <th>Current Limit</th>
              <th>Requested Limit</th>
              <th>Required Business Justification</th>
              <th>Submitted</th>
              <th>Admin Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredRequests.map(r => {
              const delta = r.requested_budget_usd - r.current_budget_usd;
              const isPending = r.status === 'pending';

              return (
                <tr key={r.id}>
                  <td>
                    {r.status === 'approved' ? (
                      <span className="badge badge-success" style={{ fontSize: 10.5 }}>
                        <CheckCircle2 size={11} /> Approved
                      </span>
                    ) : r.status === 'denied' ? (
                      <span className="badge badge-danger" style={{ fontSize: 10.5 }}>
                        <XCircle size={11} /> Denied
                      </span>
                    ) : (
                      <span className="badge badge-warning" style={{ fontSize: 10.5 }}>
                        <Clock size={11} /> Pending
                      </span>
                    )}
                  </td>
                  <td>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{r.team_name}</span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
                      <User size={12} style={{ color: 'var(--text-dim)' }} />
                      <span className="mono" style={{ color: 'var(--text-secondary)' }}>{r.requested_by}</span>
                    </div>
                  </td>
                  <td className="mono">${r.current_budget_usd.toFixed(2)}</td>
                  <td>
                    <span className="mono" style={{ fontWeight: 700, color: 'var(--brand-primary)' }}>
                      ${r.requested_budget_usd.toFixed(2)}
                    </span>
                    <span style={{ fontSize: 10.5, color: 'var(--status-success)', marginLeft: 4 }}>
                      (+${delta.toFixed(0)})
                    </span>
                  </td>
                  <td style={{ maxWidth: 320 }}>
                    <div style={{
                      fontSize: 12,
                      color: 'var(--text-secondary)',
                      lineHeight: 1.4,
                      whiteSpace: 'normal',
                      wordBreak: 'break-word',
                    }}>
                      &ldquo;{r.reason}&rdquo;
                    </div>
                  </td>
                  <td style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                    {new Date(r.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td>
                    {isPending ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <button
                          type="button"
                          className="btn btn-primary btn-sm"
                          style={{ padding: '3px 9px', fontSize: 11 }}
                          onClick={() => handleReview(r, 'approve')}
                          disabled={reviewingId === r.id}
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          style={{ padding: '3px 9px', fontSize: 11 }}
                          onClick={() => handleReview(r, 'deny')}
                          disabled={reviewingId === r.id}
                        >
                          Deny
                        </button>
                      </div>
                    ) : (
                      <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                        {r.reviewed_by || 'Reviewed'}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}

            {filteredRequests.length === 0 && (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '36px 20px', color: 'var(--text-muted)' }}>
                  No budget requests found for active filter &ldquo;{filter}&rdquo;.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* "Request Budget Increase" Modal */}
      {showRequestModal && (
        <Modal title="Request Departmental Budget Increase" onClose={() => setReqModal(false)}>
          <form onSubmit={handleSubmitRequest} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="form-group">
              <label className="form-label" htmlFor="req-team-select">Department / Team</label>
              <select
                id="req-team-select"
                className="form-select"
                value={formTeam}
                onChange={e => setFormTeam(e.target.value)}
              >
                {teams.map(t => (
                  <option key={t.id} value={t.id}>{t.name} (Current: ${t.budget.toFixed(2)})</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="form-group">
                <label className="form-label">Current Monthly Limit</label>
                <input
                  type="text"
                  readOnly
                  className="form-input mono"
                  value={`$${currentBudget.toFixed(2)}`}
                  style={{ background: 'var(--bg-surface-3)', color: 'var(--text-secondary)' }}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="req-new-budget">Requested New Limit ($)</label>
                <input
                  id="req-new-budget"
                  type="number"
                  step="10"
                  min={currentBudget + 1}
                  required
                  placeholder={`> ${currentBudget.toFixed(0)}`}
                  className="form-input mono"
                  value={formRequestedBudget}
                  onChange={e => setFormReq(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="req-email">Requester Email</label>
              <input
                id="req-email"
                type="email"
                required
                className="form-input mono"
                value={formEmail}
                onChange={e => setFormEmail(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="req-reason">
                Business Justification Reason <span style={{ color: 'var(--status-danger)' }}>*</span>
              </label>
              <textarea
                id="req-reason"
                required
                rows={3}
                className="form-input"
                style={{ resize: 'vertical', minHeight: 70 }}
                placeholder="Explain why this increase is needed (e.g. new agent workload, model benchmark evaluation, campaign launch)..."
                value={formReason}
                onChange={e => setFormReason(e.target.value)}
              />
              <span style={{ fontSize: 10.5, color: 'var(--text-dim)' }}>
                Required per Person B budget governance policy. Reviewed by organization admins.
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 12 }}>
              <button type="button" className="btn btn-ghost" onClick={() => setReqModal(false)}>Cancel</button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={submitting || !formReason.trim() || !formRequestedBudget}
              >
                <Send size={13} />
                <span>Submit Request</span>
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
