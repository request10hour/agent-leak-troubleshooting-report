#!/usr/bin/env bash
set -euo pipefail

# 지정한 환경변수로 agent-app-leak를 실행하고 로그, PID, 메타 정보를 저장한다.
# 실제 장애 판단은 하지 않고, 사람이 확인할 원본 증거만 남긴다.

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

# 케이스별 evidence 파일 경로를 준비한다.
mkdir -p "$EVIDENCE_DIR"
APP_LOG="$EVIDENCE_DIR/${LABEL}_app.log"
META_FILE="$EVIDENCE_DIR/${LABEL}_meta.txt"
PID_FILE="$EVIDENCE_DIR/${LABEL}_pid.txt"

# 실행 조건을 나중에 그대로 확인할 수 있도록 저장한다.
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

# 앱을 백그라운드로 실행하고 launcher PID를 기록한다.
"$APP_PATH" > "$APP_LOG" 2>&1 &
PID="$!"
echo "$PID" > "$PID_FILE"
echo "pid=$PID" >> "$META_FILE"
echo "$PID"
