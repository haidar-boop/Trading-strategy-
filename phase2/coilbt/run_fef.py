"""
Phase-2 runner for Funding-Extreme Fade (Candidate 2). Reuses the strategy-agnostic
harness (walk-forward, DSR/PSR/MinTRL, Monte Carlo, cost/funding model, data layer);
only the strategy/engine/config are FEF-specific. Every number is measured on real data.

    python -m phase2.coilbt.run_fef --start 2020-01-01 --end 2025-12-31
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from . import stats
from .config_fef import ConstantsFEF, CostsFEF, FiltersFEF, ValidationFEF, full_grid_fef
from .costs import CostModel
from .data.download import download_metrics
from .data.loader import SymbolData, load_symbol
from .backtest_fef import run_symbol_fef
from .strategy_fef import build_decision_table
from .montecarlo import block_bootstrap_envelope
from .walkforward import generate_folds, trial_sharpes, walk_forward_select
from .run_phase2 import (REF_EQUITY, ARTIFACTS, _beta_in_costume, _portfolio_daily_returns,
                         _run_jitter, _verdict)


def _best_month_excision(deployed: pd.Series) -> dict:
    """FEF-specific: removing the single best OOS calendar month must leave OOS PnL > 0."""
    if deployed.size < 30:
        return {"pass": False, "total": float("nan"), "ex_best": float("nan")}
    # additive daily P&L (returns are small; sum is a fair proxy for the equity delta)
    monthly = deployed.groupby(deployed.index.to_period("M")).sum()
    total = float(deployed.sum())
    ex_best = float(total - monthly.max())
    return {"pass": bool(ex_best > 0), "total": total, "ex_best": ex_best,
            "best_month": str(monthly.idxmax())}


def run(symbols, start, end, spec, consts, filters, costs_cfg, risk_frac=0.01, verbose=True):
    t0 = time.time()
    data, oi = {}, {}
    tables = {}
    for sym in symbols:
        if verbose:
            print(f"[load] {sym} ...", flush=True)
        data[sym] = load_symbol(sym, start, end)
        oi[sym] = download_metrics(sym, start, end)
        tables[sym] = build_decision_table(data[sym], oi[sym], consts, filters)

    grid = full_grid_fef(spec, risk_frac=risk_frac)
    if verbose:
        print(f"[grid] {len(grid)} variants x {len(symbols)} symbols", flush=True)

    variant_returns, variant_trades = {}, {}
    for gi, v in enumerate(grid):
        per_sym, all_tr = {}, []
        for sym in symbols:
            tr, dpnl = run_symbol_fef(data[sym], oi[sym], v, consts, filters, costs_cfg,
                                      REF_EQUITY, tbl=tables[sym])
            per_sym[sym] = dpnl
            all_tr.extend(tr)
        variant_returns[v.label()] = _portfolio_daily_returns(per_sym)
        variant_trades[v.label()] = all_tr
        if verbose and (gi + 1) % 48 == 0:
            print(f"[grid] {gi+1}/{len(grid)} ({time.time()-t0:.0f}s)", flush=True)

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
    cm = CostModel(costs_cfg.TAKER_FEE_BPS, costs_cfg.MAKER_FEE_BPS, costs_cfg.SLIPPAGE_BPS)
    jitter = _run_jitter(oos_meta, data, cm, spec)
    beta = _beta_in_costume(deployed, data.get("BTCUSDT"))
    excision = _best_month_excision(deployed)

    checks = {
        "dsr_pass": bool(dsr.dsr >= spec.DSR_CONF),
        "pf_pass": bool(pf == float("inf") or (np.isfinite(pf) and pf >= spec.OOS_PF_MIN)),
        "trades_pass": bool(oos_pnls.size >= spec.OOS_MIN_TRADES),
        "mintrl_pass": bool(dsr.n_obs >= dsr.min_trl),
        "single_episode_pass": bool(excision["pass"]),
        "mc_envelope_pass": bool(boot.passed),
        "mc_jitter_pass": bool(jitter["passed"]) if jitter else False,
    }
    verdict = _verdict(checks, oos_pnls.size, spec.OOS_MIN_TRADES)

    result = {
        "strategy": "Funding-Extreme Fade (FEF)",
        "window": {"start": str(start), "end": str(end), "symbols": symbols},
        "n_variants": len(grid), "n_folds": len(folds),
        "oos_days": int(r_oos.size), "oos_trades": int(oos_pnls.size),
        "side_breakdown": {"long": int(sum(1 for t in oos_meta if t.side > 0)),
                           "short": int(sum(1 for t in oos_meta if t.side < 0))},
        "exit_reasons": {r: int(sum(1 for t in oos_meta if t.reason == r))
                         for r in ["stop", "funding_sign", "normalization", "time_cap"]},
        "selected_per_fold": [(str(f.oos_start.date()), lab) for f, lab in selected],
        "metrics": {
            "oos_sharpe_annualized": dsr.sr_hat * np.sqrt(365.0),
            "psr_vs_0": psr0, "dsr": dsr.dsr,
            "dsr_deflation_benchmark": dsr.sr_star_deflated, "dsr_n_trials": dsr.n_trials,
            "min_trl_obs": dsr.min_trl, "profit_factor": pf,
            "best_month_excision_total": excision["total"], "ex_best_month": excision["ex_best"],
            "mc_real_terminal": boot.real_terminal, "mc_p5_terminal": boot.p5_terminal,
            "jitter_base_terminal": jitter["base_terminal"] if jitter else None,
            "jitter_median_terminal": jitter["jitter_median"] if jitter else None,
            "beta_corr_to_btc": beta["corr"],
            "total_funding_pnl": float(sum(t.funding_pnl for t in oos_meta)),
        },
        "checks": checks, "verdict": verdict, "runtime_sec": round(time.time() - t0, 1),
    }
    if verbose:
        _print_report(result)
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "fef_result.json").write_text(json.dumps(result, indent=2, default=float))
    if deployed.size:
        eq = (1.0 + deployed).cumprod()
        pd.DataFrame({"date": deployed.index, "daily_return": deployed.values,
                      "equity": eq.values}).to_csv(ARTIFACTS / "fef_oos_equity.csv", index=False)
    return result


def _print_report(r):
    m = r["metrics"]
    print("\n" + "=" * 72)
    print("FUNDING-EXTREME FADE — PHASE-2 OOS REPORT (all numbers measured)")
    print("=" * 72)
    print(f"Window {r['window']['start']}..{r['window']['end']}  symbols={r['window']['symbols']}")
    print(f"Variants={r['n_variants']} folds={r['n_folds']} OOS days={r['oos_days']} OOS trades={r['oos_trades']}")
    print(f"  side: {r['side_breakdown']}  exits: {r['exit_reasons']}")
    print("-" * 72)
    print(f"  OOS Sharpe (ann.)      {m['oos_sharpe_annualized']:+.3f}")
    print(f"  PSR vs 0               {m['psr_vs_0']:.3f}")
    print(f"  Deflated Sharpe (DSR)  {m['dsr']:.4f}  (benchmark {m['dsr_deflation_benchmark']:.4f}, N={m['dsr_n_trials']})")
    print(f"  MinTRL (obs)           {m['min_trl_obs']:.0f}  vs OOS days {r['oos_days']}")
    print(f"  OOS profit factor      {m['profit_factor']:.3f}")
    print(f"  total funding P&L      {m['total_funding_pnl']:+.2f}")
    print(f"  ex-best-month PnL      {m['ex_best_month']:+.4f} (total {m['best_month_excision_total']:+.4f})")
    print(f"  MC real vs p5 terminal {m['mc_real_terminal']:.4f} vs {m['mc_p5_terminal']:.4f}")
    print(f"  jitter med vs base     {m['jitter_median_terminal']} vs {m['jitter_base_terminal']}")
    print(f"  corr to BTC B&H        {m['beta_corr_to_btc']:.3f}")
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
        ValidationFEF(), ConstantsFEF(), FiltersFEF(), CostsFEF())


if __name__ == "__main__":
    main()
