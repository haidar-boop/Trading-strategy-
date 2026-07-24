"""Tests for the ported quantlib machinery (PBO/CSCV, HRP, metrics, impact costs)."""
import numpy as np

from phase2.coilbt.quantlib.pbo import pbo_cscv
from phase2.coilbt.quantlib.allocation import hrp, inverse_variance, erc
from phase2.coilbt.quantlib import metrics as qm
from phase2.coilbt.quantlib.impact_costs import ImpactCostModel


def test_pbo_noise_is_overfit_prone():
    # N pure-noise configs -> the IS-best config regresses OOS (winner's curse), so PBO
    # sits AT OR ABOVE 0.5 (finite-sample PBO for the null is commonly 0.6-0.8, not 0.5).
    rng = np.random.default_rng(0)
    M = rng.normal(0, 0.01, size=(600, 20))
    pbo, logits = pbo_cscv(M, n_subsets=10)
    assert pbo >= 0.5
    assert logits.size > 0


def test_pbo_real_edge_lower():
    # one column carries a persistent positive drift present across the whole sample;
    # it should stay the OOS-best when picked IS -> PBO markedly below the noise case.
    rng = np.random.default_rng(1)
    M = rng.normal(0, 0.01, size=(600, 20))
    M[:, 5] += 0.004  # real, persistent edge in config 5
    pbo, _ = pbo_cscv(M, n_subsets=10)
    assert pbo < 0.3


def test_pbo_degenerate_guard():
    pbo, logits = pbo_cscv(np.zeros((100, 1)))   # <2 configs
    assert np.isnan(pbo) and logits.size == 0


def test_hrp_weights_valid():
    rng = np.random.default_rng(2)
    X = rng.normal(0, 1, size=(500, 5))
    cov = np.cov(X.T)
    w = hrp(cov)
    assert abs(w.sum() - 1.0) < 1e-9
    assert (w >= -1e-12).all()          # HRP is long-only by construction


def test_hrp_diagonal_matches_inverse_variance():
    # for a diagonal covariance HRP reduces to inverse-variance weighting
    cov = np.diag([1.0, 4.0, 9.0, 16.0])
    w_hrp = hrp(cov)
    w_ivp = inverse_variance(cov)
    assert np.allclose(np.sort(w_hrp), np.sort(w_ivp), atol=1e-6)


def test_erc_sums_to_one():
    rng = np.random.default_rng(3)
    cov = np.cov(rng.normal(0, 1, size=(400, 4)).T)
    w = erc(cov)
    assert abs(w.sum() - 1.0) < 1e-6


def test_metrics_sanity():
    r = np.array([0.01, -0.005, 0.02, -0.01, 0.015, 0.0, 0.008])
    s = qm.summary(r, ann=252)
    assert set(["CAGR", "Sharpe", "Sortino", "Calmar", "MaxDD", "Ulcer", "CVaR95"]).issubset(s)
    assert qm.max_drawdown(np.array([0.01, 0.01, 0.01])) == 0.0  # monotone up -> no DD
    assert qm.sharpe(np.array([0.01, 0.01, 0.01])) != qm.sharpe(np.array([0.01, 0.01, 0.01]))  # 0 std -> nan


def test_effective_n():
    from phase2.coilbt.quantlib.effn import effective_n_participation, effective_n_clusters
    rng = np.random.default_rng(0)
    indep = rng.normal(0, 1, (400, 15))
    assert effective_n_participation(indep) > 10          # ~15 independent
    assert effective_n_clusters(indep) > 10
    base = rng.normal(0, 1, (400, 1))
    ident = base + rng.normal(0, 0.005, (400, 15))
    assert effective_n_participation(ident) < 2           # ~1 (all identical)
    assert effective_n_clusters(ident) <= 2
    # N_eff never exceeds the raw trial count
    assert effective_n_participation(indep) <= 15 + 1e-6


def test_impact_cost_monotone():
    m = ImpactCostModel()
    assert m.round_trip_bps(0.10, 0.02) > m.round_trip_bps(0.01, 0.02)   # more participation costs more
    base = m.cost_fraction(np.array([0.5]), np.array([0.02]), np.array([0.05]))
    stressed = ImpactCostModel(stress_mult=3.0).cost_fraction(
        np.array([0.5]), np.array([0.02]), np.array([0.05]))
    assert stressed > 2.9 * base
