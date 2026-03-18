# Component Reference

## Directory Structure

```
tradingagents/
├── __init__.py
├── default_config.py              # Central config with env var overrides
├── agents/
│   ├── __init__.py
│   ├── analysts/                  # Trading pipeline analyst agents
│   │   ├── fundamentals_analyst.py
│   │   ├── market_analyst.py
│   │   ├── news_analyst.py
│   │   └── social_media_analyst.py
│   ├── managers/                  # Research & risk management
│   │   ├── research_manager.py
│   │   └── risk_manager.py
│   ├── researchers/               # Bull/Bear debate agents
│   │   ├── bear_researcher.py
│   │   └── bull_researcher.py
│   ├── risk_mgmt/                 # Risk debate agents
│   │   ├── aggressive_debator.py
│   │   ├── conservative_debator.py
│   │   └── neutral_debator.py
│   ├── trader/                    # Trader agent
│   │   └── trader.py
│   ├── scanners/                  # Scanner pipeline agents
│   │   ├── __init__.py
│   │   ├── geopolitical_scanner.py
│   │   ├── industry_deep_dive.py
│   │   ├── macro_synthesis.py
│   │   ├── market_movers_scanner.py
│   │   └── sector_scanner.py
│   └── utils/                     # Shared agent utilities
│       ├── agent_states.py        # AgentState, InvestDebateState, RiskDebateState
│       ├── agent_utils.py         # Tool exports for trading graph
│       ├── core_stock_tools.py    # Core stock data tools
│       ├── fundamental_data_tools.py  # Fundamental analysis tools
│       ├── json_utils.py          # extract_json() for LLM output parsing
│       ├── memory.py              # FinancialSituationMemory
│       ├── news_data_tools.py     # News & sentiment tools
│       ├── scanner_states.py      # ScannerState with _last_value reducers
│       ├── scanner_tools.py       # Scanner-specific LangChain tools
│       ├── technical_indicators_tools.py  # Technical indicator tools
│       └── tool_runner.py         # run_tool_loop() — inline tool loop for scanners
├── dataflows/                     # Data access layer (vendor routing)
│   ├── __init__.py
│   ├── interface.py               # route_to_vendor(), VENDOR_METHODS, FALLBACK_ALLOWED
│   ├── config.py                  # Dataflow configuration
│   ├── utils.py                   # Shared dataflow utilities
│   ├── alpha_vantage.py           # AV facade (re-exports)
│   ├── alpha_vantage_common.py    # AV rate limiter (75/min), auth, exceptions
│   ├── alpha_vantage_fundamentals.py  # AV financial statements
│   ├── alpha_vantage_indicator.py     # AV technical indicators
│   ├── alpha_vantage_news.py      # AV news with sentiment scores
│   ├── alpha_vantage_scanner.py   # AV scanner (movers, sectors)
│   ├── alpha_vantage_stock.py     # AV stock data
│   ├── finnhub.py                 # Finnhub facade (re-exports)
│   ├── finnhub_common.py          # Finnhub rate limiter (60/min), auth, exceptions
│   ├── finnhub_fundamentals.py    # Finnhub profile, metrics
│   ├── finnhub_indicators.py      # Finnhub technical indicators
│   ├── finnhub_news.py            # Finnhub news, insider transactions
│   ├── finnhub_scanner.py         # Finnhub scanner (calendars)
│   ├── finnhub_stock.py           # Finnhub quotes, candles
│   ├── macro_regime.py            # Macro regime classifier (risk-on/off/transition)
│   ├── peer_comparison.py         # Peer comparison: sector peers, relative performance
│   ├── stockstats_utils.py        # stockstats technical indicators (local computation)
│   ├── ttm_analysis.py            # Trailing Twelve Months financial analysis
│   ├── y_finance.py               # yfinance OHLCV, fundamentals
│   ├── yfinance_news.py           # yfinance news
│   └── yfinance_scanner.py        # yfinance sector/industry ETF proxies
├── graph/                         # Workflow orchestration
│   ├── __init__.py
│   ├── trading_graph.py           # TradingAgentsGraph class
│   ├── scanner_graph.py           # ScannerGraph class
│   ├── setup.py                   # GraphSetup — trading graph node wiring
│   ├── scanner_setup.py           # ScannerGraphSetup — scanner fan-out/fan-in wiring
│   ├── conditional_logic.py       # ConditionalLogic — debate routing
│   ├── scanner_conditional_logic.py  # ScannerConditionalLogic — scanner routing
│   ├── propagation.py             # Propagator — forward propagation
│   ├── reflection.py              # Reflector — learning & memory
│   └── signal_processing.py       # SignalProcessor — signal aggregation
├── llm_clients/                   # Multi-provider LLM support
│   ├── __init__.py                # Exports: BaseLLMClient, create_llm_client
│   ├── base_client.py             # BaseLLMClient abstract base class
│   ├── factory.py                 # create_llm_client() — provider dispatch
│   ├── openai_client.py           # OpenAIClient, UnifiedChatOpenAI
│   ├── anthropic_client.py        # AnthropicClient
│   ├── google_client.py           # GoogleClient, NormalizedChatGoogleGenerativeAI
│   └── validators.py              # Input/output validators
└── pipeline/                      # Pipeline orchestration
    ├── __init__.py
    └── macro_bridge.py            # MacroBridge, MacroContext, StockCandidate, TickerResult
```

