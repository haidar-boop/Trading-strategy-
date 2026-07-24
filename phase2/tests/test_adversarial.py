"""
Adversarial data simulations (#14): inject corrupted / missing / delayed data and verify the
engine degrades SANELY — the accounting invariant (daily MTM == trade net P&L) must still hold,
P&L stays finite, and no crash. A backtest that silently mis-accounts on bad data is worse than
one that fails loudly; these tests pin that it does neither.
"""
import numpy as np
import pandas as pd

from phase2.coilbt.config_carry import ConstantsCarry, CostsCarry, FiltersCarry, ParamsCarry, VariantCarry
from phase2.coilbt.strategy_carry import build_carry_table
from phase2.coilbt.backtest_carry import run_symbol_carry, build_aligned
from conftest import make_symbol_data

MS_PER_DAY = 86_400_000


def _spot_from_perp(sd, basis_frac=0.0005):
    m = sd.minute.rename(columns={"open_time_ms": "open_time"}).copy()
    for c in ["open", "high", "low", "close"]:
        m[c] = m[c] * (1 - basis_frac)
    return m[["open_time", "open", "high", "low", "close"]]


def _run(sd, spot):
    tbl = build_carry_table(sd, spot, ConstantsCarry(), FiltersCarry())
    aligned = build_aligned(sd, spot)
    v = VariantCarry(ParamsCarry(ENTRY_FUND_BPS=1.0, EXIT_FUND_BPS=0.0))
    return run_symbol_carry(sd, spot, v, ConstantsCarry(), FiltersCarry(), CostsCarry(),
                            10_000.0, tbl, aligned)


def _invariant(trades, dpnl):
    net = sum(t.net_pnl for t in trades)
    assert np.isfinite(net) and np.isfinite(float(dpnl.sum()))
    assert abs(net - float(dpnl.sum())) < 1e-6, "accounting invariant broke under adversarial data"


def _base():
    closes = list(100 * np.exp(np.cumsum(np.random.default_rng(7).normal(0, 0.02, 500))))
    sd = make_symbol_data(closes, funding_rate=0.0003)
    return sd, _spot_from_perp(sd)


def test_missing_candles():
    sd, spot = _base()
    # drop 5% of perp minute bars at random -> gaps
    rng = np.random.default_rng(1)
    keep = rng.random(len(sd.minute)) > 0.05
    sd.minute = sd.minute[keep].reset_index(drop=True)
    trades, dpnl = _run(sd, spot)
    _invariant(trades, dpnl)


def test_corrupted_price_spike():
    sd, spot = _base()
    # inject a 10x spike in a handful of perp bars (fat-finger / bad tick)
    m = sd.minute.copy()
    idx = [1000, 5000, 20000]
    for i in idx:
        if i < len(m):
            m.loc[i, ["open", "high", "low", "close"]] *= 10.0
    sd.minute = m
    trades, dpnl = _run(sd, spot)
    _invariant(trades, dpnl)
    assert all(np.isfinite(t.net_pnl) for t in trades)


def test_negative_and_inverted_basis():
    # spot ABOVE perp (inverted basis) -> basis negative; engine must handle signs cleanly
    sd, _ = _base()
    spot = _spot_from_perp(sd, basis_frac=-0.002)  # spot 20bps above perp
    trades, dpnl = _run(sd, spot)
    _invariant(trades, dpnl)


def test_delayed_missing_funding():
    sd, spot = _base()
    # drop 20% of funding prints (delayed / missing feed)
    rng = np.random.default_rng(3)
    f = sd.funding
    sd.funding = f[rng.random(len(f)) > 0.2].reset_index(drop=True)
    trades, dpnl = _run(sd, spot)
    _invariant(trades, dpnl)


def test_nan_prices():
    sd, spot = _base()
    m = sd.minute.copy()
    m.loc[3000:3010, ["open", "high", "low", "close"]] = np.nan
    sd.minute = m.dropna(subset=["open"]).reset_index(drop=True)  # feed handler drops NaN rows
    trades, dpnl = _run(sd, spot)
    _invariant(trades, dpnl)
