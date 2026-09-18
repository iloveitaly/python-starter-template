#!/usr/bin/env bash
set -euo pipefail

# Cursor long-lived services belong in `start`, not `install`.
# https://cursor.com/docs/cloud-agent/setup#running-docker
curl -fsSL https://raw.githubusercontent.com/iloveitaly/agent-containers/master/cursor/start.sh | bash

# Expand gitignored Cursor/Claude/Copilot/OpenCode files from instructions.md
export MISE_ENV="${MISE_ENV:-dev,extras}"
mise install uv
mise exec -- uvx llm-ide-rules explode instructions.md
