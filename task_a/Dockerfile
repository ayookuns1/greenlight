# ── Task A Dockerfile ──────────────────────────────────────────────────────────
# Team Greenlight — DSN x BCT LLM Agent Hackathon 3.0
# Runs the User Modeling API on port 8001

FROM python:3.10-slim

# Metadata
LABEL maintainer="Team Greenlight"
LABEL task="A - User Modeling"
LABEL port="8001"

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer caching)
COPY task_a/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY task_a/ .

# Copy the data directory (user_profiles.json lives here)
COPY data/ /app/data/

# Expose API port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"

# Run the API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
