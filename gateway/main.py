"""
Aperture Gateway — FastAPI application entrypoint.

This is the universal AI gateway that accepts OpenAI-compatible requests
and routes them to upstream LLM providers (Anthropic, OpenAI).

Request pipeline order:
1. request_id generation (here, before any middleware)
2. auth_middleware (Person B)
3. budget_check_middleware (Person B)
4. translator + router (Person A)

See: PRD section 5.1, architecture diagram
"""

import uuid
import time
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
import os
import boto3
from contextlib import asynccontextmanager

from gateway.middleware.auth import auth_middleware
from gateway.middleware.budget import budget_check_middleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Redis connection pool
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    app.state.redis = redis.from_url(redis_url, decode_responses=True)

    # Initialize DynamoDB client (Team C dependency)
    dynamodb_endpoint = os.getenv("DYNAMODB_URL", "http://localhost:8000")
    app.state.dynamo = boto3.client(
        "dynamodb",
        endpoint_url=dynamodb_endpoint,
        region_name="us-east-1",
        aws_access_key_id="DUMMYIDEXAMPLE",
        aws_secret_access_key="DUMMYEXAMPLEKEY",
    )

    # Load Lua budget script
    script_path = os.path.join(
        os.path.dirname(__file__), "redis_scripts", "budget_script.lua"
    )
    try:
        with open(script_path, "r") as f:
            script_content = f.read()
            # Load script into Redis and store SHA for fast execution
            app.state.budget_script_sha = await app.state.redis.script_load(
                script_content
            )
            logger.info(f"Loaded budget Lua script. SHA: {app.state.budget_script_sha}")
    except Exception as e:
        logger.error(f"Failed to load Lua script: {e}")
        app.state.budget_script_sha = None

    yield

    # Shutdown
    await app.state.redis.close()


app = FastAPI(
    title="Aperture AI Gateway",
    description="Enterprise AI Gateway & Spend Management Platform",
    version="1.0.0",
    lifespan=lifespan,
)


# ──────────────────────────────────────────────
# CORS Middleware
# ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Middleware: request_id generation
# Per design decision #8 — generated ONCE at request start,
# before auth or budget middleware, so retries/reconciliation
# share the same ID.
#
# B and C: read this from request.state.request_id
# ──────────────────────────────────────────────
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    request.state.start_time = time.time()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


# ──────────────────────────────────────────────
# Health check — for Docker healthchecks and manual testing
# ──────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


# ──────────────────────────────────────────────
# Main endpoint — OpenAI-compatible chat completions
# PRD 5.1: Universal API Endpoint
# ──────────────────────────────────────────────
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    OpenAI-compatible chat completions endpoint.

    Pipeline:
    1. request_id already set by middleware above
    2. Auth middleware (Person B) — resolves identity
    3. Budget check middleware (Person B) — reserves estimated cost
    4. Translate to provider format, call provider, translate response back
    5. Reconcile actual cost (Person B)
    6. Publish usage event to Kafka (Person C) — fire-and-forget
    """
    # Step 2: Auth (stub — always passes)
    request = await auth_middleware(request)

    # Step 3: Budget check (stub — always allows)
    request = await budget_check_middleware(request)

    # Step 4: Parse the request body
    body = await request.json()

    # For now, return a placeholder response showing the pipeline works
    # TODO (Tasks 3-4): Replace with real translator + provider call
    return JSONResponse(
        content={
            "id": f"chatcmpl-{request.state.request_id[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.get("model", "unknown"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "[STUB] Gateway pipeline working — translator not yet implemented.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
            "_debug": {
                "request_id": request.state.request_id,
                "key_id": request.state.key_id,
                "team_id": request.state.team_id,
                "role": request.state.role,
                "reserved": request.state.reserved,
            },
        }
    )
