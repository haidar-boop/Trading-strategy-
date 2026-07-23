"""
Event-driven FEF engine for one symbol. Decisions on the 8h funding clock.

Exit types (earliest by timestamp wins):
  * intrabar ATR hard stop (fixed at entry; no trailing) — checked on 1m bars
  * funding-SIGN exit — at a settlement where funding flips to the side we now PAY
  * funding-NORMALIZATION exit — at a settlement where the percentile has decayed to EXIT_PCT
  * 7-day time cap

Entry fills at the 1m bar opening at the settlement (taker; backtest never assumes maker).
Costs + funding accrual reuse the shared CostModel/FundingModel. Daily MTM reuses the
shared _mark_daily so the accounting invariant (daily P&L sums to trade net) holds here too.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .backtest import Trade, _mark_daily
from .config_fef import ConstantsFEF, CostsFEF, FiltersFEF, VariantFEF
from .costs import BPS, CostModel, FundingModel
from .data.loader import SymbolData
from .strategy_fef import build_decision_table, raw_signal

MS_PER_DAY = 86_400_000
MS_PER_HOUR = 3_600_000


def _stop_breach(side: int, hard_stop: float, m_time, m_open, m_high, m_low,
                 start_idx: int, end_ms: int):
    """First 1m bar in [entry, end_ms] breaching the fixed hard stop. Returns (idx, px) or None."""
    end_idx = int(np.searchsorted(m_time, end_ms, side="right"))
    end_idx = min(end_idx, m_time.size)
    lo, hi = start_idx, end_idx
    if hi <= lo + 1:
        return None
    l = m_low[lo:hi]
    h = m_high[lo:hi]
    o = m_open[lo:hi]
    if side > 0:
        breach = l <= hard_stop
    else:
        breach = h >= hard_stop
    breach[0] = False  # not on the entry bar itself
    if not breach.any():
        return None
    j = int(np.argmax(breach))
    if side > 0:
        px = min(hard_stop, o[j])
    else:
        px = max(hard_stop, o[j])
    return lo + j, float(px)


def run_symbol_fef(sd: SymbolData, oi_5m: pd.DataFrame, variant: VariantFEF,
                   consts: ConstantsFEF, filters: FiltersFEF, costs_cfg: CostsFEF,
                   ref_equity: float, extra_events: list[str] | None = None,
                   tbl: pd.DataFrame | None = None):
    """Backtest one symbol; returns (trades, daily_pnl Series). `tbl` may be precomputed
    (it depends only on frozen constants/filters, not on the variant's params)."""
    if tbl is None:
        tbl = build_decision_table(sd, oi_5m, consts, filters, extra_events=extra_events)
    p = variant.params
    sig = raw_signal(tbl, p, variant.side_mode)

    cm = CostModel(costs_cfg.TAKER_FEE_BPS, costs_cfg.MAKER_FEE_BPS, costs_cfg.SLIPPAGE_BPS)
    fund = FundingModel(sd.funding)
    ecf, xcf = cm.entry_cost_frac(False), cm.exit_cost_frac(False)

    m = sd.minute.sort_values("open_time_ms").reset_index(drop=True)
    m_time = m["open_time_ms"].to_numpy(dtype="int64")
    m_open = m["open"].to_numpy(dtype=float)
    m_high = m["high"].to_numpy(dtype=float)
    m_low = m["low"].to_numpy(dtype=float)

    dt = tbl["dt_ms"].to_numpy(dtype="int64")
    f_now = tbl["f_now"].to_numpy(dtype=float)
    pct = tbl["pct"].to_numpy(dtype=float)
    atr = tbl["atr"].to_numpy(dtype=float)
    entry_open = tbl["entry_open_px"].to_numpy(dtype=float)
    sig_arr = sig.to_numpy()

    daily_close = sd.daily["close"]
    daily_pnl = pd.Series(0.0, index=sd.daily.index)
    max_hold_ms = consts.MAX_HOLD_DAYS * MS_PER_DAY
    trades: list[Trade] = []

    n = dt.size
    k = 0
    while k < n:
        side_str = sig_arr[k]
        if side_str == "":
            k += 1
            continue
        a = atr[k]
        epx = entry_open[k]
        if not (np.isfinite(a) and a > 0 and np.isfinite(epx) and epx > 0):
            k += 1
            continue
        side = 1 if side_str == "LONG" else -1
        stop_dist = p.STOP_ATR_MULT * a
        entry_ms = int(dt[k])
        start_idx = int(np.searchsorted(m_time, entry_ms, side="left"))
        if start_idx >= m_time.size or m_time[start_idx] != entry_ms:
            k += 1
            continue

        # sizing: fixed-fractional risk to stop, per-position leverage cap.
        # NOTE: TOTAL_LEV (3x) is not separately enforced here — with the frozen 2-symbol
        # universe at PER_POS_LEV=1.5x each, aggregate exposure is capped at 3x by construction.
        # A larger universe would need an explicit portfolio-exposure cap in the aggregation step.
        qty = (p.RISK_FRAC * ref_equity) / stop_dist
        qty = min(qty, consts.PER_POS_LEV * ref_equity / epx)
        if qty <= 0:
            k += 1
            continue

        hard_stop = epx - side * stop_dist
        cap_ms = entry_ms + max_hold_ms

        # decision-based exit: first settlement > entry with sign-flip or normalization
        dec_exit_ms, dec_reason = None, None
        j = k + 1
        while j < n and dt[j] <= cap_ms:
            fj = f_now[j]
            if np.isfinite(fj):
                pays = (fj > 0) if side > 0 else (fj < 0)
                if pays:
                    dec_exit_ms, dec_reason = int(dt[j]), "funding_sign"
                    break
                pj = pct[j]
                if np.isfinite(pj):
                    normalized = (pj <= p.EXIT_PCT) if side < 0 else (pj >= 100.0 - p.EXIT_PCT)
                    if normalized:
                        dec_exit_ms, dec_reason = int(dt[j]), "normalization"
                        break
            j += 1

        # intrabar stop within [entry, min(cap, dec_exit)]
        horizon = cap_ms if dec_exit_ms is None else min(cap_ms, dec_exit_ms)
        stop = _stop_breach(side, hard_stop, m_time, m_open, m_high, m_low, start_idx, horizon)

        # choose earliest exit
        candidates = []
        if stop is not None:
            candidates.append((int(m_time[stop[0]]), stop[1], "stop"))
        if dec_exit_ms is not None:
            fpos = int(np.searchsorted(m_time, dec_exit_ms, side="left"))
            if fpos < m_time.size and m_time[fpos] == dec_exit_ms:
                candidates.append((dec_exit_ms, float(m_open[fpos]), dec_reason))
        # time cap fallback
        cpos = int(np.searchsorted(m_time, cap_ms, side="left"))
        cpos = min(cpos, m_time.size - 1)
        candidates.append((int(m_time[cpos]), float(m_open[cpos]), "time_cap"))

        exit_ms, exit_px, reason = min(candidates, key=lambda x: x[0])

        notional = qty * epx
        price_pnl = side * qty * (exit_px - epx)
        funding_pnl = fund.funding_pnl_frac(side, entry_ms, exit_ms) * notional
        exit_notional = qty * exit_px
        cost = ecf * notional + xcf * exit_notional
        net = price_pnl + funding_pnl - cost

        entry_day = pd.Timestamp((entry_ms // MS_PER_DAY) * MS_PER_DAY, unit="ms", tz="UTC")
        exit_day = pd.Timestamp((exit_ms // MS_PER_DAY) * MS_PER_DAY, unit="ms", tz="UTC")
        trades.append(Trade(
            symbol=sd.symbol, side=side, entry_ms=entry_ms, exit_ms=exit_ms,
            entry_day=entry_day, exit_day=exit_day, entry_px=epx, exit_px=exit_px,
            qty=qty, notional=notional, price_pnl=price_pnl, funding_pnl=funding_pnl,
            cost=cost, net_pnl=net, reason=reason))
        _mark_daily(daily_pnl, daily_close, side, qty, epx, exit_px, entry_day, exit_day,
                    notional, ecf, xcf, exit_notional, fund, entry_ms, exit_ms)

        # advance strictly PAST the exit settlement (side="right") so we never re-enter on the
        # very settlement a decision exit closed on; for a stop (exit_ms between settlements)
        # this lands on the next settlement, as intended.
        exit_k = int(np.searchsorted(dt, exit_ms, side="right"))
        k = max(k + 1, exit_k)

    return trades, daily_pnl
