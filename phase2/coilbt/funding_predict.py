"""
Leak-free funding *predictability* study (#3 / #10 / #20 — "predict funding instead of react").

The carry strategy currently REACTS: it enters when funding is high *now* and hopes it persists.
The proposed upgrade is to PREDICT next-window funding and gate on the forecast. Before building
a predictive entry, this module answers the prior scientific question honestly:

    Is Binance perp funding forecastable beyond its own autocorrelation?

Funding is strongly autocorrelated: "funding is high now" already predicts "funding stays high".
So the only forecast that MATTERS is one that beats the naive persistence baseline
(predict next-K mean funding == current funding). This module measures the INCREMENTAL out-of-sample
R^2 of a causal feature model over that baseline. If incremental R^2 ~ 0, the honest conclusion is
that the naive threshold the strategy already uses is near-optimal and a "prediction model" would be
curve-fit theater.

Leakage discipline (why this is written by hand, not delegated):
  * Panel is built on the 8h funding settlement grid. Every FEATURE at settlement t uses only data
    with timestamp <= t (the rate realized AT t is known at t). Every TARGET uses settlements
    strictly AFTER t.
  * Walk-forward: standardization mean/std and ridge coefficients are fit on the TRAIN slice only;
    the test point never touches the fit. Rolling train window, gap/embargo between train and test.
  * Baselines computed on the identical test points so R^2 is apples-to-apples.

Data: BTC + ETH (the two symbols with full cached OI/metrics history). Features are all free-data:
funding momentum/level/vol, OI z-score/acceleration, trailing realized vol.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from .data.loader import load_symbol, MS_PER_DAY


# --------------------------------------------------------------------------------------
# Panel construction — all features causal at settlement t, target strictly forward.
# --------------------------------------------------------------------------------------

def build_funding_panel(sd, k_fwd: int = 3, mom_win: int = 9, oi_win: int = 14,
                        vol_win: int = 14) -> pd.DataFrame:
    """One row per funding settlement. Columns = causal features + forward target.

    k_fwd  : target = mean funding over the next k_fwd settlements (a carry trade entered at t
             holding ~k_fwd*8h collects roughly this). 3 settlements = ~1 day.
    mom_win: window (in settlements) for funding momentum / mean / vol features.
    oi_win : window (in days) for OI z-score / acceleration.
    vol_win: window (in days) for trailing realized vol.
    """
    f = sd.funding.sort_values("calc_time").reset_index(drop=True)
    t_ms = f["calc_time"].to_numpy(dtype="int64")
    rate = f["last_funding_rate"].to_numpy(dtype="float64")
    n = len(rate)
    if n < mom_win + k_fwd + 5:
        return pd.DataFrame()

    s = pd.Series(rate)
    # --- funding features (all use only settlements up to and including t) ---
    f_now = rate
    # trailing mean/std EXCLUDING look-ahead: window ends at t (inclusive), min 3 obs.
    f_mean = s.rolling(mom_win, min_periods=3).mean().to_numpy()
    f_std = s.rolling(mom_win, min_periods=3).std(ddof=1).to_numpy()
    f_ewma = s.ewm(span=mom_win, adjust=False).mean().to_numpy()
    # momentum: current minus trailing mean (is funding rising or falling into t?)
    f_mom = f_now - f_mean
    # short-vs-long: last-3 mean minus mom_win mean
    f_short = s.rolling(3, min_periods=1).mean().to_numpy()
    f_slope = f_short - f_mean

    # --- OI features, aligned causally: OI for settlement t = last daily OI known by t ---
    oi = sd.oi_daily.dropna(subset=["oi_level"]).copy()
    oi_z = np.full(n, np.nan)
    oi_accel = np.full(n, np.nan)
    dvol = np.full(n, np.nan)
    if len(oi) > oi_win:
        # OI level for day D is known at decision_ms = day_ms + MS_PER_DAY.
        oi_known_ms = oi.index.to_numpy(dtype="int64") + MS_PER_DAY
        oi_level = oi["oi_level"].to_numpy(dtype="float64")
        oi_series = pd.Series(oi_level)
        oi_mean = oi_series.rolling(oi_win, min_periods=5).mean().to_numpy()
        oi_sd = oi_series.rolling(oi_win, min_periods=5).std(ddof=1).to_numpy()
        z = (oi_level - oi_mean) / np.where(oi_sd > 0, oi_sd, np.nan)
        # relative day-over-day OI change (acceleration proxy)
        accel = oi["delta_oi"].to_numpy(dtype="float64") / np.where(oi_level > 0, oi_level, np.nan)
        # for each settlement t, last daily obs with oi_known_ms <= t
        pos = np.searchsorted(oi_known_ms, t_ms, side="right") - 1
        ok = pos >= 0
        oi_z[ok] = z[pos[ok]]
        oi_accel[ok] = accel[pos[ok]]

    # --- trailing realized vol from daily closes, causal ---
    daily = sd.daily
    d_known_ms = daily["decision_ms"].to_numpy(dtype="int64")
    d_close = daily["close"].to_numpy(dtype="float64")
    logret = np.diff(np.log(d_close), prepend=np.log(d_close[0]))
    rv = pd.Series(logret).rolling(vol_win, min_periods=5).std(ddof=1).to_numpy()
    pos_d = np.searchsorted(d_known_ms, t_ms, side="right") - 1
    okd = pos_d >= 0
    dvol[okd] = rv[pos_d[okd]]

    # --- forward target: mean of next k_fwd settlements (strictly after t) ---
    target = np.full(n, np.nan)
    for i in range(n - k_fwd):
        target[i] = rate[i + 1:i + 1 + k_fwd].mean()

    panel = pd.DataFrame({
        "t_ms": t_ms,
        "f_now": f_now, "f_mean": f_mean, "f_std": f_std, "f_ewma": f_ewma,
        "f_mom": f_mom, "f_slope": f_slope,
        "oi_z": oi_z, "oi_accel": oi_accel, "dvol": dvol,
        "target": target,
    })
    return panel


FEATURES = ["f_now", "f_mean", "f_std", "f_ewma", "f_mom", "f_slope", "oi_z", "oi_accel", "dvol"]

# Ablation groups: does the EXOGENOUS story (OI/vol — "why is funding high") add anything over
# just using the funding autocorrelation better? If FUNDING_ONLY ~= ALL, the exogenous taxonomy
# adds no incremental point-forecast power and the naive threshold is near-optimal.
FEATURE_SETS = {
    "funding_only": ["f_now", "f_mean", "f_std", "f_ewma", "f_mom", "f_slope"],
    "oi_vol_only": ["oi_z", "oi_accel", "dvol"],
    "all": FEATURES,
}


# --------------------------------------------------------------------------------------
# Closed-form ridge with in-fold standardization (no leakage, fully auditable).
# --------------------------------------------------------------------------------------

def _ridge_fit(X, y, lam):
    """Standardize on train, ridge on standardized X (intercept unpenalized via centering)."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0, ddof=0)
    sd = np.where(sd > 1e-12, sd, 1.0)
    Xs = (X - mu) / sd
    ybar = y.mean()
    yc = y - ybar
    p = Xs.shape[1]
    A = Xs.T @ Xs + lam * np.eye(p)
    beta = np.linalg.solve(A, Xs.T @ yc)
    return {"mu": mu, "sd": sd, "ybar": ybar, "beta": beta}


