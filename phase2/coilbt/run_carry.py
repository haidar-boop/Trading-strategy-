"""
Phase-2 runner for the delta-neutral cash-and-carry. Reuses the full harness
(walk-forward, DSR/PSR/MinTRL, PBO/CSCV, Monte Carlo, rich metrics) plus the
√-impact stressed-cost option. Loads perp + spot + funding per symbol.

    python -m phase2.coilbt.run_carry --start 2020-01-01 --end 2025-12-31
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import date

import numpy as np
import pandas as pd

from . import stats
from .config_carry import (ConstantsCarry, CostsCarry, FiltersCarry, ValidationCarry,
                           full_grid_carry)
from .costs import CostModel
from .data.download import download_spot_klines
from .data.loader import load_symbol
from .backtest_carry import build_aligned, run_symbol_carry
from .strategy_carry import build_carry_table
from .montecarlo import block_bootstrap_envelope
from .walkforward import generate_folds, trial_sharpes, walk_forward_select
from .run_phase2 import (REF_EQUITY, ARTIFACTS, _beta_in_costume, _portfolio_daily_returns,
                         _run_jitter, _verdict, compute_pbo, rich_metrics)
from .run_fef import _best_month_excision


def run(symbols, start, end, spec, consts, filters, costs_cfg, notional_frac=0.5, verbose=True):
    t0 = time.time()
    data, spot, tables, aligns = {}, {}, {}, {}
    for sym in symbols:
        if verbose:
            print(f"[load] {sym} perp+spot ...", flush=True)
        data[sym] = load_symbol(sym, start, end)
        spot[sym] = download_spot_klines(sym, start, end)
        tables[sym] = build_carry_table(data[sym], spot[sym], consts, filters)
        aligns[sym] = build_aligned(data[sym], spot[sym])

    grid = full_grid_carry(spec, notional_frac=notional_frac)
    if verbose:
        print(f"[grid] {len(grid)} variants x {len(symbols)} symbols", flush=True)

    variant_returns, variant_trades = {}, {}
    for v in grid:
        per_sym, all_tr = {}, []
        for sym in symbols:
            tr, dpnl = run_symbol_carry(data[sym], spot[sym], v, consts, filters, costs_cfg,
                                        REF_EQUITY, tables[sym], aligns[sym])
            per_sym[sym] = dpnl
            all_tr.extend(tr)
        variant_returns[v.label()] = _portfolio_daily_returns(per_sym)
        variant_trades[v.label()] = all_tr

    cal = None
    for r in variant_returns.values():
        cal = r.index if cal is None else cal.union(r.index)
    cal = pd.DatetimeIndex(sorted(cal))
    variant_returns = {k: v.reindex(cal).fillna(0.0) for k, v in variant_returns.items()}

    folds = generate_folds(cal, spec.IS_MONTHS, spec.OOS_MONTHS, spec.STEP_MONTHS)
    deployed, selected, oos_windows, trial_oos = walk_forward_select(
        variant_returns, folds, spec.PURGE_DAYS, spec.EMBARGO_DAYS)

    r_oos = deployed.to_numpy(dtype=float)
    ts = trial_sharpes(trial_oos)
    dsr = stats.deflated_sharpe_ratio(r_oos, ts, n_trials=spec.TRIAL_COUNT_N, conf=spec.DSR_CONF)
    psr0 = stats.probabilistic_sharpe_ratio(r_oos, sr_star=0.0)

    epoch = pd.Timestamp("1970-01-01", tz="UTC")
    oos_pnls, oos_meta = [], []
    for (fold, lab) in selected:
        s = (fold.oos_start - epoch) // pd.Timedelta(milliseconds=1)
        e = (fold.oos_end - epoch) // pd.Timedelta(milliseconds=1)
        for t in variant_trades[lab]:
            if s <= t.entry_ms < e:
                oos_pnls.append(t.net_pnl)
                oos_meta.append(t)
    oos_pnls = np.asarray(oos_pnls, dtype=float)
    pf = stats.profit_factor(oos_pnls)

    boot = block_bootstrap_envelope(r_oos, spec.MC_BLOCK_TRADES, spec.MC_PATHS,
                                    pctile=spec.MC_ENVELOPE_PCTILE, seed=0)
    cm = CostModel(costs_cfg.TAKER_FEE_BPS, 2.0, costs_cfg.SLIPPAGE_BPS)
    jitter = _run_jitter(oos_meta, data, cm, spec)
    beta = _beta_in_costume(deployed, data.get("BTCUSDT"))
    excision = _best_month_excision(deployed)
    pbo, pbo_n = compute_pbo(trial_oos)
    rmets = rich_metrics(r_oos)

    checks = {
        "dsr_pass": bool(dsr.dsr >= spec.DSR_CONF),
        "pf_pass": bool(pf == float("inf") or (np.isfinite(pf) and pf >= spec.OOS_PF_MIN)),
        "trades_pass": bool(oos_pnls.size >= spec.OOS_MIN_TRADES),
        "mintrl_pass": bool(dsr.n_obs >= dsr.min_trl),
        "single_episode_pass": bool(excision["pass"]),
        "pbo_pass": bool(np.isfinite(pbo) and pbo < 0.5),
        "mc_envelope_pass": bool(boot.passed),
        "mc_jitter_pass": bool(jitter["passed"]) if jitter else False,
    }
    verdict = _verdict(checks, oos_pnls.size, spec.OOS_MIN_TRADES)

    result = {
        "strategy": "Delta-neutral cash-and-carry",
        "window": {"start": str(start), "end": str(end), "symbols": symbols},
        "n_variants": len(grid), "n_folds": len(folds),
        "oos_days": int(r_oos.size), "oos_trades": int(oos_pnls.size),
        "exit_reasons": {r: int(sum(1 for t in oos_meta if t.reason == r))
                         for r in ["funding_decay", "basis_stop", "time_cap"]},
        "selected_per_fold": [(str(f.oos_start.date()), lab) for f, lab in selected],
        "metrics": {
            "oos_sharpe_annualized": dsr.sr_hat * np.sqrt(365.0),
            "psr_vs_0": psr0, "dsr": dsr.dsr,
            "dsr_deflation_benchmark": dsr.sr_star_deflated, "dsr_n_trials": dsr.n_trials,
            "min_trl_obs": dsr.min_trl, "profit_factor": pf,
            "total_funding_pnl": float(sum(t.funding_pnl for t in oos_meta)),
            "total_basis_pnl": float(sum(t.price_pnl for t in oos_meta)),
            "total_cost": float(sum(t.cost for t in oos_meta)),
            "total_net_pnl": float(oos_pnls.sum()),
            "ex_best_month": excision["ex_best"], "best_month_total": excision["total"],
            "mc_real_terminal": boot.real_terminal, "mc_p5_terminal": boot.p5_terminal,
            "jitter_base_terminal": jitter["base_terminal"] if jitter else None,
            "jitter_median_terminal": jitter["jitter_median"] if jitter else None,
            "beta_corr_to_btc": beta["corr"], "pbo": pbo, "pbo_n_configs": pbo_n, "rich": rmets,
        },
        "checks": checks, "verdict": verdict, "runtime_sec": round(time.time() - t0, 1),
    }
    if verbose:
        _print_report(result)
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "carry_result.json").write_text(json.dumps(result, indent=2, default=float))
    if deployed.size:
        eq = (1.0 + deployed).cumprod()
        pd.DataFrame({"date": deployed.index, "daily_return": deployed.values,
                      "equity": eq.values}).to_csv(ARTIFACTS / "carry_oos_equity.csv", index=False)
    return result


def _print_report(r):
    m = r["metrics"]
    print("\n" + "=" * 72)
    print("DELTA-NEUTRAL CASH-AND-CARRY — PHASE-2 OOS REPORT (all measured)")
    print("=" * 72)
    print(f"Window {r['window']['start']}..{r['window']['end']}  symbols={r['window']['symbols']}")
    print(f"Variants={r['n_variants']} folds={r['n_folds']} OOS days={r['oos_days']} OOS trades={r['oos_trades']}")
    print(f"  exits: {r['exit_reasons']}")
    print("-" * 72)
    print(f"  OOS Sharpe (ann.)      {m['oos_sharpe_annualized']:+.3f}")
    print(f"  Deflated Sharpe (DSR)  {m['dsr']:.4f}  (benchmark {m['dsr_deflation_benchmark']:.4f}, N={m['dsr_n_trials']})")
    print(f"  MinTRL (obs)           {m['min_trl_obs']:.0f}  vs OOS days {r['oos_days']}")
    print(f"  OOS profit factor      {m['profit_factor']:.3f}")
    print(f"  P&L decomp: funding={m['total_funding_pnl']:+.1f}  basis={m['total_basis_pnl']:+.1f}"
          f"  cost={m['total_cost']:+.1f}  NET={m['total_net_pnl']:+.1f}")
    if m.get("pbo") is not None:
        print(f"  PBO / CSCV             {m['pbo']:.3f}  over {m['pbo_n_configs']} configs")
    rm = m.get("rich") or {}
    if rm:
        parts = [f"{k}={rm[k]:+.3f}" for k in ["Sortino", "Calmar", "MaxDD", "CVaR95"]
                 if k in rm and rm[k] == rm[k]]
        print("  rich (deployed OOS):  ", "  ".join(parts))
    print("-" * 72)
    for k, ok in r["checks"].items():
        print(f"    [{'PASS' if ok else 'FAIL'}] {k}")
    print("-" * 72)
    print("VERDICT:", r["verdict"])
    print(f"(runtime {r['runtime_sec']}s)")
    print("=" * 72 + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2020-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    args = ap.parse_args()
    run(args.symbols, date.fromisoformat(args.start), date.fromisoformat(args.end),
        ValidationCarry(), ConstantsCarry(), FiltersCarry(), CostsCarry())


if __name__ == "__main__":
    main()
