# Project: Discord Analytics Bot

## Overview

A Discord bot that tracks server activity and displays fun analytics (top words, most active users, swear counts, emoji usage, etc.) on a web dashboard. Built as a portfolio/resume project.

## Tech Stack

- Python 3.12
- discord.py v2
- PostgreSQL 16 (via Docker)
- FastAPI + Jinja2 + Chart.js + wordcloud2.js + Tom Select (dashboard)
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
- `.claude/` — Claude Code configuration: agents (code-reviewer, dashboard-builder, etc.), skills (perf-review, security-check, refactor, pr-review, lint, etc.), hooks, and `settings.json` for project-level settings (`settings.local.json` for local overrides, not committed)

## Key Design Decisions

- Full message content stored (not just metadata) to enable flexible future analytics
- Three separate entry points (bot, dashboard, backfill) share one DB via `db/operations.py`
- Async database access via asyncpg + SQLAlchemy async sessions (discord.py is fully async)
- Dashboard queries in `dashboard/queries.py` return plain dicts; route handler stays thin
- Every main query accepts optional `after` datetime for time filtering (`7d`/`30d`/`90d`)
- Per-user stats via JSON API + client-side rendering; main dashboard via server-rendered Jinja2 + `data-*` attributes
- Text analytics (top words, emoji, profanity, sentiment, catchphrases, brainrot) use Python-side aggregation over bounded recent rows — simple now, materialized views later if needed
- Hour-of-day analytics (heatmap, peak hours, awards) use `AT TIME ZONE 'US/Pacific'` in PostgreSQL; daily aggregation uses UTC
- `VIZ_REGISTRY` pattern for customizable dashboard blocks — Tom Select dropdown with localStorage persistence on both pages
- Streamlined pages: core stats as static cards, all other visualizations via Custom View dropdown
- CDN dependencies: wordcloud2.js and Tom Select loaded in `base.html`

See the **Learning Opportunity** section below for detailed rationale on each decision.

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
- **Client-side time filtering** — the user page uses `<button>` elements with JavaScript click handlers (not `<a>` page reloads) since user selection already works client-side. The selected range persists when switching users. All per-user query functions accept `after: datetime | None = None`.
- **Per-user peak hours** — mirrors `get_peak_hours()` with `member_id` filter and the same 24-bar zero-fill pattern.
- **Per-user vocabulary diversity** — returns stat cards (TTR, unique words, total words) instead of a chart. Returns `total_words: 0` when under the 10-word threshold; client checks this to show/hide the panel.
- **Per-user profanity words** — reuses `_clean_content()`, `WORD_PATTERN`, and `settings.load_profanity_words()` from the server-wide leaderboard, filtered by `member_id`. Rendered as a styled list (not a chart).
- **Per-user brainrot stats** — uses `_normalize_for_brainrot()` and `_count_brainrot_in_message()` with the cached brainrot matching structures. Shows stat cards (keyword hits, repeated messages) plus a term badge list. Rendered as HTML (not a chart).

### Profanity Leaderboard

The `get_profanity_leaderboard()` query scans recent messages and counts profanity hits per user. Key choices:

- **File-based word list** — profanity words are loaded from `config/profanity.txt` (one word per line, `#` comments supported). This makes the list editable by server admins without code changes.
- **Cached loading** — `settings.load_profanity_words()` reads the file once and caches the result as a `frozenset` for O(1) membership checks. Subsequent calls return the cached set. There is no reload mechanism — the bot or dashboard must be restarted to pick up changes to `profanity.txt`.
- **Python-side counting** — like top-words and emoji stats, profanity counting is done in Python over a bounded set of messages (10,000). The same scalability comments apply.

### Activity Heatmap

The `get_activity_heatmap()` query uses PostgreSQL's `EXTRACT(dow)` and `EXTRACT(hour)` on timestamps converted to Pacific Time via `func.timezone("US/Pacific", Message.created_at)`. Key choices:

