---
name: refactor
description: Analyze code for refactoring opportunities — duplication, long functions, tangled dependencies, and naming issues.
argument-hint: [file-or-directory]
user-invocable: true
allowed-tools: Bash Read Grep Glob Agent AskUserQuestion
---

# Code Refactor Review

Scan the codebase (or a targeted path) for refactoring opportunities, then present findings in a structured report grouped by category and severity. Ask the user before making any changes.

Arguments: `$ARGUMENTS` (optional file or directory path; defaults to full project scan)

## Steps

1. **Determine scan scope** — If `$ARGUMENTS` specifies a file or directory, limit the scan to that path. Otherwise scan these directories: `dashboard/`, `db/`, `bot/`, `config/`, `scripts/`.

2. **Run all four category scans in parallel:**

   a. **Duplication (`DUP`)** — Check for:
      - Repeated code blocks: look for near-identical logic appearing in multiple functions or files (e.g., the same message-fetching + word-processing pattern in `get_top_words`, `get_user_top_words`, `get_profanity_leaderboard`).
      - Duplicate constants: look for the same regex pattern, magic number, or configuration value defined in multiple places (e.g., `EMOJI_PATTERN`, stopword lists, message limits).
      - Copy-pasted query structures: identify query functions that differ only by a `WHERE` clause filter and could share a common base.

   b. **Complexity (`CX`)** — Check for:
      - Long functions: identify functions exceeding 50 lines that could be broken into smaller, well-named helpers.
      - Deep nesting: look for 3+ levels of indentation from conditionals, loops, or try/except blocks.
      - God functions: functions that handle multiple unrelated responsibilities (e.g., a route handler that does validation, querying, transformation, and rendering).
      - Complex comprehensions: list/dict comprehensions with nested loops or multiple conditions that would be clearer as explicit loops.

   c. **Structure (`STR`)** — Check for:
      - Tangled imports: circular dependencies or modules importing from unexpected layers (e.g., `db/` importing from `dashboard/`, `bot/` importing from `scripts/`).
      - Mixed abstraction levels: functions that mix high-level orchestration with low-level details (e.g., a route handler that builds SQL and also formats HTML).
      - Missing shared utilities: repeated helper logic (e.g., cleaning message content, extracting words) that should live in a shared module.
      - Inconsistent patterns: similar operations handled differently across the codebase (e.g., some queries use `.scalars().all()` while equivalent ones use `.execute()` + manual extraction).

   d. **Naming & Clarity (`NM`)** — Check for:
      - Unclear variable names: single-letter variables outside of simple loop counters, or names that don't convey purpose.
      - Inconsistent naming conventions: mixing `snake_case` and `camelCase`, or inconsistent prefixes for similar concepts (e.g., `get_` vs `fetch_` vs `load_`).
      - Misleading names: functions whose name doesn't match what they actually do.
      - Missing or outdated docstrings on public functions that have non-obvious behavior.

3. **Classify each finding by severity:**
   - **HIGH** — Actively harms maintainability: duplicated logic that must be updated in sync, functions over 100 lines, circular dependencies.
   - **MEDIUM** — Makes the code harder to understand or extend: 50-100 line functions, inconsistent patterns across similar operations, missing shared utilities.
   - **LOW** — Cosmetic or minor clarity improvement: naming inconsistencies, could-be-clearer variable names, slightly verbose comprehensions.

4. **Compile the report** — Present findings in this format:

   ```
   ## Refactor Review — <scope>

   **Scanned:** <list of files/directories checked>
   **Findings:** N total (X high, Y medium, Z low)

   ---

   ### HIGH

   #### [DUP-001] Duplicated word-processing logic across 3 query functions
   **Files:** `dashboard/queries.py:198-220`, `dashboard/queries.py:310-335`, `dashboard/queries.py:378-410`
   **Issue:** `get_top_words`, `get_user_top_words`, and `get_profanity_leaderboard` each independently fetch messages, clean content, split into words, and count with `Counter`. The core logic is identical — only the filter and post-processing differ.
   **Impact:** Bug fixes or changes to word extraction must be applied in 3 places. Risk of drift between implementations.
   **Fix:** Extract a shared `_count_words(session, filters, after)` helper that returns a `Counter`, then have each function call it with its specific filter and post-process the result.

   ---

   ### MEDIUM

   #### [CX-001] `get_awards` function exceeds 80 lines
   ...

   ---

   ### LOW

   #### [NM-001] Inconsistent query function return types
   ...
   ```

   Each finding must include: ID (category prefix + number), file path(s) with line numbers, issue description, impact statement, and suggested fix.

5. **Present findings to the user** — Display the compiled report.

6. **Ask the user how to proceed** — If any findings exist, ask:
   - "Fix all" — apply all suggested refactors across all severity levels
   - "Fix high only" — apply only HIGH-level refactors
   - "Pick individually" — walk through findings one by one and let the user accept or skip each
   - "Export only" — do nothing, user takes the report as-is

7. **Apply fixes based on user choice:**
   - For duplication: extract shared helpers, update callers, verify behavior is preserved.
   - For complexity: break long functions into well-named helpers, flatten nesting with early returns.
   - For structure: move shared logic to appropriate modules, fix import directions.
   - For naming: rename consistently, update all references.
   - After applying any fixes, run `/lint` to verify code quality and `/run-tests` to verify nothing broke.

## Important
- Never auto-fix without presenting findings and asking the user first
- Run all four category scans in parallel to save time
- Include specific line numbers and file paths in every finding — never report a vague issue
- Refactors must preserve existing behavior — never change functionality while refactoring
- When extracting shared helpers, place them in the module where they are most used (e.g., a shared query helper stays in `queries.py` as a private `_function`)
- Do NOT flag code that is intentionally duplicated for clarity (e.g., test fixtures, simple one-liners)
- Do NOT suggest refactors that would make the code harder to understand for the sake of DRY — sometimes a small amount of repetition is clearer than an abstraction
- Consider the project's learning context — prefer straightforward patterns over clever abstractions
- If all checks pass cleanly, report success and skip the fix prompt