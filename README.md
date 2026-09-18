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
| **DynamoDB Local** | `8000` | Keys, budgets, usage aggregates |

## Project Structure

```
aperture/
├── gateway/                 # FastAPI gateway (Person A)
│   ├── main.py              # App entrypoint, middleware chain
│   ├── config.py            # Environment variable loading
│   ├── middleware/           # Request pipeline middleware (Person B)
│   │   ├── auth.py          # Virtual key authentication
│   │   └── budget.py        # Budget check & cost reservation
│   ├── routing/             # Provider routing & translation (Person A)
│   │   ├── translator.py    # OpenAI <-> Anthropic format translation
│   │   ├── streaming.py     # SSE streaming passthrough
│   │   └── circuit_breaker.py # Provider fallback logic
│   ├── events/              # Event publishing (Person C)
│   │   └── producer.py      # Kafka usage event producer
│   └── models/              # Shared Pydantic models (everyone)
│       └── schemas.py       # Request/response schemas
├── consumer/                # Kafka consumer service (Person C)
├── dashboard/               # React analytics dashboard (Person C)
├── docker-compose.yml       # Local dev environment
├── Dockerfile               # Gateway container image
├── .env.example             # Environment variable template
└── requirements.txt         # Python dependencies
```

## Key Design Decisions

- **`request_id`**: Generated in `gateway/main.py` at request start (before auth/budget middleware). Read from `request.state.request_id`. See decision #8.
- **Usage field names**: Normalized to OpenAI format (`prompt_tokens` / `completion_tokens`). Shared contract across all services.
- **Port mapping**: Gateway runs on **host port 8080** (container port 8000) to avoid collision with DynamoDB Local on port 8000.
- **Kafka**: Fire-and-forget publishing (decision #7). Dropped events accepted as lost for hackathon scope.

## Known Limitations

- Virtual key revocation may take up to 60 seconds to propagate (Redis TTL, decision #4)
- Budget resets on fixed calendar boundaries (midnight UTC), not rolling windows (decision #5)
- Circuit breaker state is per-process, not shared across instances (decision #3)
- Redis fail-open window is per-instance (decision #2)
