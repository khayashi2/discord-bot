---
name: pr-review
description: Run lint, code review, tests, performance, security, and refactor checks before a PR. Shows all findings and lets you decide how to fix issues.
argument-hint: [base-branch]
user-invocable: true
allowed-tools: Bash Read Grep Glob Agent AskUserQuestion
---

# Pre-PR Review Pipeline

Run the full quality pipeline — lint, code review, tests, performance review, security check, and refactor analysis — then present findings and ask how to proceed with fixes.

Arguments: `$ARGUMENTS` (optional base branch, defaults to `main`)

## Steps

1. **Identify changed files** — Determine which files were modified on this branch compared to the base branch (default: `main`):
   ```bash
   git diff --name-only main...HEAD -- '*.py'
   ```
   Save this list — it scopes the targeted scans in step 2.

2. **Run all six checks in parallel:**

   a. **Lint** — Run ruff linter and formatter:
      ```bash
      ruff check .
      ruff format --check .
      ```

   b. **Code review** — Launch the `code-reviewer` agent to review changes against the base branch (default: `main`). Pass the base branch if provided via arguments.

   c. **Tests** — Run the test suite:
      ```bash
      pytest tests/ -v
      ```

   d. **Performance review** — Run `/perf-review` scoped to the changed files from step 1. If no Python files changed, skip this check.

   e. **Security check** — Run `/security-check` scoped to the changed files from step 1. If no Python files changed, skip this check.

   f. **Refactor analysis** — Run `/refactor` scoped to the changed files from step 1. If no Python files changed, skip this check.

3. **Compile results** — Combine output from all six checks into a single report:

   ```
   ## Lint Results
   - ✅ No issues / ❌ N issues found (list them)

   ## Code Review
   (Paste the code-reviewer agent's structured output: Summary, Issues Found, Verdict)

   ## Test Results
   - ✅ All passed / ❌ N failed (list failures)

   ## Performance Review
   - ✅ No issues / ❌ N findings (X critical, Y warning, Z info)
   (List CRITICAL and WARNING findings; summarize INFO count)

   ## Security Check
   - ✅ No issues / ❌ N findings (X critical, Y warning, Z info)
   (List CRITICAL and WARNING findings; summarize INFO count)

   ## Refactor Analysis
   - ✅ No issues / ❌ N findings (X high, Y medium, Z low)
   (List HIGH findings; summarize MEDIUM and LOW counts)
   ```

4. **Present findings to the user** — Display the compiled report.

5. **Ask the user how to proceed** — If any issues were found, ask:
   - "Auto-fix all" — apply ruff auto-fixes, send code review findings to the appropriate agent (e.g., dashboard-builder) for fixes, and apply performance/security/refactor fixes
   - "Fix manually" — user will handle the fixes themselves
   - "Ignore and proceed" — skip fixes, the issues are acceptable

6. **Apply fixes based on user choice:**
   - If auto-fix: run `ruff check --fix .` and `ruff format .` for lint issues, then dispatch code review findings to the appropriate agent, then apply performance/security/refactor fixes following each skill's fix guidance
   - If manual: do nothing, user handles it
   - If ignore: do nothing

7. **Update documentation** — After all issues are resolved (or skipped), run `/update-docs` to ensure README.md and CLAUDE.md are in sync with the changes on this branch. This step runs regardless of whether fixes were needed — any code change may warrant a docs update.

## Important
- Always present findings before fixing — never auto-fix without asking
- Run all six checks in parallel to save time
- Scope performance, security, and refactor checks to changed files only — this keeps the review focused on the PR's diff, not pre-existing issues
- If all six checks pass cleanly, report success then proceed directly to the docs update step (skip the fix prompt)
- For performance/security/refactor findings, only include CRITICAL/HIGH findings in the main report summary — lower severity items are informational and should not block a PR
