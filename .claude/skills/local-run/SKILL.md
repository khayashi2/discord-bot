---
name: local-run
description: Build and run the app locally with Docker Compose for manual inspection. Starts db, runs migrations, and lets you pick which services to launch.
argument-hint: [bot|dashboard|all]
user-invocable: true
allowed-tools: Bash Read AskUserQuestion
---

# Local Run

Build and start the app locally so you can inspect it in the browser or test the bot live.

Arguments: `$ARGUMENTS` (optional: `bot`, `dashboard`, or `all` — if omitted, will ask)

## Steps

1. **Pick services to start** — if no argument provided, ask the user:
   - `dashboard` — start db + dashboard (browse at http://localhost:8000)
   - `bot` — start db + bot (watch bot logs)
   - `all` — start db + bot + dashboard

2. **Build the Docker images:**
   ```bash
   docker compose build <selected services>
   ```

3. **Start the database:**
   ```bash
   docker compose up -d db
   ```
   Wait for it to be healthy before proceeding.

4. **Run migrations:**
   ```bash
   docker compose --profile migration run --rm migrate
   ```

5. **Start the selected services:**
   ```bash
   docker compose up -d <selected services>
   ```

6. **Verify everything is running:**
   ```bash
   docker compose ps
   ```
   If dashboard was started, also verify it responds:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
   ```

7. **Report to the user:**
   - Which services are running
   - Dashboard URL: http://localhost:8000 (if started)
   - How to view logs: `docker compose logs -f <service>`
   - How to stop: `docker compose down`
