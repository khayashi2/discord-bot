---
name: run-tests
description: Run the pytest test suite for the discord bot project. Use after making code changes or before committing.
argument-hint: [test-file-or-pattern]
user-invocable: true
allowed-tools: Bash Read
---

# Run Tests

Run the project's test suite using pytest.

Arguments: `$ARGUMENTS`

## Steps

1. **Ensure the database is running** (needed for integration tests):
   ```bash
   cd /Users/khayashi2/vs-code/repos/discord-bot && docker compose ps db
   ```
   If not running, inform the user they may need `docker compose up -d db`.

2. **Run the tests**:
   - If arguments provided, run specific tests:
     ```bash
     cd /Users/khayashi2/vs-code/repos/discord-bot && pytest $ARGUMENTS -v
     ```
   - If no arguments, run the full suite:
     ```bash
     cd /Users/khayashi2/vs-code/repos/discord-bot && pytest tests/ -v
     ```

3. **Report results** clearly:
   - Number of tests passed/failed/skipped
   - For any failures, show the relevant assertion error and suggest a fix
