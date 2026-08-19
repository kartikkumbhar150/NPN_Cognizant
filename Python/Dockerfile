# ── NPN Bank Backend — v12 ───────────────────────────────────────────────────
# Single container serves:
#   - Redis Server (local cache, 4-hour data TTL)
#   - Employee Dashboard API  →  /api/*
#   - Chatbot                 →  /chatbot/ask
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV REDIS_URL=redis://localhost:6379/0

# Install Redis server
RUN apt-get update && apt-get install -y redis-server && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Explicitly copy marketing images (folder name has a space — be explicit)
COPY ["marketing images", "/app/marketing images"]

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose port 8000
EXPOSE 8000

# Start both Redis and FastAPI
CMD ["./entrypoint.sh"]
