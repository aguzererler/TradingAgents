import asyncio
import time
import json
from typing import Dict, Any, AsyncGenerator, List
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.graph.scanner_graph import ScannerGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.json_utils import extract_json
from tradingagents.report_paths import get_market_dir, get_ticker_dir

class LangGraphEngine:
    """Orchestrates LangGraph pipeline executions and streams events."""
    
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        # Per-run tracking: llm_run_id -> { start_time, model, node_id, ... }
        self._llm_runs: Dict[str, Dict[str, Any]] = {}
        # Per-execution node ordering
        self._node_counter: int = 0
        # Track the last emitted node_id for edge chaining
        self._last_node_id: str = "start"
        # Track per-graph-node the last emitted node_id
        self._graph_node_last_id: Dict[str, str] = {}

    def _reset_run_state(self):
        """Reset per-execution state."""
        self._llm_runs = {}
        self._node_counter = 0
        self._last_node_id = "start"
        self._graph_node_last_id = {}

    def _next_node_id(self, base_name: str) -> str:
        """Generate a unique, sequential node ID."""
        self._node_counter += 1
        return f"{base_name}_{self._node_counter}"

    def _save_events(self, run_id: str, run_type: str, events: List[Dict[str, Any]]):
        """Save livestream events to a dedicated folder."""
        import json
        from pathlib import Path
        events_dir = Path("reports/events")
        events_dir.mkdir(parents=True, exist_ok=True)
        (events_dir / f"{run_type}_{run_id}.json").write_text(json.dumps(events, indent=2))

    def _save_scan_reports(self, date: str, final_state: Dict[str, Any]):
        """Save scan outputs to disk matching cli/main.py behavior."""
        import json
        save_dir = get_market_dir(date)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        for key in [
            "geopolitical_report",
            "market_movers_report",
            "sector_performance_report",
            "industry_deep_dive_report",
            "macro_scan_summary",
        ]:
            content = final_state.get(key, "")
            if content:
                (save_dir / f"{key}.md").write_text(content)
                
        summary = final_state.get("macro_scan_summary", "")
        if summary:
            try:
                summary_data = extract_json(summary)
                (save_dir / "scan_summary.json").write_text(
                    json.dumps(summary_data, indent=2)
                )
            except Exception:
                pass

    async def run_scan(self, run_id: str, params: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Run the 3-phase macro scanner and stream events."""
        self._reset_run_state()
        date = params.get("date", time.strftime("%Y-%m-%d"))
        
        scanner = ScannerGraph(config=self.config)
        
        print(f"Engine: Starting SCAN {run_id} for date {date}")
        
        initial_state = {
            "scan_date": date,
            "messages": [],
            "geopolitical_report": "",
            "market_movers_report": "",
            "sector_performance_report": "",
            "industry_deep_dive_report": "",
            "macro_scan_summary": "",
            "sender": "",
        }

        events_log = []
        async for event in scanner.graph.astream_events(initial_state, version="v2"):
            mapped_event = self._map_langgraph_event(event)
            if mapped_event:
                events_log.append(mapped_event)
                yield mapped_event
                
            if event.get("event") == "on_chain_end" and event.get("name") == "LangGraph":
                final_state = event.get("data", {}).get("output")
                if isinstance(final_state, dict):
                    self._save_scan_reports(date, final_state)
                    
        self._save_events(run_id, "scan", events_log)

    async def run_pipeline(self, run_id: str, params: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Run per-ticker analysis pipeline and stream events."""
        self._reset_run_state()
        ticker = params.get("ticker", "AAPL")
        date = params.get("date", time.strftime("%Y-%m-%d"))
        analysts = params.get("analysts", ["market", "news", "fundamentals"])
        
        print(f"Engine: Starting PIPELINE {run_id} for {ticker} on {date}")
        
        graph_wrapper = TradingAgentsGraph(
            selected_analysts=analysts,
            config=self.config,
            debug=True
        )
        
        initial_state = graph_wrapper.propagator.create_initial_state(ticker, date)
        
        events_log = []
        async for event in graph_wrapper.graph.astream_events(initial_state, version="v2"):
            mapped_event = self._map_langgraph_event(event)
            if mapped_event:
                events_log.append(mapped_event)
                yield mapped_event
                
            if event.get("event") == "on_chain_end" and event.get("name") == "LangGraph":
                final_state = event.get("data", {}).get("output")
                if isinstance(final_state, dict):
                    from cli.main import save_report_to_disk
                    from tradingagents.report_paths import get_ticker_dir
                    save_path = get_ticker_dir(date, ticker)
                    try:
                        save_report_to_disk(final_state, ticker, save_path)
                    except Exception as e:
                        print(f"Engine: Error saving pipeline reports: {e}")
                        
        self._save_events(run_id, "pipeline", events_log)

    async def run_portfolio(self, run_id: str, params: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Run the portfolio management workflow and stream events."""
        print(f"Engine: Starting PORTFOLIO {run_id}")
        yield {
            "id": run_id,
            "type": "system",
            "agent": "SYSTEM",
            "message": "Portfolio workflow streaming not yet implemented.",
        }

    async def run_auto(self, run_id: str, params: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Run the full auto (scan → filter → portfolio) workflow and stream events."""
        print(f"Engine: Starting AUTO {run_id}")
        yield {
            "id": run_id,
            "type": "system",
            "agent": "SYSTEM",
            "message": "Auto workflow streaming not yet implemented.",
        }

    def _extract_graph_node_name(self, event: Dict[str, Any]) -> str:
        """Extract human-readable graph node name from a LangGraph v2 event."""
        metadata = event.get("metadata", {})
        lg_node = metadata.get("langgraph_node")
        if lg_node:
            return lg_node
        
        tags = event.get("tags", [])
        for tag in tags:
            if tag.startswith("graph:node:"):
                return tag.split(":", 2)[-1]
        
        return event.get("name", "unknown")

    def _extract_model_name(self, event_data: Dict[str, Any]) -> str:
        """Extract model name from on_chat_model_start event data."""
        invocation_params = event_data.get("invocation_params", {})
        model = (
            invocation_params.get("model")
            or invocation_params.get("model_name")
            or invocation_params.get("model_id")
            or "unknown"
        )
        return str(model).strip()

    def _extract_request_summary(self, event_data: Dict[str, Any]) -> str:
        """Extract a summary of the LLM request input for the detail view."""
        try:
            messages = event_data.get("messages", [])
            if not messages:
                return ""
            # messages can be a list of lists or list of message objects
            parts = []
            msg_list = messages[0] if messages and isinstance(messages[0], list) else messages
            for msg in msg_list[:5]:  # First 5 messages max
                if hasattr(msg, "content"):
                    role = getattr(msg, "type", "unknown")
                    content = str(msg.content)[:500]
                    parts.append(f"[{role}]: {content}")
                elif isinstance(msg, dict):
                    role = msg.get("role", "unknown")
                    content = str(msg.get("content", ""))[:500]
                    parts.append(f"[{role}]: {content}")
            return "\n\n".join(parts)[:3000]
        except Exception:
            return ""

    def _map_langgraph_event(self, event: Dict[str, Any]) -> Dict[str, Any] | None:
        """Map LangGraph v2 events to AgentOS frontend contract."""
        kind = event["event"]
        graph_node = self._extract_graph_node_name(event)
        
        # ── on_chat_model_start ──
        if kind == "on_chat_model_start":
            llm_run_id = event["run_id"]
            start_time = time.time()
            
            data = event.get("data", {})
            model = self._extract_model_name(data)
            request_summary = self._extract_request_summary(data)
            
            node_id = self._next_node_id(graph_node)
            parent_id = self._graph_node_last_id.get(graph_node, self._last_node_id)
            
            self._llm_runs[llm_run_id] = {
                "start_time": start_time,
                "model": model,
                "node_id": node_id,
                "graph_node": graph_node,
                "request_summary": request_summary,
            }
            
            self._last_node_id = node_id
            self._graph_node_last_id[graph_node] = node_id
            
            agent_label = graph_node.replace("_", " ").upper()
            
            return {
                "id": llm_run_id,
                "node_id": node_id,
                "parent_node_id": parent_id,
                "type": "thought",
                "agent": agent_label,
                "message": "Thinking...",
                "metrics": {
                    "model": model,
                    "latency_ms": 0,
                },
                "details": {
                    "request_content": request_summary,
                    "response_content": "",
                    "model_used": model,
                    "latency_ms": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                },
            }
        
        # ── on_tool_start ──
        elif kind == "on_tool_start":
            tool_name = event.get("name", "tool")
            node_id = self._next_node_id(f"tool_{tool_name}")
            parent_id = self._graph_node_last_id.get(graph_node, self._last_node_id)
            
            # Try to get input from tool call
            tool_input = ""
            try:
                inp = event.get("data", {}).get("input", {})
                if inp:
                    tool_input = json.dumps(inp, indent=2, default=str)[:2000]
            except Exception:
                pass
            
            self._last_node_id = node_id
            self._graph_node_last_id[graph_node] = node_id
            
            agent_label = graph_node.replace("_", " ").upper()
            
            return {
                "id": event["run_id"],
                "node_id": node_id,
                "parent_node_id": parent_id,
                "type": "tool",
                "agent": agent_label,
                "message": f"> Tool Call: {tool_name}",
                "metrics": {},
                "details": {
                    "request_content": tool_input,
                    "response_content": "",
                    "model_used": "",
                    "latency_ms": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                },
            }
            
        # ── on_chat_model_end ──
        elif kind == "on_chat_model_end":
            llm_run_id = event["run_id"]
            start_info = self._llm_runs.pop(llm_run_id, {})
            start_time = start_info.get("start_time", time.time())
            latency_ms = int((time.time() - start_time) * 1000)
            
            node_id = self._next_node_id(graph_node)
            thought_node_id = start_info.get("node_id", self._last_node_id)
            
            output = event.get("data", {}).get("output")
            usage = {}
            model = start_info.get("model", "unknown")
            raw_content = ""
            request_summary = start_info.get("request_summary", "")
            
            is_tool_call = False
            if hasattr(output, "tool_calls") and output.tool_calls:
                is_tool_call = True
                
            msg_text = "Using tools..." if is_tool_call else "Response generated."
            
            if hasattr(output, "usage_metadata") and output.usage_metadata:
                usage = output.usage_metadata
            if hasattr(output, "response_metadata") and output.response_metadata:
                resp_meta = output.response_metadata
                # Only override model if response has a clean, distinct value
                resp_model = resp_meta.get("model_name") or resp_meta.get("model")
                if resp_model and isinstance(resp_model, str):
                    resp_model = resp_model.strip()
                    # Avoid duplicated model names (some providers concatenate)
                    if resp_model and resp_model != model:
                        model = resp_model
                
                # Also try to get token usage from response_metadata
                # Some providers put it under "token_usage" or "usage"
                if not usage:
                    token_usage = resp_meta.get("token_usage") or resp_meta.get("usage", {})
                    if token_usage:
                        usage = {
                            "input_tokens": token_usage.get("prompt_tokens", 0) or token_usage.get("input_tokens", 0),
                            "output_tokens": token_usage.get("completion_tokens", 0) or token_usage.get("output_tokens", 0),
                        }

            if hasattr(output, "content") and output.content:
                import re
                full_content = str(output.content)
                # Parse out <think> tags (often huge for DeepSeek R1) so they don't truncate the actual answer
                cleaned_content = re.sub(r'<think>.*?</think>', '', full_content, flags=re.DOTALL).strip()
                raw_content = cleaned_content[:3000]
            
            tokens_in = usage.get("input_tokens", 0) or 0
            tokens_out = usage.get("output_tokens", 0) or 0
            
            self._last_node_id = node_id
            self._graph_node_last_id[graph_node] = node_id
            
            agent_label = graph_node.replace("_", " ").upper()
            
            return {
                "id": f"{llm_run_id}_end",
                "node_id": node_id,
                "parent_node_id": thought_node_id,
                "type": "result",
                "agent": agent_label,
                "message": msg_text,
                "metrics": {
                    "model": model,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                    "latency_ms": latency_ms,
                },
                "details": {
                    "request_content": request_summary,
                    "response_content": raw_content,
                    "model_used": model,
                    "latency_ms": latency_ms,
                    "input_tokens": tokens_in,
                    "output_tokens": tokens_out,
                    "is_tool_call": is_tool_call,
                },
            }
            
        # ── on_tool_end ──
        elif kind == "on_tool_end":
            node_id = self._next_node_id(f"{graph_node}_tool_result")
            parent_id = self._graph_node_last_id.get(graph_node, self._last_node_id)
            
            output = event.get("data", {}).get("output")
            content = str(output)[:3000] if output else "Tool execution completed."
            
            self._last_node_id = node_id
            self._graph_node_last_id[graph_node] = node_id
            
            agent_label = graph_node.replace("_", " ").upper()
            
            return {
                "id": f"{event['run_id']}_end",
                "node_id": node_id,
                "parent_node_id": parent_id,
                "type": "result",
                "agent": agent_label,
                "message": "Tool execution completed.",
                "metrics": {
                    "model": "tool_execution",
                    "latency_ms": 0,
                },
                "details": {
                    "request_content": "",
                    "response_content": content,
                    "model_used": "Tool",
                    "latency_ms": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                },
            }
            
        # ── on_chain_error ──
        elif kind == "on_chain_error":
            node_id = self._next_node_id(f"{graph_node}_error")
            parent_id = self._graph_node_last_id.get(graph_node, self._last_node_id)
            
            err = event.get("data", {}).get("error")
            content = str(err) if err else "An unknown error occurred."
            
            self._last_node_id = node_id
            self._graph_node_last_id[graph_node] = node_id
            
            return {
                "id": f"{event['run_id']}_err",
                "node_id": node_id,
                "parent_node_id": parent_id,
                "type": "system",
                "agent": "SYSTEM",
                "message": f"Error: {content[:200]}",
                "details": {
                    "request_content": "",
                    "response_content": content,
                    "model_used": "System",
                    "latency_ms": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                },
            }
            
        return None
