import json
import logging
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from langchain_core.messages import HumanMessage
from tradingagents.agents.utils.json_utils import extract_json
from tradingagents.report_paths import get_market_dir
from tradingagents.portfolio.report_store import ReportStore
from tradingagents.dataflows.peer_comparison import _safe_pct
from tradingagents.dataflows.finnhub import get_company_news

logger = logging.getLogger(__name__)

def load_scan_candidates(scan_date: str) -> list[dict]:
    """Read macro_scan_summary.md for scan_date, extract stocks_to_investigate.
    Falls back to report_store.load_scan() if .md absent."""
    try:
        scan_dir = get_market_dir(scan_date)
        summary_path = scan_dir / "macro_scan_summary.md"
        if summary_path.exists():
            content = summary_path.read_text(encoding="utf-8")
            data = extract_json(content)
            if isinstance(data, dict) and "stocks_to_investigate" in data:
                return data["stocks_to_investigate"]
    except Exception as e:
        logger.warning(f"Error reading macro_scan_summary.md for {scan_date}: {e}")

    try:
        store = ReportStore()
        scan_data = store.load_scan(scan_date)
        if scan_data and isinstance(scan_data, dict) and "stocks_to_investigate" in scan_data:
            return scan_data["stocks_to_investigate"]
    except Exception as e:
        logger.warning(f"Error loading scan from ReportStore for {scan_date}: {e}")

    return []

def fetch_price_data(ticker: str, start_date: str, end_date: str) -> tuple[float | None, float | None, float | None, float | None, list[str]]:
    """Download [ticker, SPY] via yf.download().
    Returns (stock_pct, spy_pct, mfe_pct, mae_pct, top_move_dates).
    - mfe_pct: Maximum Favorable Excursion (peak return vs entry)
    - mae_pct: Maximum Adverse Excursion (worst drawdown from entry)
    - top_move_dates: up to 3 dates with largest single-day absolute price moves
    Returns (None, None, None, None, []) if < 2 trading days or download fails.
    """
    try:
        hist = yf.download(
            [ticker, "SPY"],
            start=start_date,
            end=end_date,
            auto_adjust=True,
            progress=False
        )
        if hist.empty or len(hist) < 2:
            return None, None, None, None, []

        if isinstance(hist.columns, pd.MultiIndex):
            closes = hist["Close"]
        else:
            closes = hist

        if ticker not in closes.columns or "SPY" not in closes.columns:
             return None, None, None, None, []

        stock_closes = closes[ticker].dropna()
        spy_closes = closes["SPY"].dropna()

        if len(stock_closes) < 2 or len(spy_closes) < 2:
            return None, None, None, None, []

        # Terminal returns
        stock_pct = _safe_pct(stock_closes, len(stock_closes) - 1)
        spy_pct = _safe_pct(spy_closes, len(spy_closes) - 1)

        # MFE / MAE
        entry_price = stock_closes.iloc[0]
        if entry_price == 0:
            return None, None, None, None, []

        peak_price = stock_closes.max()
        worst_price = stock_closes.min()

        mfe_pct = (peak_price - entry_price) / entry_price * 100
        mae_pct = (worst_price - entry_price) / entry_price * 100

        # Top move dates
        stock_returns = stock_closes.pct_change().dropna()
        abs_returns = stock_returns.abs()
        top_moves = abs_returns.nlargest(3)
        top_move_dates = [d.strftime("%Y-%m-%d") for d in top_moves.index]

        return stock_pct, spy_pct, mfe_pct, mae_pct, top_move_dates

    except Exception as e:
        logger.warning(f"Error fetching price data for {ticker}: {e}")
        return None, None, None, None, []

def fetch_news_summary(ticker: str, start_date: str, end_date: str, top_move_dates: list[str], n: int = 5) -> str:
    """Fetch n headlines, weighted toward largest-move dates.
    Strategy: 2 headlines from window start (initial catalyst context),
    3 headlines from dates nearest top_move_dates (outcome context).
    Returns bullet-list string."""
    from datetime import datetime
    import re

    headlines = []

    # 1. Fetch 2 headlines from the start of the window
    try:
        start_news_md = get_company_news(ticker, start_date, start_date)
        # Assuming get_company_news returns markdown list, extract lines starting with -
        if start_news_md:
            start_lines = [line for line in start_news_md.split('\n') if line.strip().startswith('-')]
            headlines.extend(start_lines[:2])
    except Exception as e:
        logger.warning(f"Failed to fetch start news for {ticker}: {e}")

    # 2. Fetch 3 headlines from top move dates
    try:
        top_news_lines = []
        for date_str in top_move_dates:
            news_md = get_company_news(ticker, date_str, date_str)
            if news_md:
                lines = [line for line in news_md.split('\n') if line.strip().startswith('-')]
                if lines:
                    top_news_lines.append(lines[0]) # Get best headline for each top move date

        headlines.extend(top_news_lines[:3])
    except Exception as e:
        logger.warning(f"Failed to fetch top move news for {ticker}: {e}")

    if not headlines:
        return "No specific headlines found."

    return "\n".join(headlines)

