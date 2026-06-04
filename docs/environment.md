# Environment Check

## Summary
- User: `c10hour0574`
- Root 여부: root가 아닌 일반 사용자
- Ubuntu 버전: Ubuntu 24.04.4 LTS
- Kernel: `Linux ubuntu-b12 6.17.8-orbstack-00308-g8f9c941121b1`
- CPU core: 6
- Memory: 15GiB total, 15GiB available
- Disk: `/` 기준 403G total, 401G available
- Port 15034: listening 프로세스 없음. 현재 비어 있음.
- GitHub CLI: 설치됨 (`gh version 2.45.0`)
- GitHub Auth: 인증됨 (`request10hour`, repo scope 포함)
- Required tools: `curl`, `timeout`, `ps`, `top`, `kill`, `grep`, `awk`, `sed`, `tee`, `date`, `ss` 사용 가능. `unzip`, `wget`은 `which` 결과에 없음.

## 판단
- 현재 사용자는 root가 아니므로 agent-leak-app을 일반 사용자 조건으로 실행할 수 있다.
- `AGENT_PORT=15034`는 1024보다 큰 포트이고 현재 사용 중인 프로세스가 없으므로 바인딩 가능하다고 판단된다.
- GitHub CLI가 설치되어 있고 인증도 되어 있어 push 단계 진행이 가능하다.
- `unzip`은 없지만 `curl`과 `python3`가 있으므로 zip 다운로드 및 압축 해제는 대체 방법으로 진행할 수 있다.
- 메모리와 디스크 여유가 충분해 OOM, CPU, Deadlock 재현 실험을 제한 시간 안에서 수행할 수 있다.

## Raw Command Outputs

```text
Collection timestamp: 2026-06-05T03:32:51+09:00
```

```text
$ whoami
c10hour0574
```

```text
$ id
uid=1267600506(c10hour0574) gid=1267600506(c10hour0574) groups=1267600506(c10hour0574),4(adm),27(sudo),44(video),50(staff),67278(orbstack)
```

```text
$ pwd
/home/c10hour0574
```

```text
$ uname -a
Linux ubuntu-b12 6.17.8-orbstack-00308-g8f9c941121b1 #1 SMP PREEMPT Thu Nov 20 09:34:02 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
```

```text
$ cat /etc/os-release
PRETTY_NAME="Ubuntu 24.04.4 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION="24.04.4 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=noble
LOGO=ubuntu-logo
```

```text
$ lsb_release -a 2>/dev/null || true
Distributor ID:	Ubuntu
Description:	Ubuntu 24.04.4 LTS
Release:	24.04
Codename:	noble
```

```text
$ arch
x86_64
```

```text
$ nproc
6
```

```text
$ free -h
               total        used        free      shared  buff/cache   available
Mem:            15Gi       595Mi        15Gi       1.0Mi       306Mi        15Gi
Swap:           16Gi          0B        16Gi
```

```text
$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/vdb1       403G  1.3G  401G   1% /
none            492K  4.0K  488K   1% /dev
orbstack        7.9G  520K  7.9G   1% /opt/orbstack-guest
tmpfs            13G     0   13G   0% /tmp
/dev/vdb1       403G  1.3G  401G   1% /opt/orbstack-guest/data
orbstack        7.9G  4.0K  7.9G   1% /opt/orbstack-guest/run
mac             466G   44G  423G  10% /mnt/mac
machines        7.9G  4.0K  7.9G   1% /mnt/machines
tmpfs           7.9G     0  7.9G   0% /dev/shm
tmpfs           3.2G  400K  3.2G   1% /run
tmpfs           5.0M     0  5.0M   0% /run/lock
tmpfs           1.6G  8.0K  1.6G   1% /run/user/1267600506
```

```text
$ ulimit -a
real-time non-blocking time  (microseconds, -R) unlimited
core file size              (blocks, -c) 0
data seg size               (kbytes, -d) unlimited
scheduling priority                 (-e) 0
file size                   (blocks, -f) unlimited
pending signals                     (-i) 64172
max locked memory           (kbytes, -l) unlimited
max memory size             (kbytes, -m) unlimited
open files                          (-n) 1048576
pipe size                (512 bytes, -p) 8
POSIX message queues         (bytes, -q) 819200
real-time priority                  (-r) 0
stack size                  (kbytes, -s) 8192
cpu time                   (seconds, -t) unlimited
max user processes                  (-u) 64172
virtual memory              (kbytes, -v) unlimited
file locks                          (-x) unlimited
```

```text
$ bash --version | head -n 1
GNU bash, version 5.2.21(1)-release (x86_64-pc-linux-gnu)
```

```text
$ git --version
git version 2.43.0
```

```text
$ gh --version 2>/dev/null || true
gh version 2.45.0 (2025-07-18 Ubuntu 2.45.0-1ubuntu0.3)
https://github.com/cli/cli/releases/tag/v2.45.0
```

```text
$ gh auth status 2>&1 || true
github.com
  ✓ Logged in to github.com account request10hour (/home/c10hour0574/.config/gh/hosts.yml)
  - Active account: true
  - Git operations protocol: https
  - Token: gho_************************************
  - Token scopes: 'gist', 'read:org', 'repo', 'workflow'
```

```text
$ python3 --version
Python 3.12.3
```

```text
$ ps --version 2>/dev/null || true
ps from procps-ng 4.0.4
```

```text
$ top -v 2>/dev/null || top -h 2>/dev/null | head || true

Usage:
 top [options]

Options:
 -b, --batch-mode                run in non-interactive batch mode
 -c, --cmdline-toggle            reverse last remembered 'c' state
 -d, --delay =SECS [.TENTHS]     iterative delay as SECS [.TENTHS]
 -E, --scale-summary-mem =SCALE  set mem as: k,m,g,t,p,e for SCALE
 -e, --scale-task-mem =SCALE     set mem with: k,m,g,t,p for SCALE
```

```text
$ which unzip curl wget timeout ps top kill grep awk sed tee date
/usr/bin/curl
/usr/bin/timeout
/usr/bin/ps
/usr/bin/top
/usr/bin/kill
/usr/bin/grep
/usr/bin/awk
/usr/bin/sed
/usr/bin/tee
/usr/bin/date
```

```text
$ which ss
/usr/bin/ss
```

```text
$ ss -ltnp 2>/dev/null | grep ':15034' || true
```

출력이 없다는 것은 수집 시점에 TCP 15034 포트를 점유한 listening 프로세스가 없었다는 뜻이다.
