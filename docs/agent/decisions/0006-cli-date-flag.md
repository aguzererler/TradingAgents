---
title: CLI --date Flag for Scanner
date: 2026-03-17
status: implemented
tags: [cli, scanner, automation]
---

# ADR-0006: CLI --date Flag for Scanner

## Context

`python -m cli.main scan` was interactive-only (prompts for date). Needed non-interactive invocation for testing and automation.

## Decision

Added `--date` / `-d` option to the `scan` command. Falls back to interactive prompt if not provided.

**File**: `cli/main.py`

## Consequences & Constraints

- The `--date` flag accepts `YYYY-MM-DD` format.
- When omitted, the CLI prompts interactively for a date.
- Automated scripts and CI can use `--date` for non-interactive runs.

## Actionable Rules

1. **New CLI commands that require dates** should follow the same pattern: optional `--date` flag with interactive fallback.
2. **Use `python -m cli.main scan --date YYYY-MM-DD`** for non-interactive scanner invocation.
