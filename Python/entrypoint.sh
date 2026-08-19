#!/bin/bash
# Start Redis server in the background
echo "Starting Redis server..."
redis-server --daemonize yes

# Wait for Redis to be ready
sleep 2

# Start the FastAPI app
echo "Starting FastAPI app..."
exec uvicorn api_server:app --host 0.0.0.0 --port 8000
