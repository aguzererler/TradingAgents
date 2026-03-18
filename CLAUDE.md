# TradingAgents Framework - Project Knowledge

Multi-agent LLM trading framework using LangGraph for financial analysis and decision making.

## Quick Start

```bash
conda activate tradingagents
pytest tests/ -v                           # Run tests
python -m cli.main scan --date 2026-03-17  # Run scanner
python -m cli.main analyze                 # Run per-ticker analysis
```

## Repository Memory System

All structured project knowledge lives in `docs/agent/`. Read these files at session start:

| File | Purpose | When to Update |
|------|---------|---------------|
| `docs/agent/CURRENT_STATE.md` | Live milestone, progress, blockers | Every session |
| `docs/agent/context/ARCHITECTURE.md` | System design, workflows, data flow | Per milestone |
| `docs/agent/context/CONVENTIONS.md` | Coding patterns, rules, gotchas | When patterns change |
| `docs/agent/context/COMPONENTS.md` | File map, extension points, tests | When files are added/moved |
| `docs/agent/context/TECH_STACK.md` | Dependencies, APIs, providers | When deps change |
| `docs/agent/context/GLOSSARY.md` | Term definitions, acronyms | When new concepts are added |
| `docs/agent/decisions/` | Architecture Decision Records (binding) | Append-only |
| `docs/agent/plans/` | Implementation checklists | Per task |

### Skills

| Skill | Location | Purpose |
|-------|----------|---------|
| Architecture-First Reading Protocol | `.claude/skills/architecture-coordinator/` | Enforces ADR reading before coding |
| Memory Extraction & Builder | `.claude/skills/memory-extraction/` | Defines how to extract and write memory files |

### Builder Agent

`.github/agents/memory-builder.agent.md` — Specialized agent for building/refreshing memory files.

## Critical Rules (see full details in `docs/agent/context/CONVENTIONS.md`)

- If `bind_tools()` is used → there MUST be a tool execution path
- Functions in `route_to_vendor` MUST raise on failure (not embed errors)
- Vendor fallback is opt-in only — `FALLBACK_ALLOWED` whitelist (ADR 011)
- LangGraph parallel state fields MUST have a reducer
- Never hold a lock during `sleep()` or IO
- `llm_provider` and `backend_url` must always exist at top level in config
