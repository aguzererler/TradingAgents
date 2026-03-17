---
title: Thread-Safe Rate Limiter for Alpha Vantage
date: 2026-03-17
status: implemented
tags: [rate-limiting, alpha-vantage, threading, concurrency]
---

# ADR-0009: Thread-Safe Rate Limiter for Alpha Vantage

## Context

The Alpha Vantage rate limiter in `alpha_vantage_common.py` initially slept *inside* the lock when re-checking the rate window. This blocked all other threads from making API requests during the sleep period, effectively serializing all AV calls.

## Decision

Two-phase rate limiting:
1. **First check**: Acquire lock, check timestamps, release lock, sleep if needed.
2. **Re-check loop**: Acquire lock, re-check timestamps. If still over limit, release lock *before* sleeping, then retry. Only append timestamp and break when under the limit.

This ensures the lock is never held during `sleep()` calls.

**File**: `tradingagents/dataflows/alpha_vantage_common.py`

## Consequences & Constraints

- The rate limiter uses a `while True` loop with lock release before sleep.
- Multiple threads can proceed concurrently when under the rate limit.
- Sleep timing is approximate due to lock contention, but includes a 0.1s buffer.

## Actionable Rules

1. **Never hold a lock during `sleep()` or IO.** Release the lock, perform the blocking operation, then re-acquire. See Mistake #10.
2. **Rate limiter pattern**:
   ```python
   while True:
       with _rate_lock:
           if len(_call_timestamps) < _RATE_LIMIT:
               _call_timestamps.append(_time.time())
               break
           extra_sleep = 60 - (now - _call_timestamps[0]) + 0.1
       _time.sleep(extra_sleep)  # ← outside lock
   ```