def _ridge_pred(model, X):
    Xs = (X - model["mu"]) / model["sd"]
    return model["ybar"] + Xs @ model["beta"]


def _r2(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan


# --------------------------------------------------------------------------------------
# Walk-forward evaluation: ridge vs persistence vs train-mean baselines.
# --------------------------------------------------------------------------------------

def walk_forward(panel: pd.DataFrame, train_win: int = 400, test_win: int = 100,
                 embargo: int = 5, lam: float = 10.0, features=None):
    """Rolling walk-forward. Returns arrays of OOS predictions for every baseline aligned to the
    same test rows, so R^2 comparisons are apples-to-apples.

    train_win : settlements in each train slice (~400 = ~133 days)
    test_win  : settlements predicted per step before rolling forward
    embargo   : gap (settlements) between train end and test start (target uses k_fwd forward
                settlements, so an embargo prevents train target overlapping test features)
    features  : which feature columns to fit on (defaults to FEATURES; used for ablations)
    """
    features = features or FEATURES
    df = panel.dropna(subset=features + ["target"]).reset_index(drop=True)
    Xall = df[features].to_numpy(dtype="float64")
    yall = df["target"].to_numpy(dtype="float64")
    fnow = df["f_now"].to_numpy(dtype="float64")

    yt, yp_ridge, yp_persist, yp_mean = [], [], [], []
    start = 0
    while start + train_win + embargo + 1 <= len(df):
        tr = slice(start, start + train_win)
        te_lo = start + train_win + embargo
        te_hi = min(te_lo + test_win, len(df))
        if te_lo >= te_hi:
            break
        model = _ridge_fit(Xall[tr], yall[tr], lam)
        te = slice(te_lo, te_hi)
        yp_ridge.append(_ridge_pred(model, Xall[te]))
        yp_persist.append(fnow[te])                       # naive: next == now
        yp_mean.append(np.full(te_hi - te_lo, yall[tr].mean()))  # train-mean constant
        yt.append(yall[te])
        start += test_win

    if not yt:
        return None
    yt = np.concatenate(yt)
    return {
        "n_test": len(yt),
        "r2_ridge": _r2(yt, np.concatenate(yp_ridge)),
        "r2_persist": _r2(yt, np.concatenate(yp_persist)),
        "r2_mean": _r2(yt, np.concatenate(yp_mean)),
        "yt": yt,
        "yp_ridge": np.concatenate(yp_ridge),
        "yp_persist": np.concatenate(yp_persist),
    }


def ablation(panel: pd.DataFrame, lam: float = 10.0):
    """Fit each FEATURE_SET separately and report OOS R^2. Isolates whether the EXOGENOUS
    features (OI/vol) add anything over just using the funding autocorrelation better."""
    out = {}
    for name, feats in FEATURE_SETS.items():
        res = walk_forward(panel, lam=lam, features=feats)
        out[name] = res["r2_ridge"] if res else float("nan")
    # persistence baseline is invariant to feature set
    any_res = walk_forward(panel, lam=lam, features=FEATURE_SETS["all"])
    out["persist"] = any_res["r2_persist"] if any_res else float("nan")
    return out


def decision_test(res, entry_bps: float = 1.5):
    """Decision-level test: does gating entries on the FORECAST collect more realized forward
    funding than gating on CURRENT funding? Both gates use the same threshold on predicted vs
    current funding; we compare the mean realized next-K funding (in bps) among selected entries
    and the selection rate. This is what actually matters for the carry trade.
    """
    thr = entry_bps * 1e-4
    yt, yp, yn = res["yt"], res["yp_ridge"], res["yp_persist"]
    out = {}
    for name, gate in [("current (naive)", yn), ("forecast (ridge)", yp)]:
        sel = gate >= thr
        out[name] = {
            "rate": float(sel.mean()),
            "n": int(sel.sum()),
            "realized_bps": float(yt[sel].mean() * 1e4) if sel.any() else float("nan"),
            "hit": float((yt[sel] > 0).mean()) if sel.any() else float("nan"),
        }
    return out


def run(symbols, start, end, k_fwd=3, lam=10.0):
    print("=" * 84)
    print("FUNDING PREDICTABILITY — is funding forecastable BEYOND its own autocorrelation?")
    print(f"target = mean funding over next {k_fwd} settlements (~{k_fwd*8}h); walk-forward, "
          f"leak-free")
    print("=" * 84)
    print(f"{'symbol':<10}{'n_test':>8}{'R2 persist':>12}{'R2 mean':>10}{'R2 ridge':>10}"
          f"{'incr. R2':>10}")
    print("-" * 84)
    pooled = []
    for sym in symbols:
        sd = load_symbol(sym, start, end, with_oi=True)
        panel = build_funding_panel(sd, k_fwd=k_fwd)
        if panel.empty:
            print(f"{sym:<10}  (insufficient data)")
            continue
        res = walk_forward(panel, lam=lam)
        if res is None:
            print(f"{sym:<10}  (insufficient walk-forward folds)")
            continue
        incr = res["r2_ridge"] - res["r2_persist"]
        print(f"{sym:<10}{res['n_test']:>8}{res['r2_persist']:>12.3f}{res['r2_mean']:>10.3f}"
              f"{res['r2_ridge']:>10.3f}{incr:>10.3f}")
        pooled.append((sym, res))

    print("-" * 84)
    print("ABLATION — does the EXOGENOUS story (OI/vol) add over funding-autocorrelation alone?")
    print(f"{'symbol':<10}{'persist':>10}{'funding_only':>14}{'oi_vol_only':>13}{'all':>8}"
          f"{'exog gain':>11}")
    for sym, res in pooled:
        pass  # printed below with panels; recompute ablation per symbol
    for sym in symbols:
        sd = load_symbol(sym, start, end, with_oi=True)
        panel = build_funding_panel(sd, k_fwd=k_fwd)
        if panel.empty:
            continue
        ab = ablation(panel, lam=lam)
        gain = ab["all"] - ab["funding_only"]
        print(f"{sym:<10}{ab['persist']:>10.3f}{ab['funding_only']:>14.3f}"
              f"{ab['oi_vol_only']:>13.3f}{ab['all']:>8.3f}{gain:>11.3f}")

    print("-" * 84)
    print("Decision-level test (does a forecast gate collect more realized forward funding?):")
    print(f"{'symbol':<10}{'gate':<20}{'select %':>10}{'realized bps':>14}{'hit %':>8}")
    for sym, res in pooled:
        dt = decision_test(res)
        for name, d in dt.items():
            print(f"{sym:<10}{name:<20}{d['rate']*100:>9.1f}%{d['realized_bps']:>14.2f}"
                  f"{d['hit']*100:>7.1f}%")
    print("=" * 84)
    print("Reading: incr. R2 = R2(ridge) - R2(persistence). If <=~0, features add NOTHING over")
    print("the autocorrelation the naive threshold already exploits -> no predictive edge to build.")
    print("If the forecast gate's realized bps <= the naive gate's, prediction does not improve")
    print("the actual carry entry decision either.")
    print("=" * 84)
    return pooled


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2021-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    ap.add_argument("--k_fwd", type=int, default=3)
    ap.add_argument("--lam", type=float, default=10.0)
    args = ap.parse_args()
    run(args.symbols, date.fromisoformat(args.start), date.fromisoformat(args.end),
        k_fwd=args.k_fwd, lam=args.lam)


if __name__ == "__main__":
    main()
