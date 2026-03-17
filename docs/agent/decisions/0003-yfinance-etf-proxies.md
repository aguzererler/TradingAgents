---
title: yfinance Sector Performance via ETF Proxies
date: 2026-03-17
status: implemented
tags: [data, yfinance, sectors, etf]
---

# ADR-0003: yfinance Sector Performance via ETF Proxies

## Context

`yfinance.Sector("technology").overview` returns only metadata (companies_count, market_cap, etc.) — no performance data (oneDay, oneWeek, etc.).

## Decision

Use SPDR sector ETFs as proxies:
```python
sector_etfs = {
    "Technology": "XLK", "Healthcare": "XLV", "Financials": "XLF",
    "Energy": "XLE", "Consumer Discretionary": "XLY", ...
}
```
Download 6 months of history via `yf.download()` and compute 1-day, 1-week, 1-month, YTD percentage changes from closing prices.

**File**: `tradingagents/dataflows/yfinance_scanner.py`

## Consequences & Constraints

- Performance data accuracy depends on ETF tracking fidelity (generally close but not exact).
- ETF proxy approach requires network access to download price history.
- The ETF ticker map must be kept in sync with SPDR fund availability.

## Actionable Rules

1. **Never use `yfinance.Sector.overview` for performance data.** It only returns metadata. See Mistake #2.
2. **Always test data source APIs interactively** before writing agent code. Run `python -c "import yfinance as yf; print(yf.Sector('technology').overview)"` to verify actual data shape.
3. **yfinance `top_companies` has ticker as INDEX, not a column.** Use `for symbol, row in top_companies.iterrows()`, not `row.get('symbol')`. See Mistake #3.
