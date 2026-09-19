import { useState, useEffect } from 'react';
import Header from './components/Header.jsx';
import Sidebar from './components/Sidebar.jsx';
import OverviewView from './views/OverviewView.jsx';
import LogsView from './views/LogsView.jsx';
import KeysView from './views/KeysView.jsx';
import BudgetsView from './views/BudgetsView.jsx';
import GatewayView from './views/GatewayView.jsx';
import LoginView from './views/LoginView.jsx';
import ConfigView from './views/ConfigView.jsx';

const VIEWS = {
  overview: OverviewView,
  logs:     LogsView,
  keys:     KeysView,
  budgets:  BudgetsView,
  gateway:  GatewayView,
  config:   ConfigView,
};

const DEFAULT_USER = {
  name: 'Soham Banerjee',
  email: 'soham@aperture.io',
  role: 'Admin',
  team: 'Engineering',
};

export default function App() {
  const [view, setView] = useState(() => {
    // Check url hash or path if available
    const path = window.location.pathname;
    if (path === '/login') return 'login';
    if (path === '/logs') return 'logs';
    if (path === '/keys') return 'keys';
    if (path === '/budgets') return 'budgets';
    if (path === '/gateway') return 'gateway';
    return 'overview';
  });

  const [timeFilter, setTime] = useState('24H');
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('aperture_user');
      if (saved) return JSON.parse(saved);
    } catch {
      // ignore
    }
    return DEFAULT_USER;
  });

  const handleLogin = (userData) => {
    setUser(userData);
    try {
      localStorage.setItem('aperture_user', JSON.stringify(userData));
    } catch {
      // ignore
    }
    setView('overview');
    window.history.pushState(null, '', '/');
  };

  const handleLogout = () => {
    setUser(null);
    try {
      localStorage.removeItem('aperture_user');
    } catch {
      // ignore
    }
    setView('login');
    window.history.pushState(null, '', '/login');
  };

  const handleNavigate = (newView) => {
    setView(newView);
    const path = newView === 'overview' ? '/' : `/${newView}`;
    window.history.pushState(null, '', path);
  };

  // If user is explicitly viewing login or if user is logged out
  if (!user || view === 'login') {
    return (
      <LoginView
        onLogin={handleLogin}
      />
    );
  }

  const ViewComponent = VIEWS[view] || OverviewView;

  return (
    <div className="app-shell">
      <Header
        timeFilter={timeFilter}
        onTimeFilter={setTime}
        user={user}
        onLogout={handleLogout}
        onNavigate={handleNavigate}
      />
      <Sidebar
        currentView={view}
        onNavigate={handleNavigate}
        onLogout={handleLogout}
      />
      <main className="main-content">
        <ViewComponent timeFilter={timeFilter} />
      </main>
    </div>
  );
}
