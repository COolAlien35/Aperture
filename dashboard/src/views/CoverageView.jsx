import { useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Info,
  Terminal,
  Cpu,
  Layers,
  ArrowRight,
  ExternalLink,
  Code2,
  Copy,
  Check,
} from 'lucide-react';

const COVERED = [
  {
    name: 'Claude Code CLI & Anthropic Agents',
    category: 'Autonomous Coding Agents',
    status: 'Full Coverage',
    description: 'Fully intercepted via ANTHROPIC_BASE_URL=http://localhost:8080. Captures session_id, token cost, model, and enforces pre-flight kill-switches.',
    configSnippet: 'export ANTHROPIC_BASE_URL="http://localhost:8080"\nexport ANTHROPIC_API_KEY="sk-gw-eng-001"',
  },
  {
    name: 'OpenAI Python & TypeScript SDKs',
    category: 'SDK & Direct API',
    status: 'Full Coverage',
    description: 'Standard OpenAI client configurations pointing baseURL to Aperture. Supports chat completions, embeddings, and streaming responses.',
    configSnippet: 'from openai import OpenAI\nclient = OpenAI(base_url="http://localhost:8080/v1", api_key="sk-gw-eng-001")',
  },
  {
    name: 'Custom Internal Agent Services',
    category: 'Enterprise Microservices',
    status: 'Full Coverage',
    description: 'Internal backend microservices using LangChain, LlamaIndex, or raw HTTP clients routed through Aperture with virtual keys.',
    configSnippet: 'curl -X POST http://localhost:8080/v1/chat/completions \\\n  -H "Authorization: Bearer sk-gw-eng-001" \\\n  -d \'{"model":"claude-3-5-sonnet","messages":[{"role":"user","content":"hi"}]}\'',
  },
  {
    name: 'CI/CD Automated Eval Sweeps',
    category: 'DevOps & Testing',
    status: 'Full Coverage',
    description: 'GitHub Actions and automated test pipelines configured with scoped virtual keys and daily spend ceilings.',
    configSnippet: 'env:\n  OPENAI_BASE_URL: http://aperture-gateway:8080/v1\n  OPENAI_API_KEY: ${{ secrets.APERTURE_CI_KEY }}',
  },
];

const UNCOVERED = [
  {
    name: 'Cursor & Windsurf Background Speculative Indexing',
    category: 'Proprietary IDE Tunnels',
    reason: 'Hardcoded TLS / gRPC Tunnel',
    explanation: 'Native Cursor and Windsurf background agents (codebase vector indexing, shadow autocomplete, fast edits) route through hardcoded, proprietary RPC proxies that bypass OS-level HTTP proxy environment variables (HTTP_PROXY / HTTPS_PROXY).',
    mitigation: 'When developers manually enter their own API key in Cursor settings, regular chat interactions flow through Aperture; however, native agent indexing traffic remains outside proxy reach.',
    roadmap: 'Phase 3 Roadmap: An optional eBPF packet-filter kernel daemon will intercept outbound TLS handshakes to LLM endpoints at the socket layer.',
  },
  {
    name: 'Direct Browser Web UI Prompts (ChatGPT Plus / Claude Pro)',
    category: 'Consumer Web Interfaces',
    reason: 'Consumer Auth & Out-of-Band SaaS',
    explanation: 'Manual prompts typed directly into chatgpt.com or claude.ai consumer subscriptions do not hit enterprise API endpoints and cannot be measured by any gateway proxy.',
    mitigation: 'Enterprise SSO policies and workspace provisioning encourage developers to use virtual keys with Claude Code CLI and IDE tools rather than consumer browser subscriptions.',
    roadmap: 'Browser extension auditing is intentionally out of scope to preserve developer privacy and avoid invasive client-side keystroke logging.',
  },
];

