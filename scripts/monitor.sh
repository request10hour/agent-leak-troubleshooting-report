#!/usr/bin/env bash
set -euo pipefail

# 지정한 PID가 살아있는 동안 ps로 CPU/MEM/RSS를 주기적으로 기록한다.
# 프로세스가 사라지면 process_missing을 남기고 종료한다.

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 PID OUTPUT_FILE [INTERVAL_SECONDS] [COUNT]" >&2
  exit 2
fi

PID="$1"
OUTPUT_FILE="$2"
INTERVAL="${3:-1}"
COUNT="${4:-0}"
mkdir -p "$(dirname "$OUTPUT_FILE")"

# 로그 맨 위에 관찰 시작 시각과 컬럼 의미를 남긴다.
{
  echo "monitor_start=$(date -Is)"
  echo "pid=$PID"
  echo "columns=timestamp pid stat pcpu pmem rss_kb vsz_kb etime cmd"
} >> "$OUTPUT_FILE"

i=0
while true; do
  # PID가 사라진 시점도 중요한 증거이므로 별도 메시지로 기록한다.
  if ! ps -p "$PID" >/dev/null 2>&1; then
    echo "$(date -Is) process_missing pid=$PID" >> "$OUTPUT_FILE"
    break
  fi

  # ps 출력에는 CPU, 메모리, RSS, 실행 시간이 포함된다.
  printf "%s " "$(date -Is)" >> "$OUTPUT_FILE"
  ps -p "$PID" -o pid=,stat=,pcpu=,pmem=,rss=,vsz=,etime=,cmd= >> "$OUTPUT_FILE" || true

  i=$((i + 1))
  if [ "$COUNT" -gt 0 ] && [ "$i" -ge "$COUNT" ]; then
    break
  fi
  sleep "$INTERVAL"
done
