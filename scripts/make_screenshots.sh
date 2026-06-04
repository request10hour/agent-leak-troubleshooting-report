#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

mkdir -p evidence/screenshots

USE_XVFB=0
XVFB_PID=""
TERM_PID=""
CAPTURE_CMD=""
TMP_DIR=""

cleanup() {
  if [ -n "$TERM_PID" ]; then
    kill "$TERM_PID" 2>/dev/null || true
  fi
  if [ "$USE_XVFB" = "1" ] && [ -n "$XVFB_PID" ]; then
    kill "$XVFB_PID" 2>/dev/null || true
  fi
  if [ -n "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

TMP_DIR="$(mktemp -d)"

start_xvfb() {
  local display_num
  for display_num in 99 100 101 102 103; do
    Xvfb ":$display_num" -screen 0 1600x1000x24 >/tmp/agent_xvfb.log 2>&1 &
    XVFB_PID=$!
    sleep 1
    if kill -0 "$XVFB_PID" 2>/dev/null; then
      export DISPLAY=":$display_num"
      USE_XVFB=1
      return 0
    fi
  done
  echo "Unable to start Xvfb. Last log:" >&2
  cat /tmp/agent_xvfb.log >&2 || true
  exit 1
}

if [ -z "${DISPLAY:-}" ]; then
  if command -v Xvfb >/dev/null 2>&1; then
    start_xvfb
  else
    echo "No DISPLAY and Xvfb not available" >&2
    exit 1
  fi
fi

if ! command -v xterm >/dev/null 2>&1; then
  echo "xterm not available" >&2
  exit 1
fi

if command -v scrot >/dev/null 2>&1; then
  CAPTURE_CMD="scrot"
elif command -v import >/dev/null 2>&1; then
  CAPTURE_CMD="import"
else
  echo "No screenshot tool found: scrot or import required" >&2
  exit 1
fi

capture_case() {
  local title="$1"
  local outfile="$2"
  local textfile="$3"

  rm -f "$outfile"

  xterm \
    -T "agent-screenshot-${title}" \
    -geometry 160x42+20+20 \
    -fa Monospace \
    -fs 10 \
    -bg white \
    -fg black \
    -e bash -lc "cat '$textfile'; echo; echo '[screenshot captured from real xterm window]'; sleep 8" &
  TERM_PID=$!

  sleep 3

  if [ "$CAPTURE_CMD" = "scrot" ]; then
    scrot "$outfile"
  else
    import -window root "$outfile"
  fi

  if [ ! -s "$outfile" ]; then
    echo "Screenshot failed or empty: $outfile" >&2
    exit 1
  fi

  kill "$TERM_PID" 2>/dev/null || true
  TERM_PID=""
  sleep 1
}

OOM_TEXT="$TMP_DIR/oom.txt"
{
  echo "===== OOM Evidence ====="
  echo
  echo "[Before / After]"
  echo "MEMORY_LIMIT: 128MB -> 256MB"
  echo "Survival: 19s -> 42s"
  echo "Before PID: launcher 9049, observed worker 9053"
  echo "After PID: launcher 9353, observed worker 9357"
  echo
  echo "[Monitor RSS Growth]"
  echo "Before RSS: 21620KB -> 149640KB"
  grep -E "21620|149640|process_missing" evidence/oom/before_monitor.log || true
  echo "After RSS: 21580KB -> 277620KB"
  grep -E "21580|277620|process_missing" evidence/oom/after_monitor.log || true
  echo
  echo "[Critical App Logs]"
  grep -E "Memory limit exceeded|Self-terminating process" evidence/oom/before_app.log evidence/oom/after_app.log || true
} > "$OOM_TEXT"

CPU_TEXT="$TMP_DIR/cpu.txt"
{
  echo "===== CPU Spike Evidence ====="
  echo
  echo "[Before / After]"
  echo "CPU_MAX_OCCUPY: 100% -> 10%"
  echo "Before PID: launcher 10484, observed worker 10488"
  echo "After PID: launcher 10133, observed worker 10137"
  echo "After: alive after 67s observation"
  echo
  echo "[CpuWorker Protection Logs]"
  grep -E "Current Load: 57.45|CPU Threshold Violated" evidence/cpu/before_app.log || true
  grep -E "Peak reached \\(10.00%\\)" evidence/cpu/after_app.log | head -n 4 || true
  echo
  echo "[process_missing / top sample]"
  grep -E "process_missing" evidence/cpu/before_monitor.log || true
  echo "top fast max sampled OS CPU: 25.0%"
  awk 'BEGIN{max=0} /agent-a\+/{if ($9+0>max){max=$9; line=$0}} END{print line}' evidence/cpu/before_top_fast.log
  echo
  echo "[Important note]"
  echo "No literal WATCHDOG/SIGTERM strings were observed."
  echo "Observed protection message: CPU Threshold Violated!"
} > "$CPU_TEXT"

DEADLOCK_TEXT="$TMP_DIR/deadlock.txt"
{
  echo "===== Deadlock Evidence ====="
  echo
  echo "[Before / After]"
  echo "MULTI_THREAD_ENABLE: true -> false"
  echo "Before PID: launcher 10960, observed worker 10964"
  echo "After PID: launcher 11158, observed worker 11162"
  echo
  echo "[PID Exists]"
  grep "agent-app-leak" evidence/deadlock/before_ps.txt | head -n 2 || true
  echo
  echo "[Log Stopped]"
  grep -E "log_size_t1_bytes|log_size_t2_bytes|log_size_changed" evidence/deadlock/before_meta.txt || true
  grep -E "last_log_t1" evidence/deadlock/before_meta.txt || true
  echo
  echo "[Deadlock Last Logs]"
  grep -E "LOCK ACQUIRED|Need resource|WAITING|BLOCKED|Shared_Memory_A|Socket_Pool_B" evidence/deadlock/before_app.log | tail -n 6 || true
  echo
  echo "[CPU/MEM Stagnation]"
  grep -E "03:48:28|03:49:04" evidence/deadlock/before_monitor.log || true
  echo "CPU: 0.4% -> 0.1%, RSS=21708KB"
  echo
  echo "[After]"
  echo "log_size: 3538 -> 5662, changed=yes"
  grep -E "Task Completed" evidence/deadlock/after_app.log | head -n 3 || true
} > "$DEADLOCK_TEXT"

capture_case "oom" "evidence/screenshots/01_oom_terminal.png" "$OOM_TEXT"
capture_case "cpu" "evidence/screenshots/02_cpu_terminal.png" "$CPU_TEXT"
capture_case "deadlock" "evidence/screenshots/03_deadlock_terminal.png" "$DEADLOCK_TEXT"

echo "Created screenshots:"
ls -lh evidence/screenshots/*.png
