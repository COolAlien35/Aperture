# Aperture

An OpenAI-compatible AI gateway and proxy featuring real-time spend management, hard budget kill-switches, semantic response caching, and automatic multi-provider failover.

## Quick Start

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- API keys for Anthropic and/or OpenAI

### Setup

```bash
# 1. Clone the repo
git clone <repo-url> && cd Aperture

# 2. Create your .env file
cp .env.example .env
# Edit .env and add your API keys

# 3. Start all services
docker-compose up --build

# 4. Verify the gateway is running
curl http://localhost:8080/health
# → {"status": "ok"}
```

### Test the Gateway

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Services

| Service | Host Port | Description |
|---------|-----------|-------------|
| **Gateway** (FastAPI) | `8080` | OpenAI-compatible AI gateway |
| **Redis** | `6379` | Budget enforcement hot path |
| **Kafka** (KRaft) | `9092` | Usage event streaming |
| **DynamoDB Local** | `8001` | Keys, budgets, usage aggregates |

> **Port note:** DynamoDB Local is exposed on host port **8001** (container port 8000) to avoid collision with SSH tunnels or other services on 8000. The gateway reaches it at `http://dynamodb-local:8000` on the internal Docker network.

---

## DynamoDB — Single-Table Schema (`aperture_data`)

Aperture uses a **single DynamoDB table** with a composite primary key and one GSI. All entity types live in the same table, keyed by prefix conventions.

### Primary Key

| Attribute | Type | Role |
|-----------|------|------|
| `PK` | String | Partition Key |
| `SK` | String | Sort Key |

### GSI1: `team_id-index`

| GSI Attribute | Maps to |
|---------------|---------|
| `GSI1PK` | `team_id` (the team this item belongs to) |
| `GSI1SK` | `SK` of the source item |

**Purpose:** Query all keys or usage events belonging to a team. Used by the dashboard and budget enforcement fallback.

### Entity Access Patterns

| Entity | PK | SK | Purpose |
|--------|----|----|---------|
| **Virtual Key Metadata** | `KEY#<key_id>` | `METADATA` | Role, team, budget limit, active status |
| **Per-Request Usage Log** | `KEY#<key_id>` | `USAGE#<iso_timestamp>` | Token counts, cost, model, status per request |
| **Team Monthly Spend** | `TEAM#<team_id>` | `SPEND#<YYYY-MM>` | Running monthly spend aggregate per team |
| **Idempotency Marker** | `PROCESSED#<request_id>` | `MARKER` | Prevents double-spend on Kafka at-least-once replay |

### Key Attribute Reference

**Virtual Key Metadata** (`KEY#<id>` / `METADATA`)
```
key_id          str      e.g. "sk-gw-abc123"
name            str      human-readable label
team_id         str      e.g. "engineering"
role            str      "admin" | "team_lead" | "developer"
budget_limit    Decimal  monthly USD limit (Decimal for atomic math)
is_active       bool     False = revoked key
created_at      str      ISO 8601 UTC
GSI1PK          str      = team_id
GSI1SK          str      = "METADATA"
```

**Team Monthly Spend** (`TEAM#<id>` / `SPEND#YYYY-MM`)
```
team_id              str
month                str      "YYYY-MM"
total_spend_usd      Decimal  running sum — supports atomic ADD
total_requests       int
total_tokens         int
requests_blocked     int      budget-rejected request count (dashboard metric)
last_updated         str      ISO 8601 UTC
```

**Per-Request Usage Log** (`KEY#<id>` / `USAGE#<ts>`)
```
request_id          str
key_id              str
team_id             str
model               str      e.g. "claude-sonnet-4-6"
prompt_tokens       int
completion_tokens   int
total_tokens        int
actual_cost_usd     Decimal
estimated_cost_usd  Decimal
status              str      "success" | "error" | "partial"
timestamp           str      ISO 8601 UTC
GSI1PK              str      = team_id
GSI1SK              str      = "USAGE#<ts>"
```

**Idempotency Marker** (`PROCESSED#<req_id>` / `MARKER`)
```
request_id    str
processed_at  str   ISO 8601 UTC
TTL           int   Unix epoch timestamp — auto-expires in 30 days
```

### Setting Up the Database

```bash
# Start DynamoDB Local
docker-compose up -d dynamodb-local

# Provision table + seed 3 virtual keys and 2 team spend aggregates
python scripts/init_dynamodb.py

# Run 4-loop schema verification suite (all access patterns tested)
python scripts/test_schema_comprehensive.py
```

The verification suite covers:
1. **Loop 1** — Key RBAC: create, duplicate rejection, revocation, GSI1 team listing
2. **Loop 2** — Usage log time-series range queries and team-wide GSI1 queries
3. **Loop 3** — Atomic spend aggregate math with `Decimal` precision (5 concurrent updates verified)
4. **Loop 4** — Kafka idempotency replay protection via `attribute_not_exists(PK)` + TTL

---

## Project Structure

```
aperture/
├── gateway/                 # FastAPI gateway (Person A)
│   ├── main.py              # App entrypoint, middleware chain
│   ├── config.py            # Environment variable loading
│   ├── middleware/          # Request pipeline middleware (Person B)
│   │   ├── auth.py          # Virtual key authentication
│   │   └── budget.py        # Budget check & cost reservation
│   ├── routing/             # Provider routing & translation (Person A)
│   │   ├── translator.py    # OpenAI <-> Anthropic format translation
│   │   ├── streaming.py     # SSE streaming passthrough
│   │   └── circuit_breaker.py # Provider fallback logic
│   ├── events/              # Event publishing (Person C)
│   │   └── producer.py      # Kafka usage event producer
│   └── models/              # Shared Pydantic models (everyone)
│       └── schemas.py       # Request/response schemas + UsageEvent
├── consumer/                # Kafka consumer service (Person C)
├── dashboard/               # React analytics dashboard (Person C)
├── scripts/                 # One-time setup & verification (Person C)
│   ├── init_dynamodb.py     # Provision DynamoDB table & seed data
│   └── test_schema_comprehensive.py  # 4-loop schema verification suite
├── docker-compose.yml       # Local dev environment
├── Dockerfile               # Gateway container image
├── .env.example             # Environment variable template
└── requirements.txt         # Python dependencies
```

## Key Design Decisions

- **`request_id`**: Generated in `gateway/main.py` at request start (before auth/budget middleware). Read from `request.state.request_id`. See decision #8.
- **Usage field names**: Normalized to OpenAI format (`prompt_tokens` / `completion_tokens`). Shared contract across all services.
- **Port mapping**: Gateway → host `8080`, DynamoDB Local → host `8001` (container `8000`).
- **Kafka**: Fire-and-forget publishing (decision #7). Dropped events accepted as lost for hackathon scope.
- **Decimal precision**: All monetary amounts stored as DynamoDB `Number` via Python `Decimal` — enables native atomic `ADD` without floating-point drift.
- **Idempotency**: Kafka consumer writes `PROCESSED#<request_id>` with `attribute_not_exists(PK)` before updating spend aggregates, preventing double-counting on at-least-once delivery (decision #8).

## Known Limitations

- Virtual key revocation may take up to 60 seconds to propagate (Redis TTL, decision #4)
- Budget resets on fixed calendar boundaries (midnight UTC), not rolling windows (decision #5)
- Circuit breaker state is per-process, not shared across instances (decision #3)
- Redis fail-open window is per-instance (decision #2)
- DynamoDB TTL on idempotency markers is honoured eventually (not immediately) per AWS behaviour
