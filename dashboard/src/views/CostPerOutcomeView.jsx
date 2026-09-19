import { useState, useEffect } from 'react';
import {
  GitPullRequest,
  ExternalLink,
  DollarSign,
  Clock,
  FileCode2,
  Search,
  User,
  Info,
  ArrowUpDown,
  Sparkles,
  CheckCircle2,
  TrendingDown,
  Layers,
} from 'lucide-react';
import { fetchPRCorrelations } from '../services/api.js';

export default function CostPerOutcomeView() {
  const [prs, setPrs]           = useState([]);
  const [search, setSearch]     = useState('');
  const [sortBy, setSortBy]     = useState('cost-desc'); // 'cost-desc' | 'cost-asc' | 'time-desc' | 'files-desc'
  const [loading, setLoading]   = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchPRCorrelations().then(data => {
      setPrs(data);
      setLoading(false);
    });
  }, []);

  const filtered = prs
    .filter(p => {
      const q = search.toLowerCase();
      return (
        !q ||
        p.pr_title.toLowerCase().includes(q) ||
        p.author.toLowerCase().includes(q) ||
        String(p.pr_number).includes(q)
      );
    })
    .sort((a, b) => {
      if (sortBy === 'cost-desc') return b.total_ai_cost_usd - a.total_ai_cost_usd;
      if (sortBy === 'cost-asc') return a.total_ai_cost_usd - b.total_ai_cost_usd;
      if (sortBy === 'time-desc') return b.time_to_merge_hours - a.time_to_merge_hours;
      if (sortBy === 'files-desc') return b.files_changed - a.files_changed;
      return 0;
    });

  const totalCost = prs.reduce((s, p) => s + p.total_ai_cost_usd, 0);
  const avgCost = prs.length ? totalCost / prs.length : 0;
  const avgMergeHours = prs.length
    ? (prs.reduce((s, p) => s + p.time_to_merge_hours, 0) / prs.length).toFixed(1)
    : 0;
  const maxCost = prs.length ? Math.max(...prs.map(p => p.total_ai_cost_usd)) : 0;

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Cost per Outcome (GitHub PRs)</h1>
          <p className="page-subtitle">
            Attribute gateway token costs directly to pull requests, developer sessions, and merged features
          </p>
        </div>
      </div>

      {/* Honesty Caveat Banner (Person A Contract requirement) */}
      <div className="alert-banner info" style={{
        background: 'rgba(6, 182, 212, 0.08)',
        border: '1px solid rgba(6, 182, 212, 0.25)',
        color: 'var(--text-secondary)',
        lineHeight: 1.5,
        marginBottom: 20,
      }}>
        <Info size={20} style={{ color: 'var(--status-cyan)', flexShrink: 0, marginTop: 2 }} />
        <div>
          <strong style={{ color: 'var(--status-cyan)' }}>Methodology & Attribution Notice:</strong> Cost attribution is algorithmically estimated by correlating session timing windows (`session_id`), branch activity, and Claude Code commit timestamps against gateway usage events. Attribution may not be fully precise for asynchronous background tasks or out-of-band manual prompts.
        </div>
      </div>

      {/* Top Stats Strip */}
      <div className="stats-info-row">
        <div className="stat-info-item">
          <div className="stat-info-label">Total Correlated PRs</div>
          <div className="stat-info-value">{prs.length} merged</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Total AI Spend on PRs</div>
          <div className="stat-info-value" style={{ color: 'var(--brand-primary)' }}>${totalCost.toFixed(4)}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Average Cost / PR</div>
          <div className="stat-info-value" style={{ color: 'var(--status-success)' }}>${avgCost.toFixed(2)}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Most Expensive PR</div>
          <div className="stat-info-value" style={{ color: 'var(--status-warning)' }}>${maxCost.toFixed(4)}</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Avg Time to Merge</div>
          <div className="stat-info-value">{avgMergeHours} hours</div>
        </div>
      </div>

      {/* Filter & Sort Bar */}
      <div className="table-panel">
        <div className="filter-bar">
          <div className="search-wrap" style={{ maxWidth: 380 }}>
            <Search size={14} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search by PR title, author, or #number…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginLeft: 'auto' }}>
            <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>Sort By:</span>
            <select
              className="form-select"
              style={{ width: 'auto', padding: '6px 12px', fontSize: 12 }}
              value={sortBy}
              onChange={e => setSortBy(e.target.value)}
            >
              <option value="cost-desc">AI Cost: High &rarr; Low (Default)</option>
              <option value="cost-asc">AI Cost: Low &rarr; High</option>
              <option value="time-desc">Time to Merge (Longest)</option>
              <option value="files-desc">Files Changed (Most)</option>
            </select>
          </div>
        </div>

        {/* PR Cost Table */}
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Pull Request</th>
                <th>Author</th>
                <th>Correlated AI Cost</th>
                <th>Primary Model</th>
                <th>Time to Merge</th>
                <th>Files Changed</th>
                <th>Sessions</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(p => (
                <tr key={p.id}>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 3, maxWidth: 380 }}>
                      <a
                        href={p.pr_url}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 6,
                          fontWeight: 600,
                          color: 'var(--text-primary)',
                          textDecoration: 'none',
                          fontSize: 13,
                        }}
                        onMouseEnter={e => e.currentTarget.style.color = 'var(--brand-primary)'}
                        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-primary)'}
                      >
                        <GitPullRequest size={14} style={{ color: 'var(--brand-primary)', flexShrink: 0 }} />
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          #{p.pr_number} {p.pr_title}
                        </span>
                        <ExternalLink size={12} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
                      </a>
                      <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>{p.repo_id}</span>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                      <div style={{
                        width: 22,
                        height: 22,
                        borderRadius: '50%',
                        background: 'var(--bg-surface-3)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 11,
                        color: 'var(--text-secondary)',
                      }}>
                        <User size={12} />
                      </div>
                      <span className="mono" style={{ fontSize: 12 }}>{p.author}</span>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                      <span className="mono" style={{
                        fontSize: 13.5,
                        fontWeight: 700,
                        color: p.total_ai_cost_usd > 1.0 ? 'var(--brand-primary)' : 'var(--text-primary)',
                      }}>
                        ${p.total_ai_cost_usd.toFixed(4)}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12 }}>
                      <span style={{ width: 7, height: 7, borderRadius: '50%', background: p.top_model.includes('Claude') ? '#F97316' : '#10B981' }} />
                      <span>{p.top_model}</span>
                    </span>
                  </td>
                  <td className="mono" style={{ fontSize: 12 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                      <Clock size={12} style={{ color: 'var(--text-dim)' }} />
                      <span>{p.time_to_merge_hours} hrs</span>
                    </div>
                  </td>
                  <td>
                    <span className="badge badge-default mono" style={{ fontSize: 11 }}>
                      {p.files_changed} files
                    </span>
                  </td>
                  <td>
                    <span className="mono" style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      {p.session_count} sess
                    </span>
                  </td>
                  <td>
                    <span className="badge badge-success" style={{ fontSize: 10.5 }}>
                      Merged
                    </span>
                  </td>
                </tr>
              ))}

              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                    No correlated pull requests matched your filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
