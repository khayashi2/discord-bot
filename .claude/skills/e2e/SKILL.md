---
name: e2e
description: Full end-to-end local run — start db, run migrations, backfill historical data, then start bot and dashboard. Use for a complete fresh environment setup.
argument-hint: [--skip-backfill]
user-invocable: true
allowed-tools: Bash Read AskUserQuestion
---

# End-to-End Run

Stand up the entire environment from scratch: database, migrations, backfill, bot, and dashboard.

Arguments: `$ARGUMENTS` (optional: `--skip-backfill` to skip the backfill step)

## Steps

1. **Build all images:**
   ```bash
   docker compose build bot dashboard backfill
   ```

2. **Start the database:**
   ```bash
   docker compose up -d db
   ```
   Wait for it to be healthy before proceeding.

3. **Run migrations:**
   ```bash
   docker compose --profile migration run --rm migrate
   ```

4. **Run the backfill** (unless `--skip-backfill` was passed):
   ```bash
   docker compose --profile backfill run --rm backfill
   ```
   This will stream logs to the terminal. Do NOT run in the background — the user needs to see progress. Report any skipped channels or errors.

5. **Start bot and dashboard:**
   ```bash
   docker compose up -d bot dashboard
   ```

6. **Verify everything is running:**
   ```bash
   docker compose ps
   ```
   Also verify the dashboard responds:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
   ```

7. **Report to the user:**
   - Backfill results (messages ingested, skipped channels) — or note it was skipped
   - All running services and their status
   - Dashboard URL: http://localhost:8000
   - How to view logs: `docker compose logs -f bot` or `docker compose logs -f dashboard`
   - How to stop: `docker compose down`
