FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/list/*

ENV PATH="/root/.local/bin:$PATH"
RUN python -m pip install --user pipx && \
    pipx install uv

WORKDIR /app

COPY requirements.txt .
COPY .env .
RUN  uv pip install --no-cache-dir --system -r requirements.txt

COPY src ./src

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]