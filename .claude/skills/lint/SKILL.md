---
name: lint
description: Run ruff linter and formatter checks on the codebase. Use to check code quality or before committing.
argument-hint: [file-or-directory]
user-invocable: true
allowed-tools: Bash Read
---

# Lint & Format Check

Run ruff linter and formatter on the project.

Arguments: `$ARGUMENTS`

## Steps

1. **Run ruff check** (linting):
   ```bash
   cd /Users/khayashi2/vs-code/repos/discord-bot && ruff check $ARGUMENTS .
   ```
   If arguments provided, check only those paths. Otherwise check the whole project.

2. **Run ruff format check** (formatting):
   ```bash
   cd /Users/khayashi2/vs-code/repos/discord-bot && ruff format --check $ARGUMENTS .
   ```

3. **If issues found**, ask the user if they'd like auto-fixes applied:
   - `ruff check --fix .` for lint auto-fixes
   - `ruff format .` for formatting fixes

4. **Report results**: list any remaining issues that need manual fixes.
