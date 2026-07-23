"""
FEF decision-table construction. One row per 8h funding settlement (decision time),
with everything the entry rule and filters need — all STRICTLY CAUSAL (known at the
settlement timestamp t):

  f_now   : realized funding rate settled at t (interval ENDING at t)
  pct     : percentile rank of f_now within the trailing 365d of funding prints
  d_oi    : OI(t) - OI(t-24h)   (both sampled as the last 5m obs <= their timestamp)
  oi_z    : z-score of d_oi vs the trailing 90d distribution of 24h OI changes
  atr     : Wilder ATR(14) on 4h bars, the bar ending at/ before t
  entry_open_px, next_open_ms : fill = open of the 1m bar starting at t
  filters : ok_liq / ok_vol_hi / ok_vol_lo / ok_mech / ok_event

Signal (applied per variant on top of this table):
  SHORT if pct >= ENTRY_PCT and oi_z >= OI_Z_MIN         (crowd long; short receives funding)
  LONG  if pct <= 100-ENTRY_PCT and oi_z >= OI_Z_MIN     (symmetric variant only)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config_fef import ConstantsFEF, FiltersFEF
from .data.loader import SymbolData
from .events import event_timestamps_ms
from .strategy import wilder_atr

MS_PER_DAY = 86_400_000
MS_PER_HOUR = 3_600_000
MS_PER_MIN = 60_000


def aggregate_bars(minute: pd.DataFrame, hours: int) -> pd.DataFrame:
    step = hours * MS_PER_HOUR
    m = minute.copy()
    m["bar_ms"] = (m["open_time_ms"] // step) * step
    grp = m.groupby("bar_ms", sort=True)
    bars = pd.DataFrame({
        "open": grp["open"].first(), "high": grp["high"].max(),
        "low": grp["low"].min(), "close": grp["close"].last(),
    })
    bars.index = pd.to_datetime(bars.index.to_numpy(dtype="int64"), unit="ms", utc=True)
    return bars


def _rolling_pct_rank(values: np.ndarray, times_ms: np.ndarray, window_days: int,
                      min_history: int) -> np.ndarray:
    """pct[i] = 100 * fraction of trailing-window prints (<= t_i) that are <= values[i]."""
    win = window_days * MS_PER_DAY
    n = values.size
    out = np.full(n, np.nan)
    for i in range(n):
        lo = np.searchsorted(times_ms, times_ms[i] - win, side="left")
        w = values[lo : i + 1]  # causal, inclusive of i
        if w.size >= min_history:
            out[i] = 100.0 * np.mean(w <= values[i])
    return out


def _oi_at(oi_ms: np.ndarray, oi_val: np.ndarray, query_ms: np.ndarray) -> np.ndarray:
    """Last OI observation with create_time <= query_ms (causal)."""
    if oi_ms.size == 0:
        return np.full(query_ms.shape, np.nan)
    pos = np.searchsorted(oi_ms, query_ms, side="right") - 1
    return np.where(pos >= 0, oi_val[np.clip(pos, 0, oi_val.size - 1)], np.nan)


def _price_at(m_time: np.ndarray, m_open: np.ndarray, query_ms: np.ndarray) -> np.ndarray:
    """1m open at exactly query_ms if present else the last open <= query_ms (causal)."""
    pos = np.searchsorted(m_time, query_ms, side="right") - 1
    return np.where(pos >= 0, m_open[np.clip(pos, 0, m_open.size - 1)], np.nan)


def build_decision_table(sd: SymbolData, oi_5m: pd.DataFrame, consts: ConstantsFEF,
                         filters: FiltersFEF, extra_events: list[str] | None = None) -> pd.DataFrame:
    f = sd.funding.sort_values("calc_time").reset_index(drop=True)
    dt = f["calc_time"].to_numpy(dtype="int64")
    f_now = f["last_funding_rate"].to_numpy(dtype=float)
    interval = f.get("funding_interval_hours", pd.Series(8, index=f.index)).to_numpy(dtype=float)

    pct = _rolling_pct_rank(f_now, dt, consts.PCT_LOOKBACK_DAYS, consts.PCT_MIN_HISTORY)

    # 4h ATR: value of the bar ending at/ before each decision time
    bars4h = aggregate_bars(sd.minute, consts.BAR_HOURS)
    atr4h = wilder_atr(bars4h, consts.ATR_PERIOD)
    bar_ms = bars4h.index.to_numpy(dtype="int64")           # bar START ms; bar closes at start+4h
    bar_close_ms = bar_ms + consts.BAR_HOURS * MS_PER_HOUR
    atr_vals = atr4h.to_numpy(dtype=float)
    apos = np.searchsorted(bar_close_ms, dt, side="right") - 1
    atr_at_dt = np.where(apos >= 0, atr_vals[np.clip(apos, 0, atr_vals.size - 1)], np.nan)

    # OI now / 24h ago -> d_oi ; z-score over trailing 90d of 24h changes
    if oi_5m is not None and len(oi_5m):
        o = oi_5m.sort_values("create_time_ms")
        oi_ms = o["create_time_ms"].to_numpy(dtype="int64")
        oi_val = o["sum_open_interest"].to_numpy(dtype=float)
    else:
        oi_ms = np.array([], dtype="int64"); oi_val = np.array([], dtype=float)
    oi_now = _oi_at(oi_ms, oi_val, dt)
    oi_prev = _oi_at(oi_ms, oi_val, dt - consts.OI_CHANGE_HOURS * MS_PER_HOUR)
    d_oi = oi_now - oi_prev
    d_oi_s = pd.Series(d_oi, index=pd.to_datetime(dt, unit="ms", utc=True))
    roll = d_oi_s.rolling(f"{consts.OI_LOOKBACK_DAYS}D")
    oi_z = ((d_oi_s - roll.mean()) / roll.std(ddof=1)).to_numpy(dtype=float)

    # prices at decision time and 24h earlier (for the vol_hi filter + entry fill)
    m = sd.minute.sort_values("open_time_ms").reset_index(drop=True)
    m_time = m["open_time_ms"].to_numpy(dtype="int64")
    m_open = m["open"].to_numpy(dtype=float)
    px_now = _price_at(m_time, m_open, dt)
    px_24h = _price_at(m_time, m_open, dt - 24 * MS_PER_HOUR)
    ret_24h = np.abs(px_now / px_24h - 1.0)

    # entry fill = the 1m bar whose open_time == dt (the bar opening at settlement)
    fill_pos = np.searchsorted(m_time, dt, side="left")
    valid_fill = (fill_pos < m_time.size) & (m_time[np.clip(fill_pos, 0, m_time.size - 1)] == dt)
    entry_open = np.where(valid_fill, m_open[np.clip(fill_pos, 0, m_open.size - 1)], np.nan)
    next_open_ms = np.where(valid_fill, dt, -1)

    # daily-derived filters (liquidity, 30d annualized vol): use the last daily bar COMPLETED
    # by the decision time t. A bar for day X only completes at X+1 00:00 UTC (the loader's
    # decision_ms), so map t to the newest bar with day_ms + 1d <= t (NO same-day look-ahead).
    d = sd.daily
    day_ms = d["day_ms"].to_numpy(dtype="int64")
    liq_30 = d["quote_volume"].rolling(30, min_periods=30).median().to_numpy(dtype=float)
    ann_vol = (d["close"].pct_change().rolling(30, min_periods=30).std(ddof=1)
               * np.sqrt(365.0)).to_numpy(dtype=float)
    raw = np.searchsorted(day_ms + MS_PER_DAY, dt, side="right") - 1  # last COMPLETED bar
    liq_at = np.where(raw >= 0, liq_30[np.clip(raw, 0, day_ms.size - 1)], np.nan)
    vol_at = np.where(raw >= 0, ann_vol[np.clip(raw, 0, day_ms.size - 1)], np.nan)

    # event exclusion: +/- EVENT_EXCL_MINUTES around any FOMC/CPI timestamp
    ev = event_timestamps_ms(extra=extra_events).to_numpy(dtype="int64")
    win = int(filters.EVENT_EXCL_MINUTES * MS_PER_MIN)
    if ev.size:
        lo = np.searchsorted(ev, dt - win, side="left")
        hi = np.searchsorted(ev, dt + win, side="right")
        ok_event = ~(hi > lo)
    else:
        ok_event = np.ones(dt.size, dtype=bool)

    tbl = pd.DataFrame({
        "dt_ms": dt,
        "f_now": f_now,
        "pct": pct,
        "d_oi": d_oi,
        "oi_z": oi_z,
        "atr": atr_at_dt,
        "entry_open_px": entry_open,
        "next_open_ms": next_open_ms,
        "valid_fill": valid_fill,
        "px_now": px_now,
        "ret_24h": ret_24h,
        "ann_vol_30d": vol_at,
        "liq_30d": liq_at,
        "ok_liq": liq_at >= filters.LIQ_FLOOR_USD,
        "ok_vol_hi": ret_24h <= filters.VOL_HI_24H,
        "ok_vol_lo": vol_at >= filters.VOL_LO_ANN,
        "ok_mech": interval == consts.FUNDING_INTERVAL_HOURS,
        "ok_event": ok_event,
    }, index=pd.to_datetime(dt, unit="ms", utc=True))
    tbl.index.name = "decision"
    return tbl


def raw_signal(tbl: pd.DataFrame, params, side_mode: str) -> pd.Series:
    """Per-decision candidate side 'SHORT'/'LONG'/'' from the table + variant."""
    filt = (tbl["ok_liq"] & tbl["ok_vol_hi"] & tbl["ok_vol_lo"] & tbl["ok_mech"]
            & tbl["ok_event"] & tbl["valid_fill"])
    oi_ok = tbl["oi_z"] >= params.OI_Z_MIN
    short_ok = filt & oi_ok & (tbl["pct"] >= params.ENTRY_PCT)
    long_ok = filt & oi_ok & (tbl["pct"] <= (100.0 - params.ENTRY_PCT))
    if side_mode == "positive_only":
        long_ok = pd.Series(False, index=tbl.index)
    sig = pd.Series("", index=tbl.index, dtype=object)
    sig[short_ok.fillna(False)] = "SHORT"
    sig[long_ok.fillna(False) & (sig == "")] = "LONG"
    return sig
