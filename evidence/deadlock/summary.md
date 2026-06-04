# Deadlock Evidence Summary

- Before: `MEMORY_LIMIT=512`, `CPU_MAX_OCCUPY=10`, `MULTI_THREAD_ENABLE=true`
- Before PID: launcher `10960`, observed worker `10964`
- Before observation: 56 seconds
- Before result: process remained alive, but app log stopped growing.
- Log size at t1: `2693` bytes
- Log size at t2: `2693` bytes
- Last log at both checks:

```text
2026-06-05 03:48:24,750 [INFO] [AgentWorker][Worker-Thread-1] WAITING for [Socket_Pool_B]... (Status: BLOCKED)
```

- After: `MEMORY_LIMIT=512`, `CPU_MAX_OCCUPY=10`, `MULTI_THREAD_ENABLE=false`
- After PID: launcher `11158`, observed worker `11162`
- After observation: 56 seconds
- After result: process remained alive and app log continued growing.
- After log size changed from `3538` bytes to `5662` bytes.

The before logs show Worker-Thread-1 holding `Shared_Memory_A` and waiting for `Socket_Pool_B`, while Worker-Thread-2 holds `Socket_Pool_B` and waits for `Shared_Memory_A`.
