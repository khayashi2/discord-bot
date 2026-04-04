# Project: Discord Analytics Bot

## Overview

A Discord bot that tracks server activity and displays fun analytics (top words, most active users, swear counts, emoji usage, etc.) on a web dashboard. Built as a portfolio/resume project.

## Tech Stack

- Python 3.12
- discord.py v2
- PostgreSQL 16 (via Docker)
- FastAPI + Jinja2 + Chart.js (dashboard)
- SQLAlchemy 2.0 + Alembic (ORM & migrations)
- Docker & Docker Compose
- GitHub Actions (CI/CD)

## Release Management

- Do NOT commit directly to main
- Branch naming: `feature/<command-name>` for new features
- All commits must follow conventional commit messages: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`
- Always create PRs to merge into main

## Environment Variable Handling

- NEVER hardcode API keys, Discord tokens, or any credentials
- Always reference a `.env` file (see `.env.example` for required variables)
- When adding new required variables, update `.env.example`

## Architecture

- `bot/` — Discord bot (discord.py), live message listener
- `dashboard/` — Web dashboard (FastAPI + Jinja2 + Chart.js)
- `db/` — Database layer (SQLAlchemy models, Alembic migrations)
- `scripts/` — One-off scripts (e.g., historical backfill)
- `tests/` — Test suite (pytest + pytest-asyncio)
- `config.py` — Centralized settings from environment variables
- `.claude/` — Claude Code configuration: agents (code-reviewer, dashboard-builder, etc.), skills, hooks, and `settings.json` for project-level settings (`settings.local.json` for local overrides, not committed)

## Key Design Decisions

- Storing full message content (not just metadata) to enable flexible analytics
- Bot, dashboard, and backfill script are separate entry points sharing the same DB
- PostgreSQL via Docker Compose for all environments
- Async database access via asyncpg + SQLAlchemy async sessions

## Running Locally

```bash
docker compose up -d db
docker compose --profile migration run --rm migrate
docker compose up -d bot dashboard
```

## Testing & Linting

```bash
pytest tests/ -v
ruff check .
ruff format --check .
```

## Learning Opportunity

As a junior developer, I also document why certain decisions were made, how it was implemented, and anything to consider when implementing. I want to include this part in the README file — a section that explains the thought process.

### Message Listener Cog

The `listener.py` cog uses discord.py's `Cog.listener()` decorator to hook into the `on_message` event. Every non-DM, non-bot message triggers upserts for the channel and member, followed by an insert for the message itself. Key choices:

- **Upserts via `ON CONFLICT`** — PostgreSQL's `INSERT ... ON CONFLICT DO UPDATE` keeps metadata fresh (e.g., a user's display name) without failing on duplicates. Messages use `ON CONFLICT DO NOTHING` since message content doesn't change.
- **Emoji counting with regex** — a compiled regex pattern matches both custom Discord emojis (`<:name:id>`) and standard Unicode emoji ranges, giving us an `emoji_count` column for analytics without a separate parsing step.
- **Single-server design** — the bot is designed for one server, so there is no `guilds` table. Members use their Discord user ID as the primary key.

## Coding Standards and Best Practices

Use [PEP-0008](https://peps.python.org/pep-0008/) as a reference for coding practice in Python. As for other tech stacks, follow what a professional software engineer would commonly follow for practices and standards as stated on [Geek for Geeks SWE Guidelines](https://www.geeksforgeeks.org/software-engineering/coding-standards-and-guidelines/)

### Project-Specific Rules

- **Always use async sessions**: `async with async_session() as session` — never use synchronous `Session()`
- **Use `select()` over `session.query()`**: Follow SQLAlchemy 2.0 style with `select(Model).where(...)` instead of the legacy `session.query(Model).filter(...)` pattern
- **Upserts use raw `insert()` + `on_conflict_do_update()`**: For channels and members, use PostgreSQL's native `ON CONFLICT` via SQLAlchemy's `insert()` dialect, not ORM merge
- **Environment variables via `config.py`**: All settings flow through `config.py` — never read `os.environ` directly in bot or dashboard code
