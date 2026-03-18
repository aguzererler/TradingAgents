# Coding Conventions & Patterns

## Configuration

- **Env var override pattern**: `TRADINGAGENTS_<UPPERCASE_KEY>=value`
  - `_env()` / `_env_int()` helpers in `default_config.py` read from environment
  - Empty or unset vars preserve hardcoded defaults
  - `None`-default fields (like `mid_think_llm`) stay `None` when unset
- **Top-level fallback keys**: `llm_provider` and `backend_url` MUST always exist at top level — `scanner_graph.py` and `trading_graph.py` use them as fallbacks when per-tier values are `None`
- **`.env` loading**: `load_dotenv()` runs at module level in `default_config.py` — import-order-independent

## Agent Creation

- **Factory pattern**: `create_X(llm)` returns a closure that accepts `(state: dict)` and returns `dict`
- **Trading agents**: Use graph-level `ToolNode` for tool execution
- **Scanner agents**: Use `run_tool_loop()` inline for tool execution
- **Rule**: If `bind_tools()` is used, there MUST be a tool execution path

## Tool Execution

- **Trading graph**: `ToolNode` in graph (agent → tool_node → agent routing loop)
- **Scanner agents**: `run_tool_loop()` in `tradingagents/agents/utils/tool_runner.py`
  - Max 5 tool rounds per invocation
  - Nudge mechanism: if first response has no `tool_calls` and is under 2000 chars (`MIN_REPORT_LENGTH`), appends a `HumanMessage` nudge (fires once only)

## Vendor Routing

- Functions inside `route_to_vendor` MUST **raise** on failure, not embed errors in return values
- Catch `(AlphaVantageError, FinnhubError, ConnectionError, TimeoutError)` for fallback
- Fallback is **opt-in only** (ADR 011): only methods in `FALLBACK_ALLOWED` get cross-vendor fallback
- Calendar functions return graceful empty-state strings (not raise) when API returns empty list

## yfinance Specifics

- `top_companies` has ticker as **INDEX**, not column — use `.iterrows()` or check `.index`
- `Sector.overview` has NO performance data — use ETF proxies (ADR 003)
- Always inspect DataFrame structure with `.head()`, `.columns`, `.index` before writing code

## LangGraph State

- Any state field written by **parallel nodes** MUST have a reducer (`Annotated[str, reducer_fn]`)
- `ScannerState` uses `_last_value` reducer for all fields
- New state fields should default to empty string to avoid `KeyError`

## Threading & Rate Limiting

- **Never** hold a lock during `sleep()` or IO — release, sleep, re-acquire
- Alpha Vantage: 75 calls/min, two-phase rate limiter in `alpha_vantage_common.py`
- Finnhub: 60 calls/min, `_rate_limited_request` in `finnhub_common.py`

## Ollama / Remote LLMs

- **Never** hardcode `localhost:11434` — always use configured `base_url`
- Per-tier providers fall back to top-level `llm_provider` when `None`

## Testing

- Run tests: `pytest tests/ -v`
- Network-dependent tests auto-skip when services are unreachable
- Finnhub live tests require `FINNHUB_API_KEY` env var
- Use `@pytest.mark.integration` for tests requiring live APIs
- Use `@pytest.mark.paid_tier` + `@pytest.mark.skip` for Finnhub paid-tier tests
- When testing config in isolation: clean env + `patch("dotenv.load_dotenv")` to block `.env` re-reads

## Error Handling

- New data methods are **fail-fast by default** — only add to `FALLBACK_ALLOWED` after verifying data contract compatibility
- Exception chaining: `raise RuntimeError(...) from last_error` to preserve original cause
- `FINNHUB_API_KEY` missing → `APIKeyInvalidError`; never call paid endpoints on free tier

