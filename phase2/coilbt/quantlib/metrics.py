# Adapted from the uploaded quant_system research sandbox (synthetic-data
# methodology toolkit); integrated verbatim-algorithm into the phase2 harness.
"""
metrics.py - Honest performance metrics. All functions operate on a return
series at a given frequency (default daily, 252/yr). No metric here is ever
populated with invented numbers; they are computed from a returns array.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

ANN = 252


def _arr(r):
    return np.asarray(r, dtype=float).ravel()


def sharpe(r, ann=ANN):
    r = _arr(r)
    sd = r.std(ddof=1)
    return np.nan if sd == 0 else (r.mean() / sd) * np.sqrt(ann)


def sortino(r, ann=ANN):
    r = _arr(r)
    downside = r[r < 0]
    dd = downside.std(ddof=1) if downside.size > 1 else 0.0
    return np.nan if dd == 0 else (r.mean() / dd) * np.sqrt(ann)


def equity_curve(r):
    return np.cumprod(1.0 + _arr(r))


def max_drawdown(r):
    eq = equity_curve(r)
    peak = np.maximum.accumulate(eq)
    dd = eq / peak - 1.0
    return float(dd.min())


def cagr(r, ann=ANN):
    r = _arr(r)
    eq = equity_curve(r)
    years = len(r) / ann
    return float(eq[-1] ** (1 / years) - 1) if years > 0 else np.nan


def calmar(r, ann=ANN):
    mdd = abs(max_drawdown(r))
    return np.nan if mdd == 0 else cagr(r, ann) / mdd


def ulcer_index(r):
    eq = equity_curve(r)
    peak = np.maximum.accumulate(eq)
    dd_pct = 100.0 * (eq / peak - 1.0)
    return float(np.sqrt(np.mean(dd_pct ** 2)))


def value_at_risk(r, alpha=0.95):
    return float(-np.quantile(_arr(r), 1 - alpha))


def cvar(r, alpha=0.95):
    r = _arr(r)
    var = -np.quantile(r, 1 - alpha)
    tail = r[r <= -var]
    return float(-tail.mean()) if tail.size else var


def tail_ratio(r):
    r = _arr(r)
    lo = np.quantile(r, 0.05)
    hi = np.quantile(r, 0.95)
    return np.nan if lo == 0 else abs(hi / lo)


def omega(r, threshold=0.0):
    r = _arr(r) - threshold
    gains = r[r > 0].sum()
    losses = -r[r < 0].sum()
    return np.inf if losses == 0 else gains / losses


def turnover(weights: pd.DataFrame):
    """Average one-sided turnover per period from a weight DataFrame."""
    dw = weights.diff().abs().sum(axis=1)
    return float(dw.iloc[1:].mean())


def summary(r, weights=None, ann=ANN) -> dict:
    out = {
        "CAGR": cagr(r, ann),
        "AnnVol": float(_arr(r).std(ddof=1) * np.sqrt(ann)),
        "Sharpe": sharpe(r, ann),
        "Sortino": sortino(r, ann),
        "Calmar": calmar(r, ann),
        "MaxDD": max_drawdown(r),
        "Ulcer": ulcer_index(r),
        "VaR95": value_at_risk(r, 0.95),
        "CVaR95": cvar(r, 0.95),
        "TailRatio": tail_ratio(r),
        "Omega": omega(r),
    }
    if weights is not None:
        out["TurnoverAvg"] = turnover(weights)
    return out