```
cli/
├── __init__.py
├── main.py                        # Typer CLI: analyze, scan, pipeline commands + MessageBuffer
├── config.py                      # CLI configuration
├── models.py                      # AnalystType enum and data models
├── utils.py                       # CLI utility functions
├── announcements.py               # News/announcements handler
├── stats_handler.py               # StatsCallbackHandler — token counting, timing
└── static/                        # Static assets for CLI
```

## Key Classes

| Class | File | Purpose |
|-------|------|---------|
| `TradingAgentsGraph` | `graph/trading_graph.py` | Main trading workflow orchestrator |
| `ScannerGraph` | `graph/scanner_graph.py` | Scanner pipeline orchestrator |
| `GraphSetup` | `graph/setup.py` | Trading graph node wiring |
| `ScannerGraphSetup` | `graph/scanner_setup.py` | Scanner fan-out/fan-in wiring |
| `MacroBridge` | `pipeline/macro_bridge.py` | Scanner → trading bridge |
| `MacroContext` | `pipeline/macro_bridge.py` | Macro-level context dataclass |
| `StockCandidate` | `pipeline/macro_bridge.py` | Stock surfaced by scanner dataclass |
| `TickerResult` | `pipeline/macro_bridge.py` | Per-ticker result dataclass |
| `AgentState` | `agents/utils/agent_states.py` | LangGraph state for trading pipeline |
| `InvestDebateState` | `agents/utils/agent_states.py` | Bull/Bear debate state |
| `RiskDebateState` | `agents/utils/agent_states.py` | Risk discussion state |
| `ScannerState` | `agents/utils/scanner_states.py` | LangGraph state with `_last_value` reducers |
| `BaseLLMClient` | `llm_clients/base_client.py` | Abstract base for LLM clients |
| `OpenAIClient` | `llm_clients/openai_client.py` | OpenAI/compatible provider client |
| `UnifiedChatOpenAI` | `llm_clients/openai_client.py` | ChatOpenAI subclass for GPT-5 compat |
| `MessageBuffer` | `cli/main.py` | Real-time agent status + report manager |
| `StatsCallbackHandler` | `cli/stats_handler.py` | LLM call token/timing metrics |
| `AlphaVantageError` | `dataflows/alpha_vantage_common.py` | AV base exception |
| `FinnhubError` | `dataflows/finnhub_common.py` | Finnhub base exception |

## Agent Extension Points

### Adding a New Analyst (Trading Pipeline)

1. Create `tradingagents/agents/analysts/new_analyst.py` using factory pattern:
   `create_new_analyst(llm)`