def generate_lesson(llm, candidate: dict, stock_pct: float | None,
                    spy_pct: float | None, mfe_pct: float | None,
                    mae_pct: float | None, news_summary: str,
                    horizon_days: int) -> dict | None:
    """Invoke quick_think LLM, parse JSON via extract_json(), return lesson dict.
    Returns None on parse failure (logs warning)."""
    if stock_pct is None or spy_pct is None:
        return None

    alpha = stock_pct - spy_pct

    prompt = f"""STOCK SELECTION REVIEW
======================
Ticker:       {candidate.get('ticker')} | Sector: {candidate.get('sector')}
Original thesis: {candidate.get('thesis_angle')} — {candidate.get('rationale')}
Conviction:   {candidate.get('conviction')}
{horizon_days}-day window: scan_date → reflect_date

PERFORMANCE vs SPY
------------------
Terminal return: {candidate.get('ticker')}: {stock_pct:+.1f}% | SPY: {spy_pct:+.1f}% | Alpha: {alpha:+.1f}%
Peak return (MFE): {mfe_pct:+.1f}% (best point in the window)
Max drawdown (MAE): {mae_pct:+.1f}% (worst point in the window)

TOP HEADLINES (initial + largest-move days)
--------------------------------------------
{news_summary}

Return ONLY a JSON object with keys:
  "situation"  — 1-2 sentences describing the stock pattern/thesis type as a search key
                 (include sector, thesis type, key risk factors)
  "advice"     — 1 sentence lesson. Consider MFE/MAE: if MFE >> terminal return,
                 the entry was sound but timing/exit mattered more than selection.
                   terminal alpha < -5%  + thesis wrong → "Avoid stocks where..."
                   terminal alpha < -5%  + unpredictable shock → "Macro shock risk in..."
                   mfe > +10% but terminal alpha < 0% → "Momentum thesis valid but requires..."
                   alpha > +5%  → "Thesis confirmed:"
                   else         → "Neutral outcome:"
  "sentiment"  — "negative" | "positive" | "neutral"
"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        data = extract_json(response.content if hasattr(response, 'content') else response)

        if not data or not isinstance(data, dict):
            logger.warning(f"LLM response parse failure: {response}")
            return None

        # Verify required keys
        if not all(k in data for k in ["situation", "advice", "sentiment"]):
            logger.warning(f"LLM response missing required keys: {data}")
            return None

        return data
    except Exception as e:
        logger.warning(f"Error generating lesson: {e}")
        return None

def reflect_on_scan(scan_date: str, reflect_date: str, llm, horizon_days: int) -> list[dict]:
    """Top-level: load candidates, fetch data, generate lessons, return list."""
    candidates = load_scan_candidates(scan_date)
    lessons = []

    for cand in candidates:
        ticker = cand.get("ticker")
        if not ticker:
            continue

        stock_pct, spy_pct, mfe_pct, mae_pct, top_move_dates = fetch_price_data(ticker, scan_date, reflect_date)
        if stock_pct is None:
            continue

        news_summary = fetch_news_summary(ticker, scan_date, reflect_date, top_move_dates)

        lesson_data = generate_lesson(
            llm=llm,
            candidate=cand,
            stock_pct=stock_pct,
            spy_pct=spy_pct,
            mfe_pct=mfe_pct,
            mae_pct=mae_pct,
            news_summary=news_summary,
            horizon_days=horizon_days
        )

        if lesson_data:
            alpha = stock_pct - spy_pct
            lesson = {
                "ticker": ticker,
                "scan_date": scan_date,
                "reflect_date": reflect_date,
                "horizon_days": horizon_days,
                "stock_return_pct": round(stock_pct, 2),
                "spy_return_pct": round(spy_pct, 2),
                "alpha_pct": round(alpha, 2),
                "news_summary": news_summary,
                "situation": lesson_data["situation"],
                "advice": lesson_data["advice"],
                "sentiment": lesson_data["sentiment"],
                "created_at": datetime.now().isoformat()
            }
            lessons.append(lesson)

    return lessons
