---
name: update-docs
description: Update project documentation (README.md) to reflect recent changes. Use after adding a cog, new feature, migration, or any significant change to the project.
argument-hint: [what-changed]
user-invocable: true
allowed-tools: Read Edit Glob Grep
---

# Update Documentation

Keep the project's README.md and CLAUDE.md in sync with the current state of the codebase.

Arguments (what changed): `$ARGUMENTS`

## Steps

1. **Read the current docs**:
   - `README.md` — the public-facing project overview
   - `CLAUDE.md` — the developer/architecture notes

2. **Scan the codebase** to understand the current state:
   - `bot/main.py` — check the `EXTENSIONS` list for registered cogs
   - `bot/cogs/` — list all cog files
   - `db/models.py` — check for new/changed models
   - `db/migrations/versions/` — list all migrations
   - `dashboard/app.py` — check routes
   - `.env.example` — check required environment variables

3. **Update README.md** as needed:
   - **Project Structure** section: reflect any new files, cogs, or directories
   - **Tech Stack**: update if new dependencies were added (check `requirements.txt`)
   - **Getting Started / Setup**: update if new env vars are required (from `.env.example`)
   - **Features section** (add one if it doesn't exist): describe what the bot tracks/displays
   - **Design Decisions & Thought Process** section (add if it doesn't exist): for each major feature or architectural choice, document:
     - **What was decided** — the approach taken (e.g., upserts, composite keys, regex parsing)
     - **Why** — the reasoning behind it (e.g., "upserts keep metadata fresh without duplicates")
     - **What to consider** — trade-offs, gotchas, or alternatives a junior developer should know about
     - Group entries by feature/cog so the section grows naturally as the project evolves
     - Write in plain language — this section is meant to teach, not just document
   - Keep the tone clear and beginner-friendly — this is a portfolio project

4. **Update CLAUDE.md** as needed (architecture/developer notes):
   - **Architecture** section: reflect new cogs, modules, or design decisions
   - **Key Design Decisions**: document *why* new choices were made, not just what changed
   - **Learning Opportunity** section: if a new pattern or concept was introduced, add a brief explanation of the thought process and what to consider — this is intentional for the portfolio

5. **Conventional commit reminder**: After updating docs, remind the user to commit with:
   ```
   docs: update README and CLAUDE.md to reflect <what-changed>
   ```

## Important
- Do NOT rewrite sections that are already accurate — only update what's out of date
- Keep the **Learning Opportunity** / thought-process explanations in CLAUDE.md — they are intentional
- The **Design Decisions & Thought Process** section in README is a key part of the portfolio — always check if new work needs an entry there. If the section doesn't exist yet, create it.
- README is public-facing: keep it clean, concise, and non-technical where possible
- CLAUDE.md is developer-facing: include rationale, trade-offs, and implementation notes
