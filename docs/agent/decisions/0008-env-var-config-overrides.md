---
title: Environment Variable Config Overrides
date: 2026-03-17
status: implemented
tags: [configuration, environment, dotenv, config]
---

# ADR-0008: Environment Variable Config Overrides

## Context

`DEFAULT_CONFIG` hardcoded all values (LLM providers, models, vendor routing, debate rounds). Users had to edit `default_config.py` to change any setting. The `load_dotenv()` call in `cli/main.py` ran *after* `DEFAULT_CONFIG` was already evaluated at import time, so env vars like `TRADINGAGENTS_LLM_PROVIDER` had no effect. This also created a latent bug (Mistake #9): `llm_provider` and `backend_url` were removed from the config but `scanner_graph.py` still referenced them as fallbacks.

## Decision

1. **Module-level `.env` loading**: `default_config.py` calls `load_dotenv()` at the top of the module, before `DEFAULT_CONFIG` is evaluated. Loads from CWD first, then falls back to project root (`Path(__file__).resolve().parent.parent / ".env"`).
2. **`_env()` / `_env_int()` helpers**: Read `TRADINGAGENTS_<KEY>` from environment. Return the hardcoded default when the env var is unset or empty (preserving `None` semantics for per-tier fallbacks).
3. **Restored top-level keys**: `llm_provider` (default: `"openai"`) and `backend_url` (default: `"https://api.openai.com/v1"`) restored as env-overridable keys. Resolves Mistake #9.
4. **All config keys overridable**: LLM models, providers, backend URLs, debate rounds, data vendor categories — all follow the `TRADINGAGENTS_<KEY>` pattern.
5. **Explicit dependency**: Added `python-dotenv>=1.0.0` to `pyproject.toml` (was used but undeclared).

**Naming convention**: `TRADINGAGENTS_` prefix + uppercase config key. Examples:
```
TRADINGAGENTS_LLM_PROVIDER=openrouter
TRADINGAGENTS_DEEP_THINK_LLM=deepseek/deepseek-r1-0528
TRADINGAGENTS_MAX_DEBATE_ROUNDS=3
TRADINGAGENTS_VENDOR_SCANNER_DATA=alpha_vantage
```

**Files**: `tradingagents/default_config.py`, `main.py`, `pyproject.toml`, `.env.example`, `tests/test_env_override.py`

**Alternative considered**: YAML/TOML config file. Rejected — env vars are simpler, work with Docker/CI, and don't require a new config file format.

## Consequences & Constraints

- `load_dotenv()` runs at module level in `default_config.py` — import-order-independent.
- Empty or unset env vars preserve the hardcoded default.
- `None`-default fields (like `mid_think_llm`) stay `None` when unset, preserving fallback semantics.
- Top-level `llm_provider` and `backend_url` **must always exist** as fallback keys.

## Actionable Rules

1. **All `DEFAULT_CONFIG` values are overridable** via `TRADINGAGENTS_<KEY>` environment variables.
2. **Top-level `llm_provider` and `backend_url` must always exist** in `DEFAULT_CONFIG`. `scanner_graph.py` and `trading_graph.py` use them as fallbacks when per-tier values are `None`. See Mistake #9.
3. **Use `_env()` for string config, `_env_int()` for integer config.** Empty strings are treated as unset (returns default).
4. **Never remove config keys** that downstream code references as fallbacks. Always grep for all references before removing keys.
5. **`load_dotenv()` must remain at module level** in `default_config.py` to ensure env vars are loaded before `DEFAULT_CONFIG` evaluation.
