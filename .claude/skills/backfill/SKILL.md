---
name: backfill
description: Run the historical backfill script to populate the database with past Discord messages. Starts db, runs migrations, then executes the backfill service.
argument-hint:
user-invocable: true
allowed-tools: Bash Read
---

# Backfill

Run the historical message backfill to populate the analytics database with past Discord messages.

Arguments: `$ARGUMENTS` (none expected)

## Steps

1. **Build the backfill image:**
   ```bash
   docker compose build backfill
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

4. **Run the backfill:**
   ```bash
   docker compose --profile backfill run --rm backfill
   ```
   This will stream logs to the terminal. Do NOT run in the background — the user needs to see progress.

5. **Report to the user:**
   - Whether the backfill completed successfully or had errors
   - Total messages ingested (from the log output)
   - Any channels that were skipped (permissions, HTTP errors)
   - How to stop the database if no other services are needed: `docker compose down`
