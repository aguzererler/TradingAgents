"""Smart Money Scanner — Phase 1 parallel node.

Runs three Finviz screeners to find institutional footprints:
  1. Insider buying (open-market purchases by insiders)
  2. Unusual volume (2x+ normal, price > $10)
  3. Breakout accumulation (52-week highs on 2x+ volume)

Each screener tool has no parameters — filters are hardcoded to prevent LLM
hallucinations. Results feed into macro_synthesis for the "Golden Overlap" step.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.scanner_tools import (
    get_breakout_accumulation_stocks,
    get_insider_buying_stocks,
    get_unusual_volume_stocks,
)
from tradingagents.agents.utils.tool_runner import run_tool_loop


def create_smart_money_scanner(llm):
    def smart_money_scanner_node(state):
        scan_date = state["scan_date"]
        tools = [
            get_insider_buying_stocks,
            get_unusual_volume_stocks,
            get_breakout_accumulation_stocks,
        ]

        system_message = (
            "You are a quantitative analyst hunting for 'Smart Money' institutional footprints in today's market. "
            "You MUST call all three of these tools exactly once each:\n"
            "1. `get_insider_buying_stocks` — insider open-market purchases\n"
            "2. `get_unusual_volume_stocks` — stocks trading at 2x+ normal volume\n"
            "3. `get_breakout_accumulation_stocks` — institutional breakout accumulation pattern\n\n"
            "After running all three scans, write a concise report highlighting the best 5 to 8 specific tickers "
            "you found. For each ticker, state: which scan flagged it, its sector, and why it is anomalous "
            "(e.g., 'XYZ has heavy insider buying in a beaten-down energy sector despite macro headwinds'). "
            "If any scan returned unavailable or empty, note it briefly and focus on the remaining results. "
            "This report will be used by the Macro Strategist to identify high-conviction candidates via the "
            "Golden Overlap (bottom-up smart money signals cross-referenced with top-down macro themes)."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants.\n{system_message}"
                    "\nFor your reference, the current date is {current_date}.",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=scan_date)

        chain = prompt | llm.bind_tools(tools)
        result = run_tool_loop(chain, state["messages"], tools)
        report = result.content or ""

        return {
            "messages": [result],
            "smart_money_report": report,
            "sender": "smart_money_scanner",
        }

    return smart_money_scanner_node
