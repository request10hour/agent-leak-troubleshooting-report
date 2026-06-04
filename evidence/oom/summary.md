# OOM Evidence Summary

- Before: `MEMORY_LIMIT=128`, `CPU_MAX_OCCUPY=100`, `MULTI_THREAD_ENABLE=false`
- Before PID: launcher `9049`, observed worker `9053`
- Before duration: 19 seconds
- Before result: `Memory limit exceeded (150MB >= 128MB)`, `Self-terminating process 9053`
- After: `MEMORY_LIMIT=256`, `CPU_MAX_OCCUPY=100`, `MULTI_THREAD_ENABLE=false`
- After PID: launcher `9353`, observed worker `9357`
- After duration: 42 seconds
- After result: `Memory limit exceeded (275MB >= 256MB)`, `Self-terminating process 9357`

Key monitor evidence:

```text
before RSS: 21620KB -> 149640KB, then process_missing
after RSS: 21580KB -> 277620KB, then process_missing
```

The `MEMORY_LIMIT=256` run survived longer than the `MEMORY_LIMIT=128` run while showing the same increasing memory pattern.
