FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    GUNICORN_WORKERS=4 \
    GUNICORN_THREADS=2 \
    GUNICORN_TIMEOUT=120 \
    GUNICORN_GRACEFUL_TIMEOUT=30

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt gunicorn==21.2.0

RUN useradd --create-home --shell /bin/bash app

COPY --chown=app:app . /app

RUN mkdir -p /app/logs && chown app:app /app/logs
RUN mkdir -p /app/.pytest_cache && chown -R app:app /app/.pytest_cache

USER app

EXPOSE 8001

CMD ["gunicorn", "notification_app.main:app", \
    "--workers", "4", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--bind", "0.0.0.0:8001", \
    "--timeout", "120", \
    "--graceful-timeout", "30", \
    "--keep-alive", "5", \
    "--max-requests", "1000", \
    "--max-requests-jitter", "50", \
    "--log-level", "info", \
    "--access-logfile", "-", \
    "--error-logfile", "-"]