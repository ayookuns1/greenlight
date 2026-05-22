# ── Task B Dockerfile ──────────────────────────────────────────────────────────
# Team Greenlight — DSN x BCT LLM Agent Hackathon 3.0
# Runs the Recommendation API on port 8002

FROM python:3.10-slim

LABEL maintainer="Team Greenlight"
LABEL task="B - Recommendation"
LABEL port="8002"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY task_b/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download the sentence-transformer model so Docker image is self-contained
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY task_b/ .

# Copy data (combined_sample.json, user_profiles.json, faiss_index.pkl)
COPY data/ /app/data/

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]
