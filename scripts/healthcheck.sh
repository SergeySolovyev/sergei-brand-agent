#!/bin/sh
# Healthcheck for sergei-brand-agent container.
# Returns 0 if agent is responsive, 1 otherwise.
set -e
test -f /workspace/SOUL.md || exit 1
test -d /workspace/personas || exit 1
test -d /workspace/knowledge_base || exit 1
test -d /workspace/skills || exit 1
sqlite3 /workspace/data/state.sqlite "SELECT 1;" >/dev/null 2>&1 || exit 1
echo "ok"
