# Plan: EOD Meta-Learning Loop — Remaining Work (post PR #124)

**Status**: pending
**Epic**: EOD Meta-Learning Loop (Trend DNA & Trade Management)
**Depends on**: PR #124 (macro scanner feedback loop — base implementation)
**Reference**: PR #124 review at aguzererler/TradingAgents#124

## Context

PR #124 delivers the skeleton of the EOD meta-learning loop: `selection_reflector.py`,
`lesson_store.py`, `memory_loader.py`, the BM25 gate in `candidate_prioritizer.py`, and
the `reflect` CLI command. However it has critical bugs and leaves several EPIC phases
incomplete. This plan tracks everything remaining.

---

## Part A — PR #124 Bug Fixes (pre-merge blockers)

These must be fixed in PR #124 itself before merging.

### A1. Key name mismatch: `stock_return_pct` → `terminal_return_pct`

**File:** `tradingagents/portfolio/selection_reflector.py` (line ~230)

`reflect_on_scan` stores `stock_return_pct`, but `cli/main.py::run_reflect` reads
`terminal_return_pct`. The Alpha column in the Rich table is always `+0.0%`.

- [ ] Rename `stock_return_pct` → `terminal_return_pct` in the lesson dict
- [ ] Update `alpha_pct` calculation comment for clarity

### A2. `mfe_pct` / `mae_pct` not persisted in lesson dict

**File:** `tradingagents/portfolio/selection_reflector.py` (line ~225–238)

The lesson dict omits `mfe_pct` and `mae_pct` even though `cli/main.py` reads them.
Both columns show `0.0%`.

- [ ] Add `"mfe_pct": round(mfe_pct, 2)` to the lesson dict
- [ ] Add `"mae_pct": round(mae_pct, 2)` to the lesson dict

### A3. Store-factory violation: direct `ReportStore()` instantiation

**File:** `tradingagents/portfolio/selection_reflector.py` (line ~30)

`load_scan_candidates` does `store = ReportStore()` instead of
`create_report_store()`. This bypasses `DualReportStore` and silently fails for
Mongo-backed deployments.

- [ ] Replace `from tradingagents.portfolio.report_store import ReportStore` with
      `from tradingagents.portfolio.store_factory import create_report_store`
- [ ] Replace `store = ReportStore()` with `store = create_report_store()`

### A4. Unused / redundant imports in `fetch_news_summary`

**File:** `tradingagents/portfolio/selection_reflector.py` (inside `fetch_news_summary`)

- [ ] Remove `from datetime import datetime` (already imported at module top)
- [ ] Remove `import re` (never used)

---

## Part B — EPIC Phase 1 Completions (Trend DNA math)

### B1. Calculate `days_to_peak`

**File:** `tradingagents/portfolio/selection_reflector.py` → `fetch_price_data`

The EPIC requires `days_to_peak`: the integer number of trading days from entry to
the date of `Highest_High`. Currently not calculated.

- [ ] After computing `peak_price`, find its date:
      `peak_date = stock_closes.idxmax()`
- [ ] Compute `days_to_peak = (peak_date - stock_closes.index[0]).days`
- [ ] Return `days_to_peak` as a 6th element from `fetch_price_data`
- [ ] Store `days_to_peak` in the lesson dict in `reflect_on_scan`

### B2. Use High/Low instead of Close for MFE/MAE

**File:** `tradingagents/portfolio/selection_reflector.py` → `fetch_price_data`

The EPIC specifies MFE = `(Highest_High - Start_Close) / Start_Close * 100` and
MAE = `(Lowest_Low - Start_Close) / Start_Close * 100`. PR #124 uses Close prices
for both, which understates both extremes.

- [ ] Change `yf.download()` to include `"High"` and `"Low"` columns
      (already available — `auto_adjust=True` gives OHLCV)
- [ ] `mfe_pct = (hist["High"][ticker].max() - entry_price) / entry_price * 100`
- [ ] `mae_pct = (hist["Low"][ticker].min() - entry_price) / entry_price * 100`

### B3. Stop importing private `_safe_pct`

**File:** `tradingagents/portfolio/selection_reflector.py`

`_safe_pct` is a private helper from `peer_comparison.py` with non-obvious
semantics. The reflector only needs a two-line calculation.

- [ ] Remove `from tradingagents.dataflows.peer_comparison import _safe_pct`
- [ ] Inline: `stock_pct = (stock_closes.iloc[-1] - stock_closes.iloc[0]) / stock_closes.iloc[0] * 100`
- [ ] Same pattern for `spy_pct`

