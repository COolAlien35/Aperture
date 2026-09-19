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

const SECTIONS = [
  {
    title: 'OBSERVABILITY',
    items: [
      { id: 'overview', icon: LayoutDashboard, label: 'Overview', path: '/' },
      { id: 'logs', icon: ListFilter, label: 'Logs & Traces', path: '/logs', badge: 'LIVE' },
    ],
  },
  {
    title: 'AI GATEWAY',
    items: [
      { id: 'keys', icon: KeyRound, label: 'Virtual Keys', path: '/keys' },
      { id: 'gateway', icon: GitFork, label: 'Routing & Fallbacks', path: '/gateway' },
    ],
  },
  {
    title: 'GOVERNANCE',
    items: [
      { id: 'budgets', icon: ShieldCheck, label: 'Budgets & RBAC', path: '/budgets' },
    ],
  },
  {
    title: 'AUTHENTICATION',
    items: [
      {
        id: 'login',
        icon: Lock,
        label: 'Auth & Login',
        path: '/login',
        badge: 'PORTKEY',
        badgeStyle: { background: 'rgba(249, 115, 22, 0.12)', color: 'var(--brand-primary)', borderColor: 'rgba(249, 115, 22, 0.3)' },
      },
    ],
  },
  {
    title: 'SETTINGS',
    items: [
      { id: 'config', icon: Settings, label: 'Configuration', path: '/config' },
    ],
  },
];

export default function Sidebar({ currentView, onNavigate, onLogout }) {
  return (
    <nav className="sidebar" role="navigation" aria-label="Main navigation">
      {SECTIONS.map(sec => (
        <div key={sec.title} className="sidebar-group" style={{ marginBottom: 16 }}>
          <div className="nav-section-label">{sec.title}</div>
          {sec.items.map(item => {
            const Icon = item.icon;
            const active = currentView === item.id;
            return (
              <a
                key={item.id}
                id={`nav-${item.id}`}
                className={`nav-item${active ? ' active' : ''}`}
                href={item.path}
                onClick={(e) => { e.preventDefault(); onNavigate(item.id); }}
                aria-current={active ? 'page' : undefined}
              >
                <span className="nav-icon">
                  <Icon size={16} />
                </span>
                <span>{item.label}</span>
                {item.badge && (
                  <span className="nav-badge" style={item.badgeStyle || undefined}>
                    {item.badge}
                  </span>
                )}
              </a>
            );
          })}
        </div>
      ))}

      <div style={{ flex: 1 }} />

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
