FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

RUN useradd --create-home --shell /bin/bash app

COPY . /app

RUN mkdir -p /app/logs && chown app:app /app/logs

RUN mkdir -p /app/.pytest_cache && chown -R app:app /app/.pytest_cache

USER app

EXPOSE 8001

CMD ["uvicorn", "notification_app.main:app", "--host", "0.0.0.0", "--port", "8001"]
