---
name: deploy
description: Rebuild Docker services locally, run migrations, verify health, then push to remote and monitor CI. Use when ready to deploy changes.
argument-hint: [branch]
user-invocable: true
allowed-tools: Bash Read Grep Glob AskUserQuestion
---

# Deploy Pipeline

Rebuild and verify locally, then push to remote and monitor CI.

Arguments: `$ARGUMENTS` (optional branch name, defaults to current branch)

## Steps

### Phase 1 — Local Verification

1. **Check for uncommitted changes:**
   ```bash
   git status --short
   ```
   If there are uncommitted changes, warn the user and ask if they want to continue or commit first.

2. **Rebuild Docker images:**
   ```bash
   docker compose build bot dashboard
   ```

3. **Start the database** (if not already running):
   ```bash
   docker compose up -d db
   ```
   Wait for it to be healthy before proceeding.

4. **Run migrations:**
   ```bash
   docker compose --profile migration run --rm migrate
   ```

5. **Restart bot and dashboard:**
   ```bash
   docker compose up -d bot dashboard
   ```

6. **Health check** — verify services are running:
   ```bash
   docker compose ps
   ```
   Confirm `bot`, `dashboard`, and `db` are all in a healthy/running state. If the dashboard is up, also check:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
   ```
   Expect a 200 status.

7. **Report local results** — show the user which services are running and their status.

### Phase 2 — Push & CI

8. **Ask the user before pushing** — confirm they want to push to remote after local verification passes.

9. **Push to remote:**
   ```bash
   git push -u origin HEAD
   ```

10. **Monitor CI** — check GitHub Actions status:
    ```bash
    gh run list --branch $(git branch --show-current) --limit 1
    ```
    Then watch the run:
    ```bash
    gh run watch
    ```
    Report the final result (pass/fail) and link to the run.

11. **Report final status:**
    - ✅ All green — local services healthy, CI passed
    - ❌ Failures — list what failed (local build, migration, health check, CI) and suggest next steps

## Important
- Never force push — always use regular `git push`
- Always ask before pushing to remote
- If any local step fails, stop and report — do not push broken code
- If CI fails, show the failing job and suggest checking the Actions log
