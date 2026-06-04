# CPU Evidence Summary

- Before: `MEMORY_LIMIT=512`, `CPU_MAX_OCCUPY=100`, `MULTI_THREAD_ENABLE=false`
- Before PID: launcher `10484`, observed worker `10488`
- Before duration: 43 seconds
- Before result: `CpuWorker` load increased to `57.45%`, then `CPU Threshold Violated!`
- `top -b -d 0.2` captured a maximum sampled OS `%CPU` of `25.0` for PID `10488`.
- After: `MEMORY_LIMIT=512`, `CPU_MAX_OCCUPY=10`, `MULTI_THREAD_ENABLE=false`
- After PID: launcher `10133`, observed worker `10137`
- After observation: 67 seconds
- After result: process was still alive, and the log repeated `Peak reached (10.00%). Starting cooldown...`

Important note:

```text
The app did not print literal WATCHDOG or SIGTERM strings in this run.
The observed protection message was:
2026-06-05 03:46:25,904 [CRITICAL] [CpuWorker] CPU Threshold Violated! (57.45%).
```

The actual app behavior was safer when `CPU_MAX_OCCUPY` was lowered to `10`.
