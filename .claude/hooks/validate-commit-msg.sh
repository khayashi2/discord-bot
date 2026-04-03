#!/bin/bash
# Hook: Validate that git commit messages follow conventional commit format
# Required prefixes: feat:, fix:, chore:, docs:, test:, refactor:

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check git commit commands
if ! echo "$COMMAND" | grep -qE '^git commit'; then
  exit 0
fi

# Extract the commit message from -m flag
MSG=$(echo "$COMMAND" | grep -oP '(?<=-m\s["\x27])[^"\x27]+' || echo "$COMMAND" | grep -oP '(?<=-m\s)\S+')

# If using heredoc or other format, skip validation
if [ -z "$MSG" ]; then
  exit 0
fi

# Check for conventional commit prefix
if ! echo "$MSG" | grep -qE '^(feat|fix|chore|docs|test|refactor|ci|style|perf|build|revert)(\(.+\))?!?:'; then
  echo "Commit message must follow conventional commits format." >&2
  echo "Required prefix: feat:, fix:, chore:, docs:, test:, refactor:, ci:, style:, perf:, build:, or revert:" >&2
  echo "Example: feat: add word tracking cog" >&2
  echo "Got: $MSG" >&2
  exit 2
fi

exit 0
