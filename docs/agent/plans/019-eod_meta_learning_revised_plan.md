# Revised Plan: EOD Meta-Learning Loop + News Watcher

**Version:** 2.0 — Full Rewrite  
**Date:** 2026-03-27  
**Authors:** Senior Economist / PM / Lead Engineer (collaborative review)  
**Status:** Draft — pending team review  
**Supersedes:** Original PR #124 plan  
**Strategy:** Position trading, 1–3 month holding period, anomaly-driven entry

---

## Table of Contents

1. [Economist's Thesis — Why This Loop Exists](#1-economists-thesis)
2. [System Architecture — Two Subsystems](#2-system-architecture)
3. [Subsystem A — EOD Meta-Learning Loop (Revised)](#3-subsystem-a-eod-meta-learning-loop)
4. [Subsystem B — News Watcher (New, Design Only)](#4-subsystem-b-news-watcher)
5. [PR #124 Bug Fixes (Unchanged, Pre-Merge Blockers)](#5-pr-124-bug-fixes)
6. [PR #125 — Trend DNA + Dual Advice (Revised Scope)](#6-pr-125)
7. [PR #126 — PM Exit Loop (Revised Scope)](#7-pr-126)
8. [PR #127 — News Watcher v1 (New)](#8-pr-127)
9. [Future Improvements — Ranked Backlog](#9-future-improvements)
10. [PM Roadmap & Milestones](#10-pm-roadmap)
11. [Acceptance Criteria (Revised)](#11-acceptance-criteria)
12. [Risk Register](#12-risk-register)

---

## 1. Economist's Thesis — Why This Loop Exists {#1-economists-thesis}

### The Alpha Source

The TradingAgents pipeline generates alpha through a multi-agent debate
architecture: scanners identify candidates via top-down macro analysis,
then per-ticker deep dives produce BUY/SELL/HOLD decisions through
structured bull-bear debate + risk adjudication. This is a strong
information-processing engine — but it currently has **no memory of its
own past accuracy**.

A human portfolio manager at a macro hedge fund reviews their trade blotter
weekly: which positions worked, which didn't, and *why*. They develop
intuition — "every time we buy a semiconductor stock into a tightening
cycle based on a product-cycle catalyst, it works for 3 weeks then mean-
reverts" — and that intuition shapes future screening and exit timing.

The meta-learning loop is the system's equivalent of that blotter review.

### Why 1–3 Month Horizons Change Everything

The original plan used 30-day and 90-day reflection horizons, which are
reasonable starting points. But for a 1–3 month position-trading strategy,
the reflection math must be calibrated differently than for swing trading:

**Entry timing is less important than exit timing.** In a 5-day swing
trade, being 2 days early is catastrophic (40% of your holding period
wasted in drawdown). In a 60-day position trade, being 2 days early is
noise. What kills position traders is one of two things:

1. **Holding through a peak** — the stock reaches MFE on day 22, then
   gives back the gains by day 60. The lesson isn't "don't buy it" —
   it's "sell it on day 22."
2. **Cutting too early during a drawdown** — the stock drops 8% in
   week 2 (triggering stops), then rallies 25% by month 3.

Both failure modes require *temporal* data that the original plan
partially captures (MFE/MAE) but insufficiently characterizes. To
generate actionable advice, the reflector must know the *shape* of
the price curve, not just the extremes.

### The News Anomaly Thesis

Mid-term positions are vulnerable to regime-changing news events that
invalidate the original thesis. A stock bought for a product-cycle
catalyst doesn't care about sector rotation — until a regulatory action
or earnings disaster changes the fundamental story.

The scanner runs daily, but it looks at the *broad market*. It does not
monitor whether something unusual is happening *specifically to the
stocks already in the portfolio*. That's the gap the News Watcher fills.

The watcher is not a meta-learning component (it doesn't learn from the
past). It is a **real-time alerting system** that can trigger re-analysis.
After the PM acts on an alert, the *outcome* of that action feeds back
into the meta-learning loop — creating a closed cycle:

```
                    ┌─────────────────────────────────┐
                    │                                 │
        News Watcher ──alert──▶ Scanner/Pipeline ──▶ PM Action
                                                       │
                                                       ▼
                                              EOD Meta-Learning
                                              (reflect on outcomes)
                                                       │
                                                       ▼
                                              Lesson Store
                                                       │
                                  ┌────────────────────┴────────────────┐
                                  ▼                                     ▼
                          screening_advice                       exit_advice
                          (improves scanner                     (improves PM
                           candidate selection)                  sell decisions)
```

---

## 2. System Architecture — Two Subsystems {#2-system-architecture}

### Subsystem A: EOD Meta-Learning Loop (build now)

Runs end-of-day. Looks backward at scanner picks from 30/60/90 days ago.
Generates structured lessons (screening_advice + exit_advice) using actual
price outcomes. Lessons flow into two consumers:

- **candidate_prioritizer** — BM25 gate rejects candidates matching
  negative screening_advice patterns.
- **PM decision agent** — exit_advice injected into micro briefs for
  currently held tickers, informing sell/trim decisions.

### Subsystem B: News Watcher (design now, build next)

Runs on a schedule (configurable: every 4h during market hours, or
event-driven). Monitors portfolio holdings + high-conviction watchlist
for anomalous news patterns. When an anomaly is detected, it can trigger
a targeted scanner re-run or pipeline re-analysis for affected tickers.

**The watcher is NOT built in this plan.** This plan delivers the design
spec and interface contract so that the meta-learning loop is built
watcher-ready. The watcher itself ships in PR #127 or later.

---

## 3. Subsystem A — EOD Meta-Learning Loop (Revised) {#3-subsystem-a-eod-meta-learning-loop}

### 3.1 Revised Reflection Horizons

Original plan: `--horizons 30,90`

Revised for 1–3 month strategy: `--horizons 30,60,90`

Rationale: The 60-day mark is the *median* of the target holding period.
A stock that peaks at day 25 and mean-reverts by day 60 tells a different
story than one that's still climbing at day 60 but fades by day 90. The
three horizons create a temporal "film strip" of the position's lifecycle.

### 3.2 Revised Trend DNA Schema (Lesson Dict v2)

The original plan captured: `terminal_return_pct`, `mfe_pct`, `mae_pct`,
`spy_return_pct`, `alpha_pct`. The revised schema adds temporal and
contextual fields critical for position-trading lessons.

```python
lesson_v2 = {
    # --- Schema metadata ---
    "schema_version": 2,
    "ticker": "AAPL",
    "scan_date": "2026-01-15",      # when the scanner originally flagged this
    "reflect_date": "2026-03-15",   # when this reflection was generated
    "horizon_days": 60,             # which horizon produced this lesson

    # --- Price outcome (REVISED: High/Low, not Close) ---
    "entry_price": 185.20,                  # Close on scan_date
    "terminal_price": 198.50,               # Close on scan_date + horizon
    "terminal_return_pct": 7.18,            # (terminal - entry) / entry * 100
    "spy_return_pct": 3.20,                 # SPY return over same period
    "alpha_pct": 3.98,                      # terminal_return_pct - spy_return_pct

    # --- Excursion data (REVISED: from High/Low columns) ---
    "mfe_pct": 12.40,                       # (Highest_High - entry) / entry * 100
    "mae_pct": -5.10,                       # (Lowest_Low - entry) / entry * 100

    # --- NEW: Temporal dynamics ---
    "days_to_peak": 22,                     # trading days from entry to Highest_High
    "days_to_trough": 8,                    # trading days from entry to Lowest_Low
    "peak_before_trough": True,             # did peak come before trough? (shape indicator)
    "drawdown_recovery_days": 14,           # days from trough back to entry price (null if never recovered)

    # --- NEW: Sector-relative context ---
    "sector": "Technology",
    "sector_etf": "XLK",
    "sector_return_pct": 5.60,              # sector ETF return over same period
    "sector_alpha_pct": 1.58,               # terminal_return_pct - sector_return_pct

    # --- NEW: News context at entry (for watcher correlation) ---
    "entry_news_sentiment": 0.35,           # AV sentiment score at scan_date (if available)
    "entry_news_volume": 12,                # article count in 3-day window around scan_date

    # --- Scanner metadata (carried from original scan) ---
    "conviction": "high",
    "thesis_angle": "catalyst",
    "macro_regime": "TRANSITION",
    "original_rationale": "...",

    # --- LLM-generated advice (REVISED: dual output) ---
    "situation": "...",                     # narrative summary of what happened
    "screening_advice": "...",              # what to look for / avoid in future scans
    "exit_advice": "...",                   # when and how to exit similar positions
    "sentiment": "positive|negative|neutral",

    # --- NEW: Classification tags (for BM25 retrieval improvement) ---
    "outcome_class": "winner_held_too_long",  # see taxonomy below
    "lesson_tags": ["peak_before_trough", "sector_laggard", "catalyst_worked"]
}
```

### 3.3 Outcome Classification Taxonomy

The LLM generating lessons must classify each outcome into one of these
categories. This taxonomy directly maps to actionable portfolio decisions:

| Outcome Class | Definition | Lesson Focus |
|---|---|---|
| `strong_winner` | alpha > +10%, MFE captured (terminal ≥ 80% of MFE) | What made the screening correct; reinforce pattern |
| `winner_held_too_long` | MFE > +10% but terminal < 50% of MFE | Exit timing — when to sell; days_to_peak is the key datum |
| `slow_grind_winner` | alpha +2% to +10%, no sharp drawdown | Patience lesson — validate that holding through noise works |
| `whipsaw_survivor` | MAE < -8% but terminal positive | Drawdown tolerance — don't cut early; drawdown_recovery_days matters |
| `thesis_invalidated` | terminal < -5%, fundamental story changed | Screening failure — what signal was missed; news context matters |
| `sector_drag` | stock positive but sector_alpha negative | Stock was right, timing was wrong relative to sector rotation |
| `macro_casualty` | alpha negative, correlated with SPY drawdown | Not a stock-picking error — macro regime management lesson |
| `dead_money` | -2% < alpha < +2% over full horizon | Opportunity cost — capital was tied up for no return |

### 3.4 Revised Dual Advice Prompt Spec

The LLM prompt for `generate_lesson` must produce both advice fields
using the enriched data. This is the prompt structure (not the literal
prompt text — that goes in code):

**Input to the LLM:**

```
You are reviewing a stock that was flagged by a macro scanner {horizon_days}
days ago. Your job is to extract two types of lessons from the outcome.

STOCK: {ticker} ({sector})
SCAN DATE: {scan_date} | CONVICTION: {conviction} | THESIS: {thesis_angle}
MACRO REGIME AT ENTRY: {macro_regime}
ORIGINAL RATIONALE: {original_rationale}

PRICE OUTCOME ({horizon_days} trading days):
  Entry Price:        ${entry_price}
  Terminal Price:     ${terminal_price} ({terminal_return_pct:+.1f}%)
  SPY Return:         {spy_return_pct:+.1f}%
  Alpha:              {alpha_pct:+.1f}%
  Sector ({sector_etf}): {sector_return_pct:+.1f}%
  Sector Alpha:       {sector_alpha_pct:+.1f}%

EXCURSION PROFILE:
  Max Favorable (MFE):   {mfe_pct:+.1f}% (reached on Day {days_to_peak})
  Max Adverse (MAE):     {mae_pct:+.1f}% (reached on Day {days_to_trough})
  Peak before trough:    {peak_before_trough}
  Drawdown recovery:     {drawdown_recovery_days} days (null = never recovered)

NEWS CONTEXT AT ENTRY:
  Sentiment score:    {entry_news_sentiment}
  Article volume:     {entry_news_volume} articles (3-day window)

RECENT NEWS SUMMARY (around terminal date):
{terminal_news_summary}
```

**Required output (JSON):**

```json
{
  "situation": "A 2-3 sentence narrative of what happened...",
  "screening_advice": "What should the scanner look for or avoid when
    it encounters a similar setup in the future? Be specific about
    conviction level, thesis angle, macro regime, and sector context.",
  "exit_advice": "If a portfolio holds a stock with a similar profile,
    when should it sell or trim? Reference the MFE timing (Day {days_to_peak}),
    the drawdown pattern, and any news-driven inflection points.",
  "sentiment": "positive|negative|neutral",
  "outcome_class": "one of the 8 classes from the taxonomy"
}
```

### 3.5 Sector-Relative Performance (New Requirement)

The original plan calculates alpha against SPY only. For position trading,
sector-relative performance is equally important because:

- A stock that returns +5% when its sector returns +12% is a *laggard*,
  not a success. The scanner should have picked the sector ETF instead.
- A stock that returns +5% when its sector returns -3% is a genuine alpha
  generator. The screening was excellent.

**Implementation:** After fetching the stock's OHLCV data via yfinance,
also fetch the sector ETF's data for the same period. Sector ETF mapping:

```python
SECTOR_ETF_MAP = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financials": "XLF",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Real Estate": "XLRE",
    "Utilities": "XLU",
    "Communication Services": "XLC",
}
```

This is a single additional `yf.download()` call per reflection (sector
ETF data can be cached across tickers in the same sector).

### 3.6 `days_to_trough` and Price Curve Shape

The original plan calculated `days_to_peak` but not `days_to_trough`.
For position trading, the *sequence* of peak and trough determines the
lesson type:

**Peak before trough (`peak_before_trough = True`):**
Stock rallied, then gave back gains. The lesson is about *exit timing* —
"you should have sold on day {days_to_peak}."

**Trough before peak (`peak_before_trough = False`):**
Stock drew down first, then recovered and rallied. The lesson is about
*drawdown tolerance* — "don't cut the position during the first 2 weeks;
the thesis needs time to play out."

**Implementation:**
```python
peak_date = hist["High"][ticker].idxmax()
trough_date = hist["Low"][ticker].idxmin()
days_to_peak = np.busday_count(entry_date, peak_date)
days_to_trough = np.busday_count(entry_date, trough_date)
peak_before_trough = peak_date < trough_date

# Drawdown recovery: how many days from trough back to entry price?
post_trough = hist["Close"][ticker][trough_date:]
recovery_mask = post_trough >= entry_price
if recovery_mask.any():
    recovery_date = recovery_mask.idxmax()
    drawdown_recovery_days = np.busday_count(trough_date, recovery_date)
else:
    drawdown_recovery_days = None  # never recovered
```

### 3.7 News Context at Entry (Watcher-Ready)

To enable future correlation between news anomalies and position outcomes,
each lesson stores the news environment at entry time. This data is
already available via the existing `fetch_news_summary` function in
`selection_reflector.py`.

We add two lightweight fields:

- `entry_news_sentiment`: the average AV sentiment score from articles
  in a 3-day window around scan_date (already fetched by the reflector).
- `entry_news_volume`: the count of articles in that window.

These fields are not used by the meta-learning loop *now*. They become
critical when the News Watcher ships — the watcher can compare current
news volume/sentiment against historical baselines stored in lessons to
detect anomalies.

---

## 4. Subsystem B — News Watcher (Design Only) {#4-subsystem-b-news-watcher}

**Status:** Design spec. No code shipped in this plan. This section
defines the interface contract so the meta-learning loop is built
watcher-ready, and provides the blueprint for PR #127+.

### 4.1 Purpose

The News Watcher monitors **currently held tickers and high-conviction
watchlist items** for unusual news patterns that may invalidate the
original investment thesis or present an opportunity for early exit/
additional entry.

It is a **shorter decision tree** than a full scanner re-run — it does
not re-analyze macro themes, sector rotation, or fundamentals. It asks
one narrow question: *"Is something unusual happening with this specific
stock right now?"*

### 4.2 Anomaly Dimensions (Ranked by Implementation Priority)

Based on the strategy profile, here is the prioritized ranking. The first
two ship in v1; the remaining two are tracked as improvements.

**Tier 1 — Ship in v1 (PR #127):**

| # | Dimension | Signal | Data Source | Detection Logic |
|---|---|---|---|---|
| 1 | **Sentiment Divergence** | News sentiment strongly negative while price is flat/up, or vice versa | AV `NEWS_SENTIMENT` (per-article scores) | Compare rolling 3-day avg sentiment against price direction. Flag when sentiment < -0.3 but price up > 2%, or sentiment > +0.3 but price down > 2%. |
| 2 | **News Volume Spike** | Abnormally high article count for a ticker relative to its baseline | AV `NEWS_SENTIMENT` article count + Finnhub `/company-news` | Compute 30-day rolling avg article count. Flag when current 3-day count > 3× the rolling avg. |

**Tier 2 — Future improvements (post v1):**

| # | Dimension | Signal | Data Source | Notes |
|---|---|---|---|---|
| 3 | **Cross-Sector Contagion** | Negative event in one sector spreading to correlated sectors | Sector ETF correlation matrix + news overlap | Requires maintaining a sector correlation model. Flag when a sector ETF drops > 2σ and held stocks in correlated sectors haven't repriced yet. |
| 4 | **Insider/Institutional + News** | Insider selling coinciding with negative news | Finnhub `/stock/insider-transactions` + `/stock/insider-sentiment` (MSPR) + news | Combine MSPR (monthly share purchase ratio) with news sentiment. Flag when MSPR turns negative AND news sentiment drops simultaneously. |

### 4.3 Watcher Architecture (Target Design)

```
┌──────────────────────────────────────────────────────────────┐
│  News Watcher Process                                        │
│                                                              │
│  Inputs:                                                     │
│    • Portfolio holdings (from PortfolioRepository)            │
│    • High-conviction watchlist (from latest scan summary)    │
│    • Lesson store (historical baselines)                     │
│                                                              │
│  Schedule: Every 4h during market hours (configurable)       │
│            OR event-driven via CLI: `python -m cli.main watch`│
│                                                              │
│  For each monitored ticker:                                  │
│    1. Fetch recent news (AV + Finnhub)                       │
│    2. Fetch recent price data (yfinance)                     │
│    3. Compute anomaly scores per dimension                   │
│    4. If any dimension exceeds threshold → emit Alert        │
│                                                              │
│  Alert Actions (configurable):                               │
│    • LOG: Write to reports/daily/{date}/alerts/               │
│    • TRIGGER_PIPELINE: Re-run trading pipeline for ticker    │
│    • TRIGGER_SCAN: Re-run macro scanner (if cross-sector)    │
│    • NOTIFY: Console output / future: webhook/email          │
│                                                              │
│  Output:                                                     │
│    • AlertReport (JSON + MD) per triggered alert              │
│    • Dashboard event (if AgentOS is running)                  │
└──────────────────────────────────────────────────────────────┘
```

### 4.4 Watcher Interface Contract

These are the interfaces the meta-learning loop must be compatible with.
The watcher will produce `AlertReport` objects; the meta-learning loop
will eventually consume them to enrich lessons with "was there a news
anomaly during this holding period?"

```python
@dataclass
class NewsAnomaly:
    """A single detected anomaly for one ticker."""
    ticker: str
    dimension: str              # "sentiment_divergence" | "volume_spike" | ...
    severity: float             # 0.0 to 1.0 (normalized)
    description: str            # human-readable explanation
    detected_at: str            # ISO datetime
    data: dict                  # raw metrics (sentiment scores, article counts, etc.)

@dataclass
class AlertReport:
    """Watcher output for one monitoring cycle."""
    cycle_id: str               # unique ID for this watcher run
    timestamp: str              # ISO datetime
    monitored_tickers: list[str]
    anomalies: list[NewsAnomaly]
    recommended_actions: list[dict]  # [{"ticker": "AAPL", "action": "TRIGGER_PIPELINE", "reason": "..."}]
```

### 4.5 Watcher → Pipeline Integration Points

When the watcher detects an anomaly and triggers a re-analysis:

1. The pipeline re-run produces a new trading decision (BUY/HOLD/SELL).
2. If the PM acts on it (e.g., sells a position), that action is recorded
   in the trade ledger with `trigger="news_watcher"`.
3. At the next EOD reflection, the meta-learning loop sees this trade and
   its outcome. It generates a lesson that includes the news anomaly
   context — closing the feedback loop.

**What this means for the meta-learning loop now:** The lesson dict must
include a `trigger` field (default: `"scheduled_scan"`) so that future
watcher-triggered trades can be distinguished from routine scan picks
during reflection.

---

## 5. PR #124 Bug Fixes (Unchanged) {#5-pr-124-bug-fixes}

These are pre-merge blockers. Scope unchanged from the original plan.

### A1. Key name mismatch: `stock_return_pct` → `terminal_return_pct`
- File: `selection_reflector.py` (~line 230)
- Fix: Rename key in lesson dict
- Test: CLI `reflect` renders non-zero alpha column

### A2. `mfe_pct` / `mae_pct` not persisted
- File: `selection_reflector.py` (~lines 225–238)
- Fix: Add both fields to lesson dict
- Test: CLI renders non-zero MFE/MAE columns

### A3. Store-factory violation: direct `ReportStore()` instantiation
- File: `selection_reflector.py` (~line 30)
- Fix: Use `create_report_store()` from `store_factory`
- Severity: **P0** — silently uses wrong base directory when
  `PORTFOLIO_DATA_DIR` is configured. This is more severe than originally
  assessed.

### A4. Unused imports in `fetch_news_summary`
- File: `selection_reflector.py`
- Fix: Remove redundant `datetime` and unused `re` imports

---

## 6. PR #125 — Trend DNA + Dual Advice (Revised Scope) {#6-pr-125}

**Title:** `feat(reflector): position-trade Trend DNA, temporal dynamics, sector-relative alpha, dual advice`  
**Depends on:** PR #124 merged  
**Files touched:** `selection_reflector.py`, `memory_loader.py`, `lesson_store.py`  
**Estimated effort:** 5–7 days

### 6.1 Tasks

#### B1-R. Calculate `days_to_peak` AND `days_to_trough` (REVISED from original B1)

File: `selection_reflector.py` → `fetch_price_data`

- Compute `peak_date = hist["High"][ticker].idxmax()`
- Compute `trough_date = hist["Low"][ticker].idxmin()`
- Compute `days_to_peak` and `days_to_trough` using `np.busday_count`
- Compute `peak_before_trough = peak_date < trough_date`
- Compute `drawdown_recovery_days` (days from trough back to entry price;
  `None` if never recovered within the horizon)
- Return all four values as additional elements from `fetch_price_data`
- Store all four in the lesson dict

#### B2-R. Use High/Low for MFE/MAE (unchanged from original B2)

File: `selection_reflector.py` → `fetch_price_data`

- `mfe_pct = (hist["High"][ticker].max() - entry_price) / entry_price * 100`
- `mae_pct = (hist["Low"][ticker].min() - entry_price) / entry_price * 100`

#### B3-R. Inline `_safe_pct` with division-by-zero guard (REVISED from original B3)

File: `selection_reflector.py`

- Remove `from tradingagents.dataflows.peer_comparison import _safe_pct`
- Inline with guard:
  ```python
  def _pct_change(start: float, end: float) -> float:
      """Percentage change with division-by-zero safety."""
      if start == 0 or pd.isna(start) or pd.isna(end):
          return 0.0
      return (end - start) / abs(start) * 100
  ```

#### B4. NEW — Calculate sector-relative performance

File: `selection_reflector.py` → `fetch_price_data`

- Look up sector ETF from `SECTOR_ETF_MAP` (new module-level constant)
- Fetch sector ETF OHLCV data for the same date range (single
  `yf.download()` call; cache across tickers in same sector within
  one `reflect` run)
- Compute `sector_return_pct` and `sector_alpha_pct`
- Store both in lesson dict

#### B5. NEW — Capture news context at entry

File: `selection_reflector.py` → `reflect_on_scan`

- The existing `fetch_news_summary` already pulls news for the scan_date
  window. Extract from its output:
  - `entry_news_sentiment`: average sentiment score (AV) or `None`
  - `entry_news_volume`: article count
- Store both in lesson dict
- These fields are **passive** — not consumed by any current agent, but
  stored for future watcher correlation

#### C1-R. Split advice into `screening_advice` + `exit_advice` (REVISED prompt)

File: `selection_reflector.py` → `generate_lesson`

- Replace the single-advice LLM prompt with the dual-advice prompt from
  Section 3.4 of this plan
- Include all new temporal fields (`days_to_peak`, `days_to_trough`,
  `peak_before_trough`, `drawdown_recovery_days`) in the prompt
- Include sector-relative performance in the prompt
- Required output keys: `["situation", "screening_advice", "exit_advice",
  "sentiment", "outcome_class"]`
- The `outcome_class` must be one of the 8 classes from Section 3.3
- Store all fields in lesson dict
- Remove old `"advice"` key

#### C2-R. Update `memory_loader.py` (unchanged logic, new key)

File: `memory_loader.py`

- Change `l["advice"]` → `l["screening_advice"]`

#### E1-R. Schema versioning with warning log (REVISED)

File: `lesson_store.py`

- Add `schema_version: 2` to new lessons
- In `load_all`, handle v1 lessons:
  - Map `advice` → `screening_advice`, set `exit_advice` to `""`
  - Set missing temporal fields to `None`
  - Set `outcome_class` to `"unknown"`
  - **Log a warning** (not silent): `logger.warning("Migrating v1 lesson
    for %s — exit_advice and temporal fields will be empty", ticker)`
- Add `trigger` field (default: `"scheduled_scan"`) for watcher-readiness

### 6.2 Quality Validation Gate (NEW — between PR #125 and PR #126)

**This is the most important addition to the roadmap.**

Before PR #126 wires exit_advice into the PM's live decision-making, the
team must validate that the generated advice is actually useful.

**Validation protocol:**

1. Run `reflect --horizons 30,60,90` against at least 20 historical scan
   dates (covering a mix of bull, bear, and transition regimes)
2. Manually audit 15 generated lessons for:
   - **Specificity:** Does the advice reference concrete data (days, %,
     sector context), or is it generic ("be careful in volatile markets")?
   - **Actionability:** Could a PM reading this advice make a different
     decision? Or is it retrospective narration?
   - **Accuracy:** Does the outcome_class match the actual price curve?
3. Score each lesson: `actionable` (good) / `generic` (needs prompt
   tuning) / `wrong` (bug)
4. **Gate: ≥ 80% of audited lessons must score `actionable`.**
   If the gate fails, iterate on the prompt before proceeding to PR #126.

### 6.3 Tests

- Unit: `days_to_peak`, `days_to_trough`, `peak_before_trough` calculation
  with known OHLCV data
- Unit: `drawdown_recovery_days` — stock recovers vs. never recovers
- Unit: `_pct_change` division-by-zero guard
- Unit: Sector ETF lookup and sector_alpha calculation
- Unit: Schema v2 backward-compatible loading of v1 lessons (with warning
  log assertion)
- Unit: Dual advice prompt produces both required keys
- Unit: `outcome_class` is one of 8 valid values
- Integration: Full `reflect_on_scan` with mocked yfinance and LLM

### 6.4 PR Review Checklist

- [ ] `yf.download()` call includes High, Low, Open, Close, Volume columns
- [ ] `_pct_change` handles zero and NaN inputs
- [ ] Sector ETF cache is used (no duplicate downloads for same sector)
- [ ] `create_report_store()` is used (not `ReportStore()`)
- [ ] LLM prompt includes all temporal + sector fields
- [ ] Required key check includes `outcome_class`
- [ ] `trigger` field added with default `"scheduled_scan"`
- [ ] No import of `_safe_pct` from `peer_comparison`
- [ ] Logger warning on v1 → v2 migration

---

## 7. PR #126 — PM Exit Loop (Revised Scope) {#7-pr-126}

**Title:** `feat(portfolio): inject historical exit_advice into PM held-ticker briefs via pre-graph state`  
**Depends on:** PR #125 merged + quality validation gate passed  
**Files touched:** `portfolio_graph.py` or `portfolio_setup.py`, `micro_summary_agent.py`, `pm_decision_agent.py`, `portfolio_states.py`  
**Estimated effort:** 3–4 days

### 7.1 Architecture Decision: Pre-Graph State, Not In-Agent Query

**Problem:** The original plan (D1) had `micro_summary_agent.py` directly
importing and querying `LessonStore`. This couples a filesystem/JSON
dependency into an agent that is currently pure LLM + state.

**Decision:** Load exit lessons in a **pre-graph step** (similar to how
scanner results are loaded pre-graph in the pipeline). The lessons are
injected into the portfolio graph state as a new field. The micro summary
agent reads from state — keeping its dependency graph clean.

```python
# In portfolio_setup.py or portfolio_graph.py, before graph compilation:

def _load_exit_lessons_for_holdings(holdings: list[Holding]) -> str:
    """Load exit_advice from lesson store for currently held tickers.

    Returns a formatted string suitable for injection into the PM's
    micro brief, or empty string if no relevant lessons exist.
    """
    store = LessonStore()
    lessons = store.load_all()
    held_tickers = {h.ticker.upper() for h in holdings}

    relevant = []
    for lesson in lessons:
        if (lesson.get("ticker", "").upper() in held_tickers
                and lesson.get("exit_advice")
                and lesson.get("sentiment") != "positive"):
            relevant.append(lesson)

    if not relevant:
        return ""

    lines = ["## Historical Exit Lessons for Current Holdings\n"]
    for l in relevant:
        lines.append(
            f"**{l['ticker']}** ({l.get('outcome_class', 'unknown')}, "
            f"{l.get('horizon_days', '?')}d horizon): {l['exit_advice']}\n"
        )
    return "\n".join(lines)
```

### 7.2 State Field Addition

File: `portfolio_states.py`

```python
class PortfolioManagerState(MessagesState):
    # ... existing fields ...
    exit_lessons: Annotated[str, _last_value]  # NEW
```

### 7.3 Tasks

#### D1-R. Load exit lessons pre-graph (REVISED architecture)

File: `portfolio_setup.py` or `portfolio_graph.py`

- Before graph compilation, call `_load_exit_lessons_for_holdings`
- Inject result into initial state as `exit_lessons`
- Only include lessons where `sentiment != "positive"` (positive = no
  warning needed)
- Only include lessons where `outcome_class` indicates a problem:
  `winner_held_too_long`, `thesis_invalidated`, `sector_drag`,
  `macro_casualty`, `dead_money`

#### D2-R. Micro summary agent reads exit_lessons from state

File: `micro_summary_agent.py`

- At the end of micro brief generation, check if `state["exit_lessons"]`
  is non-empty
- If so, append it to the micro brief as a "Historical Memory" section
- No `LessonStore` import in this file

#### D3-R. Verify PM receives exit lessons in prompt

File: `pm_decision_agent.py`

- The micro brief content (with appended exit lessons) should already
  flow into the PM's prompt via the existing state → prompt path
- Verify this in an integration test
- No code changes expected here — just test confirmation

#### D4-R. Tests

- Unit: `_load_exit_lessons_for_holdings` returns correct lessons for
  held tickers
- Unit: Function returns empty string when no lessons match
- Unit: Function excludes positive-sentiment lessons
- Unit: `micro_summary_agent` appends exit_lessons section when present
- Unit: `micro_summary_agent` does NOT add section when exit_lessons is
  empty
- Integration: End-to-end from lesson store → state → micro brief → PM
  prompt (assert PM sees exit advice text)

### 7.4 PM Prompt Weight Consideration

**Risk:** The PM already receives a large prompt (~39 KB / ~9,750 tokens
with 2 debate rounds). Adding exit lessons increases this further. If too
many lessons match, the PM's context becomes overwhelmed.

**Mitigation:**
- Limit to **3 most relevant lessons per held ticker** (sorted by
  `reflect_date` descending — most recent lesson wins)
- Limit total exit_lessons section to **2,000 characters**
- If truncated, include a note: "Additional historical lessons available
  but omitted for brevity."

### 7.5 PR Review Checklist

- [ ] No `LessonStore` import in `micro_summary_agent.py`
- [ ] No `LessonStore` import in `pm_decision_agent.py`
- [ ] Exit lessons loaded pre-graph, injected into initial state
- [ ] Positive-sentiment lessons excluded
- [ ] Only problem `outcome_class` values included
- [ ] Max 3 lessons per ticker, 2,000 char total limit
- [ ] `exit_lessons` field added to `PortfolioManagerState`
- [ ] Integration test confirms PM agent sees exit advice in prompt

---

## 8. PR #127 — News Watcher v1 (New) {#8-pr-127}

**Title:** `feat(watcher): real-time news anomaly detection for portfolio holdings`  
**Depends on:** PR #126 merged (watcher uses same lesson store interface)  
**Files to create:** `tradingagents/watcher/`, `cli/main.py` (new `watch` command)  
**Estimated effort:** 7–10 days  
**Status:** Design only in this plan — build after meta-learning loop ships

### 8.1 Scope (v1 — Tier 1 Dimensions Only)

v1 ships with two anomaly detection dimensions:

1. **Sentiment Divergence:** News sentiment strongly disagrees with price
   action (bearish news + rising price, or bullish news + falling price).
2. **News Volume Spike:** Abnormally high article count relative to the
   ticker's historical baseline (3× the 30-day rolling average).

### 8.2 File Structure

```
tradingagents/
└── watcher/
    ├── __init__.py
    ├── news_watcher.py        # Main watcher loop + scheduling
    ├── anomaly_detector.py    # Dimension-specific detection logic
    ├── alert_store.py         # Persist + load AlertReports
    └── actions.py             # Alert action handlers (log, trigger_pipeline, etc.)
```

### 8.3 CLI Command

```bash
# One-shot: check all held tickers now
python -m cli.main watch --portfolio-id <id>

# Continuous: run every 4 hours during market hours
python -m cli.main watch --portfolio-id <id> --continuous --interval 4h

# Include watchlist (high-conviction candidates not yet bought)
python -m cli.main watch --portfolio-id <id> --include-watchlist
```

### 8.4 Data Source Budget

| Source | Calls per ticker | Rate limit | Notes |
|---|---|---|---|
| AV `NEWS_SENTIMENT` | 1 | 25/day (free) | Per-article sentiment scores. Primary source. |
| Finnhub `/company-news` | 1 | 60/min | Article count + headlines. Secondary/fallback. |
| yfinance (price) | 1 | Unrestricted | 5-day recent price for divergence check. |
| **Total per ticker** | 3 | — | For 10 held tickers: 30 calls per cycle |

### 8.5 Alert → Pipeline Trigger Flow

When `action = "TRIGGER_PIPELINE"`:

1. Watcher calls `MacroBridge.run()` for the affected ticker only
   (single-ticker mode, no full scan)
2. Pipeline produces a new BUY/HOLD/SELL decision
3. If decision differs from current position, the PM is alerted via the
   existing AgentOS WebSocket stream (or console output in CLI mode)
4. PM decision includes the alert context in its input state

### 8.6 Deferred Work (Not in v1)

- Cross-sector contagion detection (requires correlation model)
- Insider/institutional + news correlation (requires Finnhub paid tier
  for MSPR + social sentiment)
- Webhook/email notifications
- AgentOS dashboard integration (alert panel)

---

## 9. Future Improvements — Ranked Backlog {#9-future-improvements}

These items are logged for future work, in priority order:

| # | Improvement | Rationale | Depends On |
|---|---|---|---|
| 1 | **Cross-sector contagion detection** (Watcher Tier 2 dim. 3) | Sector ETF correlation matrix + news overlap. Catches "sector flu" before it hits held stocks. | PR #127 + sector correlation model |
| 2 | **Insider/institutional + news correlation** (Watcher Tier 2 dim. 4) | Combine Finnhub MSPR with news sentiment for insider-smart-money signal. | PR #127 + Finnhub paid tier |
| 3 | **Lesson quality auto-scoring** | Train a small classifier to predict lesson actionability (replacing manual audit gate). Run as CI check on new lessons. | PR #125 + 100+ manually audited lessons |
| 4 | **Multi-horizon lesson aggregation** | When the same ticker has 30d, 60d, and 90d lessons, synthesize them into a single "position lifecycle" narrative. | PR #125 stable |
| 5 | **Watcher → AgentOS dashboard** | Real-time alert panel in the React frontend. WebSocket event stream for alerts. | PR #127 + AgentOS frontend |
| 6 | **Portfolio-level meta-learning** | Reflect not just on individual stock picks but on portfolio construction decisions — "we were 40% Technology and the sector rotated." | PR #126 + portfolio snapshot history |
| 7 | **Regime-conditional advice retrieval** | BM25 retrieval in candidate_prioritizer should weight lessons from matching macro regimes higher than non-matching ones. | PR #125 + macro regime tagging in lessons |
| 8 | **Earnings calendar integration** | Finnhub `/calendar/earnings` as a watcher trigger — flag held stocks approaching earnings where the position thesis doesn't account for earnings risk. | PR #127 + Finnhub calendar endpoints |

---

## 10. PM Roadmap & Milestones {#10-pm-roadmap}

### Phase 1: Foundation (Weeks 1–2)

| Deliverable | PR | Est. Days | Gate |
|---|---|---|---|
| Bug fixes (A1–A4) | #124-fix | 1 | CI green, alpha column renders |
| Trend DNA + dual advice | #125 | 5–7 | Code review passed |
| **Quality validation** | (manual) | 2–3 | ≥ 80% lessons score "actionable" |

### Phase 2: Integration (Weeks 3–4)

| Deliverable | PR | Est. Days | Gate |
|---|---|---|---|
| Prompt iteration (if gate fails) | #125.1 | 2–3 | Re-audit passes gate |
| PM exit loop | #126 | 3–4 | Integration tests pass |
| **1-week paper trade comparison** | (manual) | 5 | PM decisions w/ exit memory are qualitatively better |

### Phase 3: Real-Time Layer (Weeks 5–7)

| Deliverable | PR | Est. Days | Gate |
|---|---|---|---|
| News Watcher v1 (sentiment + volume) | #127 | 7–10 | Alert accuracy > 70% on backtested news data |
| Watcher → pipeline trigger wiring | #127 | included | End-to-end test: alert triggers re-analysis |

### Total estimated timeline: 5–7 weeks

### Dependencies Map

```
PR #124 (fix) ──▶ PR #125 (Trend DNA) ──▶ [Quality Gate] ──▶ PR #126 (PM Exit Loop)
                                                                       │
                                                                       ▼
                                                              PR #127 (News Watcher)
```

---

## 11. Acceptance Criteria (Revised) {#11-acceptance-criteria}

| # | Criterion | Status | PRs Required |
|---|---|---|---|
| 1 | `reflect --horizons 30,60,90` pulls scanner logs and produces lessons with all v2 schema fields | ❌ | #124, #125 |
| 2 | MFE uses intraday High, MAE uses intraday Low (not Close) | ❌ | #125 |
| 3 | Each lesson includes `days_to_peak`, `days_to_trough`, `peak_before_trough`, `drawdown_recovery_days` | ❌ | #125 |
| 4 | Each lesson includes `sector_return_pct` and `sector_alpha_pct` | ❌ | #125 |
| 5 | `selection_lessons.json` populates with both `screening_advice` and `exit_advice` | ❌ | #125 |
| 6 | Each lesson has a valid `outcome_class` from the 8-class taxonomy | ❌ | #125 |
| 7 | ≥ 80% of audited lessons score "actionable" in manual review | ❌ | #125 + audit |
| 8 | `candidate_prioritizer` rejects a stock based on negative `screening_advice` | ⚠️ works but uses old key | #125 |
| 9 | PM agent sees `exit_advice` for held stocks in its prompt | ❌ | #126 |
| 10 | Exit lessons loaded pre-graph (no `LessonStore` in agent files) | ❌ | #126 |
| 11 | Schema migration handles v1 lessons with warning log | ❌ | #125 |
| 12 | Lesson dict includes `trigger` field (watcher-ready) | ❌ | #125 |
| 13 | News Watcher detects sentiment divergence anomaly for held tickers | ❌ | #127 |
| 14 | News Watcher detects volume spike anomaly | ❌ | #127 |
| 15 | Watcher alert triggers single-ticker pipeline re-run | ❌ | #127 |

---

## 12. Risk Register {#12-risk-register}

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **LLM generates generic, non-actionable advice** | Medium | High — garbage advice in PM prompt degrades decisions | Quality validation gate between PR #125 and #126. Iterate on prompt. Budget 2–3 extra days for prompt tuning. |
| **yfinance rate limiting during bulk reflection** | Low | Medium — reflection fails for some tickers | Implement per-ticker retry with exponential backoff. Cache sector ETF data across tickers. |
| **Exit lessons overwhelm PM context window** | Medium | Medium — PM ignores lessons or hallucinates from noise | Hard limits: max 3 lessons per ticker, 2,000 char total. Truncation note when exceeded. |
| **Outcome class misclassification by LLM** | Medium | Low-Medium — wrong lessons retrieved for wrong situations | Validate `outcome_class` against price data (e.g., if `terminal_return_pct` > +10% and `outcome_class` is `thesis_invalidated`, flag as error). Add a code-level sanity check. |
| **News Watcher false positives overwhelm PM** | Medium | Medium — alert fatigue degrades trust in watcher | Conservative thresholds in v1 (3× baseline for volume, ±0.3 for sentiment divergence). Tune based on backtest data. |
| **Sector ETF map incomplete** | Low | Low — some stocks get no sector-relative data | Fallback: use SPY if sector not in map. Log warning. |
| **Schema migration breaks existing lessons** | Low | High — loss of historical lesson data | v1 → v2 migration is additive (new fields default to None/empty). Never delete old fields, only add new ones. Backup `selection_lessons.json` before first v2 write. |
| **Watcher API budget exceeds free tier** | Medium | Medium — watcher fails silently | Budget analysis in Section 8.4 shows 30 calls per cycle for 10 tickers. AV free tier allows 25/day — may need Finnhub as primary for watcher. Flag in PR #127 design review. |

---

*End of revised plan. This document should be reviewed by the team and
updated as implementation progresses. Each PR should reference this plan
and update the acceptance criteria status upon merge.*
