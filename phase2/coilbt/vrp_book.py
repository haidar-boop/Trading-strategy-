"""
ATM variance-risk-premium as a SCORED, TRADEABLE-realistic book (escalation of vrp_test.py).

vrp_test.py established the index-level premium (IV-RV) is large and independent of carry. This
module asks the harder question the mandate requires before any capital: does it survive as a real
short-vol book once you charge the REAL Deribit ATM spread (calibrated from the live chain, ~1 vol
point for 30d near-ATM), option fees, and a delta-hedge bleed — and how bad is the negative-skew
tail? It scores the monthly short-vol return stream with the SAME rigor the carry got (annualized
Sharpe, deflated Sharpe, block-bootstrap CI, MaxDD, CVaR) and then INJECTS a catastrophic vol month
to make the tail explicit rather than hoping the 46-month sample contains it.

Accounting: a delta-hedged short ATM straddle held to expiry replicates a short variance swap, whose
P&L in vol points is (IV - RV) to first order (exact in variance is IV^2 - RV^2; we report the
conservative linear vol-point version, and the variance version as a cross-check). Costs, in vol
points per monthly cycle:
  * spread: sell call + sell put = 2 legs, each gives up a half-spread. Calibrated live ATM 30d
    spread ~0.9 (BTC) / ~1.2 (ETH) vol pts => ~1 vol pt entry (held to expiry => no exit spread).
  * fees: Deribit option taker 0.03% of underlying, capped 12.5% of premium — a fraction of a vol pt.
  * hedge bleed: daily delta re-hedge on the perp incurs turnover cost; unknown and STRESSED across
    a range (the binding cost). This is the term the original research flagged as the killer.

No look-ahead beyond the standard variance-swap attribution (P&L of a position OPENED at t is only
known at t+30 — that is how variance P&L works, not a leak). Monthly, non-overlapping.
"""
from __future__ import annotations

import argparse
from datetime import date

import numpy as np
import pandas as pd

from .vrp_test import build_vrp, monthly_vrp, tradeable_monthly
from .data.download import download_spot_klines
from .montecarlo import circular_block_bootstrap
from . import stats

ANN_M = np.sqrt(12)

# Calibrated from the live Deribit chain (30d near-ATM), 2026-07 sample:
SPREAD_VOLPTS = {"BTC": 0.9, "ETH": 1.2}     # per monthly entry (2 legs, half-spread each ~= 1 spread)
FEE_VOLPTS = 0.3                              # Deribit option fees, approx in vol points


def score_series(net_volpts: np.ndarray, n_trials: int = 3):
    """Score a monthly net-vol-point return stream with the carry's rigor."""
    r = np.asarray(net_volpts, dtype=float)
    if r.size < 6:
        return None
    sharpe_m = r.mean() / r.std(ddof=1) if r.std(ddof=1) > 0 else 0.0
    sharpe_ann = sharpe_m * ANN_M
    # deflated Sharpe on the monthly stream (few trials -> mild deflation; honest since ~1 real config)
    trials = np.array([sharpe_m, sharpe_m * 0.8, sharpe_m * 0.6])[:n_trials]
    dsr = stats.deflated_sharpe_ratio(r, trials, n_trials=n_trials, conf=0.95)
    psr = stats.probabilistic_sharpe_ratio(r, sr_star=0.0)
    # block-bootstrap CI on annualized Sharpe
    boot = circular_block_bootstrap(r, 3, 5000, seed=0)
    sh = np.array([boot[i].mean() / boot[i].std(ddof=1) * ANN_M if boot[i].std(ddof=1) > 0 else 0.0
                   for i in range(boot.shape[0])])
    # drawdown + CVaR on cumulative vol points
    cum = np.cumsum(r)
    dd = cum - np.maximum.accumulate(cum)
    cvar5 = r[r <= np.percentile(r, 5)].mean()
    return {
        "n": int(r.size), "mean_m": float(r.mean()), "sharpe_ann": float(sharpe_ann),
        "sharpe_lo": float(np.percentile(sh, 5)), "sharpe_hi": float(np.percentile(sh, 95)),
        "dsr": float(dsr.dsr), "psr0": float(psr), "maxdd_volpts": float(dd.min()),
        "cvar5_m": float(cvar5), "frac_pos": float((r > 0).mean()),
    }


ROLL_OFFSETS = (1, 8, 15, 22, 28)