- **Pure CSS grid, not Chart.js** — a 7×24 heatmap maps naturally to an HTML grid with colored cells. Chart.js doesn't have a native heatmap type, so using DOM manipulation avoids pulling in a chart plugin. Color intensity is linearly interpolated from the accent color based on `count / maxCount`.
- **Pacific Time via `AT TIME ZONE`** — timestamps are stored in UTC but displayed in Pacific Time. PostgreSQL's `timezone()` function handles PST/PDT transitions automatically per-row (each timestamp is converted based on its own date). Both `dow` and `hour` must be extracted from the converted timestamp — extracting only the hour would produce incorrect day-of-week for messages near midnight.
- **Day ordering** — PostgreSQL `EXTRACT(dow)` returns 0=Sunday, but the grid renders Monday first (order: 1,2,3,4,5,6,0) for a more conventional week layout.

### Awards & Superlatives

The `get_awards()` function runs 7 independent sub-queries, each finding the top member for a specific criterion. Key choices:

- **Separate sub-queries** — each award has different aggregation logic (COUNT, SUM, AVG with HAVING), so a single combined query would be complex and hard to maintain. The trade-off is up to 14 DB round-trips per page load (each award runs an aggregation query plus a member lookup). A future optimization could run sub-queries in parallel using separate sessions and `asyncio.gather()`, since a single async session is not safe for concurrent awaits.
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

### Peak Hours

The `get_peak_hours()` query groups messages by hour of day using `EXTRACT(hour FROM created_at AT TIME ZONE 'US/Pacific')`. Key choices:

- **Simple aggregation** — a single `GROUP BY hour` query returns counts for each hour. Hours with no messages are filled in with zero counts in Python so the Chart.js bar chart always renders all 24 bars.
- **Complements the heatmap** — the heatmap shows a 7×24 grid (day × hour), while peak hours collapses the day dimension for a simpler "what time is the server busiest?" view. Both use `EXTRACT` on the same Pacific Time-converted timestamp.
- **Pacific Time** — consistent with the heatmap, hours are in Pacific Time. PostgreSQL handles DST transitions per-row.

### Reaction Time Kings

The `get_reaction_time_kings()` query ranks users by average response time. Key choices:

- **Reuses consecutive-message pairing** — the same logic as `get_conversation_flow()`: consecutive messages in the same channel from different authors within a 5-minute window. Instead of counting pairs, it computes the time delta in seconds and averages per responder.
- **Minimum threshold** — users need at least 3 qualifying responses to appear, preventing outliers from a single fast reply.
- **Bounded scan** — processes up to 10,000 recent messages ordered by `(channel_id, created_at)`. The docstring notes this may under-represent users active in higher-numbered channels, a known trade-off for keeping the query fast.

### Sticky User Header & Range Bar

The user page displays a fixed header with the selected user's display name and range buttons when scrolling past the selector card. The landing page has a separate sticky range bar. Key choices:

- **IntersectionObserver over scroll events** — `IntersectionObserver` is more performant than a scroll event listener. The browser natively tracks when the selector card enters/leaves the viewport, with no debouncing or throttling needed. The same pattern is used on both pages.
- **CSS transition for smooth appear/disappear** — the header uses `opacity` and `transform: translateY` transitions rather than an abrupt `display: none` toggle. The `pointer-events: none` property prevents it from interfering with clicks when invisible; `.visible` adds `pointer-events: auto` for the range buttons.
- **switchRange() helper** — a shared function syncs both original and sticky range buttons using `classList.toggle("active", ...)`. This avoids duplicating sync logic in two click handlers.

### Channel Activity List

The `get_channel_activity()` query returns all indexed channels with message counts and last active dates. Key choices:

- **LEFT JOIN for completeness** — uses `outerjoin` so channels with zero messages still appear. When a time filter is active, the `WHERE` clause includes `OR Message.created_at IS NULL` to preserve empty channels in the result.
- **Server-rendered table** — follows the same `<table>` pattern as conversation flow. No JavaScript needed.

### Daily/Weekly Digest

The `get_digest()` function computes today-vs-yesterday and this-week-vs-last-week deltas. Key choices:

- **No `after` parameter** — the digest is always relative to "now" regardless of the dashboard time filter, since "today vs yesterday" is inherently a fixed window.
- **Week boundaries** — "this week" starts on Monday (computed via `today - today.weekday()`), consistent with ISO week numbering.
- **Division-by-zero handling** — when the comparison period has zero activity, `_pct()` returns +100% if there's any current activity, or 0% if both are zero.

### Server Growth Timeline

The `get_unique_users_over_time()` query counts distinct active users per day. Key choices:

- **UTC day boundaries** — uses `date_trunc("day", Message.created_at)` in UTC, consistent with `get_activity_over_time()`. Pacific Time is used for hour-of-day analytics (heatmap, peak hours) where the timezone matters, but daily aggregation works in UTC since the fill range is also UTC-based — using Pacific for one and UTC for the other would cause a day-key mismatch near midnight.
- **Zero-day fill** — same pattern as `get_activity_over_time()`: builds a lookup from query results, then iterates every day in the range, filling missing days with zero.

### Word Cloud

The `get_word_cloud_data()` query returns 80 words for visual density. Key choices:

- **Reuses `get_top_words` logic** — same `_clean_content()`, `WORD_PATTERN`, and stopword filtering with a higher `limit` parameter.
- **wordcloud2.js via CDN** — lightweight (~15KB), no build system needed. `requestAnimationFrame` defers rendering so the browser finishes layout before measuring the container — this prevents a zero-width crash when the canvas is created dynamically inside the custom block.

### Message Sentiment Trend

The `get_sentiment_trend()` query uses simple keyword lists for sentiment analysis. Key choices:

- **Module-level frozensets** — `POSITIVE_WORDS` and `NEGATIVE_WORDS` (~20 words each) are defined at module level for O(1) lookups, following the same pattern as `STOPWORDS`.
- **Dual-line chart** — shows both positive and negative counts (not a single score), so users can see whether a drop in sentiment is from fewer positive words or more negative ones.
- **Disclaimer text** — the template includes "Based on simple keyword matching — approximate, not AI-powered" to set expectations.

### "Who Talks to Whom" Network

The conversation flow card now includes a visual adjacency heatmap alongside the text table. Key choices:

- **Toggle button, not replacement** — two `<button>` elements with a `toggleConvView()` function switch visibility between the heatmap `<div>` and the table `<div>`. Both are rendered on page load.
- **Table-based heatmap** — the network uses an HTML `<table>` (not CSS grid) because the number of rows/columns is dynamic (depends on how many users are in the conversation flow data). The heatmap uses the same color interpolation pattern as the activity heatmap.
- **Username truncation** — long display names are truncated with an ellipsis in the grid headers, with the full name available in the `title` attribute tooltip.

### Customizable Dashboard Block

Both the landing page and user stats page include a Custom View block with a Tom Select dropdown. The card heading dynamically shows the selected visualization name instead of a static "Custom View" label. Key choices:

- **VIZ_REGISTRY pattern** — a plain object mapping string keys to `{label, dataKey, render, type}` entries. Adding a new visualization requires one new registry entry — no template or route changes needed.
- **No duplication with static cards** — visualizations already rendered as permanent cards on the page (e.g., Most Active Users) are excluded from the registry to avoid showing the same chart twice.
- **Dynamic heading** — `initCustomBlock()` updates `#custom-block-heading` text on initial load and on every dropdown change; resets to "Custom View" if the selection is cleared.
- **Separate registries per page** — the landing page uses `VIZ_REGISTRY` (14 server-wide visualizations), the user page uses `USER_VIZ_REGISTRY` (6 per-user visualizations: top-words, peak-hours, emoji, profanity, catchphrases, brainrot). Each has its own localStorage key (`dashboard-custom-viz` vs `user-custom-viz`). `activity` excluded from user registry (always static).
- **Chart cleanup** — a module-level `customChartInstance` variable tracks the current Chart.js instance. Before re-rendering, `destroy()` is called to prevent memory leaks from orphaned chart canvases.
- **Container type handling** — `canvas`-type renders create a `<canvas>` element, while `div`-type renders (heatmap, network) create a plain `<div>`. The heatmap gets a `.heatmap-grid` CSS class; the network does not, since it builds its own table internally.

### Catchphrase Lifespans

The `get_catchphrase_lifespans()` query detects multi-word catchphrases and tracks their rise, peak, and decline over time. Key choices:

