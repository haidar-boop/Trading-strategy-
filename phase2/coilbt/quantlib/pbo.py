"""
Probability of Backtest Overfitting via Combinatorially-Symmetric Cross-Validation
(Bailey, Borwein, Lopez de Prado, Zhu 2017). Adapted from the uploaded quant_system.

This is the key capability the phase2 harness lacked: it asks, across a grid of N
configurations, how often the IN-SAMPLE-best config lands BELOW the out-of-sample
median — i.e. how likely "the best backtest" is to be overfit noise. PBO ~ 0.5 means
the selection is pure overfit; low PBO means an in-sample winner tends to stay a winner.

Input is a [T_obs x N_configs] matrix of per-period returns (one column per config).
On real data, phase2 builds this from every grid variant's OOS daily-return stream.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np


def _sr_per_obs(r: np.ndarray) -> float:
    r = np.asarray(r, float).ravel()
    sd = r.std(ddof=1)
    return 0.0 if sd == 0 else r.mean() / sd


def pbo_cscv(perf_matrix: np.ndarray, n_subsets: int = 14, metric=_sr_per_obs) -> tuple:
    """PBO via CSCV.

    perf_matrix : [T x N] per-period returns per configuration.
    n_subsets   : number of disjoint time blocks S (even). CSCV enumerates all
                  C(S, S/2) ways to split blocks into IS/OOS halves.
    Returns (pbo, logits): pbo = fraction of splits where the IS-best config is
    below the OOS median (logit <= 0).
    """
    M = np.asarray(perf_matrix, float)
    if M.ndim != 2 or M.shape[1] < 2:
        return float("nan"), np.array([])
    T, N = M.shape
    if n_subsets % 2 != 0:
        n_subsets += 1
    n_subsets = min(n_subsets, T)  # cannot have more blocks than observations
    if n_subsets < 2:
        return float("nan"), np.array([])
    idx_blocks = np.array_split(np.arange(T), n_subsets)
    block_ids = list(range(n_subsets))
    logits = []
    for is_blocks in combinations(block_ids, n_subsets // 2):
        is_idx = np.concatenate([idx_blocks[b] for b in is_blocks])
        oos_idx = np.concatenate([idx_blocks[b] for b in block_ids if b not in is_blocks])
        is_perf = np.array([metric(M[is_idx, c]) for c in range(N)])
        oos_perf = np.array([metric(M[oos_idx, c]) for c in range(N)])
        n_star = int(np.argmax(is_perf))                      # IS-best config
        rank = (oos_perf <= oos_perf[n_star]).mean()          # its OOS rank (1 = best)
        rank = min(max(rank, 1e-6), 1 - 1e-6)
        logits.append(np.log(rank / (1 - rank)))
    logits = np.asarray(logits)
    pbo = float((logits <= 0).mean())                         # below OOS median => overfit
    return pbo, logits