export default function CoverageView() {
  const [copiedIdx, setCopiedIdx] = useState(null);

  const handleCopy = (text, idx) => {
    navigator.clipboard?.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 1800);
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Telemetry Coverage Map & Transparency Policy</h1>
          <p className="page-subtitle">
            An open technical accounting of where Aperture captures spend today vs. closed proprietary IDE channels
          </p>
        </div>
      </div>

      {/* Credibility statement */}
      <div className="alert-banner info" style={{
        background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.08) 0%, rgba(28, 32, 42, 0.9) 100%)',
        border: '1px solid rgba(6, 182, 212, 0.25)',
        color: 'var(--text-secondary)',
        lineHeight: 1.55,
        marginBottom: 24,
      }}>
        <Info size={22} style={{ color: 'var(--status-cyan)', flexShrink: 0, marginTop: 2 }} />
        <div>
          <strong style={{ color: 'var(--text-primary)' }}>Why We Publish This:</strong> Non-technical buyers and enterprise CFOs require authentic data boundaries. We believe credibility comes from precision, not false marketing claims of universal coverage. Below is an honest breakdown of what Aperture captures with cryptographic certainty versus closed proprietary IDE channels.
        </div>
      </div>

      {/* Coverage Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 20, marginBottom: 24 }}>
        {/* Column 1: What Aperture Can See */}
        <div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: 13,
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.6px',
            color: 'var(--status-success)',
            marginBottom: 14,
          }}>
            <ShieldCheck size={16} />
            <span>What Aperture Can See (100% Intercepted)</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {COVERED.map((item, i) => (
              <div
                key={item.name}
                className="chart-card"
                style={{
                  borderLeft: '3px solid var(--status-success)',
                  padding: '18px 20px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 8 }}>
                  <div>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: 14 }}>{item.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>{item.category}</div>
                  </div>
                  <span className="badge badge-success" style={{ fontSize: 10 }}>
                    <CheckCircle2 size={11} /> {item.status}
                  </span>
                </div>

                <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.45, marginBottom: 12 }}>
                  {item.description}
                </p>

                <div style={{
                  background: 'var(--bg-surface-2)',
                  borderRadius: 6,
                  border: '1px solid var(--border-subtle)',
                  padding: '8px 12px',
                  position: 'relative',
                }}>
                  <pre className="mono" style={{ margin: 0, fontSize: 11, color: 'var(--text-primary)', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                    {item.configSnippet}
                  </pre>
                  <button
                    type="button"
                    className="copy-btn"
                    style={{ position: 'absolute', top: 6, right: 6 }}
                    onClick={() => handleCopy(item.configSnippet, i)}
                    title="Copy configuration snippet"
                  >
                    {copiedIdx === i ? <Check size={11} style={{ color: 'var(--status-success)' }} /> : <Copy size={11} />}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Column 2: What Aperture Cannot Yet See */}
        <div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: 13,
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.6px',
            color: 'var(--status-warning)',
            marginBottom: 14,
          }}>
            <ShieldAlert size={16} />
            <span>What Aperture Cannot Yet See (Technical Boundaries)</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {UNCOVERED.map(item => (
              <div
                key={item.name}
                className="chart-card"
                style={{
                  borderLeft: '3px solid var(--status-warning)',
                  padding: '18px 20px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 8 }}>
                  <div>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: 14 }}>{item.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>{item.category}</div>
                  </div>
                  <span className="badge badge-warning" style={{ fontSize: 10 }}>
                    <AlertCircle size={11} /> {item.reason}
                  </span>
                </div>

                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--status-danger)', textTransform: 'uppercase', letterSpacing: '0.4px', marginBottom: 3 }}>
                    Technical Reason:
                  </div>
                  <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.45, margin: 0 }}>
                    {item.explanation}
                  </p>
                </div>

                <div style={{
                  padding: '10px 12px',
                  background: 'var(--bg-surface-2)',
                  borderRadius: 6,
                  border: '1px solid var(--border-subtle)',
                  marginBottom: 10,
                }}>
                  <div style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.4px', marginBottom: 2 }}>
                    Current Operational Mitigation:
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
                    {item.mitigation}
                  </p>
                </div>

                <div style={{
                  padding: '8px 12px',
                  background: 'rgba(6, 182, 212, 0.06)',
                  borderRadius: 6,
                  border: '1px solid rgba(6, 182, 212, 0.2)',
                  fontSize: 11.5,
                  color: 'var(--status-cyan)',
                }}>
                  <strong>Engineering Roadmap:</strong> {item.roadmap}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