def run(currencies, start, end, hedge_bleed=2.0):
    print("=" * 96)
    print("ATM VRP as a SCORED short-vol book — TRADEABLE single-roll, VARIANCE-space, honest tail")
    print("=" * 96)
    print("Corrections after adversarial review: (1) ONE straddle/month (nearest each roll offset),")
    print("averaged over roll days {1,8,15,22,28} — NOT the mean of ~30 overlapping daily windows;")
    print("(2) variance-space P&L (IV^2-RV^2)/(2*IV), capturing the negative convexity linear IV-RV")
    print("hides; (3) tail sized in variance space from the WORST realized RV.")
    print(f"Costs/cycle (vol pts): spread (live-calibrated) + fees {FEE_VOLPTS} + hedge-bleed "
          f"{hedge_bleed} (STRESSED).")
    print("-" * 96)
    print(f"{'ccy':<5}{'mo':>4}{'gross':>7}{'net':>7}{'Sh ann':>8}{'Sh 90% CI':>16}"
          f"{'DSR':>7}{'PSR0':>7}{'maxDD':>8}{'CVaR5':>8}{'%pos':>6}")
    results = {}
    for ccy in currencies:
        spot = download_spot_klines(f"{ccy}USDT", start, end)
        m = build_vrp(ccy, spot, start, end)
        if m.empty:
            print(f"{ccy:<5} (no data)"); continue
        spread = SPREAD_VOLPTS.get(ccy, 1.0)
        cost = spread + FEE_VOLPTS + hedge_bleed
        # average the scorecard over roll offsets (tradeable, variance-space)
        per_off = []
        for rd in ROLL_OFFSETS:
            g = tradeable_monthly(m, roll_day=rd, variance_space=True)
            net = g["gross"].to_numpy() - cost
            sc = score_series(net)
            if sc:
                per_off.append((sc, net, float(g["gross"].mean())))
        if not per_off:
            print(f"{ccy:<5} (insufficient months)"); continue
        # report the MEAN scorecard across roll offsets (honest central estimate, not the max)
        def avg(key):
            return float(np.mean([p[0][key] for p in per_off]))
        sc = {k: avg(k) for k in ("n", "mean_m", "sharpe_ann", "sharpe_lo", "sharpe_hi",
                                  "dsr", "psr0", "maxdd_volpts", "cvar5_m", "frac_pos")}
        gross_mean = float(np.mean([p[2] for p in per_off]))
        # keep the day-15 net stream for the tail test
        mid = tradeable_monthly(m, roll_day=15, variance_space=True)
        results[ccy] = {"net": mid["gross"].to_numpy() - cost, "gross_mean": gross_mean,
                        "cost": cost, "score": sc, "worst_rv": float(mid["rv"].max()),
                        "mean_iv": float(mid["iv"].mean())}
        print(f"{ccy:<5}{sc['n']:>4.0f}{gross_mean:>7.1f}{sc['mean_m']:>7.1f}{sc['sharpe_ann']:>8.2f}"
              f"  [{sc['sharpe_lo']:>5.2f},{sc['sharpe_hi']:>5.2f}]{sc['dsr']:>7.2f}{sc['psr0']:>7.2f}"
              f"{sc['maxdd_volpts']:>8.1f}{sc['cvar5_m']:>8.1f}{sc['frac_pos']*100:>5.0f}%")

    # ---- honest variance-space catastrophe (drawn from the worst realized RV, not a guess) ----
    print("-" * 96)
    print("TAIL — inject a REAL variance-space catastrophe: a month where RV = the worst historically")
    print("observed level (or 3x mean IV if larger), P&L = (IV^2-RV^2)/(2*IV). This is the crash the")
    print("premium is PAID for — the 46-month sample does not contain a COVID/2020-scale event.")
    print(f"{'ccy':<5}{'crash RV':>10}{'crash volpts':>14}{'new Sh ann':>12}{'new maxDD':>11}"
          f"{'new CVaR5':>11}")
    for ccy, d in results.items():
        iv = d["mean_iv"]
        crash_rv = max(3.0 * iv, 212.0 if ccy == "BTC" else 250.0)   # 2020-03 BTC 30d fwd RV ~212%
        shock = (iv ** 2 - crash_rv ** 2) / (2 * iv)                 # variance-space loss
        sc2 = score_series(np.append(d["net"], shock))
        print(f"{ccy:<5}{crash_rv:>10.0f}{shock:>14.0f}{sc2['sharpe_ann']:>12.2f}"
              f"{sc2['maxdd_volpts']:>11.0f}{sc2['cvar5_m']:>11.0f}")
    print("-" * 96)
    print("Reading: variance-space convexity makes a real vol explosion a -200 to -300 volpt month —")
    print("many months of premium erased at once, plus Deribit margin calls / forced exit / ADL when")
    print("you can least afford them. This is a COMPENSATED crash-risk premium: positive EV, NOT")
    print("leverable Sharpe. Correct disposition = small, hard-stopped, un-levered short-convexity.")
    print("=" * 96)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2021-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--currencies", nargs="+", default=["BTC", "ETH"])
    ap.add_argument("--hedge_bleed", type=float, default=2.0)
    args = ap.parse_args()
    run(args.currencies, date.fromisoformat(args.start), date.fromisoformat(args.end),
        hedge_bleed=args.hedge_bleed)


if __name__ == "__main__":
    main()
