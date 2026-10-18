FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=600 PIP_RETRIES=5 HF_HOME=/opt/hf-cache

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch keeps the image far smaller than the default CUDA build.
# Increase timeout/retry policy because the PyTorch wheel is large and can stall on
# slower or busy network connections during Docker builds.
RUN pip install --retries 5 --timeout 600 --index-url https://download.pytorch.org/whl/cpu torch

COPY requirements.txt .
RUN pip install -r requirements.txt \
    && python -m spacy download en_core_web_sm

# Download the transformer at build time so the first request is not slow and the
# container does not need internet access at runtime.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY . .
RUN useradd --create-home appuser && mkdir -p /app/uploads && chown -R appuser /app /opt/hf-cache
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
  CMD curl -fs http://localhost:8000/api/health || exit 1

# Apply migrations, then start the API.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
