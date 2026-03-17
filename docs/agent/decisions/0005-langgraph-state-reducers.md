---
title: LangGraph State Reducers for Parallel Fan-Out
date: 2026-03-17
status: implemented
tags: [langgraph, state, parallel, reducers]
---

# ADR-0005: LangGraph State Reducers for Parallel Fan-Out

## Context

Phase 1 runs 3 scanners in parallel. All write to shared state fields (`sender`, etc.). LangGraph requires reducers for concurrent writes — otherwise raises `INVALID_CONCURRENT_GRAPH_UPDATE`.

## Decision

Added `_last_value` reducer to all `ScannerState` fields via `Annotated[str, _last_value]`.

**File**: `tradingagents/agents/utils/scanner_states.py`

## Consequences & Constraints

- All `ScannerState` fields use the `_last_value` reducer, meaning the last write wins for concurrent updates.
- This is acceptable because parallel scanners write to *different* fields (e.g., `geopolitical_report`, `market_movers_report`).
- The `sender` field uses `_last_value` — its value after Phase 1 is non-deterministic but irrelevant after fan-in.

## Actionable Rules

1. **Any LangGraph state field written by parallel nodes MUST have a reducer.** Use `Annotated[type, reducer_fn]`. See Mistake #7.
2. **Use `_last_value` reducer** for fields where only the latest write matters.
3. **If a field needs to aggregate parallel writes** (e.g., collecting all reports into a list), use a list-append reducer instead.
