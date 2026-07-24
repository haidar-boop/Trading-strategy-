"""
Tests for the funding-predictability study — the point is to PIN THE NO-LEAKAGE property, since
leakage is the #1 way to fake predictive edge. If any feature or the walk-forward peeked at the
future, a model fit on PURE NOISE features would score OOS R^2 > 0. These tests assert it cannot.
"""
import numpy as np
import pandas as pd

from phase2.coilbt.funding_predict import (
    build_funding_panel, walk_forward, _ridge_fit, _ridge_pred, _r2, FEATURES,
)
from phase2.coilbt.data.loader import SymbolData, MS_PER_DAY

MS_8H = 8 * 3_600_000


def _synth_symbol(n_days=600, seed=0):
    rng = np.random.default_rng(seed)
    closes = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, n_days)))
    day0 = 1_609_459_200_000  # 2021-01-01
    day_ms = day0 + np.arange(n_days) * MS_PER_DAY
    daily = pd.DataFrame({
        "open": closes, "high": closes, "low": closes, "close": closes,
        "volume": 1e3, "quote_volume": 2e9, "med_1m_dollar_vol": 1e6,
        "n_minutes": 1440, "day_ms": day_ms, "decision_ms": day_ms + MS_PER_DAY,
    }, index=pd.to_datetime(day_ms, unit="ms", utc=True))
    # 3 settlements/day, AR(1) funding so persistence is a real baseline
    n_set = n_days * 3
    ct = day0 + np.arange(n_set) * MS_8H
    f = np.zeros(n_set)
    for i in range(1, n_set):
        f[i] = 0.9 * f[i - 1] + rng.normal(0, 0.0001)
    funding = pd.DataFrame({"calc_time": ct, "funding_interval_hours": 8, "last_funding_rate": f})
    oi = 1e9 * (1 + 0.1 * np.cumsum(rng.normal(0, 0.01, n_days)))
    oi_daily = pd.DataFrame({"oi_level": oi, "delta_oi": np.concatenate([[np.nan], np.diff(oi)])},
                            index=daily.index)
    minute = pd.DataFrame({"open_time_ms": day_ms, "open": closes, "high": closes,
                           "low": closes, "close": closes})
    return SymbolData("TESTUSDT", daily, minute, funding, oi_daily)


def test_target_is_strictly_forward():
    sd = _synth_symbol()
    panel = build_funding_panel(sd, k_fwd=3)
    f = sd.funding.sort_values("calc_time").reset_index(drop=True)["last_funding_rate"].to_numpy()
    # target[i] must equal mean of settlements i+1..i+3 (strictly future), never include i.
    for i in [10, 100, 500]:
        assert np.isclose(panel["target"].iloc[i], f[i + 1:i + 4].mean())
    # last k_fwd rows have no future -> NaN target
    assert panel["target"].iloc[-1] != panel["target"].iloc[-1]  # NaN


def test_features_use_only_past():
    """f_now at row i must equal the settlement AT i (not i+1); trailing means never see the future."""
    sd = _synth_symbol()
    panel = build_funding_panel(sd, k_fwd=3)
    f = sd.funding.sort_values("calc_time").reset_index(drop=True)["last_funding_rate"].to_numpy()
    assert np.allclose(panel["f_now"].to_numpy(), f)
    # f_mean at i is the trailing rolling mean ending at i -> <= max of window, and uses no i+1
    s = pd.Series(f).rolling(9, min_periods=3).mean().to_numpy()
    assert np.allclose(panel["f_mean"].to_numpy(), s, equal_nan=True)


def test_no_leakage_pure_noise_features_score_zero():
    """THE decisive leakage test: replace features with pure noise. A leak-free walk-forward must
    NOT achieve OOS R^2 meaningfully > 0 on noise. If it does, the pipeline peeked at the target."""
    rng = np.random.default_rng(42)
    n = 3000
    y = rng.normal(0, 1, n)                      # target = pure noise (no signal to find)
    df = pd.DataFrame({f: rng.normal(0, 1, n) for f in FEATURES})
    df["target"] = y
    df["f_now"] = rng.normal(0, 1, n)            # even f_now unrelated to target
    res = walk_forward(df, train_win=400, test_win=100, embargo=5, lam=10.0)
    assert res is not None
    # OOS R^2 on noise must be ~0 (allow tiny negative/positive sampling noise, never a real fit)
    assert res["r2_ridge"] < 0.05, f"leakage! noise scored R2={res['r2_ridge']:.3f}"


def test_ridge_recovers_known_linear_signal():
    """Sanity: when the target IS a linear function of features + noise, ridge OOS R^2 > 0."""
    rng = np.random.default_rng(1)
    n = 3000
    X = rng.normal(0, 1, (n, len(FEATURES)))
    beta = np.array([1.0, -0.5] + [0.0] * (len(FEATURES) - 2))
    y = X @ beta + rng.normal(0, 0.5, n)
    df = pd.DataFrame(X, columns=FEATURES)
    df["target"] = y
    res = walk_forward(df, lam=1.0)
    assert res["r2_ridge"] > 0.5


def test_ridge_standardization_no_train_test_bleed():
    """_ridge_fit must standardize on the passed (train) matrix only; predicting on a shifted test
    matrix must use the TRAIN mean/std, not recompute on test."""
    rng = np.random.default_rng(3)
    Xtr = rng.normal(5, 2, (200, 3))
    ytr = Xtr[:, 0] * 2 + rng.normal(0, 0.1, 200)
    m = _ridge_fit(Xtr, ytr, lam=1.0)
    # a test point equal to the train mean must predict ~ the train target mean
    pred = _ridge_pred(m, m["mu"].reshape(1, -1))
    assert np.isclose(pred[0], m["ybar"], atol=1e-6)
