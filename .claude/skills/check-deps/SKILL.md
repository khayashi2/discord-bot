---
name: check-deps
description: Verify all dependencies (CLI tools, Python packages, environment variables) are available to build and run the project locally.
argument-hint:
user-invocable: true
allowed-tools: Bash Read Grep
---

# Check Dependencies

Verify that your local machine has all the tools and packages needed to build and run the Discord Analytics Bot.

## Steps

1. **Check CLI tools** — verify required binaries are installed and correct versions:
   - Python 3.12+ (`python3 --version`)
   - Docker (`docker --version`)
   - Docker Compose (`docker compose --version`)
   - Git (`git --version`)
   - curl (`curl --version`)

2. **Check Python packages** — verify requirements.txt dependencies are installed:

   ```bash
   pip list
   ```

   Compare against `requirements.txt` to ensure all packages are installed.

3. **Check environment variables** — verify `.env` file exists and contains all required variables from `.env.example`:
   - Read `.env.example` to see required variables
   - Check if `.env` exists in the project root
   - Verify all required variables are set in `.env` (non-empty values)
   - Warn if any are missing

4. **Report results** in a clear format:

   ```
   ## CLI Tools
   - ✅ Python 3.12.x / ❌ Python missing or wrong version
   - ✅ Docker x.x.x / ❌ Docker not found
   - ✅ Docker Compose x.x.x / ❌ Docker Compose not found
   - ✅ Git x.x.x / ❌ Git not found
   - ✅ curl x.x.x / ❌ curl not found

   ## Python Packages
   - ✅ All required packages installed (X packages)
   - ❌ Missing packages: [list them]
   - ❌ Wrong versions: [list them]

   ## Environment Variables
   - ✅ .env file exists
   - ✅ All required variables are set
   - ❌ Missing variables: [list them]
   ```

5. **Summary** — if all checks pass, report success and user is ready to build. If anything is missing, suggest fixes:
   - For missing CLI tools: suggest `brew install <tool>` or `apt-get install <tool>` depending on OS
   - For missing Python packages: suggest `pip install -r requirements.txt`
   - For missing env vars: suggest copying `.env.example` to `.env` and filling in values

## Important

- Do not modify any files unless explicitly fixing env vars (and only if user approves)
- Focus on accurate reporting of what's missing
- Be helpful with setup suggestions for common issues
