---
title: Data Vendor Fallback Strategy
date: 2026-03-17
status: implemented
tags: [data, vendor, fallback, alpha-vantage, yfinance]
---

# ADR-0002: Data Vendor Fallback Strategy

## Context

Alpha Vantage free/demo key doesn't support ETF symbols and has strict rate limits. A reliable data source is needed for the scanner pipeline.

## Decision

- `route_to_vendor()` catches `AlphaVantageError` (base class) to trigger fallback, not just `RateLimitError`.
- AV scanner functions raise `AlphaVantageError` when ALL queries fail (not silently embedding errors in output strings).
- yfinance is the fallback vendor and uses SPDR ETF proxies for sector performance instead of broken `Sector.overview`.

**Files**: `tradingagents/dataflows/interface.py`, `tradingagents/dataflows/alpha_vantage_scanner.py`, `tradingagents/dataflows/yfinance_scanner.py`

## Consequences & Constraints

- Vendor fallback chain is built dynamically: primary vendor first, then all others.
- AV functions inside `route_to_vendor` must raise on total failure — embedding errors in return values defeats the fallback mechanism.
- Broader exception catch `(AlphaVantageError, ConnectionError, TimeoutError)` ensures network issues also trigger fallback.

## Actionable Rules

1. **Functions inside `route_to_vendor` MUST raise exceptions on total failure.** Never embed error strings in return values — this silently prevents fallback. See Mistake #6.
2. **Fallback catch must be broad.** Use `(AlphaVantageError, ConnectionError, TimeoutError)`, not just `RateLimitError`. See Decision 0010 and Mistake #5.
3. **yfinance is the primary vendor** (free, no API key). Alpha Vantage is the fallback for market movers only.
