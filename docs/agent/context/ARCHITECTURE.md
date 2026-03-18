# Architecture Overview

## System Description

TradingAgents is a multi-agent LLM framework (v0.2.1) for financial analysis and trading
decisions, built on LangGraph. It simulates a real trading firm with 17 specialized agents
— analysts, researchers, traders, scanners, and risk managers — that collaborate through
two graph-based workflows, connected by a pipeline bridge. Three data vendors supply
market data, and a multi-provider LLM factory supports six provider backends.

## Core Patterns

### Agent Factory Pattern

All agents use `create_X(llm)` → closure pattern. The factory accepts an LLM instance
and returns a callable node function compatible with LangGraph.

- Trading agents: `tradingagents/agents/analysts/*.py`, `tradingagents/agents/managers/*.py`
- Scanner agents: `tradingagents/agents/scanners/*.py`

### 3-Tier LLM System

| Tier | Purpose | Config Key | Default Model |
|------|---------|-----------|---------------|
| `quick_think` | Fast responses (scanners, analysts) | `quick_think_llm` | `gpt-5-mini` |
| `mid_think` | Balanced analysis (industry deep dive) | `mid_think_llm` | Falls back to `quick_think` |
| `deep_think` | Complex reasoning (macro synthesis, debate) | `deep_think_llm` | `gpt-5.2` |

Each tier can have its own `_llm_provider` and `_backend_url`. Falls back to top-level
`llm_provider` and `backend_url` when per-tier values are `None`.

### Multi-Provider LLM Factory

`create_llm_client()` in `tradingagents/llm_clients/factory.py` dispatches to
provider-specific client classes:

| Provider | Config Value | Client Class |
|----------|-------------|-------------|
| OpenAI | `"openai"` | `OpenAIClient` (uses `UnifiedChatOpenAI` subclass) |
| Anthropic | `"anthropic"` | `AnthropicClient` |
| Google | `"google"` | `GoogleClient` (uses `NormalizedChatGoogleGenerativeAI`) |
| xAI | `"xai"` | Via `OpenAIClient` with xAI endpoint |
| Ollama | `"ollama"` | Via `OpenAIClient` with local endpoint |
| OpenRouter | `"openrouter"` | Via `OpenAIClient` with OpenRouter endpoint |

All clients extend `BaseLLMClient` (`tradingagents/llm_clients/base_client.py`).

### Data Vendor Routing

Three vendors with purpose-specific routing via `route_to_vendor()`:

| Vendor | Role | Key Capabilities |
|--------|------|-----------------|
| **yfinance** | Primary (free) | OHLCV, Screener, Sector/Industry, index tickers |
| **Alpha Vantage** | Secondary (API key) | News sentiment (per-article NLP scores), TOP_GAINERS_LOSERS |
| **Finnhub** | Supplementary (API key) | Earnings calendar, economic calendar, insider transactions |

Vendor fallback is **opt-in only** (ADR 011). Only 5 methods in `FALLBACK_ALLOWED` get
cross-vendor fallback: `get_stock_data`, `get_market_indices`, `get_sector_performance`,
`get_market_movers`, `get_industry_performance`. All others fail-fast.

Two-level vendor configuration in `default_config.py`:
- **Category-level** (`data_vendors`): default vendor for all tools in a category
- **Tool-level** (`tool_vendors`): override for specific tool (takes precedence)

## Workflow: Trading Analysis Pipeline

```
Analysts (parallel)     →  Bull/Bear Debate  →  Research Manager  →  Trader  →  Risk Debate  →  Risk Judge
├── Fundamentals                                                                ├── Aggressive
├── Market (Technicals)                                                         ├── Conservative
├── News                                                                        └── Neutral
└── Social Media
```

- Analysts run in **parallel** using LangGraph fan-out; user selects 1-4 analysts
- Bull/Bear debate runs configurable rounds (`max_debate_rounds`, default: 1)
- Risk debate runs configurable rounds (`max_risk_discuss_rounds`, default: 1)
- Tool execution: graph-level `ToolNode` routing (agent → tool_node → agent loop)
- State: `AgentState` (extends `MessagesState`) with `InvestDebateState`, `RiskDebateState`

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

## Pipeline: Scanner → Trading Bridge

```
Scanner Output (JSON)  →  MacroBridge.parse_macro_output()  →  filter_candidates()
    → run_ticker_analysis() (per ticker)  →  TickerResult  →  render + save
```

`MacroBridge` in `tradingagents/pipeline/macro_bridge.py` bridges macro scanner output
to per-ticker `TradingAgentsGraph` analysis. Key data classes:

- `MacroContext` — economic cycle, central bank stance, geopolitical risks, key themes
- `StockCandidate` — ticker, sector, thesis angle, conviction level, catalysts, risks
- `TickerResult` — full trading reports per ticker enriched with macro context

## CLI Architecture

`cli/main.py` (Typer framework) exposes three commands: `analyze`, `scan`, `pipeline`.

- `MessageBuffer` — deque-based state manager tracking agent status, report sections,
  and message history for real-time Rich UI display
- `StatsCallbackHandler` — token counting and timing metrics per LLM call
- Fixed agent teams (Research, Trading, Risk, Portfolio) always run; analysts are selectable
- Rich-based live layout: spinner, agent status panel, report sections, statistics footer

## Key Source Files

| File | Purpose |
|------|---------|
| `tradingagents/default_config.py` | All configuration with env var overrides |
| `tradingagents/graph/trading_graph.py` | `TradingAgentsGraph` class and trading workflow |
| `tradingagents/graph/scanner_graph.py` | `ScannerGraph` class and scanner workflow |
| `tradingagents/graph/setup.py` | `GraphSetup` — trading graph node wiring |
| `tradingagents/graph/scanner_setup.py` | `ScannerGraphSetup` — scanner fan-out/fan-in wiring |
| `tradingagents/dataflows/interface.py` | `route_to_vendor()`, `VENDOR_METHODS`, `FALLBACK_ALLOWED` |
| `tradingagents/agents/utils/tool_runner.py` | Inline tool loop for scanner agents |
| `tradingagents/agents/utils/agent_states.py` | `AgentState`, `InvestDebateState`, `RiskDebateState` |
| `tradingagents/agents/utils/scanner_states.py` | `ScannerState` with `_last_value` reducers |
| `tradingagents/llm_clients/factory.py` | `create_llm_client()` — multi-provider dispatch |
| `tradingagents/pipeline/macro_bridge.py` | `MacroBridge`, `MacroContext`, `StockCandidate`, `TickerResult` |
| `cli/main.py` | CLI entry point: `analyze`, `scan`, `pipeline` commands |
| `cli/stats_handler.py` | `StatsCallbackHandler` for LLM call metrics |

<!-- Last verified: 2026-03-18 -->
