"""
Load + align the three feeds into backtest-ready frames, with NO look-ahead.

Produces, per symbol:
  daily   : one row per UTC calendar day, OHLCV aggregated from 1m bars, plus
            decision_ms = the 00:00 UTC timestamp at which day D's *completed* bar
            is acted on (= start of D+1). All of day D's data is known by decision_ms.
  minute  : 1m OHLCV (open_time_ms, open/high/low/close) for the event-driven engine.
  funding : 8h funding prints (passed through to FundingModel).
  oi_daily: OI level sampled as the last observation with create_time <= day D's
            decision_ms (causal), and delta_oi vs the prior day. NaN where OI history
            is absent (pre-2021) -> OI filter disabled for those days.

Design choice: loader is spec-agnostic. All Coil-Break feature math (channels,
compression percentile, ATR, funding gate) lives in strategy.py so the look-ahead
guards there are auditable in one place.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from . import download

MS_PER_DAY = 86_400_000


@dataclass
class SymbolData:
    symbol: str
    daily: pd.DataFrame        # index: day (Timestamp, UTC midnight); cols below
    minute: pd.DataFrame       # open_time_ms, open, high, low, close
    funding: pd.DataFrame      # calc_time, last_funding_rate
    oi_daily: pd.DataFrame     # index: day; cols: oi_level, delta_oi (may be NaN)


def _aggregate_daily(klines: pd.DataFrame) -> pd.DataFrame:
    """1m -> daily OHLCV at UTC day boundaries. Causal: a day's bar closes at 23:59:59.999."""
    k = klines.copy()
    k["day_ms"] = (k["open_time"] // MS_PER_DAY) * MS_PER_DAY  # 00:00 UTC of the bar's day
    grp = k.groupby("day_ms", sort=True)
    daily = pd.DataFrame({
        "open": grp["open"].first(),
        "high": grp["high"].max(),
        "low": grp["low"].min(),
        "close": grp["close"].last(),
        "volume": grp["volume"].sum(),
        "quote_volume": grp["quote_volume"].sum(),
        # median of the day's 1m dollar (quote) volume -> liquidity floor/cap inputs
        "med_1m_dollar_vol": grp["quote_volume"].median(),
        "n_minutes": grp["close"].size(),
    })
    # Carry the integer ms key explicitly (robust across pandas versions; no asi8 ambiguity).
    day_ms = daily.index.to_numpy(dtype="int64")
    daily["day_ms"] = day_ms
    # decision_ms: day D is acted on at start of D+1 (00:00 UTC). Everything in D is known by then.
    daily["decision_ms"] = day_ms + MS_PER_DAY
    daily.index = pd.to_datetime(day_ms, unit="ms", utc=True)
    daily.index.name = "day"
    return daily


def _align_oi_daily(metrics: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    """OI for day D = last create_time <= end of day D (causal, no look-ahead)."""
    out = pd.DataFrame(index=daily.index, columns=["oi_level", "delta_oi"], dtype="float64")
    if metrics is None or len(metrics) == 0:
        return out
    m = metrics.sort_values("create_time_ms")
    m_ts = m["create_time_ms"].to_numpy(dtype="int64")
    m_oi = m["sum_open_interest"].to_numpy(dtype="float64")
    # end of day D = decision_ms - 1 ms; last OI observation at/ before then is known at decision.
    day_close_end = daily["day_ms"].to_numpy(dtype="int64") + MS_PER_DAY - 1
    pos = np.searchsorted(m_ts, day_close_end, side="right") - 1
    lvl = np.where(pos >= 0, m_oi[np.clip(pos, 0, len(m_oi) - 1)], np.nan)
    out["oi_level"] = lvl
    out["delta_oi"] = out["oi_level"].diff()
    return out


def load_symbol(symbol: str, start: date, end: date) -> SymbolData:
    klines = download.download_klines(symbol, start, end)
    funding = download.download_funding(symbol, start, end)
    metrics = download.download_metrics(symbol, start, end)
    if len(klines) == 0:
        raise RuntimeError(f"No klines for {symbol} in [{start}, {end}]")
    daily = _aggregate_daily(klines)
    minute = klines[["open_time", "open", "high", "low", "close"]].rename(
        columns={"open_time": "open_time_ms"}
    ).reset_index(drop=True)
    oi_daily = _align_oi_daily(metrics, daily)
    return SymbolData(symbol=symbol, daily=daily, minute=minute, funding=funding, oi_daily=oi_daily)
