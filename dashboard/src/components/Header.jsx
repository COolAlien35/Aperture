import { useState, useEffect, useRef } from 'react';
import {
  Server,
  Database,
  Radio,
  ChevronDown,
  LogOut,
  User,
  Shield,
  ExternalLink,
  Sliders,
  Bell,
  BookOpen,
  CheckCircle2,
} from 'lucide-react';
import ApertureLogo from './ApertureLogo.jsx';
import { checkServiceHealth } from '../services/api.js';

const TIME_FILTERS = ['1H', '24H', '7D', '30D'];

export default function Header({ timeFilter, onTimeFilter, user, onLogout, onNavigate }) {
  const [health, setHealth] = useState({ gateway: null, kafka: null, dynamodb: null });
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [wsMenuOpen, setWsMenuOpen] = useState(false);
  const [workspace, setWorkspace] = useState('Default Workspace');
  const menuRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => {
    const poll = async () => {
      const h = await checkServiceHealth();
      setHealth(h);
    };
    poll();
    const id = setInterval(poll, 15000);
    return () => clearInterval(id);
  }, []);

  // Close menus on outside click
  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setUserMenuOpen(false);
      }
      if (wsRef.current && !wsRef.current.contains(e.target)) {
        setWsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const ServicePill = ({ label, addr, up, icon: Icon, dotClass }) => (
    <div className={`status-pill ${up === true ? 'healthy' : up === false ? 'danger' : ''}`}>
      <span className={`pulse-dot ${up === false ? 'red' : dotClass || ''}`} />
      {Icon && <Icon size={12} style={{ color: 'var(--text-muted)' }} />}
      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{label}</span>
      <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>{addr}</span>
    </div>
  );

  return (
    <header className="header">
      {/* Brand & Workspace Switcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div
          className="header-logo-container"
          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}
          onClick={() => onNavigate('overview')}
        >
          <ApertureLogo size={26} showText={true} textSub="AI Gateway" />
        </div>

        <div className="header-divider" />

        {/* Workspace Dropdown */}
        <div className="workspace-switcher" ref={wsRef} style={{ position: 'relative' }}>
          <button
            className="workspace-btn"
            onClick={() => setWsMenuOpen(!wsMenuOpen)}
            aria-expanded={wsMenuOpen}
          >
            <span className="workspace-name">{workspace}</span>
            <ChevronDown size={13} className={`chevron-icon${wsMenuOpen ? ' rotate' : ''}`} />
          </button>

          {wsMenuOpen && (
            <div className="workspace-dropdown-menu">
              <div className="workspace-dropdown-title">Workspaces</div>
              {['Default Workspace', 'Staging & QA', 'Enterprise Client AI'].map(ws => (
                <button
                  key={ws}
                  className={`workspace-item${workspace === ws ? ' active' : ''}`}
                  onClick={() => { setWorkspace(ws); setWsMenuOpen(false); }}
                >
                  <span>{ws}</span>
                  {workspace === ws && <CheckCircle2 size={13} style={{ color: 'var(--brand-primary)', marginLeft: 'auto' }} />}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="env-badge">
          <span className="env-dot" />
          <span>Production</span>
        </div>
      </div>

      {/* Live Services Telemetry */}
      <div className="header-pills">
        <ServicePill label="Gateway" addr=":8080" up={health.gateway} dotClass="orange" icon={Server} />
        <ServicePill label="Kafka" addr=":9092" up={health.kafka} dotClass="cyan" icon={Radio} />
        <ServicePill label="DynamoDB" addr=":8001" up={health.dynamodb} dotClass="" icon={Database} />
      </div>

      {/* Right Controls */}
      <div className="header-right">
        {/* Time Filters */}
        <div className="time-filter-group">
          {TIME_FILTERS.map(f => (
            <button
              key={f}
              id={`time-filter-${f.toLowerCase()}`}
              className={`time-filter-btn${timeFilter === f ? ' active' : ''}`}
              onClick={() => onTimeFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Quick Docs Link */}
        <a
          href="https://portkey.ai/docs"
          target="_blank"
          rel="noreferrer"
          className="header-icon-btn"
          title="Portkey & Aperture Documentation"
        >
          <BookOpen size={15} />
        </a>

        {/* Notifications */}
        <button
          className="header-icon-btn"
          title="Notifications"
          onClick={() => alert('All systems operational. No active alerts.')}
        >
          <Bell size={15} />
          <span className="notif-badge" />
        </button>

        {/* User Profile Dropdown */}
        <div className="user-dropdown-container" ref={menuRef} style={{ position: 'relative' }}>
          <button
            id="user-profile-btn"
            className="user-profile-trigger"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            aria-expanded={userMenuOpen}
          >
            <div className="user-avatar-pill">
              <div className="user-avatar-initials">
                {user?.name ? user.name.slice(0, 2).toUpperCase() : 'SB'}
              </div>
              <div className="user-info-text">
                <span className="user-name">{user?.name || 'Soham Banerjee'}</span>
                <span className="user-team">{user?.team || 'Engineering'}</span>
              </div>
              <ChevronDown size={14} className={`chevron-icon${userMenuOpen ? ' rotate' : ''}`} />
            </div>
          </button>

          {userMenuOpen && (
            <div className="user-dropdown-menu">
              <div className="user-dropdown-header">
                <div className="user-dropdown-name">{user?.name || 'Soham Banerjee'}</div>
                <div className="user-dropdown-email">{user?.email || 'soham@aperture.io'}</div>
                <div className="user-dropdown-badge">
                  <Shield size={11} />
                  <span>{user?.role || 'Admin'} Access</span>
                </div>
              </div>

              <div className="user-dropdown-divider" />

              <button
                className="user-dropdown-item"
                onClick={() => {
                  setUserMenuOpen(false);
                  onNavigate('login');
                }}
              >
                <ExternalLink size={14} />
                <span>Switch to Login View</span>
              </button>

              <button
                className="user-dropdown-item"
                onClick={() => {
                  setUserMenuOpen(false);
                  onNavigate('keys');
                }}
              >
                <Sliders size={14} />
                <span>Manage API Keys</span>
              </button>

              <button
                className="user-dropdown-item"
                onClick={() => {
                  setUserMenuOpen(false);
                  onNavigate('config');
                }}
              >
                <Server size={14} />
                <span>System Configuration</span>
              </button>

              <div className="user-dropdown-divider" />

              <button
                id="user-logout-btn"
                className="user-dropdown-item text-danger"
                onClick={() => {
                  setUserMenuOpen(false);
                  onLogout();
                }}
              >
                <LogOut size={14} />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
