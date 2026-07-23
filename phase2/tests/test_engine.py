"""Engine correctness: hold-resolution per exit type + the daily-MTM accounting invariant."""
import numpy as np
import pandas as pd

from phase2.coilbt.config import Constants, Costs, Filters, Params, Variant
from phase2.coilbt.costs import BPS, FundingModel
from phase2.coilbt.backtest import _resolve_hold, run_symbol
from conftest import make_symbol_data

MIN = 60_000


def _minute_series(prices, start_ms=0):
    n = len(prices)
    t = np.array([start_ms + i * MIN for i in range(n)], dtype="int64")
    px = np.asarray(prices, dtype=float)
    return t, px.copy(), px.copy(), px.copy(), px.copy()  # open=high=low=close=price


def _no_funding():
    return FundingModel(pd.DataFrame({"calc_time": np.array([], dtype="int64"),
                                      "last_funding_rate": np.array([], dtype=float)}))


def test_hard_stop_long():
    # price drifts down below entry - stop_dist -> stop exit
    prices = [100.0] * 5 + [99, 98, 97, 96, 95]
    t, o, h, l, c = _minute_series(prices)
    idx, px, reason = _resolve_hold(+1, 100.0, 3.0, t[0], t, o, h, l, c, 0,
                                    100 * 86_400_000, _no_funding(), 1000.0, 0.0025)
    assert reason == "stop"
    assert px <= 97.0001  # fills at/below hard stop 100-3=97


def test_time_cap():
    # flat price for > 14 days at 1-min bars would be huge; use a short cap via constant
    prices = [100.0] * 50
    t, o, h, l, c = _minute_series(prices)
    max_hold = 10 * MIN  # 10-minute cap for the test
    idx, px, reason = _resolve_hold(+1, 100.0, 50.0, t[0], t, o, h, l, c, 0,
                                    max_hold, _no_funding(), 1000.0, 0.0025)
    assert reason == "time_cap"
    assert (t[idx] - t[0]) >= max_hold


def test_funding_budget_stop():
    # flat price, big positive funding on a long -> adverse funding trips the 25bps budget
    prices = [100.0] * 60
    t, o, h, l, c = _minute_series(prices)
    fund = FundingModel(pd.DataFrame({
        "calc_time": np.array([t[0] + 20 * MIN], dtype="int64"),
        "last_funding_rate": np.array([0.0030], dtype=float),   # 30 bps > 25 bps budget
    }))
    idx, px, reason = _resolve_hold(+1, 100.0, 50.0, t[0], t, o, h, l, c, 0,
                                    100 * 86_400_000, fund, 1000.0, 25 * BPS)
    assert reason == "funding_budget"
    assert t[idx] >= t[0] + 20 * MIN


def test_trailing_stop_ratchets():
    # price rises to 110 then falls; chandelier with stop_dist=5 exits near 105 (110-5),
    # NOT at the hard stop 95.
    up = list(np.linspace(100, 110, 11))
    down = list(np.linspace(109, 100, 10))
    prices = up + down
    t, o, h, l, c = _minute_series(prices)
    idx, px, reason = _resolve_hold(+1, 100.0, 5.0, t[0], t, o, h, l, c, 0,
                                    100 * 86_400_000, _no_funding(), 1000.0, 0.0025)
    assert reason == "stop"
    assert 104.0 <= px <= 106.5  # trailed up, exits around 110-5=105


def test_accounting_invariant_random():
    # daily MTM must sum exactly to the sum of trade net P&L, on real-ish synthetic data.
    rng = np.random.default_rng(11)
    closes = list(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 500))))
    sd = make_symbol_data(closes)
    for oi_on in (True, False):
        v = Variant(params=Params(), oi_on=oi_on, side_mode="both")
        trades, dpnl = run_symbol(sd, v, Constants(), Filters(), Costs(), 10_000.0)
        net = sum(tr.net_pnl for tr in trades)
        assert abs(net - float(dpnl.sum())) < 1e-6, f"MTM mismatch oi_on={oi_on}"
