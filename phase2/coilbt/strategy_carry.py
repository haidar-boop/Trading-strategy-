"""
Cash-and-carry decision table + signal. One row per 8h funding settlement, causal.

  f_now     : funding rate settled at t (interval ending at t)
  pp, ps    : perp / spot price at t (1m open at t)
  basis_bps : (pp - ps)/ps * 1e4  — the perp premium at t
  filters   : ok_liq / ok_event / ok_mech

Signal: ENTER (short perp + long spot) if f_now >= ENTRY_FUND_BPS/1e4 and filters pass.
Positive-carry side only (reverse carry needs spot borrow — out of scope for retail).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config_carry import ConstantsCarry, FiltersCarry
from .data.loader import SymbolData
from .events import event_timestamps_ms

MS_PER_DAY = 86_400_000
MS_PER_HOUR = 3_600_000
MS_PER_MIN = 60_000
BPS = 1e-4


def _price_at(m_time: np.ndarray, m_open: np.ndarray, q: np.ndarray) -> np.ndarray:
    pos = np.searchsorted(m_time, q, side="left")
    valid = (pos < m_time.size) & (m_time[np.clip(pos, 0, m_time.size - 1)] == q)
    return np.where(valid, m_open[np.clip(pos, 0, m_open.size - 1)], np.nan), valid


def build_carry_table(sd: SymbolData, spot_min: pd.DataFrame, consts: ConstantsCarry,
                      filters: FiltersCarry, extra_events: list[str] | None = None) -> pd.DataFrame:
    f = sd.funding.sort_values("calc_time").reset_index(drop=True)
    dt = f["calc_time"].to_numpy(dtype="int64")
    f_now = f["last_funding_rate"].to_numpy(dtype=float)
    interval = f.get("funding_interval_hours", pd.Series(8, index=f.index)).to_numpy(dtype=float)

    pm = sd.minute.sort_values("open_time_ms").reset_index(drop=True)
    pt = pm["open_time_ms"].to_numpy(dtype="int64")
    po = pm["open"].to_numpy(dtype=float)
    sm = spot_min.rename(columns={"open_time": "open_time_ms"}).sort_values("open_time_ms").reset_index(drop=True)
    st = sm["open_time_ms"].to_numpy(dtype="int64")
    so = sm["open"].to_numpy(dtype=float)

    pp, pv = _price_at(pt, po, dt)     # perp open at t
    ps, sv = _price_at(st, so, dt)     # spot open at t
    valid_fill = pv & sv & np.isfinite(pp) & np.isfinite(ps)
    with np.errstate(invalid="ignore", divide="ignore"):
        basis_bps = (pp - ps) / ps * 1e4

    # daily-derived liquidity + vol (last COMPLETED daily bar, no same-day look-ahead)
    d = sd.daily
    day_ms = d["day_ms"].to_numpy(dtype="int64")
    liq_30 = d["quote_volume"].rolling(30, min_periods=30).median().to_numpy(dtype=float)
    dvol_30 = d["close"].pct_change().rolling(30, min_periods=30).std(ddof=1).to_numpy(dtype=float)
    raw = np.searchsorted(day_ms + MS_PER_DAY, dt, side="right") - 1
    liq_at = np.where(raw >= 0, liq_30[np.clip(raw, 0, day_ms.size - 1)], np.nan)
    dvol_at = np.where(raw >= 0, dvol_30[np.clip(raw, 0, day_ms.size - 1)], np.nan)

    # --- OI-confirmation / squeeze tell (#20), causal ---
    # squeeze signature: price RISING while OI FALLING over the trailing window (short covering).
    # A funding spike in that state is fragile (about to invert). ok_oi=False flags it for rejection.
    # Computed from the last daily bars known at t; NaN (no OI history) -> gate passes (ok_oi=True).
    ret5 = d["close"].pct_change(5).to_numpy(dtype=float)              # 5-day price momentum
    oi_lvl = sd.oi_daily["oi_level"].reindex(d.index).to_numpy(dtype=float)
    oi_chg5 = pd.Series(oi_lvl, index=d.index).pct_change(5).to_numpy(dtype=float)  # 5-day OI change
    ret5_at = np.where(raw >= 0, ret5[np.clip(raw, 0, day_ms.size - 1)], np.nan)
    oichg_at = np.where(raw >= 0, oi_chg5[np.clip(raw, 0, day_ms.size - 1)], np.nan)
    squeeze = (ret5_at > 0.02) & (oichg_at < -0.02)   # +2% price & -2% OI over 5d = covering rally
    ok_oi = ~np.where(np.isnan(ret5_at) | np.isnan(oichg_at), False, squeeze)

    ev = event_timestamps_ms(extra=extra_events).to_numpy(dtype="int64")
    win = int(filters.EVENT_EXCL_MINUTES * MS_PER_MIN)
    if ev.size:
        lo = np.searchsorted(ev, dt - win, side="left")
        hi = np.searchsorted(ev, dt + win, side="right")
        ok_event = ~(hi > lo)
    else:
        ok_event = np.ones(dt.size, dtype=bool)

    tbl = pd.DataFrame({
        "dt_ms": dt, "f_now": f_now, "pp": pp, "ps": ps, "basis_bps": basis_bps,
        "valid_fill": valid_fill,
        "adv_usd": liq_at,          # 30d median daily $ volume -> impact participation denominator
        "daily_vol": dvol_at,       # 30d daily realized vol (fraction) -> impact vol term
        "ok_liq": liq_at >= filters.LIQ_FLOOR_USD,
        "ok_event": ok_event,
        "ok_mech": interval == consts.FUNDING_INTERVAL_HOURS,
        "ok_oi": ok_oi,             # False = squeeze tell (rising price + falling OI); gate on demand
    }, index=pd.to_datetime(dt, unit="ms", utc=True))
    tbl.index.name = "decision"
    return tbl


def raw_signal_carry(tbl: pd.DataFrame, params) -> pd.Series:
    """Per-decision entry flag: True where we open a cash-and-carry (short perp + long spot)."""
    ok = (tbl["valid_fill"] & tbl["ok_liq"] & tbl["ok_event"] & tbl["ok_mech"])
    if getattr(params, "USE_OI_GATE", False) and "ok_oi" in tbl.columns:
        ok = ok & tbl["ok_oi"]
    enter = ok & (tbl["f_now"] >= params.ENTRY_FUND_BPS * BPS)
    return enter.fillna(False)
