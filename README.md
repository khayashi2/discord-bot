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
- **Upsert Strategy** — channels and members are automatically upserted so metadata stays fresh without duplicates
- **Historical Backfill** — a one-off script ingests all past messages from every text channel, with batched commits and per-channel error handling
- **Web Dashboard** — a FastAPI-powered analytics dashboard with Chart.js visualizations: overview stats, most active users and channels, activity trend, top words, emoji usage, profanity leaderboard, and message length distribution
- **Time-Filtered Analytics** — dashboard supports 7-day, 30-day, and 90-day time range filters so you can view activity over any recent window
- **User Stats Page** — a dedicated per-user analytics page with a member dropdown; selecting a user fetches their stats via a JSON API and renders charts client-side (top words, activity over time, top channels, emoji usage, message length distribution)
- **Profanity Leaderboard** — ranks users by profanity usage using a configurable word list (`config/profanity.txt`), with Python-side counting over recent messages

## Plan

### Phase 1 — Project Scaffold & CI/CD (do this first)

Set up the repo structure, .gitignore, requirements.txt, .env.example, Dockerfile, docker-compose.yml, and a GitHub Actions workflow that runs linting and tests on PR. This gives you the skeleton everything else hangs on, and it matches your project instructions about branching and conventional commits.

### Phase 2 — Data Model & Database

Design and create your tables (users, messages, channels, etc.) with migrations (Alembic). This forces you to think about what data you need before writing any bot code.

### Phase 3 — Historical Backfill Script

Write the script that connects to Discord, iterates through channels, and ingests historical messages into the database. This is where you get your dataset.

### Phase 4 — Live Bot Listener

Set up the discord.py bot that listens for new messages and inserts them in real time. This is a thin layer on top of what you already built.

### Phase 5 — Dashboard (in progress)

Build the API endpoints and frontend to visualize the trends. The dashboard is live with eight analytics panels (overview stats, top users, top channels, activity over time, top words, emoji usage, profanity leaderboard, message length distribution), time-range filtering (7d/30d/90d), and a dedicated per-user stats page.

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

