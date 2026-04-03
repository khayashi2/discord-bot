#!/bin/bash
# Hook: Auto-format Python files with ruff after editing
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only format Python files
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

# Only format files within the discord-bot project
if [[ "$FILE_PATH" != /Users/khayashi2/vs-code/repos/discord-bot/* ]]; then
  exit 0
fi

# Check if ruff is available
if ! command -v ruff &> /dev/null; then
  exit 0
fi

# Run ruff format on the file
ruff format "$FILE_PATH" 2>/dev/null
ruff check --fix "$FILE_PATH" 2>/dev/null

exit 0
