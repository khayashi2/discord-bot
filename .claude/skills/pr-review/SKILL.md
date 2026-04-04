---
name: pr-review
description: Run lint, code review, and tests before a PR. Shows all findings and lets you decide how to fix issues.
argument-hint: [base-branch]
user-invocable: true
allowed-tools: Bash Read Grep Glob Agent AskUserQuestion
---

# Pre-PR Review Pipeline

Run the full quality pipeline — lint, code review, and tests — then present findings and ask how to proceed with fixes.

Arguments: `$ARGUMENTS` (optional base branch, defaults to `main`)

## Steps

1. **Run all three checks in parallel:**

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

2. **Compile results** — Combine output from all three checks into a single report:

   ```
   ## Lint Results
   - ✅ No issues / ❌ N issues found (list them)

   ## Code Review
   (Paste the code-reviewer agent's structured output: Summary, Issues Found, Verdict)

   ## Test Results
   - ✅ All passed / ❌ N failed (list failures)
   ```

3. **Present findings to the user** — Display the compiled report.

4. **Ask the user how to proceed** — If any issues were found, ask:
   - "Auto-fix all" — apply ruff auto-fixes and send code review findings to the appropriate agent (e.g., dashboard-builder) for fixes
   - "Fix manually" — user will handle the fixes themselves
   - "Ignore and proceed" — skip fixes, the issues are acceptable

5. **Apply fixes based on user choice:**
   - If auto-fix: run `ruff check --fix .` and `ruff format .` for lint issues, then dispatch code review findings to the appropriate agent
   - If manual: do nothing, user handles it
   - If ignore: do nothing

6. **Update documentation** — After all issues are resolved (or skipped), run `/update-docs` to ensure README.md and CLAUDE.md are in sync with the changes on this branch. This step runs regardless of whether fixes were needed — any code change may warrant a docs update.

## Important
- Always present findings before fixing — never auto-fix without asking
- Run lint, code review, and tests in parallel to save time
- If all three checks pass cleanly, report success then proceed directly to the docs update step (skip the fix prompt)
