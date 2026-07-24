"""
Phase-2 runner: load real Binance data -> run the 320-variant grid -> purged
walk-forward selection -> DSR/PSR/MinTRL/PF on concatenated OOS -> Monte Carlo ->
pass/fail report against the pre-registered thresholds.

Every number this prints is MEASURED on real data. Nothing is invented. Where the
sample is too thin to conclude, the report says so (that is a legitimate verdict).

Usage:
    python -m phase2.coilbt.run_phase2 --start 2020-01-01 --end 2025-12-31
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from . import stats
from .config import Constants, Costs, Filters, ValidationSpec, full_grid
from .costs import BPS, CostModel
from .data.loader import SymbolData, load_symbol
from .montecarlo import _replay_terminal, block_bootstrap_envelope
from .backtest import run_symbol
from .walkforward import generate_folds, trial_sharpes, walk_forward_select
from .quantlib.pbo import pbo_cscv
from .quantlib import metrics as qmetrics


def compute_pbo(trial_oos: dict, n_subsets: int = 14):
    """Real-data PBO/CSCV over the grid: stack every variant's concatenated-OOS daily
    returns into a [T x N] matrix (all variants share the same OOS windows) and run CSCV.
    Returns (pbo, n_configs). PBO ~ 0.5 => the in-sample-best config is overfit noise."""
    cols, labels = [], []
    length = None
    for lab, r in trial_oos.items():
        if r is None or r.size == 0:
            continue
        if length is None:
            length = r.size
        if r.size == length:
            cols.append(r.to_numpy(dtype=float))
            labels.append(lab)
    if len(cols) < 2:
        return float("nan"), len(cols)
    M = np.column_stack(cols)
    pbo, _ = pbo_cscv(M, n_subsets=n_subsets)
    return pbo, len(cols)


def compute_effective_n(trial_oos: dict) -> float:
    """Effective number of INDEPENDENT trials from the grid's OOS return matrix (participation
    ratio of the trial correlation matrix). Corrects an over-inflated DSR deflation when configs
    are highly correlated. Always <= raw N — reported alongside, never instead of, the raw-N DSR."""
    from .quantlib.effn import effective_n_participation
    cols, length = [], None
    for r in trial_oos.values():
        if r is None or r.size == 0:
            continue
        if length is None:
            length = r.size
        if r.size == length:
            cols.append(r.to_numpy(dtype=float))
    if len(cols) < 2:
        return float(len(cols))
    return effective_n_participation(np.column_stack(cols))


def rich_metrics(returns) -> dict:
    """Sortino/Calmar/MaxDD/Ulcer/CVaR summary of a daily-return series (ported metrics)."""
    r = np.asarray(returns, dtype=float)
    if r.size < 5:
        return {}
    return qmetrics.summary(r, ann=365)

REF_EQUITY = 10_000.0
ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"


def _portfolio_daily_returns(per_symbol_daily_pnl: dict[str, pd.Series]) -> pd.Series:
    """Combine per-symbol daily P&L into portfolio daily returns on the shared calendar."""
    idx = None
    for s in per_symbol_daily_pnl.values():
        idx = s.index if idx is None else idx.union(s.index)
    total = pd.Series(0.0, index=idx)
    for s in per_symbol_daily_pnl.values():
        total = total.add(s.reindex(idx).fillna(0.0), fill_value=0.0)
    return total / REF_EQUITY


def run(symbols: list[str], start: date, end: date, spec: ValidationSpec,
        consts: Constants, filters: Filters, costs_cfg: Costs,
        f_risk: float = 0.005, verbose: bool = True) -> dict:
    t_start = time.time()
    data: dict[str, SymbolData] = {}
    for sym in symbols:
        if verbose:
            print(f"[load] {sym} ...", flush=True)
        data[sym] = load_symbol(sym, start, end)

    grid = full_grid(spec, f_risk=f_risk)
    if verbose:
        print(f"[grid] {len(grid)} variants x {len(symbols)} symbols", flush=True)

    # 1) Run every variant once over the full timeline; cache portfolio daily returns + trades.
    variant_returns: dict[str, pd.Series] = {}
    variant_trades: dict[str, list] = {}
    cm = CostModel(costs_cfg.TAKER_FEE_BPS, costs_cfg.MAKER_FEE_BPS, costs_cfg.SLIPPAGE_BPS)
    for gi, v in enumerate(grid):
        per_sym_pnl = {}
        all_trades = []
        for sym in symbols:
            trades, dpnl = run_symbol(data[sym], v, consts, filters, costs_cfg, REF_EQUITY)
            per_sym_pnl[sym] = dpnl
            all_trades.extend(trades)
        variant_returns[v.label()] = _portfolio_daily_returns(per_sym_pnl)
        variant_trades[v.label()] = all_trades
        if verbose and (gi + 1) % 40 == 0:
            print(f"[grid] {gi+1}/{len(grid)} done ({time.time()-t_start:.0f}s)", flush=True)

    # 2) Walk-forward selection on the shared daily calendar.
    cal = None
    for r in variant_returns.values():
        cal = r.index if cal is None else cal.union(r.index)
    cal = pd.DatetimeIndex(sorted(cal))
    variant_returns = {k: v.reindex(cal).fillna(0.0) for k, v in variant_returns.items()}

    folds = generate_folds(cal, spec.IS_MONTHS, spec.OOS_MONTHS, spec.STEP_MONTHS)
    if verbose:
        print(f"[wf] {len(folds)} folds", flush=True)
    deployed, selected, oos_windows, trial_oos = walk_forward_select(
        variant_returns, folds, spec.PURGE_DAYS, spec.EMBARGO_DAYS)

    # 3) Stats on the concatenated OOS record (deployed = per-fold-selected variant).
    r_oos = deployed.to_numpy(dtype=float)
    ts = trial_sharpes(trial_oos)  # dispersion V input, from all fixed variants on OOS
    dsr = stats.deflated_sharpe_ratio(r_oos, ts, n_trials=spec.TRIAL_COUNT_N, conf=spec.DSR_CONF)
    psr0 = stats.probabilistic_sharpe_ratio(r_oos, sr_star=0.0)

    # OOS trades = trades of the per-fold-selected variant whose ENTRY falls in that
    # fold's OOS window (a trade is attributed to the fold whose OOS it was entered in).
    oos_trade_pnls = []
    oos_trades_meta = []
    for (fold, lab) in selected:
        s = (fold.oos_start - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(milliseconds=1)
        e = (fold.oos_end - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(milliseconds=1)
        for t in variant_trades[lab]:
            if s <= t.entry_ms < e:
                oos_trade_pnls.append(t.net_pnl)
                oos_trades_meta.append(t)
    oos_trade_pnls = np.asarray(oos_trade_pnls, dtype=float)
    pf = stats.profit_factor(oos_trade_pnls)

    # 4) Monte Carlo on the deployed OOS returns + entry jitter on OOS trades.
    boot = block_bootstrap_envelope(r_oos, spec.MC_BLOCK_TRADES, spec.MC_PATHS,
                                    pctile=spec.MC_ENVELOPE_PCTILE, seed=0)
    jitter = _run_jitter(oos_trades_meta, data, cm, spec)

    # 5) Beta-in-a-costume: correlate deployed OOS daily returns with BTC daily returns.
    beta = _beta_in_costume(deployed, data.get("BTCUSDT"))

    # 6) PBO/CSCV (ported) on the real-data grid + rich metrics of the deployed record.
    pbo, pbo_n = compute_pbo(trial_oos)
    rmets = rich_metrics(r_oos)

    # ----- pass/fail -----
    checks = {
        "dsr_pass": bool(dsr.dsr >= spec.DSR_CONF),
        "pf_pass": bool(pf == float("inf") or (np.isfinite(pf) and pf >= spec.OOS_PF_MIN)),
        "trades_pass": bool(oos_trade_pnls.size >= spec.OOS_MIN_TRADES),
        "mintrl_pass": bool(dsr.n_obs >= dsr.min_trl),
        "pbo_pass": bool(np.isfinite(pbo) and pbo < 0.5),
        "mc_envelope_pass": bool(boot.passed),
        "mc_jitter_pass": bool(jitter["passed"]) if jitter else False,
    }
    verdict = _verdict(checks, oos_trade_pnls.size, spec.OOS_MIN_TRADES)

    result = {
        "window": {"start": str(start), "end": str(end), "symbols": symbols},
        "n_variants": len(grid),
        "n_folds": len(folds),
        "oos_days": int(r_oos.size),
        "oos_trades": int(oos_trade_pnls.size),
        "selected_per_fold": [(str(f.oos_start.date()), lab) for f, lab in selected],
        "metrics": {
            "oos_sharpe_per_bar": dsr.sr_hat,
            "oos_sharpe_annualized": dsr.sr_hat * np.sqrt(365.0),
            "psr_vs_0": psr0,
            "dsr": dsr.dsr,
            "dsr_deflation_benchmark": dsr.sr_star_deflated,
            "dsr_var_trials": dsr.var_trials,
            "dsr_n_trials": dsr.n_trials,
            "min_trl_obs": dsr.min_trl,
            "profit_factor": pf,
            "mc_real_terminal": boot.real_terminal,
            "mc_p5_terminal": boot.p5_terminal,
            "jitter_base_terminal": jitter["base_terminal"] if jitter else None,
            "jitter_median_terminal": jitter["jitter_median"] if jitter else None,
            "beta_corr_to_btc": beta["corr"],
            "pbo": pbo,
            "pbo_n_configs": pbo_n,
            "rich": rmets,
        },
        "checks": checks,
        "verdict": verdict,
        "runtime_sec": round(time.time() - t_start, 1),
    }
    if verbose:
        _print_report(result)
        _print_rich(result)
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "phase2_result.json").write_text(json.dumps(result, indent=2, default=float))
    _save_equity(deployed)
    return result


def _run_jitter(oos_trades_meta, data, cm, spec):
    """Portfolio entry-timing jitter: PER PATH, jitter every trade (all symbols) and sum
    into ONE portfolio terminal, then take the median across paths. (Summing per-symbol
    medians would be statistically meaningless — median of a sum != sum of medians.)"""
    if not oos_trades_meta:
        return None
    ecf, xcf = cm.entry_cost_frac(False), cm.exit_cost_frac(False)
    sym_arrays = {}   # sym -> (m_time, m_open, [replay dicts])
    for sym, sd in data.items():
        m = sd.minute.sort_values("open_time_ms").reset_index(drop=True)
        mt = m["open_time_ms"].to_numpy("int64")
        mo = m["open"].to_numpy(float)
        trs = []
        for t in oos_trades_meta:
            if t.symbol != sym:
                continue
            si = int(np.searchsorted(mt, t.entry_ms, side="left"))
            xi = int(np.searchsorted(mt, t.exit_ms, side="left"))
            trs.append({"side": t.side, "start_idx": si, "hold_bars": max(1, xi - si),
                        "qty": t.qty, "entry_cost_frac": ecf, "exit_cost_frac": xcf,
                        "funding_pnl": t.funding_pnl})
        if trs:
            sym_arrays[sym] = (mt, mo, trs)
    if not sym_arrays:
        return None

    rng = np.random.default_rng(0)
    jb = spec.MC_JITTER_MINUTES
    base = sum(_replay_terminal(trs, mt, mo, np.zeros(len(trs), dtype=int), None)
               for (mt, mo, trs) in sym_arrays.values())
    port = np.empty(spec.MC_PATHS)
    for pth in range(spec.MC_PATHS):
        tot = 0.0
        for (mt, mo, trs) in sym_arrays.values():
            shifts = rng.integers(-jb, jb + 1, size=len(trs))
            tot += _replay_terminal(trs, mt, mo, shifts, None)
        port[pth] = tot
    med = float(np.median(port))
    passed = bool(base > 0 and med >= spec.MC_FAIL_TERMINAL_FRAC * base)
    return {"passed": passed, "base_terminal": float(base),
            "jitter_median": med, "jitter_p5": float(np.percentile(port, 5))}


def _beta_in_costume(deployed_returns: pd.Series, btc: SymbolData | None) -> dict:
    if btc is None or deployed_returns.size < 30:
        return {"corr": float("nan")}
    btc_ret = btc.daily["close"].pct_change()
    aligned = pd.concat([deployed_returns.rename("strat"), btc_ret.rename("btc")], axis=1).dropna()
    if len(aligned) < 30:
        return {"corr": float("nan")}
    corr = float(aligned["strat"].corr(aligned["btc"]))
    return {"corr": corr}


def _verdict(checks: dict, n_trades: int, min_trades: int) -> str:
    if n_trades < min_trades:
        return ("INSUFFICIENT EVIDENCE — do not deploy "
                f"(OOS trades {n_trades} < floor {min_trades}); statistical checks are moot below the floor.")
    if all(checks.values()):
        return "PASS — clears all pre-registered thresholds on OOS."
    failed = [k for k, ok in checks.items() if not ok]
    return "FAIL — clears trade floor but misses: " + ", ".join(failed)


def _print_report(r: dict):
    m = r["metrics"]
    print("\n" + "=" * 72)
    print("COIL-BREAK PHASE-2 BACKTEST — OOS REPORT (all numbers measured)")
    print("=" * 72)
    print(f"Window {r['window']['start']}..{r['window']['end']}  symbols={r['window']['symbols']}")
    print(f"Variants={r['n_variants']}  folds={r['n_folds']}  OOS days={r['oos_days']}  OOS trades={r['oos_trades']}")
    print("-" * 72)
    print(f"  OOS Sharpe (ann.)      {m['oos_sharpe_annualized']:+.3f}   (per-bar {m['oos_sharpe_per_bar']:+.4f})")
    print(f"  PSR vs 0               {m['psr_vs_0']:.3f}")
    print(f"  Deflated Sharpe (DSR)  {m['dsr']:.3f}   (deflation benchmark SR*={m['dsr_deflation_benchmark']:.4f}, N={m['dsr_n_trials']})")
    print(f"  MinTRL (obs)           {m['min_trl_obs']:.0f}   vs OOS days {r['oos_days']}")
    print(f"  OOS profit factor      {m['profit_factor']:.3f}")
    print(f"  MC real vs p5 terminal {m['mc_real_terminal']:.4f} vs {m['mc_p5_terminal']:.4f}")
    print(f"  Jitter med vs base     {m['jitter_median_terminal']} vs {m['jitter_base_terminal']}")
    print(f"  Corr to BTC B&H        {m['beta_corr_to_btc']:.3f}")
    pbo = m.get("pbo")
    if pbo is not None:
        print(f"  PBO / CSCV             {pbo:.3f}  over {m.get('pbo_n_configs')} configs "
              f"({'overfit-prone' if (pbo == pbo and pbo >= 0.5) else 'ok'})")
    print("-" * 72)
    for k, ok in r["checks"].items():
        print(f"    [{'PASS' if ok else 'FAIL'}] {k}")
    print("-" * 72)
    print("VERDICT:", r["verdict"])
    print(f"(runtime {r['runtime_sec']}s)")
    print("=" * 72 + "\n")


def _print_rich(r: dict):
    rm = r["metrics"].get("rich") or {}
    if not rm:
        return
    order = ["CAGR", "AnnVol", "Sharpe", "Sortino", "Calmar", "MaxDD", "Ulcer", "CVaR95", "TailRatio"]
    parts = [f"{k}={rm[k]:+.3f}" for k in order if k in rm and rm[k] == rm[k]]
    print("  rich metrics (deployed OOS):", "  ".join(parts), "\n")


def _save_equity(deployed: pd.Series):
    if deployed.size == 0:
        return
    eq = (1.0 + deployed).cumprod()
    df = pd.DataFrame({"date": deployed.index, "daily_return": deployed.values, "equity": eq.values})
    df.to_csv(ARTIFACTS / "phase2_oos_equity.csv", index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2020-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    args = ap.parse_args()
    run(args.symbols, date.fromisoformat(args.start), date.fromisoformat(args.end),
        ValidationSpec(), Constants(), Filters(), Costs())


if __name__ == "__main__":
    main()
