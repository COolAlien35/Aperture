import { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Building2,
  Lock,
  Mail,
  Eye,
  EyeOff,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Sparkles,
  Zap,
} from 'lucide-react';
import ApertureLogo from '../components/ApertureLogo.jsx';

const TESTIMONIALS = [
  {
    quote: "Aperture gave us the unified routing, budget kill-switches, and fallback reliability we needed to roll out LLMs across 25+ engineering squads with zero upstream outages.",
    author: "Elena Rostova",
    role: "VP of Engineering",
    company: "Synthesia AI",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80",
    stats: "38% token cost reduction",
  },
  {
    quote: "The virtual keys and sub-millisecond gateway latency let our compliance team audit every prompt in real-time while completely mitigating 429 rate limit spikes.",
    author: "Marcus Vance",
    role: "Head of AI Infrastructure",
    company: "Quantex Data",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80",
    stats: "99.99% gateway uptime",
  },
  {
    quote: "Automated circuit breakers that seamlessly failover from Anthropic to OpenAI without application-level retries saved our customer-facing agents during peak traffic.",
    author: "Sarah Lin",
    role: "Chief Technology Officer",
    company: "Cognition Studio",
    avatar: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=100&auto=format&fit=crop&q=80",
    stats: "4.2x faster fallback recovery",
  },
];

