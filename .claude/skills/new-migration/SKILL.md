---
name: new-migration
description: Create a new Alembic database migration. Use when adding or modifying database tables/columns.
argument-hint: <migration-description>
user-invocable: true
allowed-tools: Read Edit Write Bash Grep Glob
---

# Create a New Alembic Migration

Generate a new Alembic migration for the discord-bot database.

Arguments: `$ARGUMENTS`

## Steps

1. **Read the current models** at `db/models.py` to understand the current schema.

2. **Read existing migrations** in `db/migrations/versions/` to understand the migration numbering scheme and patterns.

3. **If the user describes schema changes**, first update `db/models.py` with the new/modified SQLAlchemy models following the existing patterns (BigInteger IDs, `ingested_at` timestamps, etc.).

4. **Generate the migration** by running:
   ```bash
   cd /Users/khayashi2/vs-code/repos/discord-bot && alembic revision --autogenerate -m "<description>"
   ```
   If autogenerate isn't available or fails, create the migration manually following the pattern in existing versions.

5. **Review the generated migration** to ensure:
   - The upgrade and downgrade functions are correct
   - No unintended changes are included
   - Table/column names follow the existing snake_case convention

6. **Run linting** on the new migration file: `ruff check db/migrations/versions/`

## Important
- Always include both `upgrade()` and `downgrade()` functions
- Use `BigInteger` for Discord snowflake IDs
- Include `ingested_at` with `server_default=func.now()` for new tables
- Follow the existing migration numbering convention
