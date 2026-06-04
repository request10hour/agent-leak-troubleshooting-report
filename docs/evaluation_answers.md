# Evaluation Answers

## 1. monitor.sh로 메모리 증가 패턴을 추적한 방법

사용 명령:

```bash
scripts/monitor.sh PID evidence/oom/before_monitor.log 1 90
```

`monitor.sh`는 1초마다 `ps -p PID`를 실행해서 `pcpu`, `pmem`, `rss_kb`, `vsz_kb`, `etime`을 저장했다. OOM에서는 `rss_kb`가 `21620KB -> 149640KB`처럼 증가하는지 확인했다.

## 2. CPU 사용률 확인 도구와 옵션

`top -p PID`는 특정 프로세스 하나의 CPU/MEM 변화를 본다.

`top -H -p PID`는 프로세스 안의 스레드별 CPU 상태를 본다. Deadlock에서 스레드가 살아 있지만 거의 일하지 않는지 확인할 때 썼다.

`ps -p PID -o pid,ppid,stat,pcpu,pmem,etime,cmd`는 프로세스 상태, CPU, 메모리, 실행 시간을 한 줄로 저장한다.

`ps -L -p PID -o pid,tid,stat,pcpu,pmem,etime,comm`는 프로세스의 스레드 목록을 확인한다.

CPU 케이스에서는 추가로 짧은 spike를 잡기 위해 다음 명령을 썼다.

```bash
top -b -d 0.2 -n 220 -p 10488
```

## 3. 살아있지만 멈춘 프로세스를 진단한 순서

1. `ps -ef | grep agent-app-leak`로 PID가 살아 있는지 확인했다.
2. `wc -c app.log`와 `tail -n 1 app.log`로 로그 크기와 마지막 줄이 그대로인지 확인했다.
3. `monitor.sh`로 CPU/MEM이 거의 변하지 않는지 봤다.
4. `ps -L -p PID`와 `top -H -p PID`로 스레드 상태를 확인했다.
5. 마지막 로그의 `WAITING`, `BLOCKED`, lock 메시지로 데드락을 추론했다.

## 4. 메모리 누수 시 MemoryGuard가 종료하는 이유

메모리 사용량이 계속 증가하면 OS 전체 메모리를 압박한다. 앱은 OS OOM Killer가 개입하기 전에 `MemoryGuard`로 제한을 확인하고, 제한을 넘으면 자기 자신을 종료했다.

## 5. CPU 과점유 시 단일 프로세스를 종료하는 이유

CPU를 한 프로세스가 오래 점유하면 다른 작업의 응답성이 떨어진다. 이 앱은 `CpuWorker` load가 보호 기준을 넘으면 `CPU Threshold Violated!`를 남기고 프로세스를 종료했다.

## 6. Deadlock 원리

Deadlock은 서로 필요한 자원을 잡고 놓지 않을 때 생긴다. 이번 로그에서는 두 스레드가 각각 하나의 lock을 가진 상태에서 상대방 lock을 기다렸다. 그래서 더 이상 진행되지 않았다.

## 7. A to B, B to A 순환 의존 파악

로그에서 Worker-Thread-1은 `Shared_Memory_A`를 잡고 `Socket_Pool_B`를 기다렸다. Worker-Thread-2는 `Socket_Pool_B`를 잡고 `Shared_Memory_A`를 기다렸다. 이것이 A to B, B to A 순환 대기다.

## 8. 운영 서버라면 monitor.sh 개선점

운영에서는 CSV 형식으로 저장하고, PID뿐 아니라 자식 프로세스도 자동 추적하게 만들 것이다. 일정 기준을 넘으면 알림을 보내고, 로그 마지막 갱신 시간도 함께 기록하면 좋다.

## 9. 가장 치명적인 장애

Deadlock이 가장 치명적이라고 본다. OOM과 CPU Spike는 보호 로직으로 종료되어 눈에 띄지만, Deadlock은 프로세스가 살아 있어서 장애를 늦게 발견할 수 있다.

## 10. OOM과 Deadlock이 동시에 발생하면 순서

먼저 PID와 로그 갱신 여부를 본다. 로그가 멈췄고 CPU/MEM도 정체되면 Deadlock을 먼저 의심한다. 로그가 계속 나오고 RSS가 증가하면 OOM을 먼저 본다.

## 11. 소스 수정이 가능하다면 개선안

OOM은 누수 객체를 해제하고 캐시 크기를 제한한다.

CPU Spike는 무한 루프를 제거하고 sleep 또는 backoff를 넣는다.

Deadlock은 lock 획득 순서를 통일하고 timeout lock 또는 try-lock을 사용한다.

## 12. 다시 수행한다면 다르게 할 점

처음부터 런처 PID와 자식 PID를 분리해서 관제하겠다. 실제 리소스를 쓰는 PID가 자식 프로세스였기 때문에, 이 점을 먼저 확인하면 더 빠르게 증거를 모을 수 있다.
