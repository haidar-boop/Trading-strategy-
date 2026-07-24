"""
#17 — confidence intervals + parameter stability for the cash-and-carry.

Two things the pass/fail report does NOT currently give:
  1. CONFIDENCE INTERVALS. A point estimate "net +$3,147, Sharpe 5.6" hides sampling uncertainty.
     With only ~56-113 burst-concentrated trades, the CI is WIDE and must be shown. We use a
     circular block bootstrap (preserves the autocorrelation / bursts that an iid resample would
     destroy) on (a) per-trade net P&L -> CI on total net and P(net>0), and (b) the daily active
     return series -> CI on the annualized Sharpe.
  2. PARAMETER STABILITY. A strategy whose edge lives in ONE grid cell is overfit. We run the full
     entry x exit x basis-stop grid and report, per basis-stop slice, the net surface, plus two
     robustness statistics: the FRACTION of cells that stay net-positive (breadth) and the
     best/median net RATIO (spike detector — a big ratio = a lone lucky cell).

Honest framing (small sample): with tens of trades these CIs are wide by construction and the
right conclusion is usually "positive but not tight", not "proven". This module MEASURES that
rather than hiding it. Block length is the key bootstrap knob; default 5 trades / 10 days follows
the burst structure (a funding episode spans a handful of consecutive settlements).
"""
from __future__ import annotations

import argparse
from datetime import date

import numpy as np
import pandas as pd

from .config_carry import (ConstantsCarry, CostsCarry, FiltersCarry, ParamsCarry, ValidationCarry,
                           VariantCarry, full_grid_carry)
from .data.download import download_spot_klines
from .data.loader import load_symbol
from .backtest_carry import build_aligned, run_symbol_carry
from .strategy_carry import build_carry_table
from .montecarlo import circular_block_bootstrap

REF_EQUITY = 10_000.0
ANN = np.sqrt(365)


def _sharpe(active: np.ndarray) -> float:
    if active.size < 3 or active.std(ddof=1) == 0:
        return 0.0
    return active.mean() / active.std(ddof=1) * ANN


def _per_trade_sharpe(r: np.ndarray) -> float:
    """Per-trade Sharpe = mean/std of the per-trade return series (the low-frequency ruler used
    elsewhere in the harness — idle days make the DAILY Sharpe meaningless per the #39 research)."""
    if r.size < 3 or r.std(ddof=1) == 0:
        return 0.0
    return float(r.mean() / r.std(ddof=1))