2. Add tools to `tradingagents/agents/utils/agent_utils.py`
3. Register tool node in `tradingagents/graph/trading_graph.py` → `_create_tool_nodes()`
4. Wire into graph in `tradingagents/graph/setup.py`

### Adding a New Scanner Agent

1. Create `tradingagents/agents/scanners/new_scanner.py` using `run_tool_loop()` for
   tool execution
2. Add scanner tools to `tradingagents/agents/utils/scanner_tools.py`
3. Wire into scanner graph in `tradingagents/graph/scanner_setup.py`
4. Add state fields to `tradingagents/agents/utils/scanner_states.py` with `_last_value`
   reducer

### Adding a New Data Vendor

1. Create `tradingagents/dataflows/newvendor_common.py` (auth, rate limiter, exceptions)
2. Create domain files: `newvendor_stock.py`, `newvendor_news.py`, etc.
3. Create facade: `newvendor.py` (re-exports)
4. Register methods in `tradingagents/dataflows/interface.py` → `VENDOR_METHODS`
5. Configure in `tradingagents/default_config.py` → `data_vendors` and `tool_vendors`
6. Optionally add to `FALLBACK_ALLOWED` if data contracts are compatible
7. Add error type to catch list in `route_to_vendor()`
8. Write ADR in `docs/agent/decisions/`

### Adding a New Config Key

1. Add to `DEFAULT_CONFIG` in `tradingagents/default_config.py` using `_env()` or `_env_int()`
2. Automatically overridable via `TRADINGAGENTS_<UPPERCASE_KEY>` env var
3. Document in `.env.example`

### Adding a New LLM Provider

1. Create `tradingagents/llm_clients/new_provider_client.py` extending `BaseLLMClient`
2. Register in `tradingagents/llm_clients/factory.py` → `create_llm_client()`

## CLI Commands

| Command | Description | Entry Point |
|---------|-------------|-------------|
| `python -m cli.main analyze` | Per-ticker deep analysis | `cli/main.py` → `TradingAgentsGraph.propagate()` |
| `python -m cli.main scan --date YYYY-MM-DD` | Market-wide scan | `cli/main.py` → `ScannerGraph.run()` |
| `python -m cli.main pipeline` | Full pipeline: scan → filter → per-ticker | `cli/main.py` → `MacroBridge` |

## Test Organization

| Test File | Type | Notes |
|-----------|------|-------|
| `test_env_override.py` | Unit (offline) | Config env var overrides |
| `test_config_wiring.py` | Unit | Tool wiring verification |
| `test_industry_deep_dive.py` | Unit + network | Sector parsing, nudge mechanism |
| `test_finnhub_integration.py` | Unit (mocked HTTP) | All Finnhub endpoints |
| `test_finnhub_live_integration.py` | Live API | Auto-skip without `FINNHUB_API_KEY` |
| `test_scanner_fallback.py` | Unit (mocked) | Vendor fallback paths |
| `test_scanner_graph.py` | Unit (mocked) | Graph compilation |
| `test_vendor_failfast.py` | Unit (mocked) | Fail-fast vendor routing |
| `test_alpha_vantage_*.py` (3 files) | Unit/Integration | Exceptions, API endpoints, scanner |
| `test_yfinance_integration.py` | Integration | yfinance data access |
| `test_e2e_api_integration.py` | Integration | End-to-end API routing |
| `test_debate_rounds.py` | Unit | Debate round logic |
| `test_json_utils.py` | Unit | JSON parsing utilities |
| `test_macro_bridge.py` | Unit | Scanner-to-trading bridge |
| `test_macro_regime.py` | Unit | Macro regime classifier |
| `test_peer_comparison.py` | Unit | Peer comparison logic |
| `test_ttm_analysis.py` | Unit | TTM analysis computation |
| `test_scanner_tools.py` | Unit | Scanner tool functions |
| `test_scanner_*.py` (6 files) | Unit/Integration | Mocked, routing, E2E, comprehensive |

<!-- Last verified: 2026-03-18 -->
