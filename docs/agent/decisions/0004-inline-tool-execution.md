---
title: Inline Tool Execution Loop for Scanner Agents
date: 2026-03-17
status: implemented
tags: [agents, tools, scanner, langgraph]
---

# ADR-0004: Inline Tool Execution Loop for Scanner Agents

## Context

The existing trading graph uses separate `ToolNode` graph nodes for tool execution (agent → tool_node → agent routing loop). Scanner agents are simpler single-pass nodes — no ToolNode in the graph. When the LLM returned tool_calls, nobody executed them, resulting in empty reports.

## Decision

Created `tradingagents/agents/utils/tool_runner.py` with `run_tool_loop()` that runs an inline tool execution loop within each scanner agent node:
1. Invoke chain
2. If tool_calls present → execute tools → append ToolMessages → re-invoke
3. Repeat up to `MAX_TOOL_ROUNDS=5` until LLM produces text response

**Alternative considered**: Adding ToolNode + conditional routing to scanner_setup.py (like trading graph). Rejected — too complex for the fan-out/fan-in pattern and would require 4 separate tool nodes with routing logic.

**Files**: `tradingagents/agents/utils/tool_runner.py`, all scanner agent modules

## Consequences & Constraints

- Scanner agents use `run_tool_loop()` inline; trading agents use graph-level `ToolNode`.
- Two different tool execution patterns coexist in the codebase.
- `MAX_TOOL_ROUNDS` is hardcoded to 5 (TODO: make configurable).

## Actionable Rules

1. **When `bind_tools()` is used, there MUST be a tool execution path.** Either graph-level `ToolNode` routing or inline `run_tool_loop()`. See Mistake #1.
2. **New scanner agents must use `run_tool_loop()`** from `tradingagents/agents/utils/tool_runner.py`.
3. **New trading graph agents should continue using `ToolNode`** in the graph pattern.
