# agent-leak-troubleshooting

## Goal

이 저장소는 agent-leak-app의 OOM, CPU Spike, Deadlock 현상을 재현하고, Linux 표준 도구로 수집한 증거를 GitHub Issue 형식으로 정리한 과제 제출물이다.

## Repository Structure

```text
agent-leak-troubleshooting/
├── README.md
├── docs/
│   ├── environment.md
│   ├── final_report.md
│   ├── evaluation_answers.md
│   └── issues/
│       ├── 01_oom.md
│       ├── 02_cpu.md
│       └── 03_deadlock.md
├── evidence/
│   ├── oom/
│   ├── cpu/
│   ├── deadlock/
│   ├── screenshots/
│   └── graphs/
└── scripts/
```

- `docs/`: 환경 점검, 이슈 리포트, 발표용 답변, 최종 보고서
- `evidence/`: 실행 로그, monitor 로그, `ps/top` 출력
- `scripts/`: 실행 환경 설정과 최소한의 수집 도구

## Environment

- [Environment Check](docs/environment.md)

## Prerequisites

- [Prerequisites](docs/prerequisites.md)

## Reports

- OOM Report: [docs/issues/01_oom.md](docs/issues/01_oom.md)
- CPU Report: [docs/issues/02_cpu.md](docs/issues/02_cpu.md)
- Deadlock Report: [docs/issues/03_deadlock.md](docs/issues/03_deadlock.md)
- Evaluation Answers: [docs/evaluation_answers.md](docs/evaluation_answers.md)

## Visual Evidence

- Terminal screenshots: `evidence/screenshots/`
- Graphs: `evidence/graphs/`

## Evidence

- `evidence/oom/`: `MEMORY_LIMIT` 변경 전후 로그와 monitor 결과
- `evidence/cpu/`: `CPU_MAX_OCCUPY` 변경 전후 로그와 top/ps 결과
- `evidence/deadlock/`: `MULTI_THREAD_ENABLE` 변경 전후 PID, thread, top-H 결과
- `evidence/screenshots/`: 실제 터미널 창에서 명령어와 출력이 보이도록 캡처한 이미지
- `evidence/graphs/`: OOM RSS 증가와 CPU load 변화를 시각화한 그래프

## Reproduction Summary

| Case | MEMORY_LIMIT | CPU_MAX_OCCUPY | MULTI_THREAD_ENABLE | Result |
| --- | ---: | ---: | --- | --- |
| OOM Before | 128 | 100 | false | 19초 후 MemoryGuard 종료 |
| OOM After | 256 | 100 | false | 42초 후 MemoryGuard 종료 |
| CPU Before | 512 | 100 | false | 43초 후 CPU threshold 종료 |
| CPU After | 512 | 10 | false | 67초 관찰 후 생존 |
| Deadlock Before | 512 | 10 | true | PID 생존, 로그 정지 |
| Deadlock After | 512 | 10 | false | PID 생존, 로그 계속 증가 |

## Notes

- 바이너리 리버스 엔지니어링은 하지 않음.
- 제공 zip에는 `monitor.sh`와 README가 없어서 `scripts/monitor.sh`를 최소 Bash 스크립트로 작성함.
- 환경변수 조정은 임시 조치임.
- 실제 근본 해결은 코드 수정이 필요함.
- `secret.key`, zip 파일, 실행 바이너리는 커밋 대상에서 제외함.
