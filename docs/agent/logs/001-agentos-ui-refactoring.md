# Log 001: AgentOS UI Refactoring & DeepSeek R1 Truncation

## Date: 2026-03-23

## Context & Problem
We were receiving feedback that some AgentOS dashboard runs (particularly macro scans) were "finishing early" and "only displaying Chinese text with Java tags." The progress bar for nodes like `GEOPOLITICAL_SCANNER` was halting at bizarre intervals, and the actual pipeline tools seemingly returning `0` output tokens. 

## Investigation
- **Mistake 1 (Frontend Node State):** The React `AgentGraph.tsx` inferred `status='completed'` strictly if a child node appeared. If a thought produced a `tool` call, it was incorrectly assumed the thought was "completed." We refined the logic so that an agent's graph node stays in the `running` (animating) state until a **final response** (a `result` without `is_tool_call: true`) is natively emitted by the backend.
- **Mistake 2 (DeepSeek Tag Truncation):** DeepSeek R1 models hosted on OpenRouter output `<think>...</think>` parameter blocks before writing their response. These blocks often contain 4,000–8,000 characters of reasoning (frequently in Chinese). Our `langgraph_engine.py` had a safety limit: `raw_content = str(output.content)[:3000]`. This drastically backfired: the 3,000 character limit exclusively captured the *start* of the Chinese thinking block, completely severing the actual English answer that followed!

## Solution & Learnings
1. **Always Regex-Strip Model Reasoning Tags Before Truncating**: We implemented `re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)` in the backend. This gracefully removes the reasoning block from the UI stream payload, safely allowing the actual localized answer to fit within the 3k character slice.
2. **Persistence Must Match CLI Parity**: Streaming endpoints are visually impressive, but they completely bypassed the local `reports/daily/{date}` disk writes that the pipeline requires downstream. We resolved this by explicitly appending `on_chain_end` intercepts to the `astream_events` generators, triggering `save_report_to_disk` and `_save_events`. 
