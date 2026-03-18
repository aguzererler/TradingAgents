# Glossary

Quick reference for project-specific terms, acronyms, and identifiers.

## Agents & Workflows

| Term | Definition |
|------|-----------|
| **Trading Graph** | Per-ticker analysis pipeline: analysts → debate → trader → risk → decision |
| **Scanner Graph** | Market-wide scan pipeline: parallel scanners → deep dive → synthesis → watchlist |
| **Agent Factory** | `create_X(llm)` pattern that returns a LangGraph-compatible node function |
| **ToolNode** | LangGraph component that executes tool calls; used in trading graph |
| **run_tool_loop()** | Inline tool execution in `tool_runner.py`; used by scanner agents |
| **Nudge** | `HumanMessage` injected when LLM skips tool calls on first response (<500 chars) |

## Data Layer

| Term | Definition |
|------|-----------|
| **route_to_vendor()** | Central dispatcher in `interface.py` that routes data requests to configured vendors |
| **VENDOR_METHODS** | Dict mapping method names to vendor implementations |
| **FALLBACK_ALLOWED** | Set of methods that permit cross-vendor fallback (ADR 011) |
| **VENDOR_LIST** | Ordered list of vendor names for fallback chain |
| **ETF Proxy** | Using SPDR sector ETFs (XLK, XLV, etc.) as proxy for sector performance data |

## Configuration

| Term | Definition |
|------|-----------|
| **quick_think** | LLM tier for fast responses (scanners, simple tasks) |
| **mid_think** | LLM tier for balanced analysis (industry deep dive) |
| **deep_think** | LLM tier for complex reasoning (macro synthesis, debate) |
| **`_env()`** | Helper function in `default_config.py` that reads `TRADINGAGENTS_<KEY>` env vars |
| **`_env_int()`** | Integer variant of `_env()` for numeric config values |

## Vendor-Specific

| Term | Definition |
|------|-----------|
| **AlphaVantageError** | Base exception for all Alpha Vantage failures |
| **FinnhubError** | Base exception for all Finnhub failures |
| **APIKeyInvalidError** | Raised when a required API key is missing |
| **MSPR** | Monthly Share Purchase Ratio — Finnhub insider sentiment aggregate |
| **XBRL** | eXtensible Business Reporting Language — SEC filing format (Finnhub `/financials-reported`) |

## State Fields

| Term | Definition |
|------|-----------|
| **ScannerState** | LangGraph `TypedDict` for scanner pipeline; all fields have `_last_value` reducer |
| **AgentState** | LangGraph `TypedDict` for trading pipeline |
| **_last_value** | Reducer function that keeps the latest write in parallel state updates |

## File Conventions

| Term | Definition |
|------|-----------|
| **ADR** | Architecture Decision Record — binding rules in `docs/agent/decisions/` |
| **CURRENT_STATE.md** | Live project status: milestone, progress, blockers |
| **SKILL.md** | Claude skill definition file in `.claude/skills/<name>/SKILL.md` |