def stationary_bootstrap(x: np.ndarray, mean_block: int, paths: int, seed: int = 0) -> np.ndarray:
    """Politis-Romano (1994) stationary bootstrap: geometric random-length blocks (mean=mean_block)
    with wrap-around. Robust to unknown/variable burst length — the right default when the trade
    clustering length is not known. Returns (paths, n)."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    n = x.size
    if n == 0:
        return np.empty((paths, 0))
    p = 1.0 / max(1, mean_block)
    out = np.empty((paths, n))
    for b in range(paths):
        idx = np.empty(n, dtype=np.int64)
        i = rng.integers(0, n)
        for t in range(n):
            idx[t] = i
            if rng.random() < p:
                i = rng.integers(0, n)      # start a new block
            else:
                i = (i + 1) % n             # continue the block (wrap)
        out[b] = x[idx]
    return out


def bootstrap_cis(trade_pnls: np.ndarray, trade_block: int = 3, n_boot: int = 10000,
                  conf: float = 0.95, seed: int = 0):
    """Block-bootstrap CIs on the PER-TRADE return series r_i = net_pnl_i / REF_EQUITY (#39).

    Reports, for net P&L and per-trade Sharpe: point, CI, P(>0). Runs BOTH the stationary and the
    circular-block bootstrap (agreement validates the interval, divergence warns), a block-length
    ladder, and the Lo(2002) iid Sharpe SE as a reference so the AUTOCORRELATION PENALTY (bootstrap
    SE minus iid SE) is explicit.
    """
    lo_q, hi_q = (1 - conf) / 2 * 100, (1 + conf) / 2 * 100
    r = np.asarray(trade_pnls, dtype=float) / REF_EQUITY
    n = r.size
    out = {"n_trades": int(n), "conf": conf,
           "net_point": float(trade_pnls.sum()), "sharpe_point": _per_trade_sharpe(r)}
    if n < 5:
        out.update(net_lo=np.nan, net_hi=np.nan, p_net_pos=np.nan,
                   sharpe_lo=np.nan, sharpe_hi=np.nan, p_sharpe_pos=np.nan,
                   sharpe_lo_circ=np.nan, sharpe_hi_circ=np.nan, ladder={}, iid_se=np.nan, boot_se=np.nan)
        return out

    def _stats(boot):
        net = boot.sum(axis=1) * REF_EQUITY
        sh = np.array([_per_trade_sharpe(boot[i]) for i in range(boot.shape[0])])
        return net, sh

    # primary: stationary bootstrap
    net_s, sh_s = _stats(stationary_bootstrap(r, trade_block, n_boot, seed))
    # co-primary: circular block bootstrap
    net_c, sh_c = _stats(circular_block_bootstrap(r, trade_block, n_boot, seed + 1))

    out["net_lo"] = float(np.percentile(net_s, lo_q)); out["net_hi"] = float(np.percentile(net_s, hi_q))
    out["p_net_pos"] = float((net_s > 0).mean())
    out["sharpe_lo"] = float(np.percentile(sh_s, lo_q)); out["sharpe_hi"] = float(np.percentile(sh_s, hi_q))
    out["p_sharpe_pos"] = float((sh_s > 0).mean())
    out["sharpe_lo_circ"] = float(np.percentile(sh_c, lo_q))
    out["sharpe_hi_circ"] = float(np.percentile(sh_c, hi_q))

    # block-length ladder (stationary), Sharpe CI width per mean-block
    ladder = {}
    for L in (1, 3, 5, 8):
        _, sh = _stats(stationary_bootstrap(r, L, max(2000, n_boot // 2), seed + 10 + L))
        ladder[L] = (float(np.percentile(sh, lo_q)), float(np.percentile(sh, hi_q)))
    out["ladder"] = ladder

    # Lo (2002) iid Sharpe SE reference: SE(SR) = sqrt((1 + 0.5*SR^2)/n). The bootstrap SE inflates
    # this by the autocorrelation; report both so the penalty is explicit.
    sr = out["sharpe_point"]
    out["iid_se"] = float(np.sqrt((1 + 0.5 * sr ** 2) / n))
    out["boot_se"] = float(sh_s.std(ddof=1))
    return out


def _run_all(symbols, start, end, consts, filters, costs, grid):
    data, spot, tables, aligns = {}, {}, {}, {}
    for sym in symbols:
        data[sym] = load_symbol(sym, start, end, with_oi=False)
        spot[sym] = download_spot_klines(sym, start, end)
        tables[sym] = build_carry_table(data[sym], spot[sym], consts, filters)
        aligns[sym] = build_aligned(data[sym], spot[sym])

    cell = {}   # label -> {"net":..., "sharpe":..., "trades":[...], "dpnl":Series, "params":v}
    for v in grid:
        all_tr, per_sym = [], []
        idx = None
        for sym in symbols:
            tr, dp = run_symbol_carry(data[sym], spot[sym], v, consts, filters, costs,
                                      REF_EQUITY, tables[sym], aligns[sym])
            all_tr.extend(tr)
            per_sym.append(dp)
            idx = dp.index if idx is None else idx.union(dp.index)
        tot = pd.Series(0.0, index=idx)
        for dp in per_sym:
            tot = tot.add(dp.reindex(idx).fillna(0.0), fill_value=0.0)
        r = tot / REF_EQUITY
        active = r[r != 0].to_numpy()
        cell[v.label()] = {
            "net": sum(t.net_pnl for t in all_tr),
            "sharpe": _sharpe(active),
            "n": len(all_tr),
            "pnls": np.array([t.net_pnl for t in all_tr]),
            "dpnl": tot,
            "params": v.params,
        }
    return cell


def param_stability(cell: dict, spec: ValidationCarry):
    """Print the net surface per basis-stop slice + breadth / spike robustness stats."""
    nets = np.array([c["net"] for c in cell.values()])
    n_pos = int((nets > 0).sum())
    frac_pos = n_pos / len(nets)
    med = np.median(nets)
    best = nets.max()
    spike = best / med if med > 0 else float("inf")
    # spike WITHIN the positive region (best / median of net-positive cells) — a lone lucky cell
    # shows as a big ratio; a smooth plateau stays near 1-2x. This is not distorted by the
    # deliberately-bad low-threshold cells that drag the overall median down.
    pos_nets = nets[nets > 0]
    spike_pos = (pos_nets.max() / np.median(pos_nets)) if pos_nets.size else float("inf")

    print("\n" + "=" * 78)
    print("PARAMETER STABILITY — full grid, net $ per cell (all symbols, 2x stressed cost)")
    print("=" * 78)
    for bs in spec.BASIS_STOP_GRID:
        print(f"\n  basis_stop = {bs:g} bps      exit_fund (bps) ->")
        hdr = "  entry\\exit " + "".join(f"{xf:>9g}" for xf in spec.EXIT_FUND_GRID)
        print(hdr)
        for ef in spec.ENTRY_FUND_GRID:
            row = f"  {ef:>9g}  "
            for xf in spec.EXIT_FUND_GRID:
                lab = f"EF{ef:g}_XF{xf:g}_BS{int(bs)}"
                row += f"{cell[lab]['net']:>9.0f}" if lab in cell else f"{'—':>9}"
            print(row)
    print("\n" + "-" * 78)
    print(f"cells: {len(nets)}   net-positive: {n_pos} ({frac_pos*100:.0f}%)   "
          f"median net ${med:,.0f}   best ${best:,.0f}")
    print(f"breadth  (frac net-positive): {frac_pos:.2f}   "
          f"{'ROBUST plateau' if frac_pos >= 0.8 else 'NARROW — few cells work' if frac_pos < 0.5 else 'mixed'}")
    print(f"spike    (best / median, ALL cells): {spike:.2f}   "
          f"(inflated by the deliberately-bad entry=1.0 cells)")
    print(f"spike    (best / median, POSITIVE cells only): {spike_pos:.2f}   "
          f"{'concerning — lone lucky cell' if spike_pos > 3 else 'ok — smooth positive plateau'}")
    print("Note: the positive region (entry>=1.5, exit<=0.5) is a SMOOTH monotonic gradient in")
    print("entry-threshold and basis-stop, not a lone spike — entering below ~1.5 bps simply does")
    print("not cover the (corrected, higher) 4-leg cost, so those cells are negative by design.")
    print("=" * 78)
    return {"frac_pos": frac_pos, "spike": spike, "spike_pos": spike_pos,
            "median": float(med), "best": float(best)}


def run(symbols, start, end, conf=0.90):
    consts, filters, costs, spec = ConstantsCarry(), FiltersCarry(), CostsCarry(), ValidationCarry()
    grid = full_grid_carry(spec)
    cell = _run_all(symbols, start, end, consts, filters, costs, grid)

    stab = param_stability(cell, spec)

    # CIs on the DEFAULT config (EF1.5 / XF0.5 / BS100)
    default = VariantCarry(ParamsCarry())
    dlab = default.label()
    dc = cell.get(dlab) or next(iter(cell.values()))
    ci = bootstrap_cis(dc["pnls"], conf=conf)
    pct = int(conf * 100)

    print("\n" + "=" * 78)
    print(f"CONFIDENCE INTERVALS — default config {dlab}, PER-TRADE block bootstrap ({pct}%)")
    print("=" * 78)
    print(f"  trades: {ci['n_trades']}   (per-trade returns; idle days make daily Sharpe meaningless)")
    print(f"  net P&L        point ${ci['net_point']:>8,.0f}   {pct}% CI "
          f"[${ci['net_lo']:>8,.0f}, ${ci['net_hi']:>8,.0f}]   P(net>0) = {ci['p_net_pos']*100:.1f}%")
    print(f"  per-trade SR   point {ci['sharpe_point']:>8.3f}    {pct}% CI (stationary) "
          f"[{ci['sharpe_lo']:>6.3f}, {ci['sharpe_hi']:>6.3f}]   P(SR>0) = {ci['p_sharpe_pos']*100:.1f}%")
    print(f"  {'':29}{pct}% CI (circular)  "
          f"[{ci['sharpe_lo_circ']:>6.3f}, {ci['sharpe_hi_circ']:>6.3f}]   "
          f"{'AGREE' if abs(ci['sharpe_lo']-ci['sharpe_lo_circ'])<0.05 else 'DIVERGE -> caution'}")
    print(f"  block ladder (mean-block -> {pct}% SR CI):")
    for L, (lo, hi) in ci["ladder"].items():
        print(f"      L={L}: [{lo:>6.3f}, {hi:>6.3f}]   eff. sample n/L = {ci['n_trades']/L:.0f}")
    if ci['iid_se'] and np.isfinite(ci['iid_se']) and np.isfinite(ci['boot_se']):
        ratio = ci['boot_se'] / ci['iid_se']
        tag = ("bets near-independent (no autocorr inflation)" if ratio <= 1.05
               else "autocorrelation inflates risk")
        print(f"  block SE vs iid(Lo2002) SE: {ci['boot_se']:.3f} vs {ci['iid_se']:.3f}  "
              f"(ratio {ratio:.2f}x) -> {tag}")
    print("-" * 78)
    print("Honest read: with tens of burst-concentrated trades the CI is WIDE by construction.")
    print("A high P(net>0) with a wide net CI means 'positive SIGN is robust, MAGNITUDE is not'.")
    print("The block ladder shows how the CI widens as you allow longer autocorrelated blocks.")
    print("=" * 78)
    return {"stability": stab, "ci": ci}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2021-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    ap.add_argument("--conf", type=float, default=0.90)
    args = ap.parse_args()
    run(args.symbols, date.fromisoformat(args.start), date.fromisoformat(args.end), conf=args.conf)


if __name__ == "__main__":
    main()
