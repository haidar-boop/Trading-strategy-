"""Cost + funding accrual correctness (sign conventions are load-bearing)."""
import numpy as np
import pandas as pd

from phase2.coilbt.costs import BPS, CostModel, FundingModel

MS_PER_DAY = 86_400_000


def _funding_df(rates_at_ms: dict[int, float]) -> pd.DataFrame:
    ts = sorted(rates_at_ms)
    return pd.DataFrame({
        "calc_time": np.array(ts, dtype="int64"),
        "last_funding_rate": np.array([rates_at_ms[t] for t in ts], dtype=float),
    })


def test_round_trip_costs():
    cm = CostModel()
    assert abs(cm.round_trip_frac(False, False) - 14 * BPS) < 1e-15   # taker+taker
    assert abs(cm.round_trip_frac(True, False) - 9 * BPS) < 1e-15     # maker entry + taker exit
    assert abs(cm.round_trip_frac(True, True) - 4 * BPS) < 1e-15      # maker+maker


def test_funding_sign_long_pays_when_positive():
    # settlement at t=100 with rate +0.01; a LONG held across it pays 0.01 (negative pnl)
    f = FundingModel(_funding_df({100: 0.01}))
    assert abs(f.funding_pnl_frac(+1, 50, 200) - (-0.01)) < 1e-12   # long pays
    assert abs(f.funding_pnl_frac(-1, 50, 200) - (+0.01)) < 1e-12   # short receives


def test_funding_settlement_boundaries():
    # settlement exactly at entry is NOT charged (strictly after); at exit IS charged.
    f = FundingModel(_funding_df({100: 0.01, 200: 0.02}))
    # entry=100 (exclusive), exit=200 (inclusive) -> only the 200 settlement counts
    assert abs(f.funding_pnl_frac(+1, 100, 200) - (-0.02)) < 1e-12
    # entry=50, exit=150 -> only the 100 settlement
    assert abs(f.funding_pnl_frac(+1, 50, 150) - (-0.01)) < 1e-12


def test_adverse_funding_accumulation():
    f = FundingModel(_funding_df({100: 0.01, 200: 0.01, 300: 0.01}))
    # long across all three positive settlements -> adverse = 0.03
    assert abs(f.adverse_funding_frac(+1, 50, 350) - 0.03) < 1e-12
    # short across the same -> receives, adverse = 0
    assert f.adverse_funding_frac(-1, 50, 350) == 0.0


def test_funding_empty():
    f = FundingModel(_funding_df({}))
    assert f.funding_pnl_frac(+1, 0, 10_000) == 0.0
