"""
Effective number of independent trials for the Deflated Sharpe Ratio.

The DSR deflation benchmark uses N = number of trials. With a grid of highly CORRELATED
configs (adjacent thresholds give near-identical returns), the raw count over-deflates —
Bailey & Lopez de Prado note the correction should use the number of *independent* trials.

Two estimators of N_eff from the trials' return matrix [T x N]:
  * participation ratio of the correlation-matrix eigenvalues:
        N_eff = (sum lambda)^2 / sum(lambda^2)        (a.k.a. inverse participation number)
    This is threshold-free and equals N when trials are uncorrelated, 1 when identical.
  * cluster count: hierarchical clustering on 1-|corr| distance, N_eff = number of clusters.

HONESTY GUARDRAILS (this must not be used to game a pass):
  - N_eff is a REDUCTION of the trial count only; it is always <= the raw N, so it makes the
    bar EASIER — report it alongside the raw-N DSR, never instead of it, and never below the
    number of genuinely distinct strategy IDEAS searched across the whole project.
  - It corrects for *redundant* trials, not for the fact that you searched at all.
"""
from __future__ import annotations

import numpy as np


def _corr_from_returns(returns_matrix: np.ndarray) -> np.ndarray:
    M = np.asarray(returns_matrix, dtype=float)
    # columns = trials; drop zero-variance columns (degenerate configs)
    sd = M.std(axis=0, ddof=1)
    keep = sd > 0
    M = M[:, keep]
    if M.shape[1] < 2:
        return np.array([[1.0]])
    C = np.corrcoef(M, rowvar=False)
    return np.nan_to_num(C, nan=0.0)


def effective_n_participation(returns_matrix: np.ndarray) -> float:
    """N_eff via eigenvalue participation ratio of the trial correlation matrix.
    Returns a float in [1, N]. Uncorrelated trials -> N; identical trials -> 1."""
    C = _corr_from_returns(returns_matrix)
    if C.shape[0] < 2:
        return 1.0
    lam = np.linalg.eigvalsh(C)
    lam = np.clip(lam.real, 0.0, None)
    s1 = lam.sum()
    s2 = (lam ** 2).sum()
    if s2 <= 0:
        return 1.0
    neff = (s1 * s1) / s2
    return float(np.clip(neff, 1.0, C.shape[0]))


def effective_n_clusters(returns_matrix: np.ndarray, dist_threshold: float = 0.5) -> int:
    """N_eff via hierarchical clustering on 1-|corr| distance; N_eff = cluster count."""
    C = _corr_from_returns(returns_matrix)
    n = C.shape[0]
    if n < 2:
        return 1
    try:
        from scipy.cluster.hierarchy import fcluster, linkage
        from scipy.spatial.distance import squareform
        dist = 1.0 - np.abs(C)
        np.fill_diagonal(dist, 0.0)
        dist = (dist + dist.T) / 2.0
        link = linkage(squareform(dist, checks=False), method="average")
        labels = fcluster(link, t=dist_threshold, criterion="distance")
        return int(len(np.unique(labels)))
    except Exception:
        return int(round(effective_n_participation(returns_matrix)))
