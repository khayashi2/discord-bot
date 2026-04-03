---
name: new-cog
description: Scaffold a new discord.py cog with boilerplate code, register it in bot/main.py, and create a test file. Use when adding a new bot feature or command.
argument-hint: <cog-name> [description]
user-invocable: true
allowed-tools: Read Edit Write Grep Glob
---

# Scaffold a New Discord.py Cog

Create a new cog for the discord bot. The user will provide a cog name and optionally a description.

Arguments: `$ARGUMENTS`

## Steps

1. **Parse the cog name** from the first argument. Convert it to:
   - snake_case for the filename (e.g., `word_tracker`)
   - PascalCase for the class name (e.g., `WordTracker`)

2. **Create the cog file** at `bot/cogs/<snake_case>.py` following this project's patterns:
   - Import `logging`, `discord`, `commands` from `discord.ext`
   - Import `async_session` from `db.database` and relevant models from `db.models`
   - Use `pg_insert` from `sqlalchemy.dialects.postgresql` if doing upserts
   - Create a class inheriting from `commands.Cog` with `__init__(self, bot)` 
   - Add an `async def setup(bot)` function at the bottom that calls `bot.add_cog()`
   - Follow the exact same patterns as `bot/cogs/listener.py`

3. **Register the cog** in `bot/main.py` by adding `"bot.cogs.<snake_case>"` to the `EXTENSIONS` list.

4. **Create a test file** at `tests/test_<snake_case>.py` following the patterns in `tests/test_listener.py`:
   - Use `pytest` and `pytest.mark.asyncio`
   - Use `unittest.mock` (MagicMock, AsyncMock, patch)
   - Include the `_make_message()` helper if testing message handling
   - Test that `setup()` registers the cog
   - Add at least one test for core functionality

5. **Verify** by running `ruff check bot/cogs/<snake_case>.py tests/test_<snake_case>.py` to ensure no lint errors.

## Important
- Use async patterns consistent with the rest of the codebase
- Follow conventional commit style if making a commit
- Do NOT hardcode any credentials or tokens
