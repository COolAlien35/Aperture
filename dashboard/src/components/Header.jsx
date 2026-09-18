import { useState, useEffect, useRef } from 'react';
import {
  Activity,
  Server,
  Database,
  Radio,
  ChevronDown,
  LogOut,
  User,
  Shield,
  ExternalLink,
  Sliders,
} from 'lucide-react';
import ApertureLogo from './ApertureLogo.jsx';
import { checkServiceHealth } from '../services/api.js';

const TIME_FILTERS = ['24H', '7D', '30D', 'ALL'];

export default function Header({ timeFilter, onTimeFilter, user, onLogout, onNavigate }) {
  const [health, setHealth] = useState({ gateway: null, kafka: null, dynamodb: null });
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const poll = async () => {
      const h = await checkServiceHealth();
      setHealth(h);
    };
    poll();
    const id = setInterval(poll, 15000);
    return () => clearInterval(id);
  }, []);

  // Close user menu on outside click
  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setUserMenuOpen(false);
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
      <div
        className="header-logo-container"
        style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}
        onClick={() => onNavigate('overview')}
      >
        <ApertureLogo size={26} showText={true} textSub="AI Gateway" />
      </div>

      <div className="header-divider" />

      <div className="header-pills">
        <ServicePill label="Gateway" addr=":8080" up={health.gateway} dotClass="orange" icon={Server} />
        <ServicePill label="Kafka" addr=":9092" up={health.kafka} dotClass="cyan" icon={Radio} />
        <ServicePill label="DynamoDB" addr=":8001" up={health.dynamodb} dotClass="" icon={Database} />
      </div>

      <div className="header-right">
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

        {/* User profile dropdown */}
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
