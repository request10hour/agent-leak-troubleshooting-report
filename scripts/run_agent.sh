#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 6 ]; then
  echo "Usage: $0 APP_PATH EVIDENCE_DIR LABEL MEMORY_LIMIT CPU_MAX_OCCUPY MULTI_THREAD_ENABLE" >&2
  exit 2
fi

APP_PATH="$1"
EVIDENCE_DIR="$2"
LABEL="$3"
export MEMORY_LIMIT="$4"
export CPU_MAX_OCCUPY="$5"
export MULTI_THREAD_ENABLE="$6"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"
source "$SCRIPT_DIR/env_base.sh"

mkdir -p "$EVIDENCE_DIR"
APP_LOG="$EVIDENCE_DIR/${LABEL}_app.log"
META_FILE="$EVIDENCE_DIR/${LABEL}_meta.txt"
PID_FILE="$EVIDENCE_DIR/${LABEL}_pid.txt"

{
  echo "label=$LABEL"
  echo "start_iso=$(date -Is)"
  echo "app_path=$APP_PATH"
  echo "MEMORY_LIMIT=$MEMORY_LIMIT"
  echo "CPU_MAX_OCCUPY=$CPU_MAX_OCCUPY"
  echo "MULTI_THREAD_ENABLE=$MULTI_THREAD_ENABLE"
  echo "AGENT_HOME=$AGENT_HOME"
  echo "AGENT_PORT=$AGENT_PORT"
} > "$META_FILE"

"$APP_PATH" > "$APP_LOG" 2>&1 &
PID="$!"
echo "$PID" > "$PID_FILE"
echo "pid=$PID" >> "$META_FILE"
echo "$PID"
