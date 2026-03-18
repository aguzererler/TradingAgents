# Architecture Overview

## System Description

TradingAgents is a multi-agent LLM framework for financial analysis and trading decisions,
built on LangGraph. It simulates a real trading firm with specialized analyst, researcher,
trader, and risk management agents that collaborate through structured workflows.

## Core Patterns

### Agent Factory Pattern

All agents use `create_X(llm)` → closure pattern. The factory accepts an LLM instance
and returns a callable node function compatible with LangGraph.

- Trading agents: `tradingagents/agents/analysts/*.py`, `tradingagents/agents/managers/*.py`
- Scanner agents: `tradingagents/agents/scanners/*.py`

### 3-Tier LLM System

| Tier | Purpose | Config Key | Default Model |
|------|---------|-----------|---------------|
| `quick_think` | Fast responses (scanners, simple analysis) | `quick_think_llm` | `gpt-5-mini` |
| `mid_think` | Balanced analysis (industry deep dive) | `mid_think_llm` | Falls back to `quick_think` |
| `deep_think` | Complex reasoning (macro synthesis, debate) | `deep_think_llm` | `gpt-5.2` |

Each tier can have its own `_llm_provider` and `_backend_url`. Falls back to top-level
`llm_provider` and `backend_url` when per-tier values are `None`.

### Data Vendor Routing

Three vendors with purpose-specific routing via `route_to_vendor()`:

| Vendor | Role | Key Capabilities |
|--------|------|-----------------|
| **yfinance** | Primary (free) | OHLCV, Screener, Sector/Industry, index tickers |
| **Alpha Vantage** | Secondary (API key) | News sentiment (per-article NLP scores), TOP_GAINERS_LOSERS |
| **Finnhub** | Supplementary (API key) | Earnings calendar, economic calendar, insider transactions |

Vendor fallback is **opt-in only** (ADR 011). Only methods in `FALLBACK_ALLOWED` get
cross-vendor fallback. All others fail-fast on primary vendor failure.

### Graph-Based Workflows (LangGraph)

Two independent workflow graphs:

1. **Trading Graph** — Per-ticker deep analysis → decision
2. **Scanner Graph** — Market-wide scan → watchlist

## Workflow: Trading Analysis Pipeline

```
Analysts (parallel)     →  Bull/Bear Debate  →  Research Manager  →  Trader  →  Risk Debate  →  Risk Judge
├── Fundamentals                                                                ├── Aggressive
├── Market (Technicals)                                                         ├── Conservative
├── News                                                                        └── Neutral
└── Social Media
```

- Analysts run in **parallel** using LangGraph fan-out
- Bull/Bear debate runs configurable rounds (`max_debate_rounds`, default: 1)
- Risk debate runs configurable rounds (`max_risk_discuss_rounds`, default: 1)
- Tool execution: graph-level `ToolNode` routing (agent → tool_node → agent loop)

## Workflow: Scanner Pipeline

```
Phase 1 (parallel)              →  Phase 2             →  Phase 3
├── Geopolitical (quick_think)     Industry Deep Dive     Macro Synthesis (deep_think)
├── Market Movers (quick_think)    (mid_think)            → Top-10 watchlist JSON
└── Sector Perf (quick_think)
```

- Phase 1 scanners run in **parallel** (fan-out/fan-in)
- Tool execution: inline `run_tool_loop()` (not graph-level ToolNode)
- All `ScannerState` fields written by parallel nodes have reducers (`Annotated[str, _last_value]`)

## Key Source Files

| File | Purpose |
|------|---------|
| `tradingagents/default_config.py` | All configuration with env var overrides |
| `tradingagents/graph/trading_graph.py` | TradingAgentsGraph class and trading workflow |
| `tradingagents/graph/scanner_graph.py` | ScannerGraph class and scanner workflow |
| `tradingagents/graph/scanner_setup.py` | Scanner graph wiring (fan-out/fan-in) |
| `tradingagents/dataflows/interface.py` | Vendor routing (`route_to_vendor`, `FALLBACK_ALLOWED`) |
| `tradingagents/agents/utils/tool_runner.py` | Inline tool loop for scanner agents |
| `tradingagents/agents/utils/agent_states.py` | LangGraph state definitions |
| `tradingagents/agents/utils/scanner_states.py` | Scanner-specific state with reducers |
| `cli/main.py` | CLI entry point (Typer): `analyze`, `scan` commands |

