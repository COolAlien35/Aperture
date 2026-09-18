"""
Gateway configuration — loads environment variables for all services.

Used by: everyone (Person A, B, C)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM Provider Keys ---
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# --- Infrastructure ---
REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")
KAFKA_BROKER: str = os.getenv("KAFKA_BROKER", "kafka:9092")
DYNAMODB_ENDPOINT: str = os.getenv("DYNAMODB_ENDPOINT", "http://dynamodb-local:8000")

# --- Gateway Defaults ---
DEFAULT_MAX_TOKENS: int = int(os.getenv("DEFAULT_MAX_TOKENS", "4096"))
GATEWAY_PORT: int = int(os.getenv("GATEWAY_PORT", "8000"))
