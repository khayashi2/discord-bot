---
name: security-check
description: Scan code for security vulnerabilities — credential leaks, SQL injection, XSS, insecure config, and dependency risks.
argument-hint: [file-or-directory]
user-invocable: true
allowed-tools: Bash Read Grep Glob Agent AskUserQuestion
---

# Security Check

Scan the codebase (or a targeted path) for security vulnerabilities and misconfigurations, then present findings in a structured report grouped by category and severity. Ask the user before making any changes.

Arguments: `$ARGUMENTS` (optional file or directory path; defaults to full project scan)

## Steps

1. **Determine scan scope** — If `$ARGUMENTS` specifies a file or directory, limit the scan to that path. Otherwise scan the full project excluding `node_modules/`, `.venv/`, `__pycache__/`, and `.git/`.

2. **Run all five category scans in parallel:**

   a. **Secrets & Credentials (`SEC`)** — Check for:
      - Hardcoded secrets: search for patterns like API keys, tokens, passwords, or connection strings in source code (not `.env` or `.env.example`). Look for strings matching `token`, `secret`, `password`, `api_key`, `DATABASE_URL` assigned to literals.
      - `.env` exposure: verify `.env` is in `.gitignore`. Check that `.env.example` contains only placeholder values (no real credentials).
      - Config leaks: ensure `config.py` reads from environment variables and never defines default credential values.

   b. **Injection (`INJ`)** — Check for:
      - SQL injection: look for raw SQL strings built with f-strings or `.format()`. Verify all queries use SQLAlchemy's parameterized `select()` / `insert()` / `where()` instead of string interpolation.
      - Command injection: look for `subprocess`, `os.system`, or `os.popen` calls with user-controlled input.
      - Template injection: check Jinja2 templates for `| safe` filters or `{% autoescape false %}` blocks that disable escaping. Look for user-supplied content rendered without escaping.

   c. **Web Security (`WEB`)** — Check for:
      - XSS: look for user-generated content (messages, usernames, channel names) rendered in templates without escaping. Check that Jinja2 autoescaping is enabled.
      - CORS misconfiguration: check FastAPI middleware for overly permissive `allow_origins=["*"]` or missing CORS configuration.
      - Missing security headers: check for absence of `X-Content-Type-Options`, `X-Frame-Options`, or `Content-Security-Policy` headers in the dashboard app.
      - Open redirects: look for redirect endpoints that accept unvalidated URLs from query parameters.

   d. **Dependencies (`DEP`)** — Check for:
      - Pinned versions: verify `requirements.txt` pins exact versions (not just `>=`). Unpinned dependencies risk pulling in vulnerable versions.
      - Known vulnerabilities: run `pip audit` if available, or check for obviously outdated packages.

   e. **Configuration (`CFG`)** — Check for:
      - Debug mode in production: look for `debug=True` or `DEBUG=True` in app startup code.
      - Overly permissive database connections: check for `sslmode=disable` or missing SSL in connection strings.
      - Missing rate limiting: check if the dashboard exposes API endpoints without rate limiting.
      - Exposed error details: look for exception handlers that return full tracebacks to clients.

3. **Classify each finding by severity:**
   - **CRITICAL** — Immediate exploit risk: hardcoded credentials, SQL injection, disabled autoescape on user content.
   - **WARNING** — Exploitable under certain conditions: missing security headers, overly permissive CORS, unpinned dependencies, `| safe` on semi-trusted content.
   - **INFO** — Hardening opportunity: missing rate limiting, could add CSP headers, debug mode only in dev config.

4. **Compile the report** — Present findings in this format:

   ```
   ## Security Check — <scope>

   **Scanned:** <list of files/directories checked>
   **Findings:** N total (X critical, Y warning, Z info)

   ---

   ### CRITICAL

   #### [SEC-001] Hardcoded database password in config
   **File:** `config.py:12`
   **Issue:** `DB_PASSWORD` has a hardcoded fallback value instead of requiring the environment variable.
   **Risk:** Credentials exposed in source control. Anyone with repo access can connect to the database.
   **Fix:** Remove the default value; raise an error if the env var is missing.

   ---

   ### WARNING

   #### [WEB-001] Missing Content-Security-Policy header
   ...

   ---

   ### INFO

   #### [CFG-001] No rate limiting on API endpoints
   ...
   ```

   Each finding must include: ID (category prefix + number), file path with line numbers, issue description, risk statement, and suggested fix.

5. **Present findings to the user** — Display the compiled report.

6. **Ask the user how to proceed** — If any findings exist, ask:
   - "Fix all" — apply all suggested fixes across all severity levels
   - "Fix critical only" — apply only CRITICAL-level fixes
   - "Pick individually" — walk through findings one by one and let the user accept or skip each
   - "Export only" — do nothing, user takes the report as-is

7. **Apply fixes based on user choice:**
   - For hardcoded secrets: remove default values, add env var validation to `config.py`, update `.env.example` if needed.
   - For injection risks: replace string interpolation with parameterized queries or safe template rendering.
   - For web security: add middleware or headers to the FastAPI app.
   - For dependency issues: pin versions in `requirements.txt`.
   - After applying any fixes, run `/lint` to verify code quality and `/run-tests` to verify nothing broke.

## Important
- Never auto-fix without presenting findings and asking the user first
- Run all five category scans in parallel to save time
- Include specific line numbers and file paths in every finding — never report a vague issue
- False positives are worse than missed findings — only report issues you are confident about
- Do NOT flag `.env` contents as a finding (it is excluded from git). Only flag if `.env` is missing from `.gitignore`
- Do NOT flag test files for hardcoded test values — test fixtures with fake tokens/passwords are expected
- When checking templates, verify Jinja2 autoescaping is enabled globally before flagging individual templates
- If all checks pass cleanly, report success and skip the fix prompt
