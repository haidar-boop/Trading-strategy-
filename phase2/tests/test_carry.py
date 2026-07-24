"""Cash-and-carry correctness: delta-neutrality, funding sign, 4-leg costs, invariant."""
import numpy as np
import pandas as pd

from phase2.coilbt.config_carry import ConstantsCarry, CostsCarry, FiltersCarry, ParamsCarry, VariantCarry
from phase2.coilbt.strategy_carry import build_carry_table, raw_signal_carry
from phase2.coilbt.backtest_carry import run_symbol_carry, build_aligned
from conftest import make_symbol_data

MS_PER_DAY = 86_400_000


def _spot_from_perp(sd, basis_frac=0.0):
    """Build a spot minute frame = perp minus a constant basis fraction (delta hedge target)."""
    m = sd.minute.copy()
    m = m.rename(columns={"open_time_ms": "open_time"})
    m["open"] = m["open"] * (1 - basis_frac)
    m["high"] = m["high"] * (1 - basis_frac)
    m["low"] = m["low"] * (1 - basis_frac)
    m["close"] = m["close"] * (1 - basis_frac)
    return m[["open_time", "open", "high", "low", "close"]]


def test_delta_neutral_price_pnl_small():
    # perp and spot move together (constant basis) -> price(basis) P&L ~ 0; only funding + cost.
    closes = list(100 * np.exp(np.cumsum(np.random.default_rng(0).normal(0, 0.03, 400))))
    sd = make_symbol_data(closes, funding_rate=0.0003)   # 3 bps/8h positive funding
    spot = _spot_from_perp(sd, basis_frac=0.001)          # spot 10 bps below perp, constant
    tbl = build_carry_table(sd, spot, ConstantsCarry(), FiltersCarry())
    aligned = build_aligned(sd, spot)
    v = VariantCarry(ParamsCarry(ENTRY_FUND_BPS=1.0, EXIT_FUND_BPS=0.0))
    trades, dpnl = run_symbol_carry(sd, spot, v, ConstantsCarry(), FiltersCarry(), CostsCarry(),
                                    10_000.0, tbl, aligned)
    assert len(trades) > 0
    # basis constant -> per-trade price P&L tiny relative to funding
    for t in trades:
        assert abs(t.price_pnl) < abs(t.funding_pnl) + 1.0


def test_funding_is_received_on_positive_funding():
    closes = [100.0] * 300
    sd = make_symbol_data(closes, funding_rate=0.0004)    # +4 bps/8h
    spot = _spot_from_perp(sd, basis_frac=0.0)
    tbl = build_carry_table(sd, spot, ConstantsCarry(), FiltersCarry())
    aligned = build_aligned(sd, spot)
    v = VariantCarry(ParamsCarry(ENTRY_FUND_BPS=1.0, EXIT_FUND_BPS=0.0))
    trades, _ = run_symbol_carry(sd, spot, v, ConstantsCarry(), FiltersCarry(), CostsCarry(),
                                 10_000.0, tbl, aligned)
    # short perp receives positive funding -> funding_pnl > 0 for every trade
    assert all(t.funding_pnl > 0 for t in trades)


def test_accounting_invariant_carry():
    closes = list(100 * np.exp(np.cumsum(np.random.default_rng(3).normal(0, 0.025, 500))))
    sd = make_symbol_data(closes, funding_rate=0.00025)
    spot = _spot_from_perp(sd, basis_frac=0.0008)
    tbl = build_carry_table(sd, spot, ConstantsCarry(), FiltersCarry())
    aligned = build_aligned(sd, spot)
    for ef in (1.0, 1.5):
        v = VariantCarry(ParamsCarry(ENTRY_FUND_BPS=ef, EXIT_FUND_BPS=0.0))
        trades, dpnl = run_symbol_carry(sd, spot, v, ConstantsCarry(), FiltersCarry(), CostsCarry(),
                                        10_000.0, tbl, aligned)
        net = sum(t.net_pnl for t in trades)
        assert abs(net - float(dpnl.sum())) < 1e-6, f"MTM mismatch EF={ef}"


def test_symmetric_fallback_four_leg_cost():
    # SPOT_ASYMMETRIC=False recovers the legacy symmetric model: cost == (fee+slip)*(4 legs).
    closes = [100.0] * 200
    sd = make_symbol_data(closes, funding_rate=0.0005)
    spot = _spot_from_perp(sd, basis_frac=0.0)
    tbl = build_carry_table(sd, spot, ConstantsCarry(), FiltersCarry())
    aligned = build_aligned(sd, spot)
    v = VariantCarry(ParamsCarry(ENTRY_FUND_BPS=1.0, EXIT_FUND_BPS=0.0))
    trades, _ = run_symbol_carry(sd, spot, v, ConstantsCarry(), FiltersCarry(),
                                 CostsCarry(STRESS_MULT=1.0, SPOT_ASYMMETRIC=False),
                                 10_000.0, tbl, aligned)
    leg = (5.0 + 2.0) * 1e-4
    for t in trades:
        assert 3.5 * leg * t.notional < t.cost < 4.5 * leg * t.notional


def test_asymmetric_spot_cost_is_higher():
    # #38: the spot leg (10bps taker) is ~2x the perp leg (5bps), plus 2bps legging per side.
    # With flat prices (impact=0) and STRESS_MULT=1: cost/trade ~= (perp_leg + spot_leg + legging)*2*N
    #   perp_leg = 7bps, spot_leg = 11bps, legging = 2bps -> 20bps/side -> ~40bps/trade.
    closes = [100.0] * 200
    sd = make_symbol_data(closes, funding_rate=0.0005)
    spot = _spot_from_perp(sd, basis_frac=0.0)
    tbl = build_carry_table(sd, spot, ConstantsCarry(), FiltersCarry())
    aligned = build_aligned(sd, spot)
    v = VariantCarry(ParamsCarry(ENTRY_FUND_BPS=1.0, EXIT_FUND_BPS=0.0))
    cfg = CostsCarry(STRESS_MULT=1.0)   # SPOT_ASYMMETRIC=True by default
    sym = CostsCarry(STRESS_MULT=1.0, SPOT_ASYMMETRIC=False)
    tr_a, _ = run_symbol_carry(sd, spot, v, ConstantsCarry(), FiltersCarry(), cfg, 10_000.0, tbl, aligned)
    tr_s, _ = run_symbol_carry(sd, spot, v, ConstantsCarry(), FiltersCarry(), sym, 10_000.0, tbl, aligned)
    # asymmetric must cost strictly more than symmetric (spot 2x + legging)
    assert sum(t.cost for t in tr_a) > sum(t.cost for t in tr_s)
    per_side = (7.0 + 11.0 + 2.0) * 1e-4   # perp + spot + legging
    for t in tr_a:
        assert 1.9 * per_side * t.notional < t.cost < 2.1 * per_side * t.notional


def test_entry_threshold_gates():
    closes = [100.0] * 300
    sd = make_symbol_data(closes, funding_rate=0.0001)   # exactly baseline 1 bp
    spot = _spot_from_perp(sd)
    tbl = build_carry_table(sd, spot, ConstantsCarry(), FiltersCarry())
    # ENTRY at 2 bps -> baseline 1bp funding never qualifies -> no signal
    assert raw_signal_carry(tbl, ParamsCarry(ENTRY_FUND_BPS=2.0)).sum() == 0
    # ENTRY at 1 bp -> qualifies
    assert raw_signal_carry(tbl, ParamsCarry(ENTRY_FUND_BPS=1.0)).sum() > 0
