#!/usr/bin/env bash
set -euo pipefail

AGENT_HOME="${AGENT_HOME:-$(pwd)/agent_home}"
AGENT_PORT="${AGENT_PORT:-15034}"
AGENT_UPLOAD_DIR="${AGENT_UPLOAD_DIR:-$AGENT_HOME/upload_files}"
AGENT_KEY_PATH="${AGENT_KEY_PATH:-$AGENT_HOME/api_keys}"
AGENT_LOG_DIR="${AGENT_LOG_DIR:-$AGENT_HOME/logs}"

mkdir -p "$AGENT_UPLOAD_DIR" "$AGENT_KEY_PATH" "$AGENT_LOG_DIR"
printf "agent_api_key_test" > "$AGENT_KEY_PATH/secret.key"

export AGENT_HOME
export AGENT_PORT
export AGENT_UPLOAD_DIR
export AGENT_KEY_PATH
export AGENT_LOG_DIR
