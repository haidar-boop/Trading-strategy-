"""
Generalization + economic decomposition analysis for the cash-and-carry (#18, #19).

Runs the DEFAULT config on the full data, then slices the resulting trades/daily-P&L by
period (per calendar year) and by symbol subset (BTC-only, ETH-only, all) and reports, for
each cell: net P&L decomposed into funding / basis / cost, annualized Sharpe, and trade count.

This directly tests fragility: does the edge survive the 2022 crash? on BTC alone? every year?
And it attributes every dollar (funding vs basis vs cost) per regime.
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


def _decompose(trades, dpnl, start_ms, end_ms):
    tr = [t for t in trades if start_ms <= t.entry_ms < end_ms]
    if not tr:
        return None
    d = dpnl[(dpnl.index >= pd.Timestamp(start_ms, unit="ms", tz="UTC")) &
             (dpnl.index < pd.Timestamp(end_ms, unit="ms", tz="UTC"))]
    r = d / REF_EQUITY
    active = r[r != 0]
    sharpe = (active.mean() / active.std() * np.sqrt(365)) if active.size > 2 and active.std() > 0 else 0.0
    return {
        "n": len(tr),
        "funding": sum(t.funding_pnl for t in tr),
        "basis": sum(t.price_pnl for t in tr),
        "cost": -sum(t.cost for t in tr),
        "net": sum(t.net_pnl for t in tr),
        "sharpe": sharpe,
    }


def run(symbols, start, end, costs):
    consts, filters = ConstantsCarry(), FiltersCarry()
    default = VariantCarry(ParamsCarry())
    per_sym_trades, per_sym_dpnl = {}, {}
    for sym in symbols:
        print(f"[load] {sym}", flush=True)
        sd = load_symbol(sym, start, end, with_oi=False)
        spot = download_spot_klines(sym, start, end)
        tbl = build_carry_table(sd, spot, consts, filters)
        aligned = build_aligned(sd, spot)
        tr, dp = run_symbol_carry(sd, spot, default, consts, filters, costs, REF_EQUITY, tbl, aligned)
        per_sym_trades[sym] = tr
        per_sym_dpnl[sym] = dp

    def agg(subset, s, e):
        s_ms = int(pd.Timestamp(s, tz="UTC").timestamp() * 1000)
        e_ms = int(pd.Timestamp(e, tz="UTC").timestamp() * 1000)
        alltr = [t for sym in subset for t in per_sym_trades[sym]]
        idx = None
        for sym in subset:
            idx = per_sym_dpnl[sym].index if idx is None else idx.union(per_sym_dpnl[sym].index)
        tot = pd.Series(0.0, index=idx)
        for sym in subset:
            tot = tot.add(per_sym_dpnl[sym].reindex(idx).fillna(0.0), fill_value=0.0)
        return _decompose(alltr, tot, s_ms, e_ms)

    print("\n" + "=" * 92)
    print("GENERALIZATION x ECONOMIC DECOMPOSITION — default config, 2x stressed cost (all measured)")
    print("=" * 92)
    hdr = f"{'slice':<22}{'trades':>7}{'funding':>10}{'basis':>9}{'cost':>9}{'NET':>9}{'Sharpe':>8}"

    print("\n-- By calendar year (all symbols) --"); print(hdr)
    for y in range(2021, 2026):
        d = agg(symbols, f"{y}-01-01", f"{y+1}-01-01")
        if d:
            print(f"{str(y):<22}{d['n']:>7}{d['funding']:>10.0f}{d['basis']:>9.0f}{d['cost']:>9.0f}{d['net']:>9.0f}{d['sharpe']:>8.2f}")

    print("\n-- By symbol subset (full period) --"); print(hdr)
    for name, sub in [("BTC only", ["BTCUSDT"]), ("ETH only", ["ETHUSDT"]),
                      ("BTC+ETH", ["BTCUSDT", "ETHUSDT"]), ("all 10", symbols)]:
        sub = [s for s in sub if s in symbols]
        d = agg(sub, str(start), str(end))
        if d:
            print(f"{name:<22}{d['n']:>7}{d['funding']:>10.0f}{d['basis']:>9.0f}{d['cost']:>9.0f}{d['net']:>9.0f}{d['sharpe']:>8.2f}")
    print("=" * 92)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2021-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--symbols", nargs="+",
                    default=["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
                             "BNBUSDT", "ADAUSDT", "LINKUSDT", "AVAXUSDT", "LTCUSDT"])
    args = ap.parse_args()
    run(args.symbols, date.fromisoformat(args.start), date.fromisoformat(args.end), CostsCarry())


if __name__ == "__main__":
    main()