export default function LoginView({ onLogin }) {
  const [mode, setMode] = useState('login'); // 'login' | 'signup'
  const [authMethod, setAuthMethod] = useState('options'); // 'options' | 'email'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [activeTestimonial, setActiveTestimonial] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Auto rotate testimonials every 6 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveTestimonial(prev => (prev + 1) % TESTIMONIALS.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  const handleEmailSubmit = (e) => {
    e.preventDefault();
    setError(null);
    if (!email) {
      setError('Please enter a valid work email.');
      return;
    }
    if (!password || password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      const user = {
        name: name || email.split('@')[0].replace('.', ' '),
        email: email,
        role: 'Admin',
        team: 'Engineering',
      };
      onLogin(user);
    }, 600);
  };

  const handleQuickDemo = (demoRole = 'Admin') => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      const user = {
        name: 'Soham Banerjee',
        email: 'soham@aperture.io',
        role: demoRole,
        team: 'Engineering',
      };
      onLogin(user);
    }, 450);
  };

  const handleSocialLogin = (provider) => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      const user = {
        name: provider === 'Google' ? 'Soham Banerjee' : provider === 'GitHub' ? 'coolalien35' : 'Enterprise User',
        email: `${provider.toLowerCase()}-user@aperture.io`,
        role: 'Admin',
        team: 'Engineering',
      };
      onLogin(user);
    }, 450);
  };

  const currentT = TESTIMONIALS[activeTestimonial];

  return (
    <div className="login-root">
      <div className="login-container">
        {/* Left Panel: Testimonial & Compliance Showcase */}
        <div className="login-left-panel">
          <div className="login-left-top">
            <ApertureLogo size={32} showText={true} textSub="AI Gateway" />
            <div className="login-trust-pill">
              <Sparkles size={13} className="text-orange-400" />
              <span>Enterprise Grade AI Infrastructure</span>
            </div>
          </div>

          <div className="login-left-body">
            <div className="testimonial-card">
              <div className="testimonial-stars">
                {[...Array(5)].map((_, i) => (
                  <span key={i} className="text-amber-400">★</span>
                ))}
              </div>
              <blockquote className="testimonial-quote">
                "{currentT.quote}"
              </blockquote>

              <div className="testimonial-meta">
                <img
                  src={currentT.avatar}
                  alt={currentT.author}
                  className="testimonial-avatar"
                />
                <div className="testimonial-author-wrap">
                  <div className="testimonial-author">{currentT.author}</div>
                  <div className="testimonial-role">
                    {currentT.role} · <span className="text-zinc-400">{currentT.company}</span>
                  </div>
                </div>
                <div className="testimonial-stat-badge">
                  <Zap size={12} style={{ color: 'var(--brand-primary)' }} />
                  <span>{currentT.stats}</span>
                </div>
              </div>

              {/* Carousel Indicators */}
              <div className="testimonial-dots">
                {TESTIMONIALS.map((_, idx) => (
                  <button
                    key={idx}
                    className={`testimonial-dot${activeTestimonial === idx ? ' active' : ''}`}
                    onClick={() => setActiveTestimonial(idx)}
                    aria-label={`Slide ${idx + 1}`}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Pinned Compliance Badges */}
          <div className="login-left-footer">
            <div className="compliance-heading">SOC2 & SECURITY CERTIFICATIONS</div>
            <div className="compliance-badges">
              <div className="compliance-badge">
                <ShieldCheck size={14} className="compliance-icon" />
                <span>HIPAA Compliant</span>
              </div>
              <div className="compliance-badge">
                <ShieldCheck size={14} className="compliance-icon" />
                <span>ISO 27001</span>
              </div>
              <div className="compliance-badge">
                <ShieldCheck size={14} className="compliance-icon" />
                <span>SOC2 Type II</span>
              </div>
              <div className="compliance-badge">
                <ShieldCheck size={14} className="compliance-icon" />
                <span>GDPR Ready</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel: Authentication Form */}
        <div className="login-right-panel">
          <div className="login-card">
            <div className="login-card-header">
              <div className="login-card-logo">
                <ApertureLogo size={40} showText={false} />
              </div>
              <h1 className="login-title">
                {mode === 'login' ? 'Sign in to Aperture' : 'Create your account'}
              </h1>
              <p className="login-subtitle">
                {mode === 'login'
                  ? 'Access your unified AI Gateway and spend observability dashboard'
                  : 'Start monitoring, controlling, and routing enterprise AI requests'}
              </p>
            </div>

            {error && (
              <div className="login-error-banner">
                <span>{error}</span>
              </div>
            )}

            {/* Quick Demo Login Bypass Pill */}
            <div className="demo-access-card">
              <div className="demo-access-info">
                <Zap size={15} style={{ color: 'var(--brand-primary)' }} />
                <div>
                  <div className="demo-access-title">Instant Reviewer Access</div>
                  <div className="demo-access-sub">One-click login with pre-configured team data</div>
                </div>
              </div>
              <button
                id="quick-demo-login-btn"
                type="button"
                className="btn btn-primary btn-sm demo-btn"
                onClick={() => handleQuickDemo('Admin')}
                disabled={loading}
              >
                {loading ? 'Accessing…' : 'Quick Demo In →'}
              </button>
            </div>

            {authMethod === 'options' ? (
              <div className="auth-options-stack">
                <button
                  type="button"
                  className="auth-btn sso-btn"
                  onClick={() => handleSocialLogin('Enterprise SSO')}
                  disabled={loading}
                >
                  <Building2 size={18} className="auth-btn-icon" />
                  <span>Single sign-on (SSO)</span>
                </button>

                <button
                  type="button"
                  className="auth-btn social-btn"
                  onClick={() => handleSocialLogin('Google')}
                  disabled={loading}
                >
                  <svg className="auth-btn-icon" width="18" height="18" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                  </svg>
                  <span>Continue with Google</span>
                </button>

                <button
                  type="button"
                  className="auth-btn social-btn"
                  onClick={() => handleSocialLogin('GitHub')}
                  disabled={loading}
                >
                  <svg className="auth-btn-icon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                  </svg>
                  <span>Continue with GitHub</span>
                </button>

                <div className="auth-divider">
                  <span>or continue with email</span>
                </div>

                <button
                  type="button"
                  className="auth-btn email-btn"
                  onClick={() => setAuthMethod('email')}
                >
                  <Mail size={18} className="auth-btn-icon" />
                  <span>Continue with work email</span>
                </button>
              </div>
            ) : (
              <form onSubmit={handleEmailSubmit} className="auth-email-form">
                <button
                  type="button"
                  className="back-to-options-btn"
                  onClick={() => setAuthMethod('options')}
                >
                  <ArrowLeft size={14} />
                  <span>Back to all login options</span>
                </button>

                {mode === 'signup' && (
                  <div className="form-group">
                    <label className="form-label" htmlFor="auth-name">Full Name</label>
                    <input
                      id="auth-name"
                      type="text"
                      className="form-input"
                      placeholder="e.g. Alex Mercer"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label" htmlFor="auth-email">Work Email</label>
                  <div className="input-with-icon">
                    <Mail size={16} className="input-prefix-icon" />
                    <input
                      id="auth-email"
                      type="email"
                      className="form-input with-prefix"
                      placeholder="name@company.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <div className="label-with-action">
                    <label className="form-label" htmlFor="auth-password">Password</label>
                    {mode === 'login' && (
                      <a href="#forgot" className="forgot-link" onClick={(e) => { e.preventDefault(); alert('Password reset link sent to registered email.'); }}>
                        Forgot password?
                      </a>
                    )}
                  </div>
                  <div className="input-with-icon">
                    <Lock size={16} className="input-prefix-icon" />
                    <input
                      id="auth-password"
                      type={showPassword ? 'text' : 'password'}
                      className="form-input with-prefix with-suffix"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                    <button
                      type="button"
                      className="input-suffix-btn"
                      onClick={() => setShowPassword(!showPassword)}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                <button
                  id="auth-submit-btn"
                  type="submit"
                  className="btn btn-primary submit-auth-btn"
                  disabled={loading}
                >
                  {loading ? (
                    <span>Authenticating…</span>
                  ) : (
                    <>
                      <span>{mode === 'login' ? 'Sign In' : 'Create Account'}</span>
                      <ArrowRight size={16} />
                    </>
                  )}
                </button>

                <div className="demo-fill-hint">
                  <button
                    type="button"
                    className="demo-fill-btn"
                    onClick={() => {
                      setEmail('engineer@aperture.io');
                      setPassword('aperture2026!');
                    }}
                  >
                    Click to autofill sample credentials
                  </button>
                </div>
              </form>
            )}

            <div className="auth-footer">
              {mode === 'login' ? (
                <p>
                  Don't have an account?{' '}
                  <button
                    type="button"
                    className="mode-toggle-link"
                    onClick={() => { setMode('signup'); setAuthMethod('options'); }}
                  >
                    Sign up
                  </button>
                </p>
              ) : (
                <p>
                  Already have an account?{' '}
                  <button
                    type="button"
                    className="mode-toggle-link"
                    onClick={() => { setMode('login'); setAuthMethod('options'); }}
                  >
                    Sign in
                  </button>
                </p>
              )}
            </div>

            <div className="auth-legal">
              By proceeding, you agree to Aperture's{' '}
              <a href="#terms" onClick={(e) => e.preventDefault()}>Terms of Service</a> and{' '}
              <a href="#privacy" onClick={(e) => e.preventDefault()}>Privacy Policy</a>.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
