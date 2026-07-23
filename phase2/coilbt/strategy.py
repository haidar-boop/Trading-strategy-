"""
Coil-Break feature construction and entry-signal logic. Vectorized and STRICTLY
CAUSAL: every feature at day t uses only data known by t's decision time.

Look-ahead guards (from the spec, verified):
  * channel hh/ll = max/min over the PRIOR L days, EXCLUDING bar t
        hh_t = max(high[t-L .. t-1])  ->  high.rolling(L).max().shift(1)
  * compression range width uses close[t-1] as denominator (not close[t])
  * compression percentile threshold = Q_COMP-percentile of the trailing PCTL_WIN
        range widths (frozen 'linear' interpolation); requires a full window
  * funding gate uses the rate SETTLED at/ before the decision (interval ending at t)
  * OI sign uses delta-OI over the breakout day; NaN where OI history is absent
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Constants, Filters, Params, Variant
from .data.loader import SymbolData
from .events import event_timestamps_ms


def wilder_atr(daily: pd.DataFrame, n: int) -> pd.Series:
    """Wilder ATR (RMA of True Range), seeded with the SMA of the first n TRs."""
    h, l, c = daily["high"], daily["low"], daily["close"]
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    tr_v = tr.to_numpy(dtype=float)
    out = np.full(tr_v.size, np.nan)
    if tr_v.size > n:
        seed = np.nanmean(tr_v[1 : n + 1])  # tr_v[0] is NaN (shifted close)
        out[n] = seed
        prev = seed
        for i in range(n + 1, tr_v.size):
            prev = (prev * (n - 1) + tr_v[i]) / n
            out[i] = prev
    return pd.Series(out, index=daily.index, name="atr")


def _funding_at_decision(funding: pd.DataFrame, decision_ms: np.ndarray) -> np.ndarray:
    """Last realized funding rate with calc_time <= decision_ms (interval ending at t)."""
    if funding is None or len(funding) == 0:
        return np.full(decision_ms.shape, np.nan)
    f = funding.sort_values("calc_time")
    ft = f["calc_time"].to_numpy(dtype="int64")
    fr = f["last_funding_rate"].to_numpy(dtype=float)
    pos = np.searchsorted(ft, decision_ms, side="right") - 1
    return np.where(pos >= 0, fr[np.clip(pos, 0, fr.size - 1)], np.nan)


def _event_exclusion(decision_ms: np.ndarray, excl_hours: float,
                     extra_events: list[str] | None) -> np.ndarray:
    """True if an entry at decision_ms is BLOCKED (an event falls in (t, t+excl_hours])."""
    ev = event_timestamps_ms(extra=extra_events).to_numpy(dtype="int64")
    if ev.size == 0:
        return np.zeros(decision_ms.shape, dtype=bool)
    win = int(excl_hours * 3_600_000)
    # blocked if any event in (decision_ms, decision_ms + win]
    lo = np.searchsorted(ev, decision_ms, side="right")
    hi = np.searchsorted(ev, decision_ms + win, side="right")
    return hi > lo


def compute_features(sd: SymbolData, params: Params, consts: Constants,
                     filters: Filters, extra_events: list[str] | None = None) -> pd.DataFrame:
    """Daily-indexed feature frame with all inputs for the entry rule and filters."""
    d = sd.daily
    L, q, atr_n, pctl = params.L, params.Q_COMP, consts.ATR_N, consts.PCTL_WIN

    close = d["close"]
    atr = wilder_atr(d, atr_n)
    atr_pct = atr / close

    hh = d["high"].rolling(L).max().shift(1)     # max(high[t-L .. t-1]); excludes bar t
    ll = d["low"].rolling(L).min().shift(1)
    rw = (hh - ll) / close.shift(1)              # range width; denom = close[t-1]
    comp_thresh = rw.rolling(pctl, min_periods=pctl).quantile(q / 100.0, interpolation=consts.PCTL_METHOD)
    compressed = rw <= comp_thresh

    delta_oi = sd.oi_daily["delta_oi"].reindex(d.index)
    oi_up = delta_oi > 0
    oi_down = delta_oi < 0
    oi_present = delta_oi.notna()

    decision_ms = d["decision_ms"].to_numpy(dtype="int64")
    fr = _funding_at_decision(sd.funding, decision_ms)

    # ---- filters ----
    liq_floor = d["med_1m_dollar_vol"].rolling(30, min_periods=30).median()
    ok_liq = liq_floor >= filters.LIQ_FLOOR_USD
    ok_vol = (atr_pct >= filters.VOL_BAND_LOW) & (atr_pct <= filters.VOL_BAND_HIGH)
    blocked = _event_exclusion(decision_ms, filters.EVENT_EXCL_HOURS, extra_events)
    ok_event = pd.Series(~blocked, index=d.index)
    # data-integrity: no missing 1m bars over the last L days (full 1440/day)
    ok_data = d["n_minutes"].rolling(L, min_periods=L).min().eq(1440)
    ok_sprd = pd.Series(True, index=d.index) if not filters.LIVE else pd.Series(np.nan, index=d.index)

    feat = pd.DataFrame({
        "close": close,
        "atr": atr,
        "atr_pct": atr_pct,
        "hh": hh,
        "ll": ll,
        "rw": rw,
        "comp_thresh": comp_thresh,
        "compressed": compressed.fillna(False),
        "delta_oi": delta_oi,
        "oi_up": oi_up.fillna(False),
        "oi_down": oi_down.fillna(False),
        "oi_present": oi_present,
        "fr": fr,
        "med_1m_dollar_vol": d["med_1m_dollar_vol"],
        "ok_liq": ok_liq.fillna(False),
        "ok_vol": ok_vol.fillna(False),
        "ok_event": ok_event,
        "ok_data": ok_data.fillna(False),
        "ok_sprd": ok_sprd.fillna(True) if not filters.LIVE else ok_sprd,
        "decision_ms": d["decision_ms"],
        "day_ms": d["day_ms"],
    })
    return feat


def raw_entry_signal(feat: pd.DataFrame, variant: Variant, consts: Constants) -> pd.Series:
    """Per-day candidate signal 'LONG'/'SHORT'/'' BEFORE position-state / re-entry logic.

    The engine applies one-position-per-symbol and the fresh-compression re-entry rule.
    """
    fr = feat["fr"]
    long_break = feat["close"] > feat["hh"]
    short_break = feat["close"] < feat["ll"]
    base = (feat["compressed"] & feat["ok_liq"] & feat["ok_vol"]
            & feat["ok_event"] & feat["ok_data"] & feat["ok_sprd"].astype(bool))

    if variant.oi_on:
        long_ok = base & long_break & feat["oi_up"] & (fr < consts.FUND_GATE)
        short_ok = base & short_break & feat["oi_down"] & (fr > -consts.FUND_GATE)
    else:
        long_ok = base & long_break & (fr < consts.FUND_GATE)
        short_ok = base & short_break & (fr > -consts.FUND_GATE)

    if variant.side_mode == "long_only":
        short_ok = pd.Series(False, index=feat.index)

    sig = pd.Series("", index=feat.index, dtype=object)
    sig[long_ok.fillna(False)] = "LONG"
    sig[(short_ok.fillna(False)) & (sig == "")] = "SHORT"
    return sig
