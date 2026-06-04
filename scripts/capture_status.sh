#!/usr/bin/env bash
set -euo pipefail

# 특정 PID의 순간 상태를 ps와 top으로 저장한다.
# monitor 로그를 보완하는 스냅샷 증거로 사용한다.

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 PID EVIDENCE_DIR LABEL" >&2
  exit 2
fi

PID="$1"
EVIDENCE_DIR="$2"
LABEL="$3"
mkdir -p "$EVIDENCE_DIR"

OUT="$EVIDENCE_DIR/${LABEL}_ps_top.log"
{
  echo "timestamp=$(date -Is)"
  echo
  # ps는 프로세스 상태를 한 줄로 확인하기 좋다.
  echo "$ ps -p $PID -o pid,ppid,stat,pcpu,pmem,rss,vsz,etime,cmd"
  ps -p "$PID" -o pid,ppid,stat,pcpu,pmem,rss,vsz,etime,cmd || true
  echo
  # top은 batch 모드로 여러 번 샘플링해서 짧은 변화를 볼 수 있다.
  echo "$ top -b -n 3 -p $PID"
  top -b -n 3 -p "$PID" || true
} >> "$OUT" 2>&1
