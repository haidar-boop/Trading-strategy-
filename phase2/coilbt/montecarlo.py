"""
Monte Carlo robustness on the concatenated OOS record.

(a) Circular BLOCK bootstrap of the OOS daily returns (preserves serial dependence
    that IID reshuffle destroys). Pass rule: the realized OOS equity path must not
    fall below the pointwise 5th-percentile envelope of the bootstrap paths.
(b) Entry-timing jitter: shift each OOS trade's entry by +/- up to `jitter_minutes`
    one-minute bars, RE-DERIVE the fill from 1m data, keep the hold length, replay.
    Pass rule: median jittered terminal P&L >= frac x unjittered terminal P&L.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BootstrapResult:
    passed: bool
    real_terminal: float
    p5_terminal: float
    breached: bool


def circular_block_bootstrap(returns: np.ndarray, block: int, paths: int,
                             seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    r = np.asarray(returns, dtype=float)
    n = r.size
    if n == 0:
        return np.empty((paths, 0))
    block = max(1, min(block, n))
    n_blocks = int(np.ceil(n / block))
    out = np.empty((paths, n))
    arange_block = np.arange(block)
    for b in range(paths):
        starts = rng.integers(0, n, size=n_blocks)
        idx = np.concatenate([(s + arange_block) % n for s in starts])[:n]
        out[b] = r[idx]
    return out


def block_bootstrap_envelope(oos_returns: np.ndarray, block: int, paths: int,
                             pctile: float = 5.0, seed: int = 0) -> BootstrapResult:
    r = np.asarray(oos_returns, dtype=float)
    if r.size < 5:
        return BootstrapResult(False, float("nan"), float("nan"), True)
    boot = circular_block_bootstrap(r, block, paths, seed)
    equity = np.cumprod(1.0 + boot, axis=1)
    p5_env = np.percentile(equity, pctile, axis=0)
    real_eq = np.cumprod(1.0 + r)
    breached = bool(np.any(real_eq < p5_env))
    return BootstrapResult(
        passed=not breached,
        real_terminal=float(real_eq[-1]),
        p5_terminal=float(np.percentile(equity[:, -1], pctile)),
        breached=breached,
    )


@dataclass
class JitterResult:
    passed: bool
    base_terminal: float
    jitter_median: float
    jitter_p5: float


def _replay_terminal(trades, m_time, m_open, shifts, ref_equity):
    """Replay trades with per-trade entry-bar shift; re-derive fills from 1m opens.

    Each trade dict: side, start_idx (entry bar), hold_bars (exit_idx-start_idx), qty,
    entry_cost_frac, exit_cost_frac, funding_pnl (kept fixed — funding depends on wall
    time which the small jitter barely moves). Price P&L is re-derived from shifted fills.
    """
    n = m_time.size
    total = 0.0
    for tr, sh in zip(trades, shifts):
        si = int(np.clip(tr["start_idx"] + sh, 0, n - 1))
        ei = int(np.clip(si + tr["hold_bars"], 0, n - 1))
        entry_px = float(m_open[si])
        exit_px = float(m_open[ei])
        side, qty = tr["side"], tr["qty"]
        price_pnl = side * qty * (exit_px - entry_px)
        cost = tr["entry_cost_frac"] * qty * entry_px + tr["exit_cost_frac"] * qty * exit_px
        total += price_pnl + tr["funding_pnl"] - cost
    return total


def entry_jitter(trades: list[dict], m_time: np.ndarray, m_open: np.ndarray,
                 jitter_bars: int, paths: int, frac: float, seed: int = 0) -> JitterResult:
    if not trades:
        return JitterResult(False, float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    base = _replay_terminal(trades, m_time, m_open, np.zeros(len(trades), dtype=int), None)
    terms = np.empty(paths)
    for p in range(paths):
        shifts = rng.integers(-jitter_bars, jitter_bars + 1, size=len(trades))
        terms[p] = _replay_terminal(trades, m_time, m_open, shifts, None)
    med = float(np.median(terms))
    passed = bool(np.isfinite(base) and base != 0 and med >= frac * base) if base > 0 else False
    return JitterResult(passed=passed, base_terminal=float(base),
                        jitter_median=med, jitter_p5=float(np.percentile(terms, 5)))
