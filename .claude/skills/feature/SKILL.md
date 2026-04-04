---
name: feature
description: Create a new feature branch following the project's naming convention. Use when starting work on a new feature.
argument-hint: <feature-name>
user-invocable: true
allowed-tools: Bash Read Grep Glob Agent EnterPlanMode
---

# Start a New Feature

Plan the feature implementation, then create a git feature branch and begin work.

Arguments: `$ARGUMENTS`

## Steps

1. **Enter Plan Mode** — Immediately call `EnterPlanMode`. Use the feature name (`$ARGUMENTS`) as context to:
   - Explore the codebase for relevant files, patterns, and utilities to reuse
   - Design the implementation approach
   - Present the plan to the user for approval

2. **After plan is approved — check git state**:

   ```bash
   git status && git branch --show-current
   ```

   If there are uncommitted changes, warn the user before proceeding.

3. **Pull latest main and create the branch**:
   - Convert the argument to kebab-case (e.g., "word tracker" -> "word-tracker")

   ```bash
   git checkout main && git pull origin main && git checkout -b feature/<kebab-case-name>
   ```

4. **Confirm** the branch was created and is active. The feature is ready for implementation.

## Important

- Always plan before creating the branch — planning is read-only and avoids orphan branches if the feature is abandoned or renamed
- Never branch from anything other than `main` unless the user specifies otherwise
- Always ensure `main` is up to date first: `git pull origin main` (if remote exists)
- Branch names should be lowercase kebab-case after `feature/`
