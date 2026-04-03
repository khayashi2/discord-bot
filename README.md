# Discord Analytics Bot

A Discord bot that tracks server activity and displays fun analytics on a web dashboard — including top words, most active users, emoji usage, and more.

## Tech Stack

- **Bot**: Python 3.12, discord.py v2
- **Database**: PostgreSQL 16 (via Docker)
- **Dashboard**: FastAPI + Jinja2 + Chart.js
- **Migrations**: Alembic + SQLAlchemy 2.0
- **CI/CD**: GitHub Actions (lint, test, Docker build)

## Features

- **Live Message Tracking** — the bot listens to every message in your server and stores it in PostgreSQL (content, author, channel, emoji count, attachments, and more)
- **Upsert Strategy** — guilds, channels, and members are automatically upserted so metadata stays fresh without duplicates
- **Historical Backfill** — a one-off script can ingest past messages from channel history
- **Web Dashboard** — a FastAPI-powered dashboard to visualize analytics (work in progress)

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development)
- A Discord bot token ([create one here](https://discord.com/developers/applications))

### Setup

1. Clone the repo and copy the environment file:

   ```bash
   cp .env.example .env
   ```

2. Fill in your `.env` with your Discord bot token and guild ID.

3. Start all services:

   ```bash
   docker compose up -d db
   docker compose --profile migration run --rm migrate
   docker compose up -d bot dashboard
   ```

4. Open the dashboard at [http://localhost:8000](http://localhost:8000).

### Running the Historical Backfill

```bash
docker compose --profile backfill run --rm backfill
```

### Local Development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
ruff check .
```

## Project Structure

```text
├── bot/                  # Discord bot (discord.py)
│   ├── main.py           # Bot entry point
│   └── cogs/             # Command extensions
│       └── listener.py   # Live message listener & DB persistence
├── dashboard/            # Web dashboard (FastAPI)
│   ├── app.py            # Dashboard entry point
│   ├── templates/        # Jinja2 HTML templates
│   └── static/           # CSS, JS, images
├── db/                   # Database layer
│   ├── models.py         # SQLAlchemy ORM models
│   ├── database.py       # Async engine & session
│   └── migrations/       # Alembic migrations
├── scripts/              # One-off scripts
│   └── backfill.py       # Historical data ingestion
├── config.py             # Centralized settings from env vars
├── tests/                # Test suite
├── docker-compose.yml    # Service orchestration
├── Dockerfile            # Container image
└── .github/workflows/    # CI/CD pipeline
```

## Branch Strategy

- `main` — protected, no direct commits
- `feature/<name>` — all new work
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`
