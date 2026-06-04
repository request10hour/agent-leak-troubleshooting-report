#!/usr/bin/env bash
set -euo pipefail

# 공통 실행 환경을 준비한다.
# 앱이 요구하는 디렉터리와 secret.key를 만들고 환경변수를 export한다.

AGENT_HOME="${AGENT_HOME:-$(pwd)/agent_home}"
AGENT_PORT="${AGENT_PORT:-15034}"
AGENT_UPLOAD_DIR="${AGENT_UPLOAD_DIR:-$AGENT_HOME/upload_files}"
AGENT_KEY_PATH="${AGENT_KEY_PATH:-$AGENT_HOME/api_keys}"
AGENT_LOG_DIR="${AGENT_LOG_DIR:-$AGENT_HOME/logs}"

# 앱이 부팅 검사에서 요구하는 폴더와 인증 키 파일을 만든다.
mkdir -p "$AGENT_UPLOAD_DIR" "$AGENT_KEY_PATH" "$AGENT_LOG_DIR"
printf "agent_api_key_test" > "$AGENT_KEY_PATH/secret.key"

# 이후 실행 스크립트와 agent-app-leak 프로세스가 같은 값을 쓰도록 export한다.
export AGENT_HOME
export AGENT_PORT
export AGENT_UPLOAD_DIR
export AGENT_KEY_PATH
export AGENT_LOG_DIR
