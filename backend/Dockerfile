FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

EXPOSE 8000

# start.sh launches the MCP server (port 8001) in background first,
# then the FastAPI app (port $PORT / 8000) in foreground.
# This is needed for single-container deployments (Render, Railway, etc.)
# where docker-compose is not used.
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
