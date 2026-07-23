"""Causality guard: features at day t must not change when FUTURE data is perturbed."""
import numpy as np
import pandas as pd

from phase2.coilbt.config import Constants, Filters, Params, Variant
from phase2.coilbt.strategy import compute_features, raw_entry_signal
from conftest import make_symbol_data


def _rng_closes(n, seed=0):
    rng = np.random.default_rng(seed)
    steps = rng.normal(0, 0.02, n)
    return list(100 * np.exp(np.cumsum(steps)))


def test_features_are_causal():
    closes = _rng_closes(500, seed=7)
    sd = make_symbol_data(closes, minute_path=False)
    p, c, f = Params(), Constants(), Filters()
    feat = compute_features(sd, p, c, f)

    # perturb a FUTURE day (index 400) massively and recompute
    closes2 = list(closes)
    closes2[400] *= 1.5
    sd2 = make_symbol_data(closes2, minute_path=False)
    feat2 = compute_features(sd2, p, c, f)

    # all features strictly before day 400 must be identical (bit-for-bit on finite entries)
    cols = ["atr", "hh", "ll", "rw", "comp_thresh", "compressed", "fr", "ok_vol", "ok_data"]
    a = feat.iloc[:400][cols]
    b = feat2.iloc[:400][cols]
    for col in cols:
        va, vb = a[col].to_numpy(), b[col].to_numpy()
        mask = np.isfinite(pd.to_numeric(pd.Series(va), errors="coerce")) if va.dtype != bool else np.ones_like(va, bool)
        assert np.array_equal(np.where(mask, va, 0), np.where(mask, vb, 0)), f"look-ahead in {col}"


def test_channel_excludes_current_bar():
    # A single up-spike on day t must be a breakout (close[t] > max(prior L highs)),
    # i.e. the channel high excludes bar t itself.
    closes = [100.0] * 60
    closes[59] = 130.0  # spike on the last day
    sd = make_symbol_data(closes, minute_path=False, high_mult=1.0, low_mult=1.0)
    feat = compute_features(sd, Params(L=20), Constants(), Filters())
    # hh at day 59 = max high over days 39..58 (all ~100), so close 130 > hh -> breakout
    assert feat["close"].iloc[59] > feat["hh"].iloc[59]


def test_compression_denominator_is_prev_close():
    # rw uses close[t-1]; a huge close[t] must not change rw[t] (guards denominator leak).
    closes = _rng_closes(400, seed=3)
    sd = make_symbol_data(closes, minute_path=False)
    feat = compute_features(sd, Params(), Constants(), Filters())
    closes2 = list(closes); closes2[380] *= 3.0
    sd2 = make_symbol_data(closes2, minute_path=False)
    feat2 = compute_features(sd2, Params(), Constants(), Filters())
    # rw at day 380 depends on highs/lows[t-L:t] and close[t-1], NOT close[t]
    assert abs(float(feat["rw"].iloc[380]) - float(feat2["rw"].iloc[380])) < 1e-12
