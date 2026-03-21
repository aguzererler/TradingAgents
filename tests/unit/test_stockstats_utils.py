import pandas as pd
import numpy as np
import pytest
from tradingagents.dataflows.stockstats_utils import _clean_dataframe

def test_clean_dataframe_happy_path():
    df = pd.DataFrame({
        "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "Open": [10.0, 11.0, 12.0],
        "High": [10.5, 11.5, 12.5],
        "Low": [9.5, 10.5, 11.5],
        "Close": [10.2, 11.2, 12.2],
        "Volume": [100, 200, 300]
    })

    cleaned = _clean_dataframe(df)

    assert len(cleaned) == 3
    assert pd.api.types.is_datetime64_any_dtype(cleaned["date"])
    assert list(cleaned["close"]) == [10.2, 11.2, 12.2]
    # Check that columns are lowercase
    assert all(c.islower() for c in cleaned.columns)

def test_clean_dataframe_mixed_case_columns():
    df = pd.DataFrame({
        "DaTe": ["2023-01-01"],
        "oPeN": [10.0],
        "HIGH": [11.0],
        "low": [9.0],
        "ClOsE": [10.5],
        "VoLuMe": [100]
    })

    cleaned = _clean_dataframe(df)

    # Assert all columns are lowercase
    assert all(c.islower() for c in cleaned.columns)
    assert "date" in cleaned.columns
    assert "close" in cleaned.columns
    assert list(cleaned["close"]) == [10.5]


def test_clean_dataframe_drops_invalid_dates():
    df = pd.DataFrame({
        "Date": ["2023-01-01", "invalid_date", "2023-01-03"],
        "Close": [10.0, 11.0, 12.0]
    })

    cleaned = _clean_dataframe(df)

    assert len(cleaned) == 2
    assert cleaned["date"].dt.strftime("%Y-%m-%d").tolist() == ["2023-01-01", "2023-01-03"]
    assert cleaned["close"].tolist() == [10.0, 12.0]


def test_clean_dataframe_drops_missing_close():
    df = pd.DataFrame({
        "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "Close": [10.0, "invalid_close", 12.0]
    })

    cleaned = _clean_dataframe(df)

    assert len(cleaned) == 2
    assert cleaned["close"].tolist() == [10.0, 12.0]


def test_clean_dataframe_fills_price_gaps():
    df = pd.DataFrame({
        "Date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        "Open": [10.0, np.nan, np.nan, 13.0],
        "Close": [10.0, 11.0, 12.0, 13.0]
    })

    cleaned = _clean_dataframe(df)

    # ffill should fill open for 01-02 and 01-03 with 10.0
    assert cleaned["open"].tolist() == [10.0, 10.0, 10.0, 13.0]


def test_clean_dataframe_backward_fills_price_gaps():
    df = pd.DataFrame({
        "Date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        "Open": [np.nan, np.nan, 12.0, 13.0],
        "Close": [10.0, 11.0, 12.0, 13.0]
    })

    cleaned = _clean_dataframe(df)

    # bfill should fill open for 01-01 and 01-02 with 12.0
    assert cleaned["open"].tolist() == [12.0, 12.0, 12.0, 13.0]