---

## Part C — EPIC Phase 2 Completion (Dual Advice Prompt)

### C1. Split `advice` into `screening_advice` + `exit_advice`

**File:** `tradingagents/portfolio/selection_reflector.py` → `generate_lesson`

The EPIC requires two distinct outputs. PR #124 only asks the LLM for a single
`"advice"` key. The CLI already has separate columns for both, but they render empty.

- [ ] Update the LLM prompt to request `screening_advice` and `exit_advice`
      (see EPIC Phase 2 prompt spec)
- [ ] Include `days_to_peak` in the prompt: `"Optimal Sell Moment (MFE): {mfe_pct:+.1f}%
      (Reached on Day {days_to_peak})"`
- [ ] Update `generate_lesson` required-key check:
      `["situation", "screening_advice", "exit_advice", "sentiment"]`
- [ ] Update returned dict to include both advice fields
- [ ] Update `reflect_on_scan` lesson dict to store both fields
- [ ] Remove old `"advice"` key from lesson dict

### C2. Update `memory_loader.py` to use `screening_advice`

**File:** `tradingagents/portfolio/memory_loader.py`

Currently loads `(situation, advice)` pairs. Must change to `(situation, screening_advice)`.

- [ ] Update `load_into_memory` to reference `l["screening_advice"]` instead of `l["advice"]`

---

## Part D — EPIC Phase 4.2 (PM Exit Loop) — NEW

This is the major missing feature. The PM must receive historical `exit_advice` for
currently held tickers to inform sell decisions.

### D1. Query lesson store for held tickers in `micro_summary_agent`

**File:** `tradingagents/agents/portfolio/micro_summary_agent.py`

- [ ] At the start of micro brief generation, load `LessonStore` and find matches
      for each held ticker
- [ ] If a match exists with an `exit_advice`, inject it into the micro brief:
      `"Historical Memory: {exit_advice}"`
- [ ] Only inject lessons where `sentiment != "positive"` (positive lessons = no warning needed)

### D2. Pass exit advice through to PM decision prompt

**File:** `tradingagents/agents/portfolio/pm_decision_agent.py`

- [ ] Verify that the micro brief content (with injected exit advice) flows into
      the PM's prompt — it should already if micro_summary_agent writes to the brief
- [ ] Add a test confirming the PM sees exit advice for a held ticker

### D3. Tests for PM exit loop

- [ ] Unit test: `micro_summary_agent` injects exit advice when lesson exists
- [ ] Unit test: `micro_summary_agent` does NOT inject advice when no lesson matches
- [ ] Integration test: end-to-end from lesson store → micro brief → PM prompt

---

## Part E — Schema Migration & Backward Compatibility

### E1. Lesson store schema versioning

**File:** `tradingagents/portfolio/lesson_store.py`

Once the schema changes (adding `days_to_peak`, splitting `advice` →
`screening_advice` + `exit_advice`), existing `selection_lessons.json` files will
have the old schema.

- [ ] Add a `schema_version` field (default `2`) to new lessons
- [ ] In `load_all`, handle legacy lessons (no `screening_advice` key) by mapping
      `advice` → `screening_advice` and setting `exit_advice` to `""`
- [ ] Add test for backward-compatible loading of v1 lessons

---

## Acceptance Criteria (maps to EPIC Definition of Done)

1. **Execution:** `python -m cli.main reflect --horizons 30,90` pulls scanner logs
   from 30 and 90 days ago — ✅ already works in PR #124
2. **Trend Math:** Logs show accurate MFE (from High), MAE (from Low), and
   `days_to_peak` using a single `yfinance` request per stock — ❌ needs B1, B2
3. **JSON Output:** `selection_lessons.json` populates with both `screening_advice`
   and `exit_advice` — ❌ needs C1
4. **Prioritizer Defense:** `candidate_prioritizer` rejects a stock based on negative
   `screening_advice` — ⚠️ works but uses `advice` key; needs C1, C2
5. **PM Offense:** Portfolio graph attaches historical `exit_advice` to a held stock
   in the PM's input prompt — ❌ needs D1, D2, D3

---

## Suggested PR Sequence

| PR | Scope | Parts |
|----|-------|-------|
| PR #124 (fix) | Bug fixes only — merge-ready | A1, A2, A3, A4 |
| PR #125 | Trend DNA + dual advice | B1, B2, B3, C1, C2, E1 |
| PR #126 | PM exit loop integration | D1, D2, D3 |
