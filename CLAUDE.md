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
- `db/` — Database layer (SQLAlchemy models, Alembic migrations, shared operations)
- `scripts/` — One-off scripts (e.g., historical backfill)
- `tests/` — Test suite (pytest + pytest-asyncio)
- `config.py` — Centralized settings from environment variables
- `.claude/` — Claude Code configuration: agents (code-reviewer, dashboard-builder, etc.), skills, hooks, and `settings.json` for project-level settings (`settings.local.json` for local overrides, not committed)

## Key Design Decisions

- Storing full message content (not just metadata) to enable flexible analytics
- Bot, dashboard, and backfill script are separate entry points sharing the same DB via `db/operations.py`
- Shared DB operations (`db/operations.py`) — upsert/insert logic extracted so both listener and backfill use identical persistence code
- PostgreSQL via Docker Compose for all environments
- Async database access via asyncpg + SQLAlchemy async sessions
- Dashboard analytics split into `dashboard/queries.py` — each query function returns plain dicts so the route handler stays thin
- Time-filtered queries — every main query accepts an optional `after` datetime; `cutoff_from_range()` converts `7d`/`30d`/`90d` to a cutoff timestamp
- Per-user stats via JSON API — `/api/user/{member_id}` returns user analytics as JSON, rendered client-side by `dashboard/static/user.js`
- Profanity leaderboard — configurable word list loaded from `config/profanity.txt`, cached in `settings.load_profanity_words()`; collapsible word reference on landing page; per-user top profanity words on user stats page
- Activity heatmap — `get_activity_heatmap()` uses PostgreSQL `EXTRACT(dow/hour)` to group messages by day-of-week and hour; rendered as a CSS grid (not Chart.js) with color intensity
- Awards & superlatives — `get_awards()` runs 7 targeted sub-queries (Night Owl, Early Bird, Emoji Monarch, Novelist, Chatterbox, Editor, Attachment Pro); server-rendered badge grid, no JS
- Vocabulary diversity — `get_vocabulary_diversity()` computes type-token ratio per user over bounded message sets; horizontal bar chart via Chart.js
- Conversation flow — `get_conversation_flow()` identifies consecutive-message reply pairs within a 5-minute gap in the same channel; server-rendered HTML table

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

### Historical Backfill Script

The `scripts/backfill.py` script connects as a plain `discord.Client` (not a `commands.Bot`) since it only needs read access to channel history. Key choices:

- **Shared operations via `db/operations.py`** — the same `upsert_channel`, `upsert_member`, and `insert_message` functions are used by both the live listener and the backfill, eliminating code duplication and ensuring consistent persistence logic.
- **Batched commits (every 500 messages)** — committing periodically bounds memory usage and ensures partial progress is saved. If the script crashes mid-channel, already-committed batches are safe and `ON CONFLICT DO NOTHING` makes re-runs skip duplicates.
- **Sequential channel iteration** — channels are processed one at a time to avoid compounding Discord API rate limits. discord.py's built-in rate limiter handles throttling transparently.
- **Per-channel error handling** — `discord.Forbidden` and `discord.HTTPException` are caught per-channel so one inaccessible channel doesn't abort the entire backfill.
- **Bot messages filtered** — bot-authored messages are skipped during backfill since they don't represent real user activity for analytics.

### Analytics Dashboard

The `dashboard/queries.py` module contains all analytics query functions. Each function takes an `AsyncSession` and returns plain dicts/lists ready for Jinja2 templates. Key choices:

- **Thin route handler** — `app.py` calls query functions and passes results to the template. If a query fails, the route falls back to an empty-context dict so the page still renders.
- **Python-side aggregation for text analytics** — top-words and emoji extraction pull a bounded set of recent rows (5,000 / 2,000) and aggregate with `Counter` in Python. This is simpler than equivalent PostgreSQL functions and fast enough at current scale. Comments in the code flag where to add materialized views if volume grows.
- **Chart.js via data attributes** — analytics data is serialized into `data-*` attributes on a hidden `<div>`, then read by `dashboard.js` to render charts. This avoids inline `<script>` blocks and keeps JS separate from Jinja2 templates.
- **Stopword filtering** — top-words results exclude common English stopwords (defined in `queries.py`) so the list shows meaningful vocabulary rather than "the", "and", "is".

### Time-Filtered Dashboard

Every main query function in `queries.py` accepts an optional `after: datetime | None` parameter. The route handler converts the `?range=` query parameter into a cutoff datetime via `cutoff_from_range()`. Key choices:

- **Optional filter pattern** — adding `after` as an optional parameter means queries work unchanged for all-time stats (`after=None`) and filtered views. Each query conditionally appends `.where(Message.created_at >= after)` only when a cutoff is provided.
- **Server-side filtering** — the range buttons trigger a full page reload with a query parameter. This is simpler than client-side AJAX filtering and keeps the dashboard working without JavaScript for the main view.

### User Stats Page

The `/user` page and `/api/user/{member_id}` endpoint provide per-user analytics. Key choices:

- **JSON API + client-side rendering** — unlike the main dashboard (server-rendered via Jinja2 + `data-*` attributes), user stats are fetched as JSON and rendered by `user.js`. This avoids a page reload when switching users but introduces a second rendering path to maintain.
- **Dedicated query functions** — each per-user query (`get_user_top_words`, `get_user_activity_over_time`, etc.) mirrors the server-wide version but filters by `member_id`. These are separate functions rather than adding a `member_id` parameter to existing queries, keeping each function focused and testable.
- **Member existence check** — the API returns 404 for unknown member IDs rather than silently returning empty data, so client-side code can distinguish "no data yet" from "bad ID".

