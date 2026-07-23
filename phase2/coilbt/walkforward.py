"""
Purged, embargoed, rolling walk-forward + grid selection.

Rolling (fixed) 24m IS / 6m OOS / 6m step. Selection uses ONLY in-sample daily
returns (the last max(purge, embargo) days of each IS window are dropped so a trade
whose outcome bleeds into OOS cannot drive selection). OOS blocks are non-overlapping
(step = OOS length), so the concatenated OOS record is a clean live-equivalent stream.

DSR is computed ONCE on the concatenated OOS record (in the runner), with the trial
dispersion V estimated from ALL grid variants scored over the same OOS windows, and
N fixed to the shared batch ledger (=1000).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .stats import sharpe_ratio


@dataclass
class Fold:
    is_start: pd.Timestamp
    is_end: pd.Timestamp     # == oos_start
    oos_start: pd.Timestamp
    oos_end: pd.Timestamp


def generate_folds(index: pd.DatetimeIndex, is_months: int, oos_months: int,
                   step_months: int) -> list[Fold]:
    t0, tN = index[0], index[-1]
    folds = []
    is_start = t0
    while True:
        is_end = is_start + pd.DateOffset(months=is_months)
        oos_start = is_end
        oos_end = oos_start + pd.DateOffset(months=oos_months)
        if oos_end > tN + pd.Timedelta(days=1):
            break
        folds.append(Fold(is_start, is_end, oos_start, oos_end))
        is_start = is_start + pd.DateOffset(months=step_months)
    return folds


def _slice(returns: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    return returns[(returns.index >= start) & (returns.index < end)]


def walk_forward_select(variant_returns: dict[str, pd.Series], folds: list[Fold],
                        purge_days: int, embargo_days: int):
    """Per fold, pick the best variant by IS Sharpe; return the deployed OOS record.

    variant_returns : label -> full-timeline portfolio daily-return Series (same index).
    Returns:
      deployed        : concatenated OOS daily returns of the per-fold-selected variant
      selected        : list of (fold, label) chosen
      oos_windows     : list of (oos_start, oos_end) actually used
      trial_oos       : label -> concatenated OOS daily returns for THAT fixed variant
                        across all folds (used to estimate cross-trial Sharpe dispersion V)
    """
    drop = pd.Timedelta(days=max(purge_days, embargo_days))
    labels = list(variant_returns.keys())

    deployed_parts = []
    selected = []
    oos_windows = []
    trial_parts = {lab: [] for lab in labels}

    for fold in folds:
        # IS selection window with boundary purge/embargo removed
        is_sel_end = fold.is_end - drop
        best_lab, best_sr = None, -np.inf
        for lab in labels:
            is_r = _slice(variant_returns[lab], fold.is_start, is_sel_end)
            if is_r.size < 30:
                continue
            sr = sharpe_ratio(is_r.to_numpy())
            if sr > best_sr:
                best_sr, best_lab = sr, lab
        if best_lab is None:
            continue
        oos_r = _slice(variant_returns[best_lab], fold.oos_start, fold.oos_end)
        deployed_parts.append(oos_r)
        selected.append((fold, best_lab))
        oos_windows.append((fold.oos_start, fold.oos_end))
        for lab in labels:
            trial_parts[lab].append(_slice(variant_returns[lab], fold.oos_start, fold.oos_end))

    deployed = pd.concat(deployed_parts) if deployed_parts else pd.Series(dtype=float)
    trial_oos = {lab: (pd.concat(parts) if parts else pd.Series(dtype=float))
                 for lab, parts in trial_parts.items()}
    return deployed, selected, oos_windows, trial_oos


def trial_sharpes(trial_oos: dict[str, pd.Series]) -> np.ndarray:
    """Per-observation OOS Sharpe of each fixed variant -> dispersion input V for DSR."""
    out = []
    for lab, r in trial_oos.items():
        if r.size >= 30:
            out.append(sharpe_ratio(r.to_numpy()))
    return np.asarray(out, dtype=float)


def in_windows(ts_ms_array: np.ndarray, windows: list[tuple]) -> np.ndarray:
    """Boolean mask: which timestamps (ms) fall inside any (start,end) OOS window."""
    if len(windows) == 0:
        return np.zeros(ts_ms_array.shape, dtype=bool)
    epoch = pd.Timestamp("1970-01-01", tz="UTC")
    mask = np.zeros(ts_ms_array.shape, dtype=bool)
    for start, end in windows:
        s = (start - epoch) // pd.Timedelta(milliseconds=1)
        e = (end - epoch) // pd.Timedelta(milliseconds=1)
        mask |= (ts_ms_array >= s) & (ts_ms_array < e)
    return mask
