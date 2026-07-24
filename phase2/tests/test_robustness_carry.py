"""
Tests for the #39 robustness module: stationary bootstrap correctness + CI sanity.
"""
import numpy as np

from phase2.coilbt.robustness_carry import stationary_bootstrap, bootstrap_cis, REF_EQUITY


def test_stationary_bootstrap_shape_and_resampling():
    x = np.arange(50, dtype=float)
    boot = stationary_bootstrap(x, mean_block=5, paths=200, seed=0)
    assert boot.shape == (200, 50)
    # every value must come from the original series
    assert set(np.unique(boot)).issubset(set(x.tolist()))


def test_stationary_bootstrap_preserves_mean_in_expectation():
    rng = np.random.default_rng(0)
    x = rng.normal(3.0, 1.0, 500)
    boot = stationary_bootstrap(x, mean_block=10, paths=400, seed=1)
    # the grand mean of resampled paths must be close to the sample mean (unbiased)
    assert abs(boot.mean() - x.mean()) < 0.1


def test_bootstrap_ci_brackets_point_and_sign():
    # a clearly-positive per-trade P&L series -> CI should be positive and bracket the point
    rng = np.random.default_rng(2)
    pnls = rng.normal(50.0, 20.0, 80)          # $ per trade, clearly > 0
    ci = bootstrap_cis(pnls, trade_block=3, n_boot=3000, conf=0.90)
    assert ci["net_lo"] < ci["net_point"] < ci["net_hi"]
    assert ci["p_net_pos"] > 0.95              # sign robust
    assert ci["sharpe_lo"] < ci["sharpe_point"] < ci["sharpe_hi"]


def test_bootstrap_ci_wide_for_noisy_series():
    # a near-zero-mean noisy series -> P(net>0) near 50%, CI straddles 0
    rng = np.random.default_rng(3)
    pnls = rng.normal(1.0, 200.0, 60)
    ci = bootstrap_cis(pnls, trade_block=3, n_boot=3000, conf=0.90)
    assert ci["net_lo"] < 0 < ci["net_hi"]
    assert 0.2 < ci["p_net_pos"] < 0.8


def test_bootstrap_ci_handles_tiny_sample():
    ci = bootstrap_cis(np.array([10.0, 20.0]), conf=0.90)
    assert ci["n_trades"] == 2
    assert np.isnan(ci["net_lo"])              # too few to bootstrap -> NaN, no crash