- **N-gram extraction** — `_extract_ngrams()` generates 2-4 word n-grams from cleaned message text. N-grams where more than half the words are stopwords are filtered out to keep meaningful phrases (e.g., "skill issue") while discarding noise (e.g., "and then"). Note: `WORD_PATTERN` requires 3+ chars, so short words like "of" are never extracted.
- **Weekly timeline grouping** — usage is bucketed by ISO week (Monday start). Each qualifying phrase gets a status: `rising` (current week >= previous, includes flat), `peaked` (declining), or `dead` (zero uses this week).
- **Qualification thresholds** — server-wide requires 5+ uses from 2+ unique users; per-user requires 3+ uses from 1 user. This prevents one-off phrases from cluttering results.
- **Shared helpers** — `_accumulate_phrase_stats()` extracts n-gram accumulators from rows (used by both server-wide and per-user functions). `_prune_phrase_stats()` discards phrases below threshold to cap memory usage. `_build_catchphrase_result()` handles ranking, timeline construction, and status computation.
- **Memory management** — after accumulation, `_prune_phrase_stats()` removes all phrases that can never qualify (below `min_uses` or `min_users`), freeing the potentially large intermediate dictionaries before building the final response.
- **Bounded scan** — processes 15,000 messages server-wide, 5,000 per-user. N-gram extraction is heavier than single-word counting; consider caching at high volume.
- **Chart lifecycle** — the catchphrase Custom View renders a card grid with a click-to-reveal Chart.js timeline. The internal chart reference is stored on the container element (`container._catchphraseChart`) so it can be properly destroyed when switching visualizations.

### Brainrot / Meme Leaderboard

The brainrot analytics system detects meme vocabulary and copypasta usage across the server. Key choices:

- **File-based word list** — `config/brainrot.txt` follows the same pattern as `profanity.txt`: one entry per line, `#` comments, cached `frozenset` via `settings.load_brainrot_words()`. Multi-word phrases (e.g., "no cap") use spaces on a single line.
- **Custom matching (not WORD_PATTERN)** — brainrot terms include short tokens ("fr", "L", "W") and multi-word phrases ("no cap", "vibe check") that `WORD_PATTERN` (3+ alpha chars) cannot handle. A compiled regex with `\b` word boundaries matches single-word terms, while substring search with manual boundary checks handles multi-word phrases.
- **Double-count prevention** — multi-word phrases are matched first, and matched character spans are recorded. Single-word regex matches that fall inside any multi-word span are skipped (e.g., "cap" inside "no cap"). Additionally, single words that appear as components of multi-word phrases are excluded from the single-word regex during `_prepare_brainrot_matching()`.
- **Cached matching structures** — `_prepare_brainrot_matching()` caches the compiled regex and phrase list at module level (`_brainrot_cache`) since the word list is immutable after first load. Avoids recompiling per query call.
- **Normalization helper** — `_normalize_for_brainrot()` combines `_clean_content()`, lowercasing, stripping, and whitespace collapsing (via pre-compiled `_WHITESPACE_RE`). All four query functions use this single helper.
- **Copypasta detection** — in the server-wide leaderboard, normalized message content is tracked in a dict; messages appearing 3+ times from 2+ unique users qualify as copypasta. Per-user stats use a simpler "repeated messages" metric (same content sent 2+ times by the user). Both require messages >= 20 chars to avoid flagging common short phrases.
- **Four views** — landing page gets three `VIZ_REGISTRY` entries (leaderboard as stacked horizontal bar, top terms as vertical bar, trend as line chart); user page gets one `USER_VIZ_REGISTRY` entry (stat cards for keyword hits and repeated messages, plus term badges).

## Coding Standards and Best Practices

Use [PEP-0008](https://peps.python.org/pep-0008/) as a reference for coding practice in Python. As for other tech stacks, follow what a professional software engineer would commonly follow for practices and standards as stated on [Geek for Geeks SWE Guidelines](https://www.geeksforgeeks.org/software-engineering/coding-standards-and-guidelines/)

### Project-Specific Rules

- **Always use async sessions**: `async with async_session() as session` — never use synchronous `Session()`
- **Use `select()` over `session.query()`**: Follow SQLAlchemy 2.0 style with `select(Model).where(...)` instead of the legacy `session.query(Model).filter(...)` pattern
- **Upserts use raw `insert()` + `on_conflict_do_update()`**: For channels and members, use PostgreSQL's native `ON CONFLICT` via SQLAlchemy's `insert()` dialect, not ORM merge
- **Environment variables via `config.py`**: All settings flow through `config.py` — never read `os.environ` directly in bot or dashboard code
