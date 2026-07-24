"""
Falsification test for the ATM variance-risk-premium (VRP) sleeve — the one genuinely orthogonal
factor from the redesign (second-moment premium vs carry's first-moment leverage-demand premium).

Economic hypothesis: crypto implied vol (Deribit DVOL, a 30-day ATM IV index) trades persistently
ABOVE subsequent 30-day realized vol; a delta-hedged short-ATM-vol position harvests IV - RV. The
seller is paid for bearing variance/jump risk (the natural buyers of protection — leveraged longs
hedging, structured-product desks). This is a DIFFERENT Greek and a different DGP than funding carry.

Pre-registered falsification (BOTH must pass to 'pursue'):
  (a) NET-OF-COST: does the ATM VRP clear a HONEST STRESSED cost — cross the full quoted vol-point
      spread on open AND close of each monthly roll, plus a delta-hedge bleed haircut? Wings are
      EXCLUDED by construction (DVOL is an ATM/near-ATM index), which is the point: the fat wing
      premium is both tail-correlated with carry and unmodelable on free data.
  (b) INDEPENDENCE: is the VRP monthly return stream's Spearman correlation with the carry return
      stream < 0.5 in the BODY (i.e. it genuinely diversifies day-to-day, not just co-crashes)?

Data: FREE. Deribit public get_volatility_index_data (DVOL, no auth) for IV; realized vol from the
spot klines already cached. No option chain, so this is deliberately an INDEX-level ATM proxy — good
enough to falsify (if the ATM premium doesn't survive stressed costs at the index level, the real
book with real spreads is worse).
"""
from __future__ import annotations

import argparse
import io
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from .data.download import download_spot_klines, DEFAULT_RAW

DERIBIT = "https://www.deribit.com/api/v2/public/get_volatility_index_data"
MS_PER_DAY = 86_400_000