### Profanity Leaderboard

The `get_profanity_leaderboard()` query scans recent messages and counts profanity hits per user. Key choices:

- **File-based word list** — profanity words are loaded from `config/profanity.txt` (one word per line, `#` comments supported). This makes the list editable by server admins without code changes.
- **Cached loading** — `settings.load_profanity_words()` reads the file once and caches the result as a `frozenset` for O(1) membership checks. Subsequent calls return the cached set. There is no reload mechanism — the bot or dashboard must be restarted to pick up changes to `profanity.txt`.
- **Python-side counting** — like top-words and emoji stats, profanity counting is done in Python over a bounded set of messages (10,000). The same scalability comments apply.

### Activity Heatmap

The `get_activity_heatmap()` query uses PostgreSQL's `EXTRACT(dow)` and `EXTRACT(hour)` to bucket messages by day-of-week and hour. Key choices:

- **Pure CSS grid, not Chart.js** — a 7×24 heatmap maps naturally to an HTML grid with colored cells. Chart.js doesn't have a native heatmap type, so using DOM manipulation avoids pulling in a chart plugin. Color intensity is linearly interpolated from the accent color based on `count / maxCount`.
- **UTC hours** — all timestamps are stored in UTC, so the heatmap shows UTC hours. The heading includes a "(UTC)" label. Converting to local time would require knowing the server's timezone, which isn't tracked.
- **Day ordering** — PostgreSQL `EXTRACT(dow)` returns 0=Sunday, but the grid renders Monday first (order: 1,2,3,4,5,6,0) for a more conventional week layout.

### Awards & Superlatives

The `get_awards()` function runs 7 independent sub-queries, each finding the top member for a specific criterion. Key choices:

- **Separate sub-queries** — each award has different aggregation logic (COUNT, SUM, AVG with HAVING), so a single combined query would be complex and hard to maintain. The trade-off is 7 DB round-trips per page load; a future optimization could use `asyncio.gather()` for concurrency within the same session.
- **Minimum thresholds** — the Novelist award requires at least 50 messages to prevent a user with one long message from winning. Other count-based awards naturally favor active users.
- **Server-rendered HTML** — awards are rendered as a Jinja2 template grid (no Chart.js or client-side JS). This keeps the rendering path simple and consistent with the awards' static nature.

### Vocabulary Diversity

The `get_vocabulary_diversity()` query computes the type-token ratio (TTR = unique words / total words) for the most active users. Key choices:

- **Batch message fetch** — rather than querying messages per user (N+1), the function fetches messages for all top users in a single query using `author_id IN (...)`, then groups by author in Python.
- **Bounded sample** — up to 2,000 messages per user keeps computation tractable while providing a meaningful sample. The existing `_clean_content()` and `WORD_PATTERN` utilities are reused for word extraction.
- **Minimum word threshold** — users with fewer than 10 words are excluded to avoid meaningless ratios from very low activity.

### Conversation Flow

The `get_conversation_flow()` query identifies reply pairs by finding consecutive messages from different authors in the same channel within a time gap. Key choices:

- **Heuristic-based** — Discord's API doesn't expose reply threading for most historical messages, so consecutive-message pairing within a 5-minute gap is a reasonable approximation. The gap is configurable via the `gap_minutes` parameter.
- **Chronological ordering** — messages are ordered by `channel_id, created_at ASC` so that iterating consecutive pairs correctly identifies who spoke first (the "prompt") and who responded (the "reply").
- **Python-side pairing** — the pairing logic runs in Python over 10,000 recent messages. SQL window functions (LAG) could do this in the database, but the Python approach is simpler and matches the project's convention for text analytics.

### Per-User Profanity Words

The `get_user_top_profanity_words()` query returns the most-used profanity words for a specific user. Key choices:

- **Reuses existing infrastructure** — the same `_clean_content()`, `WORD_PATTERN`, and `settings.load_profanity_words()` used by the server-wide profanity leaderboard. The only difference is filtering by `member_id`.
- **Styled list rendering** — the user page renders profanity words as a styled list (matching the emoji list pattern) rather than a chart, since there are typically only 5 items.
- **Collapsible word reference** — the landing page includes a `<details>/<summary>` element inside the Profanity Leaderboard card that reveals the full word list. This uses zero JavaScript and degrades gracefully.

## Coding Standards and Best Practices

Use [PEP-0008](https://peps.python.org/pep-0008/) as a reference for coding practice in Python. As for other tech stacks, follow what a professional software engineer would commonly follow for practices and standards as stated on [Geek for Geeks SWE Guidelines](https://www.geeksforgeeks.org/software-engineering/coding-standards-and-guidelines/)

### Project-Specific Rules

- **Always use async sessions**: `async with async_session() as session` — never use synchronous `Session()`
- **Use `select()` over `session.query()`**: Follow SQLAlchemy 2.0 style with `select(Model).where(...)` instead of the legacy `session.query(Model).filter(...)` pattern
- **Upserts use raw `insert()` + `on_conflict_do_update()`**: For channels and members, use PostgreSQL's native `ON CONFLICT` via SQLAlchemy's `insert()` dialect, not ORM merge
- **Environment variables via `config.py`**: All settings flow through `config.py` — never read `os.environ` directly in bot or dashboard code
