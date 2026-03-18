# Glossary

Quick reference for project-specific terms, acronyms, and identifiers.

## Agents & Workflows

| Term | Definition | Source |
|------|-----------|--------|
| **Trading Graph** | Per-ticker analysis pipeline: analysts → debate → trader → risk → decision | `graph/trading_graph.py` |
| **Scanner Graph** | Market-wide scan pipeline: parallel scanners → deep dive → synthesis → watchlist | `graph/scanner_graph.py` |
| **Agent Factory** | `create_X(llm)` pattern returning a LangGraph-compatible node function | `agents/analysts/*.py` |
| **ToolNode** | LangGraph component that executes tool calls; used in trading graph | `langgraph` |
| **run_tool_loop()** | Inline tool execution loop (max 5 rounds); used by scanner agents | `agents/utils/tool_runner.py` |
| **Nudge** | `HumanMessage` injected when LLM skips tool calls on first response (<2000 chars) | `agents/utils/tool_runner.py` |

## Data Layer

| Term | Definition | Source |
|------|-----------|--------|
| **route_to_vendor()** | Central dispatcher routing data requests to configured vendors | `dataflows/interface.py` |
| **VENDOR_METHODS** | Dict mapping method names to vendor implementations | `dataflows/interface.py` |
| **FALLBACK_ALLOWED** | Set of 5 methods that permit cross-vendor fallback (ADR 011) | `dataflows/interface.py` |
| **ETF Proxy** | Using SPDR sector ETFs (XLK, XLV, etc.) as proxy for sector performance | `dataflows/yfinance_scanner.py` |
| **Macro Regime** | Risk-on / risk-off / transition classification via VIX, yield curve, breadth | `dataflows/macro_regime.py` |
| **TTM Analysis** | Trailing Twelve Months financial metrics computation | `dataflows/ttm_analysis.py` |
| **Peer Comparison** | Sector-relative performance and peer group analysis | `dataflows/peer_comparison.py` |

## Configuration

| Term | Definition | Source |
|------|-----------|--------|
| **quick_think** | LLM tier for fast responses (scanners, analysts); default: `gpt-5-mini` | `default_config.py` |
| **mid_think** | LLM tier for balanced analysis; falls back to `quick_think` when `None` | `default_config.py` |
| **deep_think** | LLM tier for complex reasoning; default: `gpt-5.2` | `default_config.py` |
| **`_env()`** | Helper reading `TRADINGAGENTS_<KEY>` env vars; returns `None` for empty | `default_config.py` |
| **`_env_int()`** | Integer variant of `_env()` for numeric config values | `default_config.py` |

## Vendor-Specific

| Term | Definition | Source |
|------|-----------|--------|
| **AlphaVantageError** | Base exception for all Alpha Vantage failures | `dataflows/alpha_vantage_common.py` |
| **FinnhubError** | Base exception for all Finnhub failures | `dataflows/finnhub_common.py` |
| **APIKeyInvalidError** | Raised when a required API key is missing (both AV and Finnhub) | `*_common.py` |
| **RateLimitError** | Raised when vendor rate limit is hit (both AV and Finnhub) | `*_common.py` |
| **ThirdPartyError** | Base for vendor HTTP/API errors (both AV and Finnhub) | `*_common.py` |
| **MSPR** | Monthly Share Purchase Ratio — Finnhub insider sentiment aggregate | `dataflows/finnhub_news.py` |

## State & Data Classes

| Term | Definition | Source |
|------|-----------|--------|
| **AgentState** | LangGraph `MessagesState` for trading pipeline (extends `TypedDict`) | `agents/utils/agent_states.py` |
| **InvestDebateState** | `TypedDict` tracking bull/bear debate history and judge decision | `agents/utils/agent_states.py` |
| **RiskDebateState** | `TypedDict` tracking 3-way risk debate (aggressive/neutral/conservative) | `agents/utils/agent_states.py` |
| **ScannerState** | LangGraph `MessagesState` for scanner pipeline; `_last_value` reducers | `agents/utils/scanner_states.py` |
| **_last_value** | Reducer function keeping the latest write in parallel state updates | `agents/utils/scanner_states.py` |
| **FinancialSituationMemory** | Agent memory utility for storing financial context | `agents/utils/memory.py` |

## Pipeline

| Term | Definition | Source |
|------|-----------|--------|
| **MacroBridge** | Orchestrator bridging scanner output to per-ticker trading analysis | `pipeline/macro_bridge.py` |
| **MacroContext** | Dataclass: economic cycle, central bank stance, risks, themes | `pipeline/macro_bridge.py` |
| **StockCandidate** | Dataclass: ticker, sector, thesis angle, conviction, catalysts | `pipeline/macro_bridge.py` |
| **TickerResult** | Dataclass: per-ticker reports enriched with macro context | `pipeline/macro_bridge.py` |
| **ConvictionLevel** | `Literal["high", "medium", "low"]` — conviction ranking for candidates | `pipeline/macro_bridge.py` |
| **CONVICTION_RANK** | Dict mapping conviction levels to integers: high=3, medium=2, low=1 | `pipeline/macro_bridge.py` |

## CLI

| Term | Definition | Source |
|------|-----------|--------|
| **MessageBuffer** | Deque-based manager for agent status, report sections, real-time UI | `cli/main.py` |
| **StatsCallbackHandler** | LLM callback tracking token counts and timing per call | `cli/stats_handler.py` |
| **AnalystType** | Enum of selectable analysts: Market, News, Social, Fundamentals | `cli/models.py` |
| **FIXED_AGENTS** | Non-selectable agent teams that always run (Research, Trading, Risk, Portfolio) | `cli/main.py` |

## Constants

| Term | Value | Source |
|------|-------|--------|
| **MAX_TOOL_ROUNDS** | 5 | `agents/utils/tool_runner.py:17` |
| **MIN_REPORT_LENGTH** | 2000 | `agents/utils/tool_runner.py:23` |
| **AV rate limit** | 75 calls/min | `dataflows/alpha_vantage_common.py` |
| **Finnhub rate limit** | 60 calls/min | `dataflows/finnhub_common.py` |
| **max_debate_rounds** | 1 (default) | `default_config.py` |
| **max_risk_discuss_rounds** | 1 (default) | `default_config.py` |
| **max_recur_limit** | 100 (default) | `default_config.py` |

## File Conventions

| Term | Definition | Source |
|------|-----------|--------|
| **ADR** | Architecture Decision Record — binding rules in `docs/agent/decisions/` | `docs/agent/decisions/` |
| **CURRENT_STATE.md** | Live project status: milestone, progress, blockers | `docs/agent/CURRENT_STATE.md` |
| **SKILL.md** | Claude skill definition file in `.claude/skills/<name>/SKILL.md` | `.claude/skills/` |

<!-- Last verified: 2026-03-18 -->
