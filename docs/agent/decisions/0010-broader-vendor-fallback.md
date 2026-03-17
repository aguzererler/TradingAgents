---
title: Broader Vendor Fallback Exception Handling
date: 2026-03-17
status: implemented
tags: [data, vendor, fallback, error-handling]
---

# ADR-0010: Broader Vendor Fallback Exception Handling

## Context

`route_to_vendor()` only caught `AlphaVantageError` for fallback. But network issues (`ConnectionError`, `TimeoutError`) from the `requests` library wouldn't trigger fallback — they'd crash the pipeline instead.

## Decision

Broadened the catch in `route_to_vendor()` to `(AlphaVantageError, ConnectionError, TimeoutError)`. Similarly, `_make_api_request()` now catches `requests.exceptions.RequestException` as a general fallback and wraps `raise_for_status()` in a try/except to convert HTTP errors to `ThirdPartyError`.

**Files**: `tradingagents/dataflows/interface.py`, `tradingagents/dataflows/alpha_vantage_common.py`

## Consequences & Constraints

- Any network-level exception now triggers vendor fallback instead of crashing.
- HTTP errors are wrapped in `ThirdPartyError` for consistent exception handling.
- The fallback chain tries all configured vendors before giving up.

## Actionable Rules

1. **Vendor fallback catch must include** `(AlphaVantageError, ConnectionError, TimeoutError)` at minimum. See Mistake #5.
2. **Wrap HTTP errors** via `raise_for_status()` in try/except and convert to domain-specific exceptions.
3. **Test fallback behavior** by simulating network failures, not just API errors. See `tests/test_scanner_fallback.py`.
