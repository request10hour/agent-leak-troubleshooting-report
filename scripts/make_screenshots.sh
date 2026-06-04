#!/usr/bin/env bash
set -euo pipefail

# 기존 evidence 로그를 실제 xterm 창에서 조회하는 장면을 캡처한다.
# 새 실험은 실행하지 않고, xdotool로 명령어를 직접 입력한다.

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

mkdir -p evidence/screenshots

USE_XVFB=0
XVFB_PID=""
TERM_PID=""
WIN_ID=""
CAPTURE_CMD=""
TMP_DIR=""

# 열려 있는 xterm과 Xvfb를 정리한다.
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

# DISPLAY가 없으면 Xvfb로 가상 GUI 화면을 만든다.
start_display_if_needed() {
  local display_num

  if [ -n "${DISPLAY:-}" ]; then
    return 0
  fi

  if ! command -v Xvfb >/dev/null 2>&1; then
    echo "No DISPLAY and Xvfb not available" >&2
    exit 1
  fi

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

# 필요한 GUI 도구가 있는지 확인한다.
check_tools() {
  for tool in xterm xdotool; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      echo "$tool not available" >&2
      exit 1
    fi
  done

  if command -v scrot >/dev/null 2>&1; then
    CAPTURE_CMD="scrot"
  elif command -v import >/dev/null 2>&1; then
    CAPTURE_CMD="import"
  else
    echo "No screenshot tool found: scrot or import required" >&2
    exit 1
  fi
}

# 자연스러운 프롬프트가 보이는 대화형 xterm을 연다.
open_terminal() {
  local title="$1"
  local rcfile="$TMP_DIR/bashrc"

  cat > "$rcfile" <<'RC'
PS1='\u@\h:\w\$ '
alias grep='grep --color=never'
RC

  xterm \
    -T "$title" \
    -geometry 160x46+10+10 \
    -fa Monospace \
    -fs 10 \
    -bg white \
    -fg black \
    -e bash --rcfile "$rcfile" -i &
  TERM_PID=$!

  WIN_ID="$(xdotool search --sync --onlyvisible --name "$title" | tail -n 1)"
  sleep 1
}

# xdotool로 명령어를 실제 입력하고 Enter를 누른다.
type_command() {
  local command="$1"

  xdotool windowfocus "$WIN_ID" 2>/dev/null || true
  xdotool type --window "$WIN_ID" --delay 1 "$command"
  xdotool key --window "$WIN_ID" Return
  sleep 0.7
}

# 현재 X 화면을 PNG로 저장한다.
capture_screen() {
  local outfile="$1"

  rm -f "$outfile"
  sleep 1
  if [ "$CAPTURE_CMD" = "scrot" ]; then
    scrot "$outfile"
  else
    import -window root "$outfile"
  fi

  if [ ! -s "$outfile" ]; then
    echo "Screenshot failed or empty: $outfile" >&2
    exit 1
  fi
}

# 현재 케이스의 xterm을 닫고 다음 캡처를 준비한다.
close_terminal() {
  if [ -n "$TERM_PID" ]; then
    kill "$TERM_PID" 2>/dev/null || true
  fi
  TERM_PID=""
  WIN_ID=""
  sleep 1
}

# OOM 로그에서 RSS 증가와 MemoryGuard 종료를 확인한다.
capture_oom() {
  open_terminal "agent-oom-terminal"
  type_command "pwd"
  type_command "whoami"
  type_command "sed -n '82,87p' docs/issues/01_oom.md"
  type_command "grep -E \"21620|149640|process_missing\" evidence/oom/before_monitor.log"
  type_command "grep -E \"21580|277620|process_missing\" evidence/oom/after_monitor.log"
  type_command "grep -E \"Memory limit exceeded|Self-terminating process\" evidence/oom/before_app.log evidence/oom/after_app.log"
  capture_screen "evidence/screenshots/01_oom_terminal.png"
  close_terminal
}

# CPU 로그에서 CpuWorker 증가, threshold 초과, cooldown을 확인한다.
capture_cpu() {
  open_terminal "agent-cpu-terminal"
  type_command "pwd"
  type_command "whoami"
  type_command "grep -n \"Before | 100%\\|After | 10%\" docs/issues/02_cpu.md"
  type_command "grep -E \"Current Load: 57.45|CPU Threshold Violated\" evidence/cpu/before_app.log"
  type_command "grep -E \"Peak reached \\(10.00%\\)\" evidence/cpu/after_app.log | head -n 3"
  type_command "grep -E \"10488|process_missing\" evidence/cpu/before_monitor.log | tail -n 5"
  type_command "grep -n \"No literal WATCHDOG\" docs/issues/02_cpu.md"
  capture_screen "evidence/screenshots/02_cpu_terminal.png"
  close_terminal
}

# Deadlock 로그에서 PID 생존, 로그 정지, lock 순환 대기를 확인한다.
capture_deadlock() {
  open_terminal "agent-deadlock-terminal"
  type_command "pwd"
  type_command "whoami"
  type_command "grep -n \"Before MULTI_THREAD_ENABLE\\|After  MULTI_THREAD_ENABLE\" docs/issues/03_deadlock.md"
  type_command "grep -E \"10960|10964\" evidence/deadlock/before_ps.txt"
  type_command "grep -E \"log_size_t1_bytes=2693|log_size_t2_bytes=2693|log_size_changed=no\" docs/issues/03_deadlock.md"
  type_command "grep -E \"WAITING|BLOCKED|Shared_Memory_A|Socket_Pool_B\" evidence/deadlock/before_app.log | tail -n 6"
  type_command "grep -E \"RSS=21708KB|SNl\" docs/issues/03_deadlock.md | head -n 4"
  type_command "grep -E \"^MULTI_THREAD_ENABLE=false$|^log_size_t1_bytes=3538$|^log_size_t2_bytes=5662$|^log_size_changed=yes$\" docs/issues/03_deadlock.md"
  capture_screen "evidence/screenshots/03_deadlock_terminal.png"
  close_terminal
}

start_display_if_needed
check_tools
capture_oom
capture_cpu
capture_deadlock

echo "Created screenshots:"
ls -lh evidence/screenshots/*.png