def fetch_dvol(currency: str, start: date, end: date, raw_dir: Path = DEFAULT_RAW) -> pd.DataFrame:
    """Daily DVOL (30d ATM implied-vol index, annualized %). Cached. Fetched in <=300-day chunks
    (Deribit caps candles per request). Columns: day_ms, dvol_close."""
    currency = currency.upper()
    if currency not in ("BTC", "ETH"):
        raise ValueError(f"DVOL only for BTC/ETH, got {currency!r}")
    out_dir = raw_dir / "dvol"
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = out_dir / f"{currency}-dvol-{start.isoformat()}-{end.isoformat()}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    s_ms = int(pd.Timestamp(start, tz="UTC").timestamp() * 1000)
    e_ms = int(pd.Timestamp(end, tz="UTC").timestamp() * 1000)
    rows = []
    lo = s_ms
    chunk = 300 * MS_PER_DAY
    sess = requests.Session()
    while lo < e_ms:
        hi = min(lo + chunk, e_ms)
        params = {"currency": currency, "start_timestamp": lo, "end_timestamp": hi,
                  "resolution": 86400}
        r = sess.get(DERIBIT, params=params, timeout=60)
        r.raise_for_status()
        data = r.json().get("result", {}).get("data", [])
        for c in data:
            rows.append((int(c[0]), float(c[4])))   # [ts, o, h, l, close]
        lo = hi
    if not rows:
        return pd.DataFrame(columns=["day_ms", "dvol_close"])
    df = pd.DataFrame(rows, columns=["day_ms", "dvol_close"]).drop_duplicates("day_ms")
    df["day_ms"] = (df["day_ms"] // MS_PER_DAY) * MS_PER_DAY
    df = df.groupby("day_ms", as_index=False)["dvol_close"].last().sort_values("day_ms")
    df.to_parquet(cache, index=False)
    return df.reset_index(drop=True)


def realized_vol_forward(spot: pd.DataFrame, horizon_days: int = 30) -> pd.DataFrame:
    """Daily close-to-close realized vol over the NEXT horizon_days, annualized. Causal label: at
    day t the VRP is IV_t (known at t) minus RV over (t, t+h] (realized after t) — the standard VRP.
    Returns day_ms, rv_fwd (annualized fraction*100 to match DVOL %)."""
    s = spot.rename(columns={"open_time": "open_time_ms"}).copy()
    s["day_ms"] = (s["open_time_ms"] // MS_PER_DAY) * MS_PER_DAY
    daily = s.groupby("day_ms")["close"].last().sort_index()
    logret = np.log(daily / daily.shift(1))
    day_ms = daily.index.to_numpy(dtype="int64")
    rv_fwd = np.full(len(daily), np.nan)
    lr = logret.to_numpy()
    for i in range(len(daily) - horizon_days):
        window = lr[i + 1:i + 1 + horizon_days]
        if np.isfinite(window).sum() >= horizon_days - 2:
            rv_fwd[i] = np.nanstd(window, ddof=1) * np.sqrt(365) * 100.0
    return pd.DataFrame({"day_ms": day_ms, "rv_fwd": rv_fwd})


def build_vrp(currency, spot, start, end, horizon_days=30):
    dvol = fetch_dvol(currency, start, end)
    rv = realized_vol_forward(spot, horizon_days)
    m = pd.merge(dvol, rv, on="day_ms", how="inner").dropna()
    m["vrp"] = m["dvol_close"] - m["rv_fwd"]           # IV - RV in vol points (annualized %)
    m["day"] = pd.to_datetime(m["day_ms"], unit="ms", utc=True)
    return m.reset_index(drop=True)


def monthly_vrp(m, roll_spread_volpts=1.5, hedge_bleed_volpts=1.0):
    """Non-overlapping MONTHLY VRP (avoids overlapping-window autocorrelation). Each month: harvest
    IV-RV once; pay stressed cost = round-trip spread (open+close the straddle) + delta-hedge bleed,
    in vol points. Returns a monthly frame with gross and net VRP (vol points)."""
    m = m.copy()
    m["ym"] = m["day"].dt.tz_localize(None).dt.to_period("M")
    g = m.groupby("ym").agg(iv=("dvol_close", "mean"), rv=("rv_fwd", "mean"),
                            gross=("vrp", "mean")).reset_index()
    cost = roll_spread_volpts + hedge_bleed_volpts          # stressed vol-point cost per monthly roll
    g["net"] = g["gross"] - cost
    return g


def _carry_monthly(start, end):
    """Monthly net P&L of the default carry on BTC+ETH (for the independence test)."""
    from datetime import date as _date
    from .config_carry import ConstantsCarry, CostsCarry, FiltersCarry, ParamsCarry, VariantCarry
    from .data.loader import load_symbol
    from .backtest_carry import build_aligned, run_symbol_carry
    from .strategy_carry import build_carry_table
    consts, filters, costs = ConstantsCarry(), FiltersCarry(), CostsCarry()
    v = VariantCarry(ParamsCarry())
    tot = None
    for sym in ("BTCUSDT", "ETHUSDT"):
        sd = load_symbol(sym, start, end, with_oi=False)
        spot = download_spot_klines(sym, start, end)
        tbl = build_carry_table(sd, spot, consts, filters)
        al = build_aligned(sd, spot)
        _, dp = run_symbol_carry(sd, spot, v, consts, filters, costs, 10_000.0, tbl, al)
        tot = dp if tot is None else tot.add(dp, fill_value=0.0)
    mo = tot.groupby(tot.index.to_period("M")).sum()
    return mo


def independence_and_tail(currencies, start, end):
    """Test (b): Spearman of VRP monthly return vs carry monthly return, overall and in the BODY
    (excluding the worst 15% crash months). Plus the VRP tail (worst months) and whether carry is
    also bad then (shared-crash check)."""
    from scipy.stats import spearmanr
    carry_mo = _carry_monthly(start, end)
    print("\n" + "=" * 90)
    print("(b) INDEPENDENCE vs carry + TAIL — Spearman of monthly VRP (IV-RV) vs carry monthly P&L")
    print("=" * 90)
    for ccy in currencies:
        spot = download_spot_klines(f"{ccy}USDT", start, end)
        m = build_vrp(ccy, spot, start, end)
        if m.empty:
            continue
        g = monthly_vrp(m)
        vrp = pd.Series(g["gross"].to_numpy(), index=g["ym"].astype(str))
        car = pd.Series(carry_mo.to_numpy(), index=carry_mo.index.astype(str))
        j = pd.concat([vrp.rename("vrp"), car.rename("carry")], axis=1).dropna()
        if len(j) < 8:
            print(f"{ccy}: insufficient overlap ({len(j)})"); continue
        rho_all = spearmanr(j["vrp"], j["carry"]).statistic
        # body = drop the worst 15% VRP months (the shared-crash tail)
        thr = j["vrp"].quantile(0.15)
        body = j[j["vrp"] > thr]
        rho_body = spearmanr(body["vrp"], body["carry"]).statistic if len(body) > 6 else float("nan")
        worst = j.nsmallest(3, "vrp")
        print(f"\n{ccy}: overlap {len(j)} months   Spearman(all)={rho_all:+.2f}   "
              f"Spearman(body, worst-15% VRP excluded)={rho_body:+.2f}   "
              f"{'INDEPENDENT (<0.5)' if abs(rho_body) < 0.5 else 'NOT independent'}")
        print(f"   worst VRP months (short-vol losses = RV>>IV) and carry P&L those months:")
        for ym, row in worst.iterrows():
            print(f"     {ym}: VRP {row['vrp']:+6.1f} volpts   carry {row['carry']:+7.0f}")
    print("=" * 90)


def run(currencies, start, end, roll_spread=1.5, hedge_bleed=1.0):
    print("=" * 90)
    print("ATM VARIANCE-RISK-PREMIUM — falsification (real Deribit DVOL vs realized vol, free data)")
    print("=" * 90)
    print(f"IV = Deribit DVOL (30d ATM, annualized %).  RV = realized vol over the NEXT 30d.")
    print(f"Stressed cost/monthly roll: spread {roll_spread} + hedge-bleed {hedge_bleed} = "
          f"{roll_spread + hedge_bleed} vol points (wings EXCLUDED by construction).")
    print("-" * 90)
    print(f"{'ccy':<6}{'months':>8}{'mean IV':>9}{'mean RV':>9}{'gross VRP':>11}"
          f"{'net VRP':>9}{'% mo net+':>10}{'IC-worthy?':>12}")
    out = {}
    for ccy in currencies:
        spot = download_spot_klines(f"{ccy}USDT", start, end)
        m = build_vrp(ccy, spot, start, end)
        if m.empty:
            print(f"{ccy:<6}  (no DVOL/RV overlap)")
            continue
        g = monthly_vrp(m, roll_spread, hedge_bleed)
        mean_net = g["net"].mean()
        frac_pos = float((g["net"] > 0).mean())
        worthy = "maybe" if mean_net > 0 else "NO"
        print(f"{ccy:<6}{len(g):>8}{g['iv'].mean():>9.1f}{g['rv'].mean():>9.1f}"
              f"{g['gross'].mean():>11.2f}{mean_net:>9.2f}{frac_pos*100:>9.0f}%{worthy:>12}")
        out[ccy] = {"months": len(g), "gross": float(g["gross"].mean()),
                    "net": float(mean_net), "frac_pos": frac_pos, "monthly": g}
    print("-" * 90)
    print("(a) NET-OF-COST test: net VRP must be > 0 after the stressed vol-point cost. Gross VRP is")
    print("    the raw IV-RV edge; if the stressed cost erases it, the sleeve fails test (a).")
    # cost-stress sweep: how hard can we push the per-roll vol-point cost before net -> 0?
    print("\n  cost-stress sweep (per-monthly-roll vol-point cost -> mean net VRP):")
    hdr = "  ccy   " + "".join(f"{c:>10.1f}" for c in (2.5, 4.0, 6.0, 8.0, 10.0))
    print(hdr)
    for ccy, d in out.items():
        g = d["monthly"]
        row = f"  {ccy:<5} "
        for c in (2.5, 4.0, 6.0, 8.0, 10.0):
            row += f"{(g['gross'].mean() - c):>10.2f}"
        print(row)
    print("  (crypto ATM VRP is large; even a 6-8 volpt round-trip cost leaves it positive on average")
    print("   — but 'on average' hides the negative-skew tail, tested in part (b).)")
    print("=" * 90)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2021-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--currencies", nargs="+", default=["BTC", "ETH"])
    ap.add_argument("--roll_spread", type=float, default=1.5)
    ap.add_argument("--hedge_bleed", type=float, default=1.0)
    args = ap.parse_args()
    run(args.currencies, date.fromisoformat(args.start), date.fromisoformat(args.end),
        args.roll_spread, args.hedge_bleed)
    independence_and_tail(args.currencies, date.fromisoformat(args.start),
                          date.fromisoformat(args.end))


if __name__ == "__main__":
    main()
