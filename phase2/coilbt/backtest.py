"""
Event-driven Coil-Break engine for one symbol.

Path-dependence handled exactly (chandelier trail, hard stop, 14-day time cap,
25-bps funding-budget stop), but each position's hold is resolved with VECTORIZED
numpy over the 1m slice [entry, entry+14d] rather than a per-minute Python loop, so
the full 320-variant x walk-forward search is tractable. Flat days contribute zero
return, so only in-position minutes are ever touched.

Accounting conventions (documented, pre-registered):
  * Sizing off a CONSTANT reference sleeve equity (non-compounding) so daily returns
    are stationary and comparable for DSR/PSR. F_RISK is fraction of that sleeve.
  * Entry fills at the OPEN of the first 1m bar of the decision day (decision_ms);
    fees+slippage charged as fractional costs on notional (entry & exit).
  * Stop exits fill at min(stop_px, bar.open) for longs / max(stop_px, bar.open) for
    shorts (a gap through the stop fills at the open — the honest, slightly-worse side).
  * Funding accrued at realized sign at each 8h settlement crossed, on entry notional.
  * Daily P&L = close-to-close mark-to-market + funding settled that day - costs that day.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import Constants, Costs, Filters, Params, Variant
from .costs import BPS, CostModel, FundingModel
from .data.loader import SymbolData
from .strategy import compute_features, raw_entry_signal

MS_PER_DAY = 86_400_000


@dataclass
class Trade:
    symbol: str
    side: int                 # +1 long, -1 short
    entry_ms: int
    exit_ms: int
    entry_day: pd.Timestamp
    exit_day: pd.Timestamp
    entry_px: float
    exit_px: float
    qty: float
    notional: float
    price_pnl: float
    funding_pnl: float
    cost: float
    net_pnl: float
    reason: str


def _resolve_hold(side: int, entry_px: float, stop_dist: float, entry_ms: int,
                  m_time: np.ndarray, m_open: np.ndarray, m_high: np.ndarray,
                  m_low: np.ndarray, m_close: np.ndarray, start_idx: int,
                  max_hold_ms: int, fund: FundingModel, notional: float,
                  budget_frac: float):
    """Vectorized exit resolution over the 1m slice starting at start_idx.

    Returns (exit_idx, exit_px, reason). start_idx is the entry bar (fill at its open);
    management is checked from the NEXT bar onward.
    """
    n = m_time.size
    # window end by time cap
    cap_ms = entry_ms + max_hold_ms
    # slice indices to consider (from entry bar to last bar within cap, +1 for exit)
    end_idx = np.searchsorted(m_time, cap_ms, side="left")  # first bar at/after cap time
    end_idx = min(end_idx, n - 1)
    lo, hi = start_idx, end_idx
    if hi <= lo:
        return lo, m_close[lo], "open_end"

    t = m_time[lo : hi + 1]
    o = m_open[lo : hi + 1]
    h = m_high[lo : hi + 1]
    l = m_low[lo : hi + 1]
    c = m_close[lo : hi + 1]
    k = c.size

    hard_stop = entry_px - side * stop_dist  # long: entry-dist ; short: entry+dist

    # chandelier trail from PRIOR closes (seed bar0 reference = entry_px)
    if side > 0:
        run_extreme = np.maximum.accumulate(c)                 # highest close so far
        prev_extreme = np.empty(k); prev_extreme[0] = entry_px
        prev_extreme[1:] = run_extreme[:-1]
        trail = prev_extreme - stop_dist
        stop_used = np.maximum(hard_stop, trail)
        breach = l <= stop_used
    else:
        run_extreme = np.minimum.accumulate(c)                 # lowest close so far
        prev_extreme = np.empty(k); prev_extreme[0] = entry_px
        prev_extreme[1:] = run_extreme[:-1]
        trail = prev_extreme + stop_dist
        stop_used = np.minimum(hard_stop, trail)
        breach = h >= stop_used

    # do not allow an exit on the entry bar itself (index 0); manage from bar 1
    breach[0] = False
    stop_idx = int(np.argmax(breach)) if breach.any() else -1

    # time cap: first bar whose time - entry >= max_hold
    cap_hit = t - entry_ms >= max_hold_ms
    cap_idx = int(np.argmax(cap_hit)) if cap_hit.any() else -1

    # funding-budget: step settlements, find first bar at/after the settlement that
    # tips cumulative adverse funding >= budget_frac
    fb_idx = -1
    fts, frates = fund.settlements_in(entry_ms, t[-1])
    if fts.size:
        cum = 0.0
        for j in range(fts.size):
            cum += -side * frates[j]          # signed funding pnl frac (credit +, cost -)
            adverse = max(0.0, -cum)
            if adverse >= budget_frac:
                b = int(np.searchsorted(t, fts[j], side="left"))
                fb_idx = min(b, k - 1)
                break

    # earliest exit
    cands = [(stop_idx, "stop"), (cap_idx, "time_cap"), (fb_idx, "funding_budget")]
    cands = [(i, r) for i, r in cands if i >= 0]
    if not cands:
        return hi, m_close[hi], "open_end"
    ex_local, reason = min(cands, key=lambda x: x[0])
    ex_idx = lo + ex_local

    if reason == "stop":
        sp = stop_used[ex_local]
        if side > 0:
            exit_px = min(sp, o[ex_local])   # gap-through fills at open
        else:
            exit_px = max(sp, o[ex_local])
    elif reason == "time_cap":
        exit_px = o[ex_local]                # exit at the bar's open
    else:  # funding_budget
        exit_px = o[ex_local]
    return ex_idx, float(exit_px), reason


def run_symbol(sd: SymbolData, variant: Variant, consts: Constants, filters: Filters,
               costs_cfg: Costs, ref_sleeve_equity: float,
               extra_events: list[str] | None = None):
    """Backtest one symbol; returns (trades, daily_pnl Series indexed by day)."""
    feat = compute_features(sd, variant.params, consts, filters, extra_events=extra_events)
    sig = raw_entry_signal(feat, variant, consts)

    cm = CostModel(costs_cfg.TAKER_FEE_BPS, costs_cfg.MAKER_FEE_BPS, costs_cfg.SLIPPAGE_BPS)
    fund = FundingModel(sd.funding)
    entry_cost_frac = cm.entry_cost_frac(maker=False)
    exit_cost_frac = cm.exit_cost_frac(maker=False)
    budget_frac = consts.FUNDING_BUDGET_STOP_BPS * BPS

    m = sd.minute.sort_values("open_time_ms").reset_index(drop=True)
    m_time = m["open_time_ms"].to_numpy(dtype="int64")
    m_open = m["open"].to_numpy(dtype=float)
    m_high = m["high"].to_numpy(dtype=float)
    m_low = m["low"].to_numpy(dtype=float)
    m_close = m["close"].to_numpy(dtype=float)

    daily_close = feat["close"]
    days = feat.index
    p = variant.params
    max_hold_ms = consts.MAX_HOLD_DAYS * MS_PER_DAY
    sleeve = consts.PER_SYMBOL_SPLIT * ref_sleeve_equity  # sizing reference (constant)

    daily_pnl = pd.Series(0.0, index=days)
    trades: list[Trade] = []

    need_fresh_compression = False
    i = 0
    ndays = len(days)
    day_ms_arr = feat["day_ms"].to_numpy(dtype="int64")
    decision_arr = feat["decision_ms"].to_numpy(dtype="int64")

    while i < ndays:
        # re-entry gate: after an exit, require compression to reset (go False) first
        if need_fresh_compression:
            if not bool(feat["compressed"].iloc[i]):
                need_fresh_compression = False
            i += 1
            continue

        s = sig.iloc[i]
        if s == "":
            i += 1
            continue

        side = 1 if s == "LONG" else -1
        atr = feat["atr"].iloc[i]
        if not np.isfinite(atr) or atr <= 0:
            i += 1
            continue
        stop_dist = p.K_ATR * atr

        # entry fills at the first 1m bar with open_time == decision_ms (00:00 of day+1)
        dms = int(decision_arr[i])
        start_idx = int(np.searchsorted(m_time, dms, side="left"))
        if start_idx >= m_time.size or m_time[start_idx] != dms:
            # decision bar not present (data gap at boundary) -> skip this signal
            i += 1
            continue
        entry_px = float(m_open[start_idx])
        entry_ms = dms

        # sizing: fixed-fractional to stop, leverage cap, liquidity cap
        qty = (p.F_RISK * sleeve) / stop_dist
        qty = min(qty, consts.MAX_LEV * sleeve / entry_px)
        med_1m = feat["med_1m_dollar_vol"].iloc[i]
        if np.isfinite(med_1m) and med_1m > 0:
            qty = min(qty, filters.LIQ_CAP_FRAC * med_1m / entry_px)
        if qty <= 0:
            i += 1
            continue
        notional = qty * entry_px

        ex_idx, exit_px, reason = _resolve_hold(
            side, entry_px, stop_dist, entry_ms, m_time, m_open, m_high, m_low,
            m_close, start_idx, max_hold_ms, fund, notional, budget_frac)
        exit_ms = int(m_time[ex_idx])

        price_pnl = side * qty * (exit_px - entry_px)
        funding_pnl = fund.funding_pnl_frac(side, entry_ms, exit_ms) * notional
        exit_notional = qty * exit_px
        cost = entry_cost_frac * notional + exit_cost_frac * exit_notional
        net = price_pnl + funding_pnl - cost

        # entry_day is the FILL day (00:00 of D+1 = entry_ms), NOT the signal day D, so
        # daily MTM attributes the first day's P&L to the day the position actually exists.
        entry_day = pd.Timestamp((entry_ms // MS_PER_DAY) * MS_PER_DAY, unit="ms", tz="UTC")
        exit_day_ms = (exit_ms // MS_PER_DAY) * MS_PER_DAY
        exit_day = pd.Timestamp(exit_day_ms, unit="ms", tz="UTC")

        trades.append(Trade(
            symbol=sd.symbol, side=side, entry_ms=entry_ms, exit_ms=exit_ms,
            entry_day=entry_day, exit_day=exit_day, entry_px=entry_px, exit_px=exit_px,
            qty=qty, notional=notional, price_pnl=price_pnl, funding_pnl=funding_pnl,
            cost=cost, net_pnl=net, reason=reason))

        _mark_daily(daily_pnl, daily_close, side, qty, entry_px, exit_px,
                    entry_day, exit_day, notional, entry_cost_frac, exit_cost_frac,
                    exit_notional, fund, entry_ms, exit_ms)

        # advance to the exit day; require fresh compression before re-entry
        need_fresh_compression = True
        exit_pos = days.searchsorted(exit_day)
        i = max(i + 1, int(exit_pos) + 1)

    return trades, daily_pnl


def _mark_daily(daily_pnl: pd.Series, daily_close: pd.Series, side: int, qty: float,
                entry_px: float, exit_px: float, entry_day, exit_day, notional: float,
                entry_cost_frac: float, exit_cost_frac: float, exit_notional: float,
                fund: FundingModel, entry_ms: int, exit_ms: int):
    """Distribute a trade's P&L across the days it spans (close-to-close MTM + funding + costs)."""
    idx = daily_close.index
    d0 = idx.searchsorted(entry_day)
    d1 = idx.searchsorted(exit_day)
    # price MTM close-to-close
    for d in range(d0, d1 + 1):
        day = idx[d]
        if d == d0 and d == d1:
            px_pnl = side * qty * (exit_px - entry_px)
        elif d == d0:
            px_pnl = side * qty * (float(daily_close.iloc[d]) - entry_px)
        elif d == d1:
            px_pnl = side * qty * (exit_px - float(daily_close.iloc[d - 1]))
        else:
            px_pnl = side * qty * (float(daily_close.iloc[d]) - float(daily_close.iloc[d - 1]))
        daily_pnl.iloc[d] += px_pnl
    # costs on their days
    daily_pnl.iloc[d0] += -entry_cost_frac * notional
    daily_pnl.iloc[d1] += -exit_cost_frac * exit_notional
    # funding settled per day
    fts, frates = fund.settlements_in(entry_ms, exit_ms)
    for ts, rate in zip(fts, frates):
        day_ms = (int(ts) // MS_PER_DAY) * MS_PER_DAY
        day = pd.Timestamp(day_ms, unit="ms", tz="UTC")
        dpos = idx.searchsorted(day)
        if 0 <= dpos < len(idx):
            daily_pnl.iloc[dpos] += (-side * rate) * notional
