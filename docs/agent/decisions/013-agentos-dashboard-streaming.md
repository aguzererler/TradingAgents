# ADR 013: AgentOS Dashboard Streaming and Disk Persistence

## Status
Accepted

## Context
The AgentOS web dashboard requires live streaming of LangGraph execution pipelines (e.g. `run_scan` and `run_pipeline`) to display a visual workflow node-graph and a live, detailed terminal. Initially, several issues degraded the user experience:
1. **Node Volatility**: Completed graph nodes would disappear from the screen because the frontend swapped them out by `node_id` without accumulating them properly.
2. **Missing Granularity**: Tool executions were completely invisible in the UI because `on_tool_end` events weren't intercepted and mapped.
3. **Ghost "Thinking" States**: The progress bar for an agent would continue to shimmer even after the agent delegated output to a tool because we were prematurely setting the node to "completed" without capturing the entire node sequence.
4. **Data Loss (Disk Persistence)**: The API streaming endpoint only sent events over the WebSocket, completely skipping the markdown and JSON file saving logic that the CLI implemented. This broke downstream pipeline compatibility.

## Decision
1. **Frontend Accumulation Model**: The `AgentGraph.tsx` component was rewritten to accumulate all incoming node events. Nodes are stacked vertically by agent (`GEOPOLITICAL_SCANNER`), and the "Thinking" state calculates completion dynamically by verifying if the backend has emitted an event belonging to the same entity devoid of tool queries.
2. **Backend Event Mapping Enrichment**: `langgraph_engine.py` was expanded to intercept `on_tool_end` and `on_chain_error` and format them as `result` and `system` events.
3. **Aligned Persistence**: We adopted the CLI's `save_report_to_disk` model within the streaming endpoint. By intercepting `on_chain_end` for the root `LangGraph` element, the API can now flawlessly mirror the CLI's behavior (writing `reports/daily` and `reports/market`), while simultaneously dumping the entire JSON-serialized event log sequence to a new `reports/events/` folder for observability.

## Consequences
- **Positive**: Complete UI parity with backend state. End-to-end execution continuity works whether triggered from Web UI or CLI.
- **Positive**: Debugging is vastly improved by the `reports/events/` JSON files which catalog exact millisecond latency, input tokens, and tool boundaries.
- **Negative**: The backend engine is somewhat tightly coupled to the LangGraph v2 internal event schema names (`on_chat_model_end`, `on_tool_end`). Any changes to LangGraph's event contract will necessitate immediate updates to `_map_langgraph_event`.
