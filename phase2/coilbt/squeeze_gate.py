"""
#20 actionable distillation: does the OI-confirmation / squeeze-rejection gate improve the real
cash-and-carry backtest?

The funding-predictability study (funding_predict.py) showed that POINT-FORECASTING funding does
not beat the naive threshold at the entry decision. The research converged instead on one
economically-grounded RISK filter: reject entries where elevated funding is a short-squeeze about
to invert (price rising while OI falls = short covering). This runs the DEFAULT carry config with
the gate OFF vs ON on BTC+ETH (the OI-covered symbols) and reports the measured delta.

Honest expectation: in a calm in-sample the squeeze->flip event is rare, so the gate should remove
few trades and barely move net P&L. Its value is insurance against a tail the backtest underweights
(same limitation as the tail-stress engine), justified by mechanism, not by a big in-sample gain.
This run MEASURES that rather than asserting it.
"""
from __future__ import annotations

import argparse
from datetime import date

import numpy as np
import pandas as pd

from .config_carry import ConstantsCarry, CostsCarry, FiltersCarry, ParamsCarry, VariantCarry
from .data.download import download_spot_klines
from .data.loader import load_symbol
from .backtest_carry import build_aligned, run_symbol_carry
from .strategy_carry import build_carry_table

REF_EQUITY = 10_000.0


def _summ(trades, dpnl):
    r = (dpnl / REF_EQUITY)
    active = r[r != 0]
    sharpe = (active.mean() / active.std() * np.sqrt(365)) if active.size > 2 and active.std() > 0 else 0.0
    return {
        "n": len(trades),
        "funding": sum(t.funding_pnl for t in trades),
        "cost": -sum(t.cost for t in trades),
        "net": sum(t.net_pnl for t in trades),
        "sharpe": sharpe,
    }


def run(symbols, start, end):
    consts, filters, costs = ConstantsCarry(), FiltersCarry(), CostsCarry()
    print("=" * 84)
    print("SQUEEZE-REJECTION GATE (#20) — default carry, OI gate OFF vs ON, 2x stressed cost")
    print("=" * 84)
    print(f"{'symbol':<10}{'gate':<6}{'trades':>7}{'rejected':>9}{'funding':>10}{'cost':>9}"
          f"{'NET':>9}{'Sharpe':>8}")
    print("-" * 84)
    agg = {False: [], True: []}
    for sym in symbols:
        sd = load_symbol(sym, start, end, with_oi=True)   # OI needed for the gate
        spot = download_spot_klines(sym, start, end)
        tbl = build_carry_table(sd, spot, consts, filters)
        aligned = build_aligned(sd, spot)
        n_flag = int((~tbl["ok_oi"].to_numpy(dtype=bool)).sum())
        res = {}
        for use in (False, True):
            v = VariantCarry(ParamsCarry(USE_OI_GATE=use))
            tr, dp = run_symbol_carry(sd, spot, v, consts, filters, costs, REF_EQUITY, tbl, aligned)
            s = _summ(tr, dp)
            res[use] = s
            agg[use].append((sym, tr, dp))
        rej = res[False]["n"] - res[True]["n"]
        for use in (False, True):
            s = res[use]
            tag = "ON" if use else "OFF"
            extra = f"{rej:>9}" if use else f"{'':>9}"
            print(f"{sym:<10}{tag:<6}{s['n']:>7}{extra}{s['funding']:>10.0f}{s['cost']:>9.0f}"
                  f"{s['net']:>9.0f}{s['sharpe']:>8.2f}")
        print(f"{'':10}{'(squeeze-flagged decisions in feed: %d)' % n_flag}")
    print("=" * 84)
    print("Reading: 'rejected' = entries the gate removed. If ~0 and NET barely changes, the")
    print("squeeze->flip tail did not occur in-sample; the gate is cheap insurance, not an in-sample")
    print("edge. A LARGE net drop would mean the gate is throwing away good trades (bad). Neither")
    print("overclaims: the honest role of this filter is tail risk reduction, measured here.")
    print("=" * 84)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2021-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    args = ap.parse_args()
    run(args.symbols, date.fromisoformat(args.start), date.fromisoformat(args.end))


if __name__ == "__main__":
    main()
