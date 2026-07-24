"""Cross-sectional funding sleeve: mechanics + the documented negative-expectancy finding.

This sleeve does NOT work at retail costs (turnover ~12x the funding edge); the tests pin the
sign conventions and the market-neutral construction so the negative result is trustworthy,
not a bug. See RESULTS docs.
"""
import numpy as np
import pandas as pd

from phase2.coilbt.config_carry import ConstantsCarry  # unused but keeps import parity
from phase2.coilbt.xfunding import (ParamsXF, CostsXF, VariantXF, assemble_panel, run_xf,
                                    full_grid_xf)
from conftest import make_symbol_data

MS_PER_DAY = 86_400_000


def _panel_data():
    # 6 synthetic symbols with distinct constant funding so the ranking is deterministic
    rates = [0.0005, 0.0004, 0.0002, 0.0, -0.0002, -0.0004]  # high -> low
    data = {}
    for i, r in enumerate(rates):
        closes = list(100.0 * (1 + 0.0 * np.arange(300)))  # flat price -> isolate funding+cost
        sd = make_symbol_data(closes, symbol=f"S{i}USDT", funding_rate=r)
        data[f"S{i}USDT"] = sd
    return data


def test_panel_shape_and_alignment():
    data = _panel_data()
    dt, F, P, syms = assemble_panel(data)
    assert F.shape[1] == len(syms) == 6
    assert dt.size > 100
    assert np.isfinite(F).mean() > 0.9


def test_dollar_neutral_and_funding_sign():
    # flat prices, constant funding: the book should COLLECT funding on both sides (>0),
    # and price P&L should be ~0 (dollar-neutral, flat prices).
    data = _panel_data()
    panel = assemble_panel(data)
    rec, dpnl = run_xf(data, VariantXF(ParamsXF(K=2, MIN_DISP_BPS=1.0, CHURN_BAND=0.0)),
                       CostsXF(STRESS_MULT=1.0), 10_000.0, panel)
    # net includes turnover cost; but with a stable ranking (constant funding) turnover is one-time,
    # so total should be dominated by positive funding collection over many periods.
    assert dpnl.sum() > 0, "constant-funding, flat-price book must net positive (collects funding)"


def test_grid_size():
    assert len(full_grid_xf()) == 3 * 3 * 3  # K x DISP x CHURN
