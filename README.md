# Discord Analytics Bot

A Discord bot that tracks server activity and displays fun analytics on a web dashboard — including top words, most active users, emoji usage, and more.

## Tech Stack

- **Bot**: Python 3.12, discord.py v2
- **Database**: PostgreSQL 16 (via Docker)
- **Dashboard**: FastAPI + Jinja2 + Chart.js + wordcloud2.js + Tom Select
- **Migrations**: Alembic + SQLAlchemy 2.0
- **CI/CD**: GitHub Actions (lint, test, Docker build)

## Features

- **Live Message Tracking** — the bot listens to every message in your server and stores it in PostgreSQL (content, author, channel, emoji count, attachments, and more)
- **Upsert Strategy** — channels and members are automatically upserted so metadata stays fresh without duplicates
- **Historical Backfill** — a one-off script ingests all past messages from every text channel, with batched commits and per-channel error handling
- **Web Dashboard** — a FastAPI-powered analytics dashboard with a streamlined landing page: daily/weekly digest, overview stats, channel activity, activity trend, most active users, a customizable visualization block, and awards & superlatives. All other visualizations (word cloud, top words, profanity, emoji, sentiment, heatmap, vocabulary diversity, conversation flow, peak hours, reaction time kings, server growth) are accessible via the Custom View dropdown
- **Customizable Dashboard Block** — a dropdown (Tom Select) on both the landing page and user stats page where end-users can choose which visualization to display; the card heading dynamically shows the selected visualization name (e.g., "Word Cloud" instead of "Custom View"); selection persists via localStorage
- **Time-Filtered Analytics** — dashboard supports 7-day, 30-day, and 90-day time range filters with a sticky range bar that follows you as you scroll, so you can change the filter from anywhere on the page
- **User Stats Page** — a dedicated per-user analytics page with a streamlined layout mirroring the landing page: stat cards, activity chart, and a Custom View dropdown for all other visualizations (top words, emoji, profanity, peak hours). Includes a sticky header showing the selected user and range buttons as you scroll
- **Profanity Leaderboard** — ranks users by profanity usage using a configurable word list (`config/profanity.txt`), with a collapsible reference showing all tracked words and per-user profanity breakdowns on the user stats page
- **Activity Heatmap** — a day-of-week × hour-of-day grid showing when the server is most active, with color intensity based on message volume (hours in Pacific Time, auto-adjusts for PST/PDT)
- **Awards & Superlatives** — fun badges highlighting server members: Night Owl, Early Bird, Emoji Monarch, Novelist, Chatterbox, Editor, and Attachment Pro
- **Vocabulary Diversity** — ranks users by type-token ratio (unique words / total words), showing who has the most diverse vocabulary
- **Conversation Flow** — analyzes consecutive messages to show who replies to whom most often, with a toggle between a visual adjacency heatmap and a text table
- **Peak Hours** — a bar chart showing message volume by hour of day (0–23 Pacific Time), revealing when the server is most active throughout the day
- **Reaction Time Kings** — ranks the fastest responders by average reply time, using the same consecutive-message pairing logic as conversation flow (minimum 3 responses to qualify)
- **Channel Activity List** — a server-rendered table showing all indexed channels with message count and last active date
- **Daily/Weekly Digest** — "today vs yesterday" and "this week vs last week" cards with percentage deltas for messages and active users
- **Server Growth Timeline** — a line chart showing unique active users per day over time (Pacific Time)
- **Word Cloud** — a visual word cloud (via wordcloud2.js) showing the most frequently used words, with size proportional to frequency
- **Message Sentiment Trend** — a dual-line chart tracking daily positive and negative keyword hits, with a disclaimer that it's keyword-based, not AI-powered

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

Build the API endpoints and frontend to visualize the trends. The dashboard is live with a streamlined landing page (digest, overview stats, channel activity, activity chart, most active users, custom view dropdown, awards) and all other visualizations accessible via the Custom View block. Includes time-range filtering (7d/30d/90d) and a dedicated per-user stats page with its own custom view block.

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
│   ├── agents/           # Specialized sub-agents (code-reviewer, dashboard-builder, etc.)
│   ├── hooks/            # Tool-use hooks
│   ├── skills/           # Quality & workflow skills (perf-review, security-check, refactor, pr-review, lint, etc.)
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

### Peak Hours

