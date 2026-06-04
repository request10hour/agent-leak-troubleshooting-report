#!/usr/bin/env bash
set -euo pipefail

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
  echo "$ ps -p $PID -o pid,ppid,stat,pcpu,pmem,rss,vsz,etime,cmd"
  ps -p "$PID" -o pid,ppid,stat,pcpu,pmem,rss,vsz,etime,cmd || true
  echo
  echo "$ top -b -n 3 -p $PID"
  top -b -n 3 -p "$PID" || true
} >> "$OUT" 2>&1
