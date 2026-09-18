import {
  LayoutDashboard,
  ListFilter,
  KeyRound,
  ShieldCheck,
  GitFork,
  Settings,
  Lock,
  LogOut,
  ExternalLink,
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'overview', icon: LayoutDashboard, label: 'Overview', path: '/' },
  { id: 'logs', icon: ListFilter, label: 'Request Logs', path: '/logs', badge: 'LIVE' },
  { id: 'keys', icon: KeyRound, label: 'Virtual Keys', path: '/keys' },
  { id: 'budgets', icon: ShieldCheck, label: 'Budgets & RBAC', path: '/budgets' },
  { id: 'gateway', icon: GitFork, label: 'Fallbacks & Breakers', path: '/gateway' },
];

export default function Sidebar({ currentView, onNavigate, onLogout }) {
  return (
    <nav className="sidebar" role="navigation" aria-label="Main navigation">
      <div className="nav-section-label">Platform</div>

      {NAV_ITEMS.map(item => {
        const Icon = item.icon;
        return (
          <a
            key={item.id}
            id={`nav-${item.id}`}
            className={`nav-item${currentView === item.id ? ' active' : ''}`}
            href={item.path}
            onClick={(e) => { e.preventDefault(); onNavigate(item.id); }}
            aria-current={currentView === item.id ? 'page' : undefined}
          >
            <span className="nav-icon">
              <Icon size={16} />
            </span>
            <span>{item.label}</span>
            {item.badge && <span className="nav-badge">{item.badge}</span>}
          </a>
        );
      })}

      <div style={{ flex: 1 }} />

      <div className="nav-section-label">Authentication</div>
      <a
        id="nav-login-view"
        className={`nav-item${currentView === 'login' ? ' active' : ''}`}
        href="/login"
        onClick={(e) => { e.preventDefault(); onNavigate('login'); }}
      >
        <span className="nav-icon">
          <Lock size={16} />
        </span>
        <span>Login Page</span>
        <span className="nav-badge" style={{ background: 'var(--brand-subtle)', color: 'var(--brand-primary)', borderColor: 'var(--border-accent)' }}>
          PORTKEY
        </span>
      </a>

      <div className="nav-section-label" style={{ marginTop: 8 }}>System</div>
      <a
        id="nav-config"
        className={`nav-item${currentView === 'config' ? ' active' : ''}`}
        href="/config"
        onClick={(e) => { e.preventDefault(); onNavigate('config'); }}
      >
        <span className="nav-icon">
          <Settings size={16} />
        </span>
        <span>Configuration</span>
      </a>

      <div className="sidebar-footer">
        <div className="sidebar-footer-version">
          <span>Aperture v0.1.0</span>
          <span className="version-dot">·</span>
          <span className="version-branch">team-c</span>
        </div>
        {onLogout && (
          <button
            className="sidebar-logout-btn"
            onClick={onLogout}
            title="Sign out of Aperture"
          >
            <LogOut size={13} />
            <span>Sign Out</span>
          </button>
        )}
      </div>
    </nav>
  );
}
