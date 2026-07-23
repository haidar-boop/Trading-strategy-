"""Stats correctness: PSR/MinTRL/DSR/PF on synthetic data with known properties."""
import numpy as np

from phase2.coilbt import stats


def test_sharpe_basic():
    r = np.array([0.01, 0.01, 0.01, 0.01])
    # zero variance -> guarded to 0
    assert stats.sharpe_ratio(r) == 0.0
    r2 = np.array([0.02, -0.01, 0.03, 0.00, 0.01])
    assert abs(stats.sharpe_ratio(r2) - r2.mean() / r2.std(ddof=1)) < 1e-12


def test_psr_at_own_sharpe_is_half():
    # PSR evaluated at the sample's OWN Sharpe must be exactly 0.5 (argument = 0 -> Phi(0)).
    rng = np.random.default_rng(1)
    r = rng.normal(0.001, 0.01, 4000)
    sr = stats.sharpe_ratio(r)
    assert abs(stats.probabilistic_sharpe_ratio(r, sr_star=sr) - 0.5) < 1e-9


def test_psr_mean_near_half_over_many_draws():
    # averaged over many zero-mean draws, PSR(0) centers on ~0.5
    vals = []
    for s in range(200):
        r = np.random.default_rng(s).normal(0.0, 0.01, 2000)
        vals.append(stats.probabilistic_sharpe_ratio(r))
    assert 0.4 < float(np.mean(vals)) < 0.6


def test_psr_strong_signal_to_one():
    rng = np.random.default_rng(2)
    r = rng.normal(0.002, 0.01, 3000)  # SR ~ 0.2/bar over 3000 obs
    assert stats.probabilistic_sharpe_ratio(r) > 0.999


def test_min_trl_infinite_when_below_benchmark():
    # deterministically-negative Sharpe: MinTRL against 0 must be infinite
    r = np.array([-0.02, -0.01, -0.03, 0.005, -0.015, -0.02, -0.01] * 20)
    assert stats.sharpe_ratio(r) < 0
    assert stats.min_track_record_length(r, sr_star=0.0) == float("inf")


def test_min_trl_finite_and_reasonable():
    rng = np.random.default_rng(4)
    r = rng.normal(0.001, 0.01, 2000)
    mtrl = stats.min_track_record_length(r, sr_star=0.0, prob=0.95)
    assert np.isfinite(mtrl) and mtrl > 0


def test_expected_max_sharpe_monotone_in_N_and_V():
    ts_low = np.array([0.0, 0.01, -0.01, 0.02, -0.02])
    ts_high = ts_low * 3.0
    # larger dispersion -> larger benchmark
    assert stats.expected_max_sharpe(ts_high, 100) > stats.expected_max_sharpe(ts_low, 100)
    # more trials -> larger benchmark
    assert stats.expected_max_sharpe(ts_low, 1000) > stats.expected_max_sharpe(ts_low, 10)


def test_dsr_higher_N_lowers_dsr():
    rng = np.random.default_rng(5)
    oos = rng.normal(0.0015, 0.01, 1500)
    trials = rng.normal(0.0, 0.05, 320)
    d_small = stats.deflated_sharpe_ratio(oos, trials, n_trials=10)
    d_big = stats.deflated_sharpe_ratio(oos, trials, n_trials=5000)
    assert d_big.dsr <= d_small.dsr  # more trials => harder hurdle


def test_profit_factor():
    assert abs(stats.profit_factor(np.array([2.0, 1.0, -1.0])) - 3.0) < 1e-12
    assert stats.profit_factor(np.array([1.0, 2.0])) == float("inf")
    assert np.isnan(stats.profit_factor(np.array([])))


def test_psr_dsr_annualization_invariant():
    # scaling all returns by a constant leaves Sharpe/PSR/DSR unchanged
    rng = np.random.default_rng(6)
    r = rng.normal(0.001, 0.01, 1500)
    trials = rng.normal(0.0, 0.04, 100)
    a = stats.deflated_sharpe_ratio(r, trials, n_trials=1000)
    b = stats.deflated_sharpe_ratio(r * 7.3, trials, n_trials=1000)
    assert abs(a.dsr - b.dsr) < 1e-9
    assert abs(a.sr_hat - b.sr_hat) < 1e-9
