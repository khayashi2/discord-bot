#!/bin/bash
# Hook: Validate that git commit messages follow conventional commit format
# Required prefixes: feat:, fix:, chore:, docs:, test:, refactor:

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check git commit commands
if ! echo "$COMMAND" | grep -qE '^git commit'; then
  exit 0
fi

# Try to extract the commit message from various formats:
# 1. Standard -m "message" or -m 'message'
# 2. Heredoc: -m "$(cat <<'EOF' ... EOF )"
MSG=""

# First try heredoc format — extract the first non-empty line after the heredoc opener
if echo "$COMMAND" | grep -qE "cat <<['\"]?EOF"; then
  MSG=$(echo "$COMMAND" | sed -n "/cat <<['\"\]\\{0,1\\}EOF/,/^[[:space:]]*EOF/{/cat <</d;/^[[:space:]]*EOF/d;p;}" | head -1 | sed 's/^[[:space:]]*//')
fi

# Fall back to standard -m flag extraction
if [ -z "$MSG" ]; then
  MSG=$(echo "$COMMAND" | grep -oP "(?<=-m\s[\"'])[^\"']+" || echo "$COMMAND" | grep -oP '(?<=-m\s)\S+')
fi

# If we still can't extract a message, allow it through (e.g., --amend with no -m)
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
