import { useState, useEffect } from 'react';
import {
  KeyRound,
  Plus,
  Copy,
  Check,
  Search,
  Shield,
  Clock,
  Sparkles,
  Lock,
  Eye,
  EyeOff,
  MoreVertical,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Sliders,
  Cpu,
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

const PROVIDER_INFO = {
  anthropic: { name: 'Anthropic', color: '#F97316', models: 'Claude 3.5' },
  openai:    { name: 'OpenAI',    color: '#10B981', models: 'GPT-4o' },
  gemini:    { name: 'Gemini',    color: '#8B5CF6', models: 'Gemini 1.5' },
  bedrock:   { name: 'Bedrock',   color: '#06B6D4', models: 'Claude / Titan' },
};

export default function KeysView() {
  const [keys, setKeys]               = useState([]);
  const [search, setSearch]           = useState('');
  const [teamFilter, setTeamFilter]   = useState('all');
  const [showModal, setModal]         = useState(false);
  const [createdKey, setCreatedKey]   = useState(null);
  const [copied, setCopied]           = useState(null);
  const [revealed, setRevealed]       = useState({});
  const [newKey, setNewKey]           = useState({
    name: '',
    team: 'engineering',
    role: 'developer',
    provider: 'anthropic',
    budget: '100',
    rpm: '120',
  });

  useEffect(() => {
    fetchKeys().then(data => {
      // Enrich with provider if not present
      const enriched = data.map((k, i) => ({
        ...k,
        provider: k.provider || (i % 2 === 0 ? 'anthropic' : 'openai'),
        rpm: k.rpm || 120,
        tpm: k.tpm || '100k',
      }));
      setKeys(enriched);
    });
  }, []);

  const handleCopy = (text, id) => {
    navigator.clipboard?.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 1800);
  };

  const toggleReveal = (id) => {
    setRevealed(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleKeyStatus = (id) => {
    setKeys(prev => prev.map(k => k.id === id ? { ...k, active: !k.active } : k));
  };

  const handleCreate = () => {
    const rawSecret = `pk-live-${newKey.team.slice(0, 3)}-${Math.random().toString(36).slice(2, 10)}${Math.random().toString(36).slice(2, 6)}`;
    const created = {
      id: rawSecret,
      name: newKey.name.trim(),
      team: newKey.team,
      role: newKey.role,
      provider: newKey.provider,
      budget: parseFloat(newKey.budget) || 50,
      spent: 0,
      active: true,
      rpm: parseInt(newKey.rpm) || 120,
      tpm: '100k',
      created: new Date().toISOString().slice(0, 10),
    };

    setKeys(prev => [created, ...prev]);
    setCreatedKey(created);
    setModal(false);
    setNewKey({ name: '', team: 'engineering', role: 'developer', provider: 'anthropic', budget: '100', rpm: '120' });
  };

  const filteredKeys = keys.filter(k => {
    const q = search.toLowerCase();
    const matchQ = !q || k.name.toLowerCase().includes(q) || k.id.toLowerCase().includes(q) || k.team.toLowerCase().includes(q);
    const matchTeam = teamFilter === 'all' || k.team === teamFilter;
    return matchQ && matchTeam;
  });

  const totalBudget = keys.reduce((s, k) => s + (k.budget || 0), 0);
  const totalSpent  = keys.reduce((s, k) => s + (k.spent || 0), 0);
  const activeCount = keys.filter(k => k.active).length;

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Virtual Keys</h1>
          <p className="page-subtitle">Scoped gateway credentials with upstream provider routing, budget enforcement, and RBAC policies</p>
        </div>
        <button id="create-key-btn" className="btn btn-primary" onClick={() => setModal(true)}>
          <Plus size={15} />
          <span>Create Virtual Key</span>
        </button>
      </div>

      {/* Portkey-style Top Stats Strip */}
      <div className="stats-info-row">
        <div className="stat-info-item">
          <div className="stat-info-label">Total Keys</div>
          <div className="stat-info-value">{keys.length}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Active Keys</div>
          <div className="stat-info-value" style={{ color: 'var(--status-success)' }}>{activeCount}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Allocated Quota</div>
          <div className="stat-info-value" style={{ color: 'var(--status-cyan)' }}>${totalBudget.toFixed(2)}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Month-To-Date Spend</div>
          <div className="stat-info-value" style={{ color: 'var(--brand-primary)' }}>${totalSpent.toFixed(4)}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Guardrail Policy</div>
          <div className="stat-info-value" style={{ fontSize: 13, fontFamily: 'var(--font-sans)', color: 'var(--status-success)' }}>Pre-Flight Block</div>
        </div>
      </div>

      <div className="table-panel">
        <div className="filter-bar">
          <div className="search-wrap" style={{ maxWidth: 360 }}>
            <Search size={14} className="search-icon" />
            <input
              id="keys-search"
              type="text"
              className="search-input"
              placeholder="Search virtual keys by name, key ID, or team…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          <select
            id="keys-team-filter"
            className="form-select"
            style={{ width: 'auto', padding: '6px 12px', fontSize: 12 }}
            value={teamFilter}
            onChange={e => setTeamFilter(e.target.value)}
          >
            <option value="all">All Teams</option>
            <option value="engineering">Engineering</option>
            <option value="product">Product</option>
            <option value="marketing">Marketing</option>
          </select>

          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Showing {filteredKeys.length} of {keys.length} keys
            </span>
          </div>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Key Name</th>
                <th>Provider Target</th>
                <th>Virtual Key ID</th>
                <th>Team</th>
                <th>Role</th>
                <th>Monthly Budget</th>
                <th>Spend Progress</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredKeys.map(k => {
                const isRevealed = !!revealed[k.id];
                const displayKey = isRevealed
                  ? k.id
                  : `${k.id.slice(0, 10)}••••••••${k.id.slice(-4)}`;
                const pct = Math.min(Math.round(((k.spent || 0) / (k.budget || 1)) * 100), 100);
                const prov = PROVIDER_INFO[k.provider] || { name: k.provider || 'Anthropic', color: '#F97316' };

                return (
                  <tr key={k.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                        <div style={{
                          width: 28,
                          height: 28,
                          borderRadius: 8,
                          background: 'rgba(249, 115, 22, 0.1)',
                          border: '1px solid rgba(249, 115, 22, 0.25)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'var(--brand-primary)',
                          flexShrink: 0,
                        }}>
                          <KeyRound size={14} />
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 13 }}>{k.name}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 1 }}>{k.created || '2026-03-12'}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                        fontSize: 12,
                        fontWeight: 500,
                        color: 'var(--text-secondary)',
                      }}>
                        <span style={{ width: 7, height: 7, borderRadius: '50%', background: prov.color, flexShrink: 0 }} />
                        <span>{prov.name}</span>
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span className="mono" style={{ fontSize: 11.5, color: 'var(--text-secondary)', letterSpacing: '0.2px' }}>
                          {displayKey}
                        </span>
                        <button
                          type="button"
                          className="copy-btn"
                          onClick={() => toggleReveal(k.id)}
                          title={isRevealed ? 'Hide secret' : 'Reveal secret'}
                        >
                          {isRevealed ? <EyeOff size={11} /> : <Eye size={11} />}
                        </button>
                        <button
                          type="button"
                          id={`copy-key-${k.id}`}
                          className="copy-btn"
                          onClick={() => handleCopy(k.id, k.id)}
                          title="Copy Virtual Key"
                        >
                          {copied === k.id ? <Check size={11} style={{ color: 'var(--status-success)' }} /> : <Copy size={11} />}
                        </button>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-default">{k.team}</span>
                    </td>
                    <td>
                      <span className={`badge ${ROLE_CLASS[k.role] || 'badge-default'}`}>
                        {ROLE_LABEL[k.role] || k.role}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span className="mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
                          ${(k.budget || 0).toFixed(2)}
                        </span>
                        <span style={{ fontSize: 10.5, color: 'var(--text-dim)' }}>{k.rpm} RPM</span>
                      </div>
                    </td>
                    <td style={{ minWidth: 130 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4 }}>
                        <span className="mono" style={{ color: pct >= 100 ? 'var(--status-danger)' : 'var(--text-secondary)' }}>
                          ${(k.spent || 0).toFixed(2)}
                        </span>
                        <span style={{ color: 'var(--text-dim)' }}>{pct}%</span>
                      </div>
                      <div className="gauge-track" style={{ height: 4 }}>
                        <div
                          className={`gauge-fill ${pct >= 100 ? 'red' : pct >= 80 ? 'amber' : 'green'}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </td>
                    <td>
                      <button
                        type="button"
                        onClick={() => toggleKeyStatus(k.id)}
                        className={`status-pill ${k.active ? 'healthy' : 'danger'}`}
                        style={{ cursor: 'pointer', userSelect: 'none' }}
                        title="Click to toggle key active status"
                      >
                        <span className={`pulse-dot ${k.active ? '' : 'red'}`} />
                        <span>{k.active ? 'Active' : 'Revoked'}</span>
                      </button>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        style={{ fontSize: 11, padding: '3px 8px' }}
                        onClick={() => handleCopy(k.id, k.id)}
                      >
                        {copied === k.id ? 'Copied' : 'Copy'}
                      </button>
                    </td>
                  </tr>
                );
              })}

              {filteredKeys.length === 0 && (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '48px 20px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                      <KeyRound size={28} style={{ color: 'var(--text-dim)' }} />
                      <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>No virtual keys match the query</span>
                      <span style={{ color: 'var(--text-dim)', fontSize: 12 }}>Create a key or adjust your filter selection</span>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Creation Modal */}
      {showModal && (
        <Modal title="Create Virtual Key" onClose={() => setModal(false)}>
          <div className="form-group">
            <label className="form-label" htmlFor="key-name">Key Friendly Name</label>
            <input
              id="key-name"
              type="text"
              className="form-input"
              placeholder="e.g. Production Customer Bot, QA Gateway Key"
              value={newKey.name}
              onChange={e => setNewKey(p => ({ ...p, name: e.target.value }))}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="key-provider">Upstream Provider Routing</label>
            <select
              id="key-provider"
              className="form-select"
              value={newKey.provider}
              onChange={e => setNewKey(p => ({ ...p, provider: e.target.value }))}
            >
              <option value="anthropic">Anthropic (Claude 3.5 Sonnet / Haiku)</option>
              <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
              <option value="gemini">Google Gemini (Gemini 1.5 Pro / Flash)</option>
              <option value="bedrock">AWS Bedrock (Claude on Bedrock)</option>
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div className="form-group">
              <label className="form-label" htmlFor="key-team">Department / Team</label>
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
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div className="form-group">
              <label className="form-label" htmlFor="key-budget">Monthly Budget Quota ($)</label>
              <input
                id="key-budget"
                type="number"
                className="form-input"
                placeholder="100.00"
                value={newKey.budget}
                onChange={e => setNewKey(p => ({ ...p, budget: e.target.value }))}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="key-rpm">Rate Limit (Requests / Min)</label>
              <input
                id="key-rpm"
                type="number"
                className="form-input"
                placeholder="120"
                value={newKey.rpm}
                onChange={e => setNewKey(p => ({ ...p, rpm: e.target.value }))}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 24 }}>
            <button type="button" className="btn btn-ghost" onClick={() => setModal(false)}>Cancel</button>
            <button
              id="save-key-btn"
              type="button"
              className="btn btn-primary"
              onClick={handleCreate}
              disabled={!newKey.name.trim()}
            >
              Generate Virtual Key
            </button>
          </div>
        </Modal>
      )}

      {/* Secret Key Success Dialog */}
      {createdKey && (
        <Modal title="Virtual Key Created" onClose={() => setCreatedKey(null)}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="alert-banner success" style={{ marginBottom: 0 }}>
              <CheckCircle2 size={16} style={{ color: 'var(--status-success)', flexShrink: 0 }} />
              <div>
                Your virtual key is active and ready for use with the Aperture SDK or OpenAI/Anthropic client.
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Virtual Key Secret</label>
              <div style={{ display: 'flex', gap: 8 }}>
                <input
                  type="text"
                  readOnly
                  className="form-input mono"
                  value={createdKey.id}
                  style={{ background: 'var(--bg-surface-3)', color: 'var(--text-primary)', fontSize: 12 }}
                />
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => handleCopy(createdKey.id, 'new-modal-copy')}
                  style={{ flexShrink: 0 }}
                >
                  {copied === 'new-modal-copy' ? <Check size={14} /> : <Copy size={14} />}
                  <span>{copied === 'new-modal-copy' ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            </div>

            <div style={{
              padding: '12px 14px',
              background: 'var(--bg-surface-2)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 8,
              fontSize: 12,
              color: 'var(--text-secondary)',
              lineHeight: 1.5,
            }}>
              <strong>How to connect:</strong> Set <code style={{ color: 'var(--brand-primary)' }}>Authorization: Bearer {createdKey.id}</code> and point your base URL to <code style={{ color: 'var(--status-cyan)' }}>http://localhost:8080/v1</code>.
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setCreatedKey(null)}
              >
                Done
              </button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
