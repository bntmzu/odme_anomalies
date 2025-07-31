# 🧭 ODME — Occult & Deviation Monitoring Engine

![ODME demo](https://media1.tenor.com/m/AWlbea7E5c8AAAAd/stranger-things-martin-brenner.gif)

**ODME** is a microservice for monitoring and resolving mythological anomalies. Agents can report supernatural events, and the system evaluates their threat level based on attributes such as magical intensity, invisibility, or aggression. The service provides endpoints for ingestion, reporting, resolving, and listing active anomalies.

---

## 🚀 Features

- Ingest mythological anomaly reports with real-time threat level evaluation.
- Manage agent reports tied to specific anomalies.
- Mark anomalies as resolved.
- SQLite + SQLAlchemy (async) with Alembic migrations.
- Clean API with FastAPI & Pydantic (v2).
- Docker-based dev/prod environments.
- Test suite with `pytest`, `httpx`, `pytest-asyncio`.

---

## 🏗️ Project Structure

The codebase uses a clean architecture with async support:

 ```
src/
├── odme_anomalies/
│ ├── api/
│ │ └── v1/
│ │ ├── endpoints/ # ingest, report, resolve, anomalies
│ │ └── router.py
│ ├── db/ # models, session, base
│ ├── crud/ # DB interactions
│ ├── schemas/ # Pydantic v2 models (with Czech aliases)
│ ├── services/ # Business logic: threat scoring
│ └── core/ # Configuration
└── tests/ # Async API tests
│
└── alembic/ # DB migrations
```

---

## 🐳 Docker – Development Workflow

```bash
# Build dev container
docker build -f Dockerfile -t odme-dev --target dev .

# Run with interactive shell to apply migrations and test
docker run --rm -it odme-dev
```

 Or manually

```bash
poetry install
alembic upgrade head
pytest
```

⚠️ .env.example file

```bash
DATABASE_URL=
ALEMBIC_DATABASE_URL=
PORT=
```

## 🧪 🏗️ Production Build

```bash
docker compose up --build
# or for standalone
docker build -f Dockerfile -t odme-prod --target prod .
docker run -p 8000:8000 odme-prod
```
