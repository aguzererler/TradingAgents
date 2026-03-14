"""Tests for scanner tools functionality."""
from langchain_core.tools import BaseTool


def test_scanner_tools_imports():
    """Verify that all scanner tools can be imported and are LangChain tools."""
    from tradingagents.agents.utils.scanner_tools import (
        get_market_movers,
        get_market_indices,
        get_sector_performance,
        get_industry_performance,
        get_topic_news,
    )

    assert isinstance(get_market_movers, BaseTool)
    assert isinstance(get_market_indices, BaseTool)
    assert isinstance(get_sector_performance, BaseTool)
    assert isinstance(get_industry_performance, BaseTool)
    assert isinstance(get_topic_news, BaseTool)


def test_scanner_tools_have_docstrings():
    """Verify that all scanner tools have descriptive docstrings."""
    from tradingagents.agents.utils.scanner_tools import (
        get_market_movers,
        get_market_indices,
        get_sector_performance,
        get_industry_performance,
        get_topic_news,
    )

    assert get_market_movers.__doc__ is not None
    assert get_market_indices.__doc__ is not None
    assert get_sector_performance.__doc__ is not None
    assert get_industry_performance.__doc__ is not None
    assert get_topic_news.__doc__ is not None


def test_interface_has_scanner_methods():
    """Verify the vendor interface exposes all scanner methods."""
    from tradingagents.dataflows.interface import VENDOR_METHODS, TOOLS_CATEGORIES

    scanner_methods = ["get_market_movers", "get_market_indices",
                       "get_sector_performance", "get_industry_performance",
                       "get_topic_news"]

    for method in scanner_methods:
        assert method in VENDOR_METHODS, f"{method} missing from VENDOR_METHODS"
        assert method in TOOLS_CATEGORIES["scanner_data"]["tools"], \
            f"{method} missing from TOOLS_CATEGORIES scanner_data"


if __name__ == "__main__":
    test_scanner_tools_imports()
    test_scanner_tools_have_docstrings()
    test_interface_has_scanner_methods()
    print("All scanner tool import tests passed.")
