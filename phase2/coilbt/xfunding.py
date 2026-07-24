"""
Cross-sectional funding-dispersion carry — a market-neutral second sleeve to diversify
the single-name cash-and-carry.

At each 8h funding settlement t, rank the perp universe by the funding rate SETTLED at t
(causal), SHORT the top-K (highest positive funding -> short receives it) and LONG the
bottom-K (most negative funding -> long receives it), equal-weight and dollar-neutral.
Hold [t, t+8h] and collect the funding settled at t+8h. Rebalance every 8h. Return driver
is the funding SPREAD (a cross-sectional long/short), structurally distinct from the
single-name carry's driver (the funding LEVEL) -> low correlation, the diversification thesis.

Honest caveats (from research, surfaced in the report):
  * dollar-neutral is NOT beta-neutral: a residual short-beta tilt remains (high funding
    clusters in freshly-pumped high-beta alts). We regress book return on BTC and report beta.
  * turnover is the killer (3 rebalances/day); a churn band + a min-dispersion gate defend it.
  * perp liquidation is unmodeled (shared tail with the single-name sleeve).

Vectorized panel backtest: everything is [T periods x S symbols]. Causal by construction
(rank on F[t], P&L uses F[t+1] and P[t+1]/P[t]).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .costs import BPS
from .data.loader import SymbolData

MS_PER_DAY = 86_400_000


@dataclass(frozen=True)
class ParamsXF:
    K: int = 2              # names per side; grid {1,2,3}
    MIN_DISP_BPS: float = 2.0   # min (top-K funding mean - bottom-K funding mean) to deploy; grid {1,2,4}
    CHURN_BAND: float = 0.25    # only rebalance a name if its target weight moves > this frac; grid {0,0.25,0.5}
    NOTIONAL_FRAC: float = 1.0  # gross exposure as fraction of equity (0.5 long + 0.5 short); not gridded


@dataclass(frozen=True)
class CostsXF:
    TAKER_FEE_BPS: float = 5.0
    SLIPPAGE_BPS: float = 2.0
    STRESS_MULT: float = 2.0


@dataclass(frozen=True)
class VariantXF:
    params: ParamsXF

    def label(self) -> str:
        p = self.params
        return f"K{p.K}_D{p.MIN_DISP_BPS:g}_C{p.CHURN_BAND:g}"


GRID_K = (1, 2, 3)
GRID_DISP = (1.0, 2.0, 4.0)
GRID_CHURN = (0.0, 0.25, 0.5)


def full_grid_xf(notional_frac: float = 1.0) -> list[VariantXF]:
    return [VariantXF(ParamsXF(K=k, MIN_DISP_BPS=d, CHURN_BAND=c, NOTIONAL_FRAC=notional_frac))
            for k in GRID_K for d in GRID_DISP for c in GRID_CHURN]


def assemble_panel(data: dict[str, SymbolData]):
    """Build aligned [T x S] funding and price panels on the common 8h decision grid."""
    symbols = list(data.keys())
    # union of all funding settlement timestamps (all settle at 00/08/16 UTC -> aligned)
    ts = None
    for sd in data.values():
        t = sd.funding["calc_time"].to_numpy(dtype="int64")
        ts = set(t) if ts is None else (ts | set(t))
    dt = np.array(sorted(ts), dtype="int64")
    S = len(symbols)
    F = np.full((dt.size, S), np.nan)
    P = np.full((dt.size, S), np.nan)
    for j, sym in enumerate(symbols):
        sd = data[sym]
        f = sd.funding.sort_values("calc_time")
        ft = f["calc_time"].to_numpy(dtype="int64")
        fr = f["last_funding_rate"].to_numpy(dtype=float)
        pos = np.searchsorted(dt, ft)
        ok = (pos < dt.size) & (dt[np.clip(pos, 0, dt.size - 1)] == ft)
        F[pos[ok], j] = fr[ok]
        # perp price at each decision time (1m open at t)
        m = sd.minute.sort_values("open_time_ms")
        mt = m["open_time_ms"].to_numpy(dtype="int64")
        mo = m["open"].to_numpy(dtype=float)
        p_pos = np.searchsorted(mt, dt, side="left")
        valid = (p_pos < mt.size) & (mt[np.clip(p_pos, 0, mt.size - 1)] == dt)
        P[valid, j] = mo[np.clip(p_pos[valid], 0, mo.size - 1)]
    return dt, F, P, symbols


def run_xf(data: dict[str, SymbolData], variant: VariantXF, costs: CostsXF, ref_equity: float,
           panel=None):
    """Vectorized market-neutral panel backtest. Returns (period_records, daily_pnl Series)."""
    if panel is None:
        panel = assemble_panel(data)
    dt, F, P, symbols = panel
    p = variant.params
    leg = (costs.TAKER_FEE_BPS + costs.SLIPPAGE_BPS) * costs.STRESS_MULT * BPS
    T, S = F.shape
    side_notional = p.NOTIONAL_FRAC / 2.0    # long side and short side gross (fraction of equity)

    # daily P&L aggregation
    day_ms = (dt // MS_PER_DAY) * MS_PER_DAY
    days = pd.to_datetime(np.unique(day_ms), unit="ms", utc=True)
    daily_pnl = pd.Series(0.0, index=days)
    day_index = {int(d): pd.Timestamp(d, unit="ms", tz="UTC") for d in np.unique(day_ms)}

    W_prev = np.zeros(S)                      # previous period target weights (signed frac of equity)
    period_returns = []
    period_deployed = []
    for t in range(T - 1):                    # need t+1 for P&L
        f_t = F[t]
        valid = np.isfinite(f_t) & np.isfinite(P[t]) & np.isfinite(P[t + 1])
        idx = np.where(valid)[0]
        W = np.zeros(S)
        deployed = False
        if idx.size >= 2 * p.K:
            order = idx[np.argsort(f_t[idx])]      # ascending funding
            longs = order[: p.K]                   # most negative funding -> long (receives)
            shorts = order[-p.K:]                  # highest funding -> short (receives)
            disp = f_t[shorts].mean() - f_t[longs].mean()   # funding spread (>=0)
            if disp >= p.MIN_DISP_BPS * BPS:
                W[longs] = side_notional / p.K
                W[shorts] = -side_notional / p.K
                deployed = True
        # churn band: keep previous weight for a name if the target barely moved
        if p.CHURN_BAND > 0:
            move = np.abs(W - W_prev)
            unit = side_notional / max(p.K, 1)
            hold = move < p.CHURN_BAND * unit
            W = np.where(hold, W_prev, W)

        # ---- period P&L over [t, t+1] on book W ----
        pr = np.nan_to_num(P[t + 1] / P[t] - 1.0)            # per-symbol price return
        price_ret = float(np.nansum(W * pr))                 # signed weights
        funding = float(np.nansum(-F[t + 1] * W))            # -f*N: long pays +f, short receives
        turn = float(np.nansum(np.abs(W - W_prev)))
        cost = turn * leg
        period = price_ret + funding - cost
        daily_pnl.loc[day_index[int(day_ms[t])]] += period * ref_equity
        period_returns.append(period)
        period_deployed.append(deployed or W.any())
        W_prev = W

    return {"period_returns": np.array(period_returns), "deployed": np.array(period_deployed),
            "symbols": symbols}, daily_pnl
