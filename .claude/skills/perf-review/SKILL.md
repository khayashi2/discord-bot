---
name: perf-review
description: Analyze code for performance inefficiencies — missing indexes, sequential awaits, Python-side aggregation, and memory concerns.
argument-hint: [file-or-directory]
user-invocable: true
allowed-tools: Bash Read Grep Glob Agent AskUserQuestion
---

# Performance Review

Scan the codebase (or a targeted path) for performance anti-patterns, then present findings in a structured report grouped by category and severity. Ask the user before making any changes.

Arguments: `$ARGUMENTS` (optional file or directory path; defaults to full project scan)

## Steps

1. **Determine scan scope** — If `$ARGUMENTS` specifies a file or directory, limit the scan to that path. Otherwise scan these directories: `dashboard/`, `db/`, `bot/`, `config/`.

2. **Run all four category scans in parallel:**

   a. **Database (`DB`)** — Check for:
      - Missing indexes: read `db/models.py` and identify columns used in `WHERE`, `ORDER BY`, `GROUP BY`, or `JOIN` clauses (cross-reference with queries in `dashboard/queries.py` and `db/operations.py`) that lack explicit `index=True` on their `mapped_column`. Common misses: `created_at`, `author_id`, `channel_id`, `emoji_count`, `is_bot`.
      - N+1 queries: look for loops or repeated helper calls that execute queries inside them (e.g., a helper function called once per award category).
      - Sequential sub-queries that could be combined or run concurrently.

   b. **Python (`PY`)** — Check for:
      - Python-side aggregation over large row sets: look for patterns where `.all()` or `.scalars().all()` pulls 1,000+ rows then processes them with `Counter`, loops, or list comprehensions (e.g., word counting, emoji extraction, profanity scanning).
      - Regex recompilation: look for `re.compile()` calls inside functions rather than at module level.
      - Duplicate constants or patterns: look for the same regex or data structure defined in multiple files (e.g., `EMOJI_PATTERN` in both `queries.py` and `operations.py`).
      - Unbounded fetches: queries using `.limit()` with values >= 5000 or no `.limit()` at all on large tables.

   c. **Async (`ASYNC`)** — Check for:
      - Sequential awaits in route handlers: scan `dashboard/app.py` for route functions that `await` multiple independent query calls that could use `asyncio.gather()`.
      - Missing batching: look for handlers (e.g., `bot/cogs/listener.py`) that make multiple individual DB calls per event instead of batching them in a single transaction.
      - Functions that await multiple independent sub-queries sequentially (e.g., `get_awards` running 7+ award queries one-by-one).

   d. **Memory (`MEM`)** — Check for:
      - Large `.all()` fetches: queries that pull thousands of rows into Python memory.
      - Unbounded counters or dictionaries built from large result sets.
      - Functions that iterate over large collections multiple times.

3. **Classify each finding by severity:**
   - **CRITICAL** — Affects every page load or every message; scales linearly or worse (e.g., missing index on a column filtered in every dashboard query, 10+ sequential awaits that could be parallel).
   - **WARNING** — Degrades performance at moderate scale (e.g., 10,000-row Python-side aggregation, N+1 sub-queries in awards, duplicate regex patterns across modules).
   - **INFO** — Improvement opportunity with modest impact (e.g., could cache a rarely-changing query result, minor batching opportunity).

4. **Compile the report** — Present findings in this format:

   ```
   ## Performance Review — <scope>

   **Scanned:** <list of files/directories checked>
   **Findings:** N total (X critical, Y warning, Z info)

   ---

   ### CRITICAL

   #### [DB-001] Missing indexes on frequently-queried columns
   **File:** `db/models.py:75-81`
   **Issue:** `Message.created_at`, `Message.author_id`, and `Message.channel_id` lack indexes but appear in WHERE/ORDER BY clauses across 15+ query functions.
   **Impact:** Full table scans on every dashboard page load. Query time grows linearly with message count.
   **Fix:** Add `index=True` to these mapped_column definitions, then run `/new-migration add-performance-indexes`.

   ---

   ### WARNING

   #### [PY-001] Python-side word counting over 5,000 rows
   **File:** `dashboard/queries.py:198-208`
   **Issue:** ...
   **Impact:** ...
   **Fix:** ...

   ---

   ### INFO

   #### [PY-003] Duplicate EMOJI_PATTERN definition
   **File:** ...
   **Issue:** ...
   **Impact:** ...
   **Fix:** ...
   ```

   Each finding must include: ID (category prefix + number), file path with line numbers, issue description, impact statement, and suggested fix.

5. **Present findings to the user** — Display the compiled report.

6. **Ask the user how to proceed** — If any findings exist, ask:
   - "Fix all" — apply all suggested fixes across all severity levels
   - "Fix critical only" — apply only CRITICAL-level fixes
   - "Pick individually" — walk through findings one by one and let the user accept or skip each
   - "Export only" — do nothing, user takes the report as-is

7. **Apply fixes based on user choice:**
   - For database index fixes: update `db/models.py` then run `/new-migration` to generate the Alembic migration.
   - For async parallelization fixes: refactor sequential awaits to use `asyncio.gather()` with proper error handling.
   - For Python-side aggregation: add TODO comments noting the optimization opportunity (these are larger refactors that need careful testing).
   - For duplicate code: consolidate to a shared module and update imports.
   - After applying any fixes, run `/lint` to verify code quality and `/run-tests` to verify nothing broke.

## Important
- Never auto-fix without presenting findings and asking the user first
- Run all four category scans in parallel to save time
- Include specific line numbers and file paths in every finding — never report a vague issue
- If the scan scope is a single file, still check cross-file concerns (e.g., a model file should still trigger a check for missing indexes referenced by query files)
- When suggesting `asyncio.gather()`, warn about shared session concerns — gather only works for queries that do not depend on each other's results and can use separate sessions
- Severity classification must be consistent: missing indexes and sequential-await bottlenecks are always CRITICAL; Python-side aggregation over 2,000+ rows is WARNING; cosmetic or minor DRY violations are INFO
- If all checks pass cleanly, report success and skip the fix prompt
