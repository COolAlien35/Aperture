import { useState, useEffect } from 'react';
import {
  KeyRound,
  Plus,
  Copy,
  Check,
  Search,
  Filter,
  Shield,
  Layers,
  Clock,
  Sparkles,
  Lock,
} from 'lucide-react';
import Modal from '../components/Modal.jsx';
import StatusBadge from '../components/StatusBadge.jsx';
import { fetchKeys } from '../services/api.js';

const ROLE_CLASS = {
  admin:     'badge-purple',
  team_lead: 'badge-cyan',
  developer: 'badge-default',
};

const ROLE_LABEL = {
  admin:     'Admin',
  team_lead: 'Team Lead',
  developer: 'Developer',
};

export default function KeysView() {
  const [keys, setKeys]         = useState([]);
  const [search, setSearch]     = useState('');
  const [showModal, setModal]   = useState(false);
  const [newKey, setNewKey]     = useState({ name: '', team: 'engineering', role: 'developer', budget: '' });
  const [copied, setCopied]     = useState(null);

  useEffect(() => {
    fetchKeys().then(setKeys);
  }, []);

  const handleCopy = (keyId) => {
    navigator.clipboard?.writeText(keyId);
    setCopied(keyId);
    setTimeout(() => setCopied(null), 1500);
  };

  const handleCreate = () => {
    const fake = {
      id: `sk-gw-${newKey.team.slice(0, 3)}-${Math.random().toString(36).slice(2, 6)}`,
      name: newKey.name,
      team: newKey.team,
      role: newKey.role,
      budget: parseFloat(newKey.budget) || 50,
      spent: 0,
      active: true,
      created: new Date().toISOString().slice(0, 10),
    };
    setKeys(prev => [fake, ...prev]);
    setModal(false);
    setNewKey({ name: '', team: 'engineering', role: 'developer', budget: '' });
  };

  const filteredKeys = keys.filter(k =>
    !search ||
    k.name.toLowerCase().includes(search.toLowerCase()) ||
    k.id.toLowerCase().includes(search.toLowerCase()) ||
    k.team.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Virtual Keys & RBAC</h1>
          <p className="page-subtitle">Manage scoped gateway keys, team assignments, model access, and monthly budget limits</p>
        </div>
        <button id="create-key-btn" className="btn btn-primary" onClick={() => setModal(true)}>
          <Plus size={15} />
          <span>Create Virtual Key</span>
        </button>
      </div>

      <div className="table-panel">
        <div className="filter-bar">
          <div className="search-wrap">
            <Search size={14} className="search-icon" />
            <input
              id="keys-search"
              type="text"
              className="search-input"
              placeholder="Search keys by name, ID, or team…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {filteredKeys.length} of {keys.length} keys active
            </span>
          </div>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Key Name</th>
                <th>Virtual Key ID</th>
                <th>Team</th>
                <th>RBAC Role</th>
                <th>Monthly Budget</th>
                <th>Current Spend</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredKeys.map(k => (
                <tr key={k.id}>
                  <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <KeyRound size={14} style={{ color: 'var(--brand-primary)', flexShrink: 0 }} />
                      <span>{k.name}</span>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span className="mono" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                        {k.id.substring(0, 16)}…
                      </span>
                      <button
                        className="copy-btn"
                        id={`copy-key-${k.id}`}
                        onClick={() => handleCopy(k.id)}
                        title="Copy key ID"
                      >
                        {copied === k.id ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                      </button>
                    </div>
                  </td>
                  <td><span className="badge badge-default">{k.team}</span></td>
                  <td><span className={`badge ${ROLE_CLASS[k.role] || 'badge-default'}`}>{ROLE_LABEL[k.role] || k.role}</span></td>
                  <td className="mono">${k.budget.toFixed(2)}</td>
                  <td className="mono" style={{ color: k.spent >= k.budget ? 'var(--status-danger)' : 'inherit' }}>
                    ${k.spent.toFixed(4)}
                  </td>
                  <td>
                    <span className={`status-pill ${k.active ? 'healthy' : 'danger'}`}>
                      <span className={`pulse-dot ${k.active ? '' : 'red'}`} />
                      <span>{k.active ? 'Active' : 'Disabled'}</span>
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn btn-ghost btn-sm"
                      style={{ fontSize: 11, padding: '3px 8px' }}
                      onClick={() => handleCopy(k.id)}
                    >
                      {copied === k.id ? 'Copied' : 'Copy Key'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <Modal title="Create Virtual Key" onClose={() => setModal(false)}>
          <div className="form-group">
            <label className="form-label" htmlFor="key-name">Key Name</label>
            <input
              id="key-name"
              type="text"
              className="form-input"
              placeholder="e.g. Production Web App"
              value={newKey.name}
              onChange={e => setNewKey(p => ({ ...p, name: e.target.value }))}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="key-team">Team</label>
            <select
              id="key-team"
              className="form-select"
              value={newKey.team}
              onChange={e => setNewKey(p => ({ ...p, team: e.target.value }))}
            >
              <option value="engineering">Engineering</option>
              <option value="product">Product</option>
              <option value="marketing">Marketing</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="key-role">RBAC Role</label>
            <select
              id="key-role"
              className="form-select"
              value={newKey.role}
              onChange={e => setNewKey(p => ({ ...p, role: e.target.value }))}
            >
              <option value="developer">Developer</option>
              <option value="team_lead">Team Lead</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="key-budget">Monthly Budget Limit ($)</label>
            <input
              id="key-budget"
              type="number"
              className="form-input"
              placeholder="e.g. 100.00"
              value={newKey.budget}
              onChange={e => setNewKey(p => ({ ...p, budget: e.target.value }))}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 24 }}>
            <button className="btn btn-ghost" onClick={() => setModal(false)}>Cancel</button>
            <button
              id="save-key-btn"
              className="btn btn-primary"
              onClick={handleCreate}
              disabled={!newKey.name.trim()}
            >
              Create Key
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
