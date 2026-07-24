"""
Tests for the ATM VRP falsification module — pin the causal realized-vol label and the
monthly cost accounting. (Network fetch of DVOL is not tested here; the pure functions are.)
"""
import numpy as np
import pandas as pd

from phase2.coilbt.vrp_test import realized_vol_forward, monthly_vrp

MS_PER_DAY = 86_400_000


def _synth_spot(n_days=120, vol=0.03, seed=0):
    rng = np.random.default_rng(seed)
    day0 = 1_609_459_200_000
    # 1m bars are not needed; realized_vol_forward groups by day on close
    closes = 100 * np.exp(np.cumsum(rng.normal(0, vol, n_days)))
    ot = day0 + np.arange(n_days) * MS_PER_DAY
    return pd.DataFrame({"open_time": ot, "open": closes, "high": closes,
                         "low": closes, "close": closes})


def test_realized_vol_forward_is_forward_looking_and_annualized():
    spot = _synth_spot(120, vol=0.03, seed=1)
    rv = realized_vol_forward(spot, horizon_days=30)
    # last 30 rows have no forward window -> NaN
    assert rv["rv_fwd"].tail(30).isna().all()
    # a populated value should be a plausible annualized vol in % (0.03 daily ~ 57% ann)
    val = rv["rv_fwd"].dropna().iloc[0]
    assert 20 < val < 120


def test_realized_vol_uses_future_not_past():
    # build a series that is calm for 40 days then explosive -> RV_fwd at day 0 (calm-ahead) must be
    # LOWER than RV_fwd at day 45 (explosive-ahead). Confirms the window looks FORWARD.
    rng = np.random.default_rng(2)
    calm = rng.normal(0, 0.005, 45)
    wild = rng.normal(0, 0.06, 75)
    lr = np.concatenate([calm, wild])
    closes = 100 * np.exp(np.cumsum(lr))
    day0 = 1_609_459_200_000
    spot = pd.DataFrame({"open_time": day0 + np.arange(120) * MS_PER_DAY,
                         "open": closes, "high": closes, "low": closes, "close": closes})
    rv = realized_vol_forward(spot, horizon_days=30).set_index("day_ms")["rv_fwd"].to_numpy()
    assert rv[0] < rv[50]     # calm-ahead << wild-ahead


def test_monthly_vrp_cost_subtraction():
    day0 = 1_609_459_200_000
    days = day0 + np.arange(90) * MS_PER_DAY
    m = pd.DataFrame({
        "day_ms": days,
        "dvol_close": np.full(90, 60.0),
        "rv_fwd": np.full(90, 50.0),
        "vrp": np.full(90, 10.0),
        "day": pd.to_datetime(days, unit="ms", utc=True),
    })
    g = monthly_vrp(m, roll_spread_volpts=1.5, hedge_bleed_volpts=1.0)
    # gross 10 vol points, cost 2.5 -> net 7.5 each month
    assert np.allclose(g["gross"], 10.0)
    assert np.allclose(g["net"], 7.5)


def test_score_series_positive_stream():
    from phase2.coilbt.vrp_book import score_series
    import numpy as np
    rng = np.random.default_rng(0)
    net = rng.normal(6.0, 8.0, 46)          # clearly-positive monthly vol-point stream
    sc = score_series(net)
    assert sc["sharpe_ann"] > 0 and sc["psr0"] > 0.9
    assert sc["maxdd_volpts"] <= 0 and sc["cvar5_m"] < sc["mean_m"]


def test_score_series_needs_min_length():
    from phase2.coilbt.vrp_book import score_series
    import numpy as np
    assert score_series(np.array([1.0, 2.0, 3.0])) is None


def test_tradeable_monthly_one_row_per_month_variance_space():
    from phase2.coilbt.vrp_test import tradeable_monthly
    day0 = 1_609_459_200_000
    days = day0 + np.arange(90) * MS_PER_DAY   # 3 months
    m = pd.DataFrame({
        "day_ms": days, "dvol_close": np.full(90, 60.0), "rv_fwd": np.full(90, 50.0),
        "vrp": np.full(90, 10.0), "day": pd.to_datetime(days, unit="ms", utc=True),
    })
    g = tradeable_monthly(m, roll_day=15, variance_space=True)
    assert len(g) == 3                          # ONE straddle per month, not 90 overlapping
    # variance-space P&L (60^2-50^2)/(2*60) = 1100/120 = 9.1667
    assert np.allclose(g["gross"], (60.0**2 - 50.0**2) / (2 * 60.0))
    # variance-space < linear IV-RV (=10) because of convexity normalization
    assert g["gross"].iloc[0] < 10.0
