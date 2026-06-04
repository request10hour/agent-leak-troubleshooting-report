===== FINAL REPORT FOR USER =====

Repository:
- URL: https://github.com/request10hour/agent-leak-troubleshooting-report

Environment:
- Ubuntu: Ubuntu 24.04.4 LTS
- User: c10hour0574
- Root 여부: root가 아닌 일반 사용자
- GitHub Push 여부: 완료

Created Files:
- README.md
- docs/environment.md
- docs/issues/01_oom.md
- docs/issues/02_cpu.md
- docs/issues/03_deadlock.md
- docs/evaluation_answers.md
- docs/evaluation_checklist.md
- docs/prerequisites.md
- docs/final_report.md
- evidence/oom/*
- evidence/cpu/*
- evidence/deadlock/*
- evidence/screenshots/*
- evidence/graphs/*
- scripts/env_base.sh
- scripts/run_agent.sh
- scripts/monitor.sh
- scripts/capture_status.sh
- scripts/make_screenshots.sh
- scripts/make_graphs.py

Screenshot Evidence:
- OOM: evidence/screenshots/01_oom_terminal.png
- CPU: evidence/screenshots/02_cpu_terminal.png
- Deadlock: evidence/screenshots/03_deadlock_terminal.png
- Terminal screenshots were captured from xterm windows only, not the full Xvfb root screen.

GUI Capture Method:
- Direct DISPLAY: not available
- Xvfb: used
- Terminal program: xterm
- Command typing tool: xdotool
- Screenshot tool: scrot

Graph Evidence:
- OOM RSS growth: evidence/graphs/01_oom_rss_growth.svg
- CPU load growth: evidence/graphs/02_cpu_load_growth.svg
- OOM graph uses two panels for Before/After, collapsed RSS change points, MEMORY_LIMIT lines, and process_missing markers while preserving raw logs.
- CPU graph uses fixed 0-60% y-axis ticks, 10%/50% reference lines, and a `CPU Threshold Violated! (57.45%)` annotation.

Evaluation Checklist:
- docs/evaluation_checklist.md

OOM Summary:
- PID: launcher 9049, observed worker 9053
- MEMORY_LIMIT Before/After: 128MB -> 256MB
- 생존 시간 변화: 19초 -> 42초
- monitor 핵심: RSS 21620KB -> 149640KB, After는 21580KB -> 277620KB
- 핵심 로그:
  - `Memory limit exceeded (150MB >= 128MB)`
  - `Self-terminating process 9053`
  - After에서는 `Memory limit exceeded (275MB >= 256MB)`와 `Self-terminating process 9357`

CPU Summary:
- PID: launcher 10484, observed worker 10488
- CPU_MAX_OCCUPY Before/After: 100% -> 10%
- CPU 사용률 변화:
  - 앱 내부 `CpuWorker` load: 5.00% -> 57.45%
  - 고빈도 `top -b -d 0.2` 샘플 최대 OS `%CPU`: 25.0%
- 핵심 로그:
  - `CpuWorker Started. Maximum CPU Limit: 100%`
  - `Current Load: 57.45%`
  - `CPU Threshold Violated! (57.45%)`
- After는 67초 관찰 후에도 살아 있었고 `Peak reached (10.00%). Starting cooldown...`를 반복했다.

Deadlock Summary:
- PID: launcher 10960, observed worker 10964
- MULTI_THREAD_ENABLE Before/After: true -> false
- CPU/MEM 정체:
  - monitor에서 RSS가 21708KB로 유지됨
  - CPU는 0.4% -> 0.1% 수준으로 낮아짐
  - 로그 크기 2693 bytes -> 2693 bytes로 변하지 않음
- 마지막 로그:
  - `Worker-Thread-2 WAITING for [Shared_Memory_A]... (Status: BLOCKED)`
  - `Worker-Thread-1 WAITING for [Socket_Pool_B]... (Status: BLOCKED)`
- After는 로그 크기 3538 bytes -> 5662 bytes로 증가했고 Thread-A/B/C가 순차 완료되었다.

Important Explanation Points:
- 실제 리소스를 쓰는 PID는 런처의 자식 프로세스였다. 그래서 launcher PID와 observed worker PID를 분리해서 기록했다.
- OOM은 RSS 증가와 MemoryGuard 자기 종료로 설명하면 된다.
- CPU는 앱 내부 `CpuWorker` 보호 기준 초과와 직후 PID 소멸로 설명하면 된다.
- Deadlock은 `Shared_Memory_A`와 `Socket_Pool_B`의 A to B, B to A 순환 대기로 설명하면 된다.
- `MULTI_THREAD_ENABLE=false`는 동시 lock 경쟁을 없애는 임시 회피책이다.

Problems / Uncertainty:
- 제공 zip에는 README와 `monitor.sh`가 없었다. 그래서 표준 `ps` 기반의 최소 `scripts/monitor.sh`를 작성했다.
- 시스템에 `unzip`과 `wget`은 없었다. 다운로드는 `curl`, 압축 해제는 `python3 -m zipfile`로 진행했다.
- 실제 압축 파일의 실행 파일명은 과제 문구의 `agent-leak-app`이 아니라 `agent-app-leak`이었다.
- CPU 로그에는 리터럴 `WATCHDOG` 또는 `SIGTERM` 문자열이 없었다. 관측된 보호 종료 메시지는 `[CRITICAL] [CpuWorker] CPU Threshold Violated!`였다.
- CPU 케이스는 실제 앱 동작상 `CPU_MAX_OCCUPY=100`에서 장애가 발생하고 `10`에서 완화되었다. 과제의 권장 예시와 방향이 달라 실제 관측값을 우선했다.