**What:** A bar chart showing message counts for each hour of the day (0–23 Pacific Time), revealing when the server is most active.

**Why:** While the heatmap shows activity by day *and* hour, the peak hours chart collapses the day dimension to give a simpler, at-a-glance answer to "what time of day is this server busiest?" It uses PostgreSQL's `EXTRACT(hour FROM created_at AT TIME ZONE 'US/Pacific')` and fills in zero-count hours so the chart always shows all 24 bars.

**Consider:** The timezone conversion is applied server-side in PostgreSQL, which correctly handles DST transitions per-row (each timestamp is converted based on its own date, not today's date). The chart complements the heatmap — one shows the weekly pattern, the other the daily pattern.

### Reaction Time Kings

**What:** A leaderboard ranking the fastest average responders — users who reply quickest after someone else posts in the same channel.

**Why:** It adds a fun competitive element ("who's always online?") and surfaces social dynamics that pure message counts miss. The logic reuses the same consecutive-message pairing from conversation flow: two messages in the same channel, from different authors, within 5 minutes.

**Consider:** A minimum of 3 responses is required to qualify, preventing someone with one fast reply from topping the list. The metric is approximate — it pairs *consecutive* messages, not explicit Discord replies, so busy channels with interleaved conversations can skew results. The scan is bounded to 10,000 recent messages for performance.

### Removing Message Lengths and Most Active Channels

**What:** The Message Lengths (doughnut chart) and Most Active Channels (bar chart) panels were removed from both the landing page and user stats page.

**Why:** These panels provided less engagement value compared to the newer analytics (heatmap, awards, vocabulary diversity, conversation flow). Message length distribution is a relatively static metric that doesn't change much over time, and channel activity overlaps with information already visible in the overview stats. Removing them keeps the dashboard focused on the most interesting insights.

**Consider:** The query functions (`get_message_length_stats`, `get_top_channels`, etc.) were intentionally left in `queries.py` as unused code — they could be re-enabled or repurposed (e.g., for a CSV export feature) without reimplementing the SQL logic.

### Activity Heatmap

**What:** A CSS grid visualization showing message volume by day-of-week and hour-of-day, with color intensity proportional to activity.

**Why:** Heatmaps are one of the best ways to spot temporal patterns at a glance — you can immediately see if your server is more active on weekends, or if there's a cluster of late-night chatters. The grid is rendered with pure DOM manipulation (no Chart.js) since a 7×24 cell grid maps more naturally to HTML/CSS than to a chart library.

**Consider:** All timestamps are stored in UTC but displayed in Pacific Time using PostgreSQL's `AT TIME ZONE 'US/Pacific'`, which automatically handles PST/PDT transitions. The timezone string is currently hardcoded in queries — a future improvement could make it configurable via `config.py` if the bot is deployed for servers in other timezones.

### Awards & Superlatives

**What:** Seven fun award categories (Night Owl, Early Bird, Emoji Monarch, Novelist, Chatterbox, Editor, Attachment Pro) that highlight the top member in each category.

**Why:** Awards make the dashboard more engaging and social. They're the kind of feature that gets people talking ("I didn't know I sent the most emoji!"). Each award runs a targeted sub-query (e.g., counting messages between midnight and 4 AM for Night Owl) and picks the top member.

**Consider:** The Novelist award requires a minimum of 50 messages to avoid a user with one long message winning. This threshold is hardcoded — in a larger project you might make it configurable. The awards section runs 7 separate queries; for a small server this is fine, but at scale you'd want to combine them into fewer queries or cache the results.

### Vocabulary Diversity

**What:** A type-token ratio (TTR) chart ranking users by how diverse their vocabulary is — `unique_words / total_words`.

**Why:** TTR is a simple but effective measure of linguistic diversity. It adds a different dimension to the analytics beyond just "who talks the most" — someone might send fewer messages but use a much richer vocabulary.

**Consider:** TTR is sensitive to sample size — users with fewer messages tend to have higher ratios. The query fetches up to 2,000 recent messages per user to keep the comparison somewhat normalized, but it's not a perfect metric. The chart uses a horizontal bar layout consistent with other user-ranking charts in the dashboard.

### Conversation Flow

**What:** A table showing the top reply pairs — who tends to respond to whom — based on consecutive messages in the same channel within a 5-minute window.

**Why:** It reveals the social dynamics of a server: who are the conversation pairs, who tends to respond to specific people. The 5-minute gap threshold filters out messages that happen to be in the same channel but aren't actually part of a conversation.

**Consider:** This is a heuristic, not true threading. Discord doesn't expose reply relationships in older messages (only explicit replies via the reply feature). Consecutive-message pairing is a reasonable approximation but can misattribute replies in busy channels. The query processes 10,000 recent messages in Python, ordered chronologically by channel.

### User Page Time Filtering

**What:** The user stats page now supports the same 7-day, 30-day, 90-day, and all-time filters as the main dashboard. The range is passed as a query parameter to the JSON API (`/api/user/{member_id}?range=30d`), and all user query functions filter accordingly.

**Why:** All-time user stats miss recent trends — a user might have been very active last week but quiet before that. Adding time filtering reuses the same `cutoff_from_range()` and `after` parameter pattern from the main dashboard, keeping the codebase consistent.

**Consider:** Unlike the main dashboard (which uses `<a>` tags and full page reloads), the user page uses `<button>` elements with JavaScript click handlers since user selection already works client-side. The selected range persists when switching between users — it's treated as a user preference about the time window, not tied to a specific member.

### Sticky User Header & Range Bar

**What:** A fixed header that appears at the top of the user page when you scroll past the selector, showing the selected user's display name and time-range buttons (7d/30d/90d/All). The landing page has a separate sticky range bar that appears when the original filter scrolls out of view.

**Why:** Long dashboard pages mean losing context — whose stats am I viewing? What time range is selected? The sticky header solves both on the user page. The landing page's sticky range bar lets you change filters without scrolling back to the top.

**Consider:** Both use `IntersectionObserver` (not scroll listeners) for performance. The user page uses a `switchRange()` helper to keep original and sticky range buttons in sync — clicking either updates both sets and reloads data. The landing page's sticky bar uses simple `<a>` tags (same as the original filter) since range changes trigger a page reload anyway.

### Pacific Time Conversion

**What:** The activity heatmap, peak hours chart, and Night Owl/Early Bird awards all display hours in Pacific Time instead of UTC, using PostgreSQL's `timezone('US/Pacific', created_at)` function.

**Why:** The server is US-based, so UTC hours were confusing — peak activity appeared shifted by 7-8 hours from what users expected. PostgreSQL's `AT TIME ZONE` handles PST/PDT transitions automatically based on each row's timestamp, which is more correct than a fixed UTC offset.

**Consider:** The timezone string `"US/Pacific"` is hardcoded in three query functions. For a multi-timezone deployment, you'd want to extract this to `config.py` as a `DASHBOARD_TIMEZONE` setting. The conversion happens server-side in SQL, not client-side in JavaScript, because the `EXTRACT(hour)` needs to operate on the converted timestamp.

### Per-User Peak Hours & Vocabulary Diversity

**What:** Two new panels on the user stats page: a per-user peak hours bar chart and a vocabulary diversity stat card showing TTR score, unique words, and total words.

**Why:** The main dashboard shows server-wide peak hours and vocabulary diversity, but users want to see their own patterns. "When am I most active?" and "How diverse is my vocabulary?" are natural follow-ups to the per-user stats already shown. Both panels include explanatory text so users understand what TTR means.

**Consider:** The vocabulary diversity panel uses stat cards (not a chart) since it's a single user's data — a bar chart would only have one bar. The TTR description ("unique words / total words, higher = more diverse") appears on both the main dashboard and user page for consistency. The server returns `total_words: 0` when the sample is too small (< 10 words), and the client hides the panel in that case.

### Channel Activity List

**What:** A server-rendered table showing every indexed channel with its message count and last active date.

**Why:** Users want to know which channels the bot is tracking and how active each one is. This was a requested feature — it provides transparency about what data exists and helps server admins spot dead channels.

**Consider:** The query uses a `LEFT JOIN` so channels with zero messages still appear. When time filtering is active, channels with no messages in the selected range are still shown (via an `OR created_at IS NULL` clause on the outer join) so the list doesn't unexpectedly shrink.

### Daily/Weekly Digest Card

**What:** Four cards showing "today vs yesterday" and "this week vs last week" comparisons for messages and active users, with colored percentage deltas.

**Why:** Dashboard visitors want to quickly answer "is the server more or less active than usual?" without mentally comparing bar charts. The digest provides instant context with green (up) and red (down) indicators.

**Consider:** The digest always uses real-time comparisons (today vs yesterday, this week vs last week) — it ignores the time range filter since "today vs yesterday" is inherently a fixed window. The percentage calculation handles division by zero gracefully: if yesterday had zero messages, a non-zero today shows +100%.

### Server Growth Timeline

**What:** A line chart showing unique active users per day, using Pacific Time for day boundaries.

**Why:** Message volume alone doesn't tell you if the server is growing. Unique daily users reveals whether the community is expanding, stable, or declining. This complements the activity-over-time chart (which shows message count).

**Consider:** Uses `func.timezone("US/Pacific", ...)` for day truncation, consistent with the heatmap and peak hours. Without this, a message sent at 10 PM Pacific would be bucketed into the next UTC day, producing misleading results for a US-based server.

### Word Cloud

**What:** A visual word cloud rendered with wordcloud2.js, showing the top 80 words with size proportional to frequency.

**Why:** Word clouds are more engaging than bar charts for showing word frequency — they're immediately scannable and make great screenshots. The larger dataset (80 words vs. 20 for the bar chart) takes advantage of the visual format.

**Consider:** wordcloud2.js requires explicit canvas dimensions. The render is deferred with `requestAnimationFrame` so the browser finishes layout before measuring the container width — this prevents a zero-width crash when the word cloud is rendered dynamically inside the custom view block.

### Message Sentiment Trend

**What:** A dual-line chart showing daily positive and negative keyword hits over time, based on simple word lists (~20 words each).

**Why:** It adds an emotional dimension to the analytics — you can spot if the server mood shifted after an event. The keyword approach is simple and transparent (no black-box ML model).

**Consider:** Keyword matching is crude — "not bad" registers as negative ("bad"), and sarcasm is undetectable. The dashboard includes a disclaimer: "Based on simple keyword matching — approximate, not AI-powered." The 5,000-message scan limit means the all-time view only covers recent history, with older days showing zero counts.

### "Who Talks to Whom" Network

**What:** An adjacency heatmap grid showing reply counts between user pairs, with a toggle button to switch between the visual heatmap and the existing text table.

**Why:** The conversation flow table shows raw numbers but doesn't reveal the overall pattern at a glance. The heatmap makes it immediately visible who the dominant conversation pairs are, using the same color intensity pattern as the activity heatmap.

**Consider:** The toggle uses two simple buttons that show/hide the respective views — no JavaScript framework needed. The heatmap truncates long usernames with an ellipsis and adds tooltip text for the full name. Both views use the same underlying data from `get_conversation_flow()`.

### Customizable Dashboard Block

**What:** A dropdown (Tom Select) on both the landing page and user stats page where end-users can select which visualization to display in a dedicated card. The card heading dynamically shows the name of the selected visualization (e.g., "Word Cloud" instead of a static "Custom View" label). The selection persists via `localStorage`.

**Why:** Both pages were simplified to show only core stats as static cards (landing: digest, overview, channel activity, activity chart, most active users, awards; user: stat cards, activity chart). All other visualizations are accessible through the Custom View dropdown. This keeps pages scannable while still giving users access to every metric.

**Consider:** The implementation uses a `VIZ_REGISTRY` pattern — a plain object mapping keys to `{label, dataKey, render, type}`. Adding a new visualization to the dropdown only requires one new registry entry. Visualizations that are already displayed as static cards on the page (like Most Active Users) are excluded from the registry to avoid duplication. Chart.js instances are tracked and properly destroyed before re-rendering to prevent memory leaks. The `div`-type renders (heatmap, network) need different container setup than `canvas`-type renders.

### Async Database Access

**What:** The bot uses `asyncpg` with SQLAlchemy's async sessions instead of synchronous database calls.

**Why:** discord.py is fully async — blocking the event loop with synchronous DB calls would freeze the bot for every message. Async sessions let database writes happen without blocking other events (like responding to commands).

**Consider:** Async code is harder to debug (stack traces are less obvious). SQLAlchemy's async API mirrors the sync one closely, but you need to be careful with session lifetimes — always use `async with` to ensure sessions are properly closed.

## Branch Strategy

- `main` — protected, no direct commits
- `feature/<name>` — all new work
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`
