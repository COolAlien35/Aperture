FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY gateway/ ./gateway/
COPY consumer/ ./consumer/

# The consumer is a module — run with python -m
CMD ["python", "-m", "consumer.main"]
