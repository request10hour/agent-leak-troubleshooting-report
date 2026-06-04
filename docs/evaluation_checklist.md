# Evaluation Checklist

| 문항 | 평가 기준 | 충족 여부 | 핵심 근거 | 근거 파일 |
| --- | --- | --- | --- | --- |
| 문항 1 | OOM 메모리 증가 후 종료 | 충족 | RSS `21620KB -> 149640KB`, `process_missing`, `Memory limit exceeded` | `docs/issues/01_oom.md`, `evidence/oom/before_monitor.log` |
| 문항 1 | OOM MEMORY_LIMIT Before & After | 충족 | `128MB -> 256MB`, 생존 시간 `19s -> 42s` | `docs/issues/01_oom.md` |
| 문항 1 | CPU 임계치 초과 후 종료 | 충족 | `CpuWorker` load `57.45%`, `CPU Threshold Violated!`, `process_missing` | `docs/issues/02_cpu.md`, `evidence/cpu/before_app.log` |
| 문항 1 | CPU_MAX_OCCUPY Before & After | 충족 | `100% -> 10%`, Before `43s` 종료, After `67s` 생존 | `docs/issues/02_cpu.md` |
| 문항 1 | Deadlock PID 생존 + 로그 정지 | 충족 | PID `10964` 생존, 로그 크기 `2693 -> 2693 bytes` | `docs/issues/03_deadlock.md`, `evidence/deadlock/before_ps.txt` |
| 문항 1 | MULTI_THREAD_ENABLE Before & After | 충족 | `true -> false`, false에서 로그 크기 `3538 -> 5662 bytes` | `docs/issues/03_deadlock.md` |
| 문항 1 | GitHub Issue 구조 | 충족 | Description, Evidence, Root Cause, Workaround 구조 유지 | `docs/issues/01_oom.md`, `docs/issues/02_cpu.md`, `docs/issues/03_deadlock.md` |
| 문항 1 | PID/타임스탬프/핵심 로그 증거 | 충족 | PID, ISO timestamp, critical log, screenshot 포함 | `docs/issues/*.md`, `evidence/screenshots/*.png` |
| 문항 2 | monitor.sh 설명 | 충족 | `ps -p PID`로 `pcpu`, `pmem`, `rss_kb`, `etime` 수집 설명 | `docs/evaluation_answers.md` |
| 문항 2 | CPU 도구와 옵션 설명 | 충족 | `top -p`, `top -H -p`, `ps -p`, `ps -L -p` 옵션 의미 설명 | `docs/evaluation_answers.md` |
| 문항 2 | 살아있지만 멈춘 프로세스 진단 순서 | 충족 | PID 확인, 로그 갱신 중단, CPU/MEM 정체, 스레드 상태, 마지막 로그 순서 | `docs/evaluation_answers.md` |
| 문항 3 | MemoryGuard 설명 | 충족 | 메모리 증가가 OS 전체를 압박하기 전에 앱이 자기 종료한다고 설명 | `docs/evaluation_answers.md`, `docs/issues/01_oom.md` |
| 문항 3 | CPU 과점유 보호 설명 | 충족 | CPU 과점유가 시스템 응답성을 낮추므로 보호 종료한다고 설명 | `docs/evaluation_answers.md`, `docs/issues/02_cpu.md` |
| 문항 3 | Deadlock 상호 배제/순환 대기 설명 | 충족 | `Shared_Memory_A`와 `Socket_Pool_B`의 A→B, B→A 대기 설명 | `docs/issues/03_deadlock.md`, `docs/evaluation_answers.md` |
| 문항 3 | A→B, B→A 순환 의존 추적 | 충족 | Thread-1은 A 보유 후 B 대기, Thread-2는 B 보유 후 A 대기 | `docs/issues/03_deadlock.md`, `docs/evaluation_answers.md` |
| 문항 4 | monitor.sh 개선안 | 충족 | CSV 저장, 자식 PID 추적, 알림, 로그 갱신 시간 기록 제안 | `docs/evaluation_answers.md` |
| 문항 4 | 가장 치명적인 장애와 이유 | 충족 | Deadlock은 프로세스가 살아 있어 장애 발견이 늦을 수 있다고 설명 | `docs/evaluation_answers.md` |
| 문항 4 | OOM + Deadlock 동시 발생 시 순서 | 충족 | PID와 로그 갱신 여부를 먼저 보고 Deadlock/OOM 방향을 분리 | `docs/evaluation_answers.md` |
| 문항 4 | 장애별 코드 레벨 개선안 | 충족 | OOM 캐시/객체 정리, CPU backoff, Deadlock lock 순서/timeout 제안 | `docs/evaluation_answers.md` |
| 문항 4 | 다시 수행한다면 바꿀 점 | 충족 | 런처 PID와 실제 worker PID를 처음부터 분리해 관제한다고 설명 | `docs/evaluation_answers.md` |

## Review Notes

- 기존 로그 기준으로 OOM, CPU Spike, Deadlock 3개 리포트는 과제의 GitHub Issue 형식을 따른다.
- 스크린샷과 그래프는 보조 자료이며, 원본 판단 근거는 `evidence/` 아래의 로그 파일과 각 issue report의 로그 발췌다.
- 새 실험은 수행하지 않았고, 기존 PID, 타임스탬프, 수치, Before & After 결과는 변경하지 않았다.
