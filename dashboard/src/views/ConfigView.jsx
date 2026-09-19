import { useState } from 'react';
import {
  Settings,
  Server,
  Database,
  Radio,
  Shield,
  Key,
  Sliders,
  Check,
  Save,
  RotateCcw,
  Zap,
  Globe,
  Lock,
  Activity,
  CheckCircle2,
  Cpu,
} from 'lucide-react';

export default function ConfigView() {
  const [saved, setSaved] = useState(false);
  const [testingKafka, setTestingKafka] = useState(false);
  const [kafkaOk, setKafkaOk] = useState(false);
  const [testingDynamo, setTestingDynamo] = useState(false);
  const [dynamoOk, setDynamoOk] = useState(false);

  const [config, setConfig] = useState({
    gatewayPort: 8080,
    gatewayHost: '0.0.0.0',
    primaryProvider: 'anthropic',
    fallbackProvider: 'openai',
    timeoutMs: 30000,
    maxRetries: 3,
    rateLimitRpm: 120,
    kafkaBroker: 'localhost:9092',
    kafkaTopic: 'aperture.usage-events',
    dynamoEndpoint: 'http://localhost:8001',
    dynamoTable: 'aperture_data',
    cacheTtlSeconds: 3600,
    enableSemanticCache: true,
  });

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2200);
  };

  const testKafka = () => {
    setTestingKafka(true);
    setTimeout(() => {
      setTestingKafka(false);
      setKafkaOk(true);
      setTimeout(() => setKafkaOk(false), 3000);
    }, 1000);
  };

  const testDynamo = () => {
    setTestingDynamo(true);
    setTimeout(() => {
      setTestingDynamo(false);
      setDynamoOk(true);
      setTimeout(() => setDynamoOk(false), 3000);
    }, 900);
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Runtime & Gateway Configuration</h1>
          <p className="page-subtitle">Configure upstream provider routing policies, async telemetry broker connections, and persistence endpoints</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleSave}
        >
          {saved ? <Check size={14} /> : <Save size={14} />}
          <span>{saved ? 'Saved Configuration' : 'Save Changes'}</span>
        </button>
      </div>

      {/* Stats row */}
      <div className="stats-info-row">
        <div className="stat-info-item">
          <div className="stat-info-label">Active Gateway</div>
          <div className="stat-info-value" style={{ color: 'var(--status-success)' }}>http://0.0.0.0:8080</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Telemetry Pipeline</div>
          <div className="stat-info-value" style={{ color: 'var(--status-cyan)' }}>Kafka v3.7 · Async</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Audit Store</div>
          <div className="stat-info-value" style={{ color: 'var(--status-purple)' }}>DynamoDB Local</div>
        </div>
        <div className="stat-info-divider" />
        <div className="stat-info-item">
          <div className="stat-info-label">Cache Engine</div>
          <div className="stat-info-value" style={{ color: 'var(--brand-primary)' }}>In-Memory Semantic</div>
        </div>
      </div>

      <form onSubmit={handleSave} className="config-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 20 }}>
        {/* Upstream Providers */}
        <div className="chart-card">
          <div className="chart-card-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Zap size={16} style={{ color: 'var(--brand-primary)' }} />
              <span>Upstream Model Routing</span>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="form-group">
              <label className="form-label">Primary LLM Provider</label>
              <select
                className="form-select"
                value={config.primaryProvider}
                onChange={e => setConfig({ ...config, primaryProvider: e.target.value })}
              >
                <option value="anthropic">Anthropic (Claude 3.5 Sonnet / Haiku)</option>
                <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                <option value="groq">Groq (Llama 3 70B)</option>
                <option value="bedrock">AWS Bedrock (Claude 3.5)</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Automated Failover Target</label>
              <select
                className="form-select"
                value={config.fallbackProvider}
                onChange={e => setConfig({ ...config, fallbackProvider: e.target.value })}
              >
                <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
                <option value="groq">Groq (Llama 3.1)</option>
              </select>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="form-group">
                <label className="form-label">Upstream Timeout (ms)</label>
                <input
                  type="number"
                  className="form-input"
                  value={config.timeoutMs}
                  onChange={e => setConfig({ ...config, timeoutMs: Number(e.target.value) })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Max Retries</label>
                <input
                  type="number"
                  className="form-input"
                  value={config.maxRetries}
                  onChange={e => setConfig({ ...config, maxRetries: Number(e.target.value) })}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Telemetry & Event Stream */}
        <div className="chart-card">
          <div className="chart-card-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Radio size={16} style={{ color: 'var(--status-cyan)' }} />
              <span>Kafka Telemetry Pipeline</span>
            </div>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              style={{ marginLeft: 'auto', padding: '3px 8px', fontSize: 11 }}
              onClick={testKafka}
              disabled={testingKafka}
            >
              {testingKafka ? <RotateCcw size={11} className="animate-spin" /> : kafkaOk ? <CheckCircle2 size={11} style={{ color: 'var(--status-success)' }} /> : <Activity size={11} />}
              <span>{testingKafka ? 'Probing…' : kafkaOk ? 'Connected' : 'Ping Broker'}</span>
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="form-group">
              <label className="form-label">Kafka Bootstrap Broker</label>
              <input
                type="text"
                className="form-input mono"
                value={config.kafkaBroker}
                onChange={e => setConfig({ ...config, kafkaBroker: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Telemetry Topic</label>
              <input
                type="text"
                className="form-input mono"
                value={config.kafkaTopic}
                onChange={e => setConfig({ ...config, kafkaTopic: e.target.value })}
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: 'var(--bg-surface-2)', borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
              <span className="pulse-dot cyan" />
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Non-blocking async producer. High-throughput Kafka queue handles &gt;10k events/sec.
              </span>
            </div>
          </div>
        </div>

        {/* DynamoDB Persistence */}
        <div className="chart-card">
          <div className="chart-card-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Database size={16} style={{ color: 'var(--status-purple)' }} />
              <span>DynamoDB State & Storage</span>
            </div>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              style={{ marginLeft: 'auto', padding: '3px 8px', fontSize: 11 }}
              onClick={testDynamo}
              disabled={testingDynamo}
            >
              {testingDynamo ? <RotateCcw size={11} className="animate-spin" /> : dynamoOk ? <CheckCircle2 size={11} style={{ color: 'var(--status-success)' }} /> : <Activity size={11} />}
              <span>{testingDynamo ? 'Probing…' : dynamoOk ? 'Accessible' : 'Check Table'}</span>
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="form-group">
              <label className="form-label">Endpoint URL</label>
              <input
                type="text"
                className="form-input mono"
                value={config.dynamoEndpoint}
                onChange={e => setConfig({ ...config, dynamoEndpoint: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Single-Table Name</label>
              <input
                type="text"
                className="form-input mono"
                value={config.dynamoTable}
                onChange={e => setConfig({ ...config, dynamoTable: e.target.value })}
              />
            </div>
          </div>
        </div>

        {/* Gateway Security & Caching */}
        <div className="chart-card">
          <div className="chart-card-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Shield size={16} style={{ color: 'var(--status-success)' }} />
              <span>Rate Limits & Cache Guard</span>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="form-group">
              <label className="form-label">Global Rate Limit (RPM per Key)</label>
              <input
                type="number"
                className="form-input"
                value={config.rateLimitRpm}
                onChange={e => setConfig({ ...config, rateLimitRpm: Number(e.target.value) })}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderTop: '1px solid var(--border-subtle)' }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Semantic Cache Engine</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Intercept identical prompt embeddings to return responses in &lt;15ms with 0 token spend</div>
              </div>
              <input
                type="checkbox"
                checked={config.enableSemanticCache}
                onChange={e => setConfig({ ...config, enableSemanticCache: e.target.checked })}
                style={{ width: 18, height: 18, accentColor: 'var(--brand-primary)', cursor: 'pointer' }}
              />
            </div>
          </div>
        </div>
      </form>
    </>
  );
}
