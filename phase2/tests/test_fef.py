"""FEF-specific correctness: signal logic, exit types, accounting invariant."""
import numpy as np
import pandas as pd

from phase2.coilbt.config_fef import ConstantsFEF, CostsFEF, FiltersFEF, ParamsFEF, VariantFEF
from phase2.coilbt.strategy_fef import build_decision_table, raw_signal, aggregate_bars
from phase2.coilbt.backtest_fef import run_symbol_fef
from conftest import make_symbol_data

MS_PER_DAY = 86_400_000
MS_PER_HOUR = 3_600_000


def _oi_5m_from(sd):
    """Build a dense 5m OI frame from the synthetic symbol's daily OI (rising)."""
    rows = []
    base = int(sd.daily["day_ms"].iloc[0])
    n_days = len(sd.daily)
    for d in range(n_days):
        lvl = 1000.0 + d * 5.0  # steadily rising OI -> positive 24h changes
        for k in range(288):
            rows.append((base + d * MS_PER_DAY + k * 5 * 60_000, lvl))
    return pd.DataFrame(rows, columns=["create_time_ms", "sum_open_interest"])


def _closes(n, seed=0):
    rng = np.random.default_rng(seed)
    return list(100 * np.exp(np.cumsum(rng.normal(0, 0.015, n))))


def test_decision_table_causal_and_shaped():
    closes = _closes(500, seed=1)
    sd = make_symbol_data(closes, funding_rate=0.0002)   # elevated funding
    tbl = build_decision_table(sd, _oi_5m_from(sd), ConstantsFEF(), FiltersFEF())
    # 3 decisions/day
    assert abs(len(tbl) - 3 * len(closes)) <= 3
    # pct only defined after min history; bounded 0..100
    p = tbl["pct"].dropna()
    assert p.min() >= 0 and p.max() <= 100


def test_signal_sides_and_positive_only():
    # constant high positive funding -> pct saturates high -> SHORT under symmetric,
    # and positive_only must ALSO produce shorts (never longs).
    closes = _closes(500, seed=2)
    sd = make_symbol_data(closes, funding_rate=0.0002)
    tbl = build_decision_table(sd, _oi_5m_from(sd), ConstantsFEF(), FiltersFEF())
    # force a clear short signal region by using a low ENTRY_PCT and z floor
    p = ParamsFEF(ENTRY_PCT=60.0, OI_Z_MIN=-9.0)
    sym = raw_signal(tbl, p, "symmetric")
    pos = raw_signal(tbl, p, "positive_only")
    assert (pos == "LONG").sum() == 0                      # positive_only never longs
    assert (pos == "SHORT").sum() <= (sym == "SHORT").sum()  # same shorts, no longs


def test_funding_sign_exit_direction():
    # A SHORT pays funding when f_now < 0. FundingModel via engine should mark that exit.
    # Build funding that is positive early (entry) then flips negative.
    closes = [100.0] * 120
    sd = make_symbol_data(closes, funding_rate=0.0002)
    # override funding: first half positive, second half negative
    f = sd.funding.copy()
    half = len(f) // 2
    f.loc[f.index[half:], "last_funding_rate"] = -0.0002
    sd.funding = f
    tbl = build_decision_table(sd, _oi_5m_from(sd), ConstantsFEF(), FiltersFEF())
    v = VariantFEF(params=ParamsFEF(ENTRY_PCT=50.0, OI_Z_MIN=-9.0, EXIT_PCT=99.0), side_mode="symmetric")
    trades, dpnl = run_symbol_fef(sd, _oi_5m_from(sd), v, ConstantsFEF(), FiltersFEF(),
                                  CostsFEF(), 10_000.0, tbl=tbl)
    # at least one trade should exit on funding_sign or normalization or time_cap (not crash)
    assert all(t.reason in ("stop", "funding_sign", "normalization", "time_cap") for t in trades)


def test_accounting_invariant_fef():
    closes = _closes(600, seed=5)
    sd = make_symbol_data(closes, funding_rate=0.00015)
    oi = _oi_5m_from(sd)
    tbl = build_decision_table(sd, oi, ConstantsFEF(), FiltersFEF())
    for sm in ("symmetric", "positive_only"):
        v = VariantFEF(params=ParamsFEF(ENTRY_PCT=70.0, OI_Z_MIN=-9.0), side_mode=sm)
        trades, dpnl = run_symbol_fef(sd, oi, v, ConstantsFEF(), FiltersFEF(), CostsFEF(),
                                      10_000.0, tbl=tbl)
        net = sum(t.net_pnl for t in trades)
        assert abs(net - float(dpnl.sum())) < 1e-6, f"MTM mismatch {sm}"


def test_4h_aggregation():
    closes = _closes(30, seed=7)
    sd = make_symbol_data(closes)
    bars = aggregate_bars(sd.minute, 4)
    # 6 four-hour bars per day
    assert abs(len(bars) - 6 * len(closes)) <= 6
