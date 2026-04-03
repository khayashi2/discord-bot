---
name: feature
description: Create a new feature branch following the project's naming convention. Use when starting work on a new feature.
argument-hint: <feature-name>
user-invocable: true
allowed-tools: Bash
---

# Create a Feature Branch

Create a new git feature branch following the project's conventions.

Arguments: `$ARGUMENTS`

## Steps

1. **Check current git state**:
   ```bash
   git status && git branch --show-current
   ```

2. **Ensure clean working tree**. If there are uncommitted changes, warn the user before proceeding.

3. **Create and switch to the new branch**:
   - Branch name format: `feature/<feature-name>` (kebab-case)
   - Convert the argument to kebab-case (e.g., "word tracker" -> "word-tracker")
   ```bash
   git checkout -b feature/<kebab-case-name>
   ```

4. **Confirm** the branch was created and is active.

## Important
- Never branch from anything other than `main` unless the user specifies otherwise
- Always ensure `main` is up to date first: `git pull origin main` (if remote exists)
- Branch names should be lowercase kebab-case after `feature/`