2. Fill in your `.env` with your Discord bot token.

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
│   ├── app.py            # Dashboard entry point & routes
│   ├── queries.py        # Analytics queries (top users, words, emoji, etc.)
│   ├── templates/        # Jinja2 HTML templates
│   │   ├── base.html     # Shared layout (nav, head, scripts)
│   │   ├── index.html    # Main dashboard page
│   │   └── user.html     # Per-user stats page
│   └── static/           # CSS, JS (Chart.js rendering)
│       ├── dashboard.js  # Main dashboard charts
│       └── user.js       # User stats client-side rendering
├── db/                   # Database layer
│   ├── models.py         # SQLAlchemy ORM models
│   ├── database.py       # Async engine & session
│   ├── operations.py     # Shared upsert/insert logic (used by listener & backfill)
│   └── migrations/       # Alembic migrations
├── scripts/              # One-off scripts
│   └── backfill.py       # Historical data ingestion
├── config.py             # Centralized settings from env vars
├── config/               # Static configuration files
│   └── profanity.txt     # Profanity word list for leaderboard
├── tests/                # Test suite
├── docker-compose.yml    # Service orchestration
├── Dockerfile            # Container image
├── .claude/              # Claude Code configuration
│   ├── agents/           # Specialized sub-agents
│   ├── hooks/            # Tool-use hooks
│   ├── skills/           # Reusable skill definitions
│   └── settings.json     # Project-level settings
└── .github/workflows/    # CI/CD pipeline
```

## Design Decisions & Thought Process

This section documents the "why" behind key decisions — useful context if you're learning or extending the project.

### Storing Full Message Content

**What:** Every message is saved in full (not just metadata like timestamps or word counts).

**Why:** Storing raw content keeps your options open. You can always derive new analytics later (e.g., sentiment analysis, slang detection) without re-fetching from Discord's API — which has strict rate limits and only retains messages in accessible channels.

**Consider:** This means the database will grow faster and stores potentially sensitive text. In a production bot you'd want to think about data retention policies and user privacy. For a portfolio project, this trade-off is worth the flexibility.

### Upserts for Channels and Members

**What:** Every time a message arrives, the bot upserts (insert-or-update) the channel and member before inserting the message.

**Why:** Discord metadata changes constantly — users update display names, channels get renamed. Upserting on every message keeps your local data fresh without needing a separate sync job. Messages themselves use `ON CONFLICT DO NOTHING` since their content doesn't change after creation.

**Consider:** This adds a few extra queries per message. At small scale it's negligible. If you were handling thousands of messages per second, you'd batch writes or use a queue. For a single-server bot, simplicity wins.

### Emoji Counting with Regex

**What:** A compiled regex pattern counts both custom Discord emojis (`<:name:id>`) and standard Unicode emojis in each message.

**Why:** Pre-computing `emoji_count` at insert time means dashboard queries can sort/filter by emoji usage without scanning message content at read time. The regex handles both emoji types in one pass.

**Consider:** Unicode emoji ranges evolve over time — new emoji get added with each Unicode release. The current pattern covers the most common ranges but won't catch every future emoji. For a portfolio project this is a reasonable trade-off; a production bot might use a dedicated emoji library.

### Shared DB Operations Module

**What:** The upsert/insert logic lives in `db/operations.py`, a shared module imported by both the live listener cog and the backfill script.

**Why:** Without this, you'd have identical upsert code in two places. When one changes (e.g., adding a new column), the other could fall out of sync, leading to subtle bugs. Extracting shared logic into a single module means both code paths are guaranteed to behave identically.

**Consider:** The alternative is keeping the logic in the listener and having the backfill import from it — but that creates a dependency from a script to a bot cog, which is architecturally backwards. A neutral `db/` module is the cleanest boundary.

### Historical Backfill Design

**What:** The backfill script connects as a plain `discord.Client`, iterates every text channel, and inserts all historical messages with batched commits (every 500 messages).

**Why:** Batching avoids holding a giant uncommitted transaction in memory. The `ON CONFLICT DO NOTHING` on messages makes the script idempotent — you can safely re-run it after a crash and it picks up where it left off (already-inserted messages are skipped). Bot messages are filtered out since they don't represent real user activity.

**Consider:** The script runs sequentially through channels (no parallelism). This is intentional — parallel channel fetches would compound Discord's rate limits and make error handling harder. For a single server, sequential iteration is simple and reliable. discord.py's built-in rate limiter handles API throttling transparently.

### Analytics Dashboard Architecture

**What:** The dashboard uses a dedicated `queries.py` module that runs analytics queries against the database and returns plain dicts/lists. Some analytics (top words, emoji extraction) are computed in Python over recent rows rather than pure SQL.

**Why:** Separating queries into their own module keeps `app.py` clean — it only handles routing and template rendering. For word counting and emoji extraction, Python's `Counter` and regex are simpler to write and maintain than equivalent PostgreSQL functions, especially when operating over a bounded set of recent messages (5,000 for words, 2,000 for emoji).

**Consider:** This approach works well at small-to-medium scale. As the dataset grows, pulling thousands of rows into Python becomes slower. The natural next step would be materialized views or PostgreSQL full-text search aggregation for word counts, and a dedicated emoji table for emoji stats. The code includes comments flagging these future optimization points.

### Time-Filtered Dashboard

**What:** Every main dashboard query accepts an optional `after` parameter. The UI offers 7-day, 30-day, and 90-day filter buttons that reload the page with a `?range=` query parameter.

**Why:** All-time stats are interesting, but users often want to see *recent* trends — who's been most active this week, what words are trending this month. Adding a cutoff parameter to each query is a minimal change that unlocks a much more useful dashboard.

**Consider:** The filter is applied server-side — each range selection triggers a full page reload. For a smoother experience you could fetch filtered data via AJAX, but a page reload is simpler and avoids managing client-side state. The `cutoff_from_range()` helper centralizes the range-to-datetime conversion so the route handler stays clean.

### User Stats Page

**What:** A dedicated `/user` page with a member dropdown. Selecting a user calls `/api/user/{member_id}`, which returns per-user analytics as JSON. The client-side JavaScript (`user.js`) renders charts from the response.

**Why:** The main dashboard shows server-wide trends, but users want to see their own stats. A JSON API + client-side rendering avoids a full page reload on every user switch and lets you reuse the same Chart.js patterns from the main dashboard.

**Consider:** This is the project's first client-side data fetching pattern — the main dashboard uses server-rendered templates with `data-*` attributes. The API approach is more flexible (you could build a mobile client or embed stats in a Discord command) but introduces a second rendering path to maintain.

### Profanity Leaderboard

**What:** A leaderboard ranking users by profanity usage. The word list is loaded from `config/profanity.txt` — a plain text file with one word per line.

**Why:** It's a fun social feature that drives engagement. Making the word list a file (not hardcoded) means server admins can customize it without touching code. The list is loaded once and cached in memory via `settings.load_profanity_words()`.

**Consider:** Like top-words, profanity counting is done in Python over a bounded set of recent messages (10,000). The same trade-off applies — simple now, materialized view later if needed. In a real deployment you'd keep the word list out of version control (e.g., mount it as a Docker secret); it's committed here for portfolio completeness.

### Async Database Access

**What:** The bot uses `asyncpg` with SQLAlchemy's async sessions instead of synchronous database calls.

**Why:** discord.py is fully async — blocking the event loop with synchronous DB calls would freeze the bot for every message. Async sessions let database writes happen without blocking other events (like responding to commands).

**Consider:** Async code is harder to debug (stack traces are less obvious). SQLAlchemy's async API mirrors the sync one closely, but you need to be careful with session lifetimes — always use `async with` to ensure sessions are properly closed.

## Branch Strategy

- `main` — protected, no direct commits
- `feature/<name>` — all new work
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`
