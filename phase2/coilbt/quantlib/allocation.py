# Adapted from the uploaded quant_system research sandbox (synthetic-data
# methodology toolkit); integrated verbatim-algorithm into the phase2 harness.
"""
allocation.py - Portfolio construction across return streams.

  - hrp()  : Hierarchical Risk Parity (Lopez de Prado, 2016). Robust to
             ill-conditioned covariance because it never inverts the matrix.
  - erc()  : Equal Risk Contribution (each asset contributes equal risk).
  - inverse_variance(), min_variance() : baselines for comparison.

HRP steps: (1) correlation -> distance d = sqrt(0.5(1-rho)); (2) hierarchical
clustering; (3) quasi-diagonalise via the cluster tree; (4) recursive bisection
allocating inverse-variance down the tree.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform
from scipy.optimize import minimize


def _cov_to_corr(cov):
    std = np.sqrt(np.diag(cov))
    corr = cov / np.outer(std, std)
    return np.clip(corr, -1, 1)


def hrp(cov: np.ndarray, return_order=False):
    cov = np.asarray(cov, float)
    corr = _cov_to_corr(cov)
    dist = np.sqrt(0.5 * (1 - corr))
    np.fill_diagonal(dist, 0.0)
    condensed = squareform(dist, checks=False)
    link = linkage(condensed, method="single")
    order = list(leaves_list(link))

    # recursive bisection
    w = pd.Series(1.0, index=order)
    clusters = [order]
    while clusters:
        new = []
        for c in clusters:
            if len(c) <= 1:
                continue
            split = len(c) // 2
            left, right = c[:split], c[split:]
            for side, other in ((left, right), (right, left)):
                # inverse-variance allocation within each sub-cluster
                cv = cov[np.ix_(side, side)]
                ivp = 1 / np.diag(cv)
                ivp /= ivp.sum()
                var_side = float(ivp @ cv @ ivp)
                cv_o = cov[np.ix_(other, other)]
                ivp_o = 1 / np.diag(cv_o)
                ivp_o /= ivp_o.sum()
                var_other = float(ivp_o @ cv_o @ ivp_o)
                alpha = 1 - var_side / (var_side + var_other)
                w[side] *= alpha
            new += [left, right]
        clusters = new

    weights = w.reindex(range(cov.shape[0])).values
    weights = weights / weights.sum()
    if return_order:
        return weights, order, link
    return weights


def erc(cov: np.ndarray):
    cov = np.asarray(cov, float)
    n = cov.shape[0]

    def obj(w):
        port_var = w @ cov @ w
        mrc = cov @ w
        rc = w * mrc
        target = port_var / n
        return np.sum((rc - target) ** 2)

    cons = ({"type": "eq", "fun": lambda w: w.sum() - 1},)
    bounds = [(0.0, 1.0)] * n
    res = minimize(obj, np.repeat(1 / n, n), method="SLSQP",
                   bounds=bounds, constraints=cons,
                   options={"maxiter": 500, "ftol": 1e-12})
    return res.x


def inverse_variance(cov: np.ndarray):
    ivp = 1 / np.diag(np.asarray(cov, float))
    return ivp / ivp.sum()


def min_variance(cov: np.ndarray):
    cov = np.asarray(cov, float)
    n = cov.shape[0]
    cons = ({"type": "eq", "fun": lambda w: w.sum() - 1},)
    bounds = [(0.0, 1.0)] * n
    res = minimize(lambda w: w @ cov @ w, np.repeat(1 / n, n),
                   method="SLSQP", bounds=bounds, constraints=cons)
    return res.x


def min_variance_unconstrained(cov: np.ndarray):
    """Closed-form long/short min-variance: w = inv(C)1 / (1' inv(C) 1).
    Requires inverting the covariance -> fragile when C is near-singular,
    which is exactly when small estimation errors blow weights up."""
    cov = np.asarray(cov, float)
    n = cov.shape[0]
    inv = np.linalg.pinv(cov)
    ones = np.ones(n)
    return inv @ ones / (ones @ inv @ ones)


def risk_contributions(w, cov):
    w = np.asarray(w, float)
    cov = np.asarray(cov, float)
    port_var = w @ cov @ w
    rc = w * (cov @ w)
    return rc / port_var  # fraction of total risk per asset
