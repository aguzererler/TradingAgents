---
title: Hybrid LLM Setup (Ollama + OpenRouter)
date: 2026-03-17
status: implemented
tags: [llm, configuration, ollama, openrouter]
---

# ADR-0001: Hybrid LLM Setup (Ollama + OpenRouter)

## Context

The scanner pipeline requires different LLM tiers for tasks of varying complexity. A cost-effective setup is needed that balances speed, quality, and cost.

## Decision

Use a hybrid approach:
- **quick_think + mid_think**: `qwen3.5:27b` via Ollama (local, free)
- **deep_think**: `deepseek/deepseek-r1-0528` via OpenRouter (cloud, paid)

Config location: `tradingagents/default_config.py` — per-tier `_llm_provider` and `_backend_url` keys.

## Consequences & Constraints

- Each LLM tier (`quick_think`, `mid_think`, `deep_think`) can have its own provider and backend URL.
- Per-tier values fall back to top-level `llm_provider` and `backend_url` when set to `None`.
- Ollama must be accessible at the configured `backend_url`; never hardcode `localhost:11434`.

## Actionable Rules

1. **Never hardcode Ollama URLs.** Always use the configured `base_url` from config. See Mistake #4.
2. **Top-level `llm_provider` and `backend_url` must always exist** in `DEFAULT_CONFIG` as fallback keys for per-tier overrides. See Decision 0008 and Mistake #9.
3. **Per-tier config keys follow the pattern** `{tier}_llm_provider`, `{tier}_backend_url`, `{tier}_llm` (e.g., `deep_think_llm_provider`).
