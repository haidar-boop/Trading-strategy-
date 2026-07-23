"""Shared fixtures / synthetic-data builders for the Coil-Break tests."""
from __future__ import annotations

import numpy as np
import pandas as pd

from phase2.coilbt.data.loader import SymbolData

MS_PER_DAY = 86_400_000


def make_symbol_data(closes: list[float], symbol: str = "TESTUSDT",
                     start_ms: int = 1_600_000_000_000 - (1_600_000_000_000 % MS_PER_DAY),
                     oi: list[float] | None = None, funding_rate: float = 0.0001,
                     high_mult: float = 1.01, low_mult: float = 0.99,
                     minute_path: bool = True) -> SymbolData:
    """Build a SymbolData from a list of daily closes.

    Each day's high/low are close*mult (unless overridden). Minute bars are a simple
    per-day path (open=prev close, then linear to close) so the engine has data.
    """
    n = len(closes)
    day_ms = np.array([start_ms + i * MS_PER_DAY for i in range(n)], dtype="int64")
    closes = np.asarray(closes, dtype=float)
    opens = np.concatenate([[closes[0]], closes[:-1]])
    highs = np.maximum(opens, closes) * high_mult
    lows = np.minimum(opens, closes) * low_mult

    daily = pd.DataFrame({
        "open": opens, "high": highs, "low": lows, "close": closes,
        "volume": np.full(n, 1000.0),
        "quote_volume": np.full(n, 5_000_000.0),      # >> liquidity floor
        "med_1m_dollar_vol": np.full(n, 2_000_000.0),
        "n_minutes": np.full(n, 1440),
        "day_ms": day_ms,
        "decision_ms": day_ms + MS_PER_DAY,
    }, index=pd.to_datetime(day_ms, unit="ms", utc=True))
    daily.index.name = "day"

    # minute bars: one 00:00 bar per day at the day's open (enough for entry fills),
    # plus a full 1440 grid if requested (for engine hold resolution).
    if minute_path:
        rows = []
        for i in range(n):
            base = day_ms[i]
            o, h, l, c = opens[i], highs[i], lows[i], closes[i]
            for minute in range(1440):
                frac = minute / 1439.0
                px = o + (c - o) * frac
                rows.append((base + minute * 60_000, px, max(px, h if minute == 720 else px),
                             min(px, l if minute == 720 else px), px))
        minute = pd.DataFrame(rows, columns=["open_time_ms", "open", "high", "low", "close"])
    else:
        minute = pd.DataFrame({
            "open_time_ms": day_ms, "open": opens, "high": highs, "low": lows, "close": closes})

    # funding: 3 settlements/day at 00:00/08:00/16:00
    fts = []
    for i in range(n):
        for h8 in (0, 8, 16):
            fts.append(day_ms[i] + h8 * 3_600_000)
    funding = pd.DataFrame({
        "calc_time": np.array(fts, dtype="int64"),
        "funding_interval_hours": np.full(len(fts), 8),
        "last_funding_rate": np.full(len(fts), funding_rate),
    })

    if oi is None:
        oi = list(np.linspace(1000, 1000 + n, n))  # gently rising OI
    oi_arr = np.asarray(oi, dtype=float)
    oi_daily = pd.DataFrame({"oi_level": oi_arr, "delta_oi": np.concatenate([[np.nan], np.diff(oi_arr)])},
                            index=daily.index)

    return SymbolData(symbol=symbol, daily=daily, minute=minute, funding=funding, oi_daily=oi_daily)
