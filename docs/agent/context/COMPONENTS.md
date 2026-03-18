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
│       ├── agent_states.py        # Trading AgentState definition
│       ├── agent_utils.py         # Tool exports
│       ├── core_stock_tools.py    # Core stock data tools
│       ├── fundamental_data_tools.py  # Fundamental analysis tools
│       ├── json_utils.py          # JSON parsing utilities
│       ├── memory.py              # Agent memory utilities
│       ├── news_data_tools.py     # News & sentiment tools
│       ├── scanner_states.py      # ScannerState with reducers
│       ├── scanner_tools.py       # Scanner-specific LangChain tools
│       ├── technical_indicators_tools.py  # Technical indicator tools
│       └── tool_runner.py         # Inline tool loop for scanners
├── dataflows/                     # Data access layer (vendor routing)
│   ├── __init__.py
│   ├── interface.py               # route_to_vendor(), VENDOR_METHODS, FALLBACK_ALLOWED
│   ├── config.py                  # Dataflow configuration
│   ├── utils.py                   # Shared dataflow utilities
│   ├── alpha_vantage.py           # AV facade (re-exports)
│   ├── alpha_vantage_common.py    # AV rate limiter, auth, base request
│   ├── alpha_vantage_fundamentals.py  # AV financial statements
│   ├── alpha_vantage_indicator.py     # AV technical indicators
│   ├── alpha_vantage_news.py      # AV news with sentiment scores
│   ├── alpha_vantage_scanner.py   # AV scanner (movers, sectors)
│   ├── alpha_vantage_stock.py     # AV stock data
│   ├── finnhub.py                 # Finnhub facade (re-exports)
│   ├── finnhub_common.py          # Finnhub rate limiter, auth
│   ├── finnhub_fundamentals.py    # Finnhub profile, metrics
│   ├── finnhub_indicators.py      # Finnhub technical indicators
│   ├── finnhub_news.py            # Finnhub news, insider transactions
│   ├── finnhub_scanner.py         # Finnhub scanner (calendars)
│   ├── finnhub_stock.py           # Finnhub quotes, candles
│   ├── macro_regime.py            # Macro regime classifier
│   ├── peer_comparison.py         # Peer comparison logic
│   ├── stockstats_utils.py        # stockstats technical indicators
│   ├── ttm_analysis.py            # TTM computation
│   ├── y_finance.py               # yfinance OHLCV, fundamentals
│   ├── yfinance_news.py           # yfinance news
│   └── yfinance_scanner.py        # yfinance sector/industry ETF proxies
├── graph/                         # Workflow orchestration
│   ├── __init__.py
│   ├── trading_graph.py           # TradingAgentsGraph class
│   ├── scanner_graph.py           # ScannerGraph class
│   ├── scanner_setup.py           # Scanner graph wiring (fan-out/fan-in)
│   ├── scanner_conditional_logic.py  # Scanner conditional routing
│   ├── setup.py                   # Trading graph setup
│   ├── conditional_logic.py       # Debate routing logic
│   ├── propagation.py             # Graph propagation utilities
│   ├── reflection.py              # Reflection utilities
│   └── signal_processing.py       # Signal processing utilities
├── llm_clients/                   # LLM provider adapters
│   ├── __init__.py
│   ├── base_client.py             # Abstract base LLM client
│   ├── factory.py                 # LLM client factory
│   ├── openai_client.py           # OpenAI/OpenRouter adapter
│   ├── anthropic_client.py        # Anthropic Claude adapter
│   ├── google_client.py           # Google Gemini adapter
│   └── validators.py              # Input/output validators
└── pipeline/                      # Pipeline orchestration
    ├── __init__.py
    └── macro_bridge.py            # Scanner-to-trading bridge
```

## Agent Extension Points

### Adding a New Analyst (Trading Pipeline)

1. Create `tradingagents/agents/analysts/new_analyst.py` using factory pattern: `create_new_analyst(llm)`
2. Add tools to `tradingagents/agents/utils/agent_utils.py`
3. Register tool node in `tradingagents/graph/trading_graph.py` → `_create_tool_nodes()`
4. Wire into graph in `tradingagents/graph/setup.py`

### Adding a New Scanner Agent

1. Create `tradingagents/agents/scanners/new_scanner.py` using `run_tool_loop()` for tool execution
2. Add scanner tools to `tradingagents/agents/utils/scanner_tools.py`
3. Wire into scanner graph in `tradingagents/graph/scanner_setup.py`
4. Add state fields to `tradingagents/agents/utils/scanner_states.py` with `_last_value` reducer

### Adding a New Data Vendor

1. Create `tradingagents/dataflows/newvendor_common.py` (auth, rate limiter, base request)
2. Create domain files: `newvendor_stock.py`, `newvendor_news.py`, etc.
3. Create facade: `newvendor.py` (re-exports)
4. Register methods in `tradingagents/dataflows/interface.py` → `VENDOR_METHODS`
5. Configure routing in `tradingagents/default_config.py` → `vendor_*` and `tool_vendors` keys
6. If data contracts are compatible, optionally add to `FALLBACK_ALLOWED`
7. Add error type to catch list: `(AlphaVantageError, FinnhubError, NewVendorError, ...)`
8. Write ADR documenting the vendor decision (see `docs/agent/decisions/010-finnhub-vendor-integration.md`)

### Adding a New Config Key

1. Add to `DEFAULT_CONFIG` in `tradingagents/default_config.py` using `_env()` or `_env_int()`
2. Key is automatically overridable via `TRADINGAGENTS_<UPPERCASE_KEY>` env var
3. Document in `.env.example`

## CLI Commands

| Command | Description | Entry Point |
|---------|-------------|-------------|
| `python -m cli.main analyze` | Per-ticker deep analysis | `cli/main.py` → `TradingAgentsGraph.propagate()` |
| `python -m cli.main scan --date YYYY-MM-DD` | Market-wide scan | `cli/main.py` → `ScannerGraph.run()` |

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
| `test_alpha_vantage_exceptions.py` | Unit | AV exception hierarchy |
| `test_alpha_vantage_integration.py` | Integration | AV API endpoints |
| `test_alpha_vantage_scanner.py` | Unit/Integration | AV scanner functions |
| `test_yfinance_integration.py` | Integration | yfinance data access |
| `test_e2e_api_integration.py` | Integration | End-to-end API routing |
| `test_debate_rounds.py` | Unit | Debate round logic |
| `test_json_utils.py` | Unit | JSON parsing utilities |
| `test_macro_bridge.py` | Unit | Scanner-to-trading bridge |
| `test_macro_regime.py` | Unit | Macro regime classifier |
| `test_peer_comparison.py` | Unit | Peer comparison logic |
| `test_ttm_analysis.py` | Unit | TTM analysis computation |
| `test_scanner_tools.py` | Unit | Scanner tool functions |
| `test_scanner_comprehensive.py` | Integration (LLM) | Full scan pipeline |
| `test_scanner_complete_e2e.py` | Integration | Full scanner E2E |
| `test_scanner_end_to_end.py` | Integration | Scanner workflow |
| `test_scanner_final.py` | Integration | Scanner final output |
| `test_scanner_mocked.py` | Unit (mocked) | Mocked scanner tests |
| `test_scanner_routing.py` | Unit | Scanner routing logic |

