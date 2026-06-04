#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 PID OUTPUT_FILE [INTERVAL_SECONDS] [COUNT]" >&2
  exit 2
fi

PID="$1"
OUTPUT_FILE="$2"
INTERVAL="${3:-1}"
COUNT="${4:-0}"
mkdir -p "$(dirname "$OUTPUT_FILE")"

{
  echo "monitor_start=$(date -Is)"
  echo "pid=$PID"
  echo "columns=timestamp pid stat pcpu pmem rss_kb vsz_kb etime cmd"
} >> "$OUTPUT_FILE"

i=0
while true; do
  if ! ps -p "$PID" >/dev/null 2>&1; then
    echo "$(date -Is) process_missing pid=$PID" >> "$OUTPUT_FILE"
    break
  fi

  printf "%s " "$(date -Is)" >> "$OUTPUT_FILE"
  ps -p "$PID" -o pid=,stat=,pcpu=,pmem=,rss=,vsz=,etime=,cmd= >> "$OUTPUT_FILE" || true

  i=$((i + 1))
  if [ "$COUNT" -gt 0 ] && [ "$i" -ge "$COUNT" ]; then
    break
  fi
  sleep "$INTERVAL"
done
