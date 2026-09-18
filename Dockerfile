FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the gateway port
EXPOSE 8000

# Run with hot-reload for dev (volume mount in docker-compose overrides the COPY)
CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
