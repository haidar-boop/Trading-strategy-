"""
Tests for the funding-flip hazard falsification module: leak-free logistic hazard + the
duration diagnostic that carries the verdict.
"""
import numpy as np
import pandas as pd

from phase2.coilbt.funding_hazard import (
    _logistic_fit, _logistic_pred, _logloss, walk_forward_hazard, HAZ_FEATURES,
)


def test_logistic_recovers_known_signal():
    rng = np.random.default_rng(0)
    n = 2000
    X = rng.normal(0, 1, (n, 3))
    eta = 1.5 * X[:, 0] - 1.0 * X[:, 1]
    y = (rng.random(n) < 1 / (1 + np.exp(-eta))).astype(float)
    m = _logistic_fit(X, y, lam=1.0)
    p = _logistic_pred(m, X)
    # in-sample log-loss must beat the constant base rate predictor
    base = _logloss(y, np.full(n, y.mean()))
    assert _logloss(y, p) < base


def test_no_leakage_noise_features_do_not_beat_base():
    """Pure-noise features fed to the walk-forward hazard must NOT beat the constant-hazard
    baseline out-of-sample — if they did, the pipeline peeked."""
    rng = np.random.default_rng(1)
    n = 2000
    df = pd.DataFrame({f: rng.normal(0, 1, n) for f in HAZ_FEATURES})
    df["flip"] = (rng.random(n) < 0.3).astype(float)   # flips independent of features
    res = walk_forward_hazard(df, train_win=300, test_win=100, embargo=3, lam=1.0)
    assert res is not None
    # model log-loss must not materially beat the baseline on noise (allow tiny sampling wiggle)
    assert res["logloss_model"] >= res["logloss_base"] - 0.01
    assert 0.4 < res["auc"] < 0.6   # no discrimination on noise


def test_logloss_basic():
    # perfect prediction -> ~0 log-loss; worst -> large
    y = np.array([1.0, 0.0, 1.0, 0.0])
    assert _logloss(y, y) < 1e-4
    assert _logloss(y, 1 - y) > 5.0
