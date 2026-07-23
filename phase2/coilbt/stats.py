"""
Performance statistics for the pass/fail decision, per Bailey & Lopez de Prado.

All Sharpe-related quantities are PER-OBSERVATION (per return bar). The annualization
factor cancels in the standardized ratios, so PSR/DSR are annualization-invariant;
MinTRL is a raw count of observations. Feed daily OOS returns.

Formulas (research-verified, primary sources cited in the module docstring history):
  SE(SR)^2 = (1 - g3*SR + ((g4-1)/4)*SR^2) / (n-1)      # Mertens/Lo, g4 NON-excess
  PSR(SR*) = Phi( (SR - SR*) * sqrt(n-1) / sqrt(1 - g3*SR + ((g4-1)/4)*SR^2) )
  MinTRL   = 1 + (1 - g3*SR + ((g4-1)/4)*SR^2) * ( z_p / (SR - SR*) )^2
  E[maxSR] = sqrt(V) * ( (1-euler)*Phi^-1(1 - 1/N) + euler*Phi^-1(1 - 1/(N*e)) )
  DSR      = PSR( E[maxSR] )
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.stats import norm

EULER = 0.5772156649015329


def sharpe_ratio(returns: np.ndarray) -> float:
    """Per-observation Sharpe = mean / std(ddof=1). Not annualized."""
    r = np.asarray(returns, dtype=float)
    if r.size < 2:
        return 0.0
    sd = r.std(ddof=1)
    if sd == 0 or not np.isfinite(sd):
        return 0.0
    return float(r.mean() / sd)


def _moments(returns: np.ndarray) -> tuple[float, float]:
    """Sample skewness (g3) and NON-excess kurtosis (g4). Gaussian => g3=0, g4=3."""
    r = np.asarray(returns, dtype=float)
    n = r.size
    mu = r.mean()
    m2 = ((r - mu) ** 2).mean()
    if m2 == 0:
        return 0.0, 3.0
    m3 = ((r - mu) ** 3).mean()
    m4 = ((r - mu) ** 4).mean()
    g3 = m3 / m2 ** 1.5
    g4 = m4 / m2 ** 2
    return float(g3), float(g4)


def _psr_denom(sr_hat: float, g3: float, g4: float) -> float:
    val = 1.0 - g3 * sr_hat + ((g4 - 1.0) / 4.0) * sr_hat ** 2
    # For any valid sample moments kurtosis >= skew^2 + 1, so val > 0 always; this guard
    # only trips on a degenerate/undefined statistic. FAIL CLOSED (nan -> PSR nan -> not a
    # pass) rather than clamping to a tiny denominator (which would blow the ratio up to a
    # spurious near-certain pass).
    return math.sqrt(val) if val > 1e-12 else float("nan")


def probabilistic_sharpe_ratio(returns: np.ndarray, sr_star: float = 0.0) -> float:
    """P(true per-obs Sharpe > sr_star). Returns a probability in [0,1]."""
    r = np.asarray(returns, dtype=float)
    n = r.size
    if n < 3:
        return float("nan")
    sr = sharpe_ratio(r)
    g3, g4 = _moments(r)
    denom = _psr_denom(sr, g3, g4)
    return float(norm.cdf((sr - sr_star) * math.sqrt(n - 1) / denom))


def min_track_record_length(returns: np.ndarray, sr_star: float = 0.0,
                            prob: float = 0.95) -> float:
    """Smallest n (in observations) so PSR(sr_star) >= prob. inf if SR<=sr_star."""
    r = np.asarray(returns, dtype=float)
    if r.size < 3:
        return float("inf")
    sr = sharpe_ratio(r)
    if sr <= sr_star:
        return float("inf")
    g3, g4 = _moments(r)
    z = norm.ppf(prob)
    var_term = 1.0 - g3 * sr + ((g4 - 1.0) / 4.0) * sr ** 2
    if var_term <= 1e-12:
        return float("inf")   # undefined variance -> no finite track record proves it (fail closed)
    return float(1.0 + var_term * (z / (sr - sr_star)) ** 2)


def expected_max_sharpe(trial_sharpes: np.ndarray, n_trials: int | None = None) -> float:
    """E[max Sharpe] under the null of zero skill across N trials (per-obs units).

    V = cross-sectional variance of the trial Sharpes (ddof=1). N defaults to the
    number of trial Sharpes, but callers pass the shared-ledger N (=1000) so the
    deflation reflects the true search breadth even when only the observed trials'
    dispersion is available to estimate V.
    """
    ts = np.asarray(trial_sharpes, dtype=float)
    ts = ts[np.isfinite(ts)]
    if ts.size < 2:
        return float("nan")   # cannot estimate trial dispersion -> deflation undefined (fail closed)
    N = int(n_trials) if n_trials is not None else ts.size
    N = max(N, 2)
    V = ts.var(ddof=1)
    if V <= 0:
        return 0.0            # zero dispersion across trials -> no selection to deflate (correct)
    q1 = norm.ppf(1.0 - 1.0 / N)
    q2 = norm.ppf(1.0 - 1.0 / (N * math.e))
    return float(math.sqrt(V) * ((1.0 - EULER) * q1 + EULER * q2))


@dataclass
class DSRResult:
    sr_hat: float
    sr_star_deflated: float
    dsr: float
    n_obs: int
    n_trials: int
    var_trials: float
    min_trl: float
    passes: bool          # dsr >= conf AND n_obs >= min_trl


def deflated_sharpe_ratio(oos_returns: np.ndarray, trial_sharpes: np.ndarray,
                          n_trials: int | None = None, conf: float = 0.95) -> DSRResult:
    """DSR on the concatenated OOS return record, deflated by E[max Sharpe] across N trials."""
    r = np.asarray(oos_returns, dtype=float)
    ts = np.asarray(trial_sharpes, dtype=float)
    ts = ts[np.isfinite(ts)]
    N = max(2, int(n_trials) if n_trials is not None else ts.size)  # clamp once; report consistently
    sr = sharpe_ratio(r)
    sr0 = expected_max_sharpe(ts, n_trials=N)
    dsr = probabilistic_sharpe_ratio(r, sr_star=sr0)
    mtrl = min_track_record_length(r, sr_star=sr0, prob=conf)
    passes = bool(np.isfinite(dsr) and dsr >= conf and r.size >= mtrl)
    return DSRResult(
        sr_hat=sr, sr_star_deflated=sr0, dsr=float(dsr), n_obs=int(r.size),
        n_trials=int(N), var_trials=float(ts.var(ddof=1) if ts.size > 1 else 0.0),
        min_trl=float(mtrl), passes=passes,
    )


def profit_factor(trade_pnls: np.ndarray) -> float:
    """Sum of winning P&L / abs(sum of losing P&L). inf if no losers, nan if no trades."""
    p = np.asarray(trade_pnls, dtype=float)
    if p.size == 0:
        return float("nan")
    gains = p[p > 0].sum()
    losses = p[p < 0].sum()
    if losses == 0:
        return float("inf") if gains > 0 else float("nan")
    return float(gains / abs(losses))
