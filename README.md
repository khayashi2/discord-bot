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

## Plan

### Phase 1 — Project Scaffold & CI/CD (do this first)
Set up the repo structure, .gitignore, requirements.txt, .env.example, Dockerfile, docker-compose.yml, and a GitHub Actions workflow that runs linting and tests on PR. This gives you the skeleton everything else hangs on, and it matches your project instructions about branching and conventional commits.

### Phase 2 — Data Model & Database
Design and create your tables (users, messages, channels, etc.) with migrations (Alembic). This forces you to think about what data you need before writing any bot code.

### Phase 3 — Historical Backfill Script
Write the script that connects to Discord, iterates through channels, and ingests historical messages into the database. This is where you get your dataset.
### Phase 4 — Live Bot Listener

Set up the discord.py bot that listens for new messages and inserts them in real time. This is a thin layer on top of what you already built.
### Phase 5 — Dashboard

Build the API endpoints and frontend to visualize the trends.

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

## Design Decisions & Thought Process

This section documents the "why" behind key decisions — useful context if you're learning or extending the project.

### Storing Full Message Content

**What:** Every message is saved in full (not just metadata like timestamps or word counts).

**Why:** Storing raw content keeps your options open. You can always derive new analytics later (e.g., sentiment analysis, slang detection) without re-fetching from Discord's API — which has strict rate limits and only retains messages in accessible channels.

**Consider:** This means the database will grow faster and stores potentially sensitive text. In a production bot you'd want to think about data retention policies and user privacy. For a portfolio project, this trade-off is worth the flexibility.

### Upserts for Guilds, Channels, and Members

**What:** Every time a message arrives, the bot upserts (insert-or-update) the guild, channel, and member before inserting the message.

**Why:** Discord metadata changes constantly — users update display names, channels get renamed, servers change icons. Upserting on every message keeps your local data fresh without needing a separate sync job. Messages themselves use `ON CONFLICT DO NOTHING` since their content doesn't change after creation.

**Consider:** This adds a few extra queries per message. At small scale it's negligible. If you were handling thousands of messages per second, you'd batch writes or use a queue. For a single-server bot, simplicity wins.

### Composite Primary Key on Members

**What:** The `members` table uses `(id, guild_id)` as its primary key instead of just the Discord user ID.

**Why:** The same Discord user can be in multiple servers with different display names, avatars, and join dates. A composite key lets you track per-server member data accurately.

**Consider:** This means foreign keys pointing to members (like on messages) also need both columns. It's a bit more work in queries, but it correctly models the relationship.

### Emoji Counting with Regex

**What:** A compiled regex pattern counts both custom Discord emojis (`<:name:id>`) and standard Unicode emojis in each message.

**Why:** Pre-computing `emoji_count` at insert time means dashboard queries can sort/filter by emoji usage without scanning message content at read time. The regex handles both emoji types in one pass.

**Consider:** Unicode emoji ranges evolve over time — new emoji get added with each Unicode release. The current pattern covers the most common ranges but won't catch every future emoji. For a portfolio project this is a reasonable trade-off; a production bot might use a dedicated emoji library.

### Async Database Access

**What:** The bot uses `asyncpg` with SQLAlchemy's async sessions instead of synchronous database calls.

**Why:** discord.py is fully async — blocking the event loop with synchronous DB calls would freeze the bot for every message. Async sessions let database writes happen without blocking other events (like responding to commands).

**Consider:** Async code is harder to debug (stack traces are less obvious). SQLAlchemy's async API mirrors the sync one closely, but you need to be careful with session lifetimes — always use `async with` to ensure sessions are properly closed.

## Branch Strategy

- `main` — protected, no direct commits
- `feature/<name>` — all new work
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`
