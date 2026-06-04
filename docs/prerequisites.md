# Prerequisites

## 1. 왜 사전 준비가 필요한가?

`agent-app-leak`는 실행 전에 몇 가지 환경 조건을 검사한다. 조건이 맞지 않으면 프로그램이 시작 과정에서 실패한다. 따라서 장애 분석을 하기 전에, 프로그램이 정상적으로 실행될 수 있는 최소 환경을 먼저 맞춰야 한다.

## 2. 준비 항목 요약

| 항목 | 설정값 | 쉬운 설명 |
| --- | --- | --- |
| 실행 계정 | root가 아닌 일반 사용자 | root는 시스템 전체 권한을 가진 관리자라서, 안전한 실험을 위해 일반 사용자로 실행했다. |
| `AGENT_HOME` | `./agent_home` | 앱이 사용할 작업 폴더다. |
| `AGENT_PORT` | `15034` | 앱이 네트워크 요청을 받을 포트 번호다. |
| `AGENT_UPLOAD_DIR` | `$AGENT_HOME/upload_files` | 업로드 파일을 저장할 폴더다. |
| `AGENT_KEY_PATH` | `$AGENT_HOME/api_keys` | 인증 키 파일이 들어가는 폴더다. |
| `AGENT_LOG_DIR` | `$AGENT_HOME/logs` | 앱 로그가 저장되는 폴더다. |
| `MEMORY_LIMIT` | `50~512 MB` | 앱이 허용하는 메모리 사용 상한이다. |
| `CPU_MAX_OCCUPY` | `10~100 %` | 앱이 허용하는 CPU 사용률 기준이다. |
| `MULTI_THREAD_ENABLE` | `true/false` | 여러 스레드를 동시에 사용할지 정하는 값이다. |
| `secret.key` | `agent_api_key_test` | 앱이 실행 전에 확인하는 인증 키 파일이다. |
| Port binding | `0.0.0.0:15034` 사용 가능 | 같은 포트를 다른 프로그램이 쓰고 있으면 앱이 시작할 수 없다. |

## 3. 이 repository에서는 어떻게 준비했는가?

`scripts/env_base.sh`가 공통 실행 환경을 준비한다.

- `AGENT_HOME` 경로를 설정한다.
- `upload_files`, `api_keys`, `logs` 디렉터리를 만든다.
- `secret.key` 파일을 만들고 `agent_api_key_test`를 쓴다.
- `AGENT_PORT`, `AGENT_UPLOAD_DIR`, `AGENT_KEY_PATH`, `AGENT_LOG_DIR`을 export한다.

과제 문서에서는 실행 대상을 `agent-leak-app`이라고 부르지만, 실제 압축 해제 후 확인된 실행 파일명은 `agent-app-leak`였다. 리포트에서는 실제 관측된 파일명을 우선 사용했다.

## 4. 발표 때 설명할 핵심 문장

- “이 단계는 장애를 고치는 단계가 아니라, 앱이 실행될 수 있는 기본 조건을 맞추는 단계입니다.”
- “환경변수는 프로그램 밖에서 동작 조건을 바꾸는 설정값입니다.”
- “`MEMORY_LIMIT`, `CPU_MAX_OCCUPY`, `MULTI_THREAD_ENABLE`은 이번 과제에서 Before & After 비교에 사용한 핵심 조절값입니다.”

## 5. 준비 상태 확인에 사용한 명령어

| 확인 대상 | 사용 명령어 | 확인 의미 |
| --- | --- | --- |
| 현재 사용자 | `whoami`, `id` | root가 아닌 일반 사용자로 실행 중인지 확인한다. |
| 작업 디렉터리 | `pwd` | repo와 `AGENT_HOME` 기준 경로를 확인한다. |
| 필수 폴더 | `test -d "$AGENT_UPLOAD_DIR"` 등 | 앱이 요구하는 업로드/키/로그 디렉터리가 있는지 확인한다. |
| `secret.key` | `cat "$AGENT_KEY_PATH/secret.key"` | 인증 키 내용이 `agent_api_key_test`인지 확인한다. |
| 포트 15034 | <code>ss -ltnp &#124; grep ':15034'</code> | 같은 포트를 이미 쓰는 프로세스가 있는지 확인한다. |
| 메모리/디스크 | `free -h`, `df -h` | 실험을 수행할 여유 자원이 있는지 확인한다. |
