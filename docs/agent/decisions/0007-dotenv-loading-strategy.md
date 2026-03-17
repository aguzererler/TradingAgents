---
title: .env Loading Strategy
date: 2026-03-17
status: superseded
superseded_by: ADR-0008
tags: [configuration, dotenv, environment]
---

# ADR-0007: .env Loading Strategy

## Context

`load_dotenv()` loads from CWD. When running from a git worktree, the worktree `.env` may have placeholder values while the main repo `.env` has real keys.

## Decision

`cli/main.py` calls `load_dotenv()` (CWD) then `load_dotenv(Path(__file__).parent.parent / ".env")` as fallback. The worktree `.env` was also updated with real API keys.

**Note**: Decision 0008 moves `load_dotenv()` into `default_config.py` itself, making it import-order-independent. The CLI-level `load_dotenv()` in `main.py` is now defense-in-depth only.

## Consequences & Constraints

- **Superseded**: This decision is superseded by ADR-0008, which provides a more robust approach.
- `.env` loading now happens at module level in `default_config.py` before `DEFAULT_CONFIG` is evaluated.

## Actionable Rules

1. **See ADR-0008 for current `.env` loading rules.**
2. **When debugging auth errors**, check `os.environ.get('KEY')` to see what value is actually loaded. Do not assume which `.env` file is being used. See Mistake #8.
