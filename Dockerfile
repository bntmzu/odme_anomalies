FROM python:3.11-slim AS base

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false

# -------------------
# PRODUCTION TARGET
# -------------------
FROM base AS prod
RUN poetry install --only main --no-root --no-interaction --no-ansi
COPY . .
ENV PYTHONPATH=/app/src

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "src.odme_anomalies.main:app", "--bind", "0.0.0.0:8000", "--workers=4", "--timeout=120"]

# -------------------
# DEV / TEST TARGET
# -------------------
FROM base AS dev
RUN poetry install --no-root --no-interaction --no-ansi
COPY . .
ENV PYTHONPATH=/app/src

CMD ["/bin/bash", "-c", "alembic upgrade head && pytest"]
