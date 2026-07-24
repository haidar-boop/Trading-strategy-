"""
Delta-neutral cash-and-carry engine for one symbol.

Position = SHORT perp qty Q + LONG spot qty Q (equal base units -> delta ~ 0). The net
price P&L reduces to Q*(basis_entry - basis_exit) with basis = Pp - Ps, so the directional
move is hedged out and only the basis change (plus funding, minus 4-leg costs) remains.

Exits (earliest wins):
  * funding-decay exit — at a settlement where funding <= EXIT_FUND
  * basis stop — intrabar, if the perp premium widens against us by >= BASIS_STOP
  * time cap (MAX_HOLD)

Costs: 4 taker legs (short perp + buy spot in; buy perp + sell spot out). Funding accrues
to the perp short at realized sign. Daily MTM is on the basis series and telescopes to the
trade's net price P&L (accounting invariant holds, same as the other engines).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .backtest import Trade
from .config_carry import ConstantsCarry, CostsCarry, VariantCarry
from .costs import BPS, FundingModel
from .data.loader import SymbolData
from .quantlib.impact_costs import ImpactCostModel

MS_PER_DAY = 86_400_000


def build_aligned(sd: SymbolData, spot_min: pd.DataFrame):
    """Inner-join perp & spot 1m bars on open_time. Returns aligned arrays + daily basis."""
    pm = sd.minute.sort_values("open_time_ms").reset_index(drop=True)
    sm = spot_min.rename(columns={"open_time": "open_time_ms", "open": "sopen",
                                  "close": "sclose"}).sort_values("open_time_ms")
    merged = pd.merge(pm[["open_time_ms", "open", "close"]],
                      sm[["open_time_ms", "sopen", "sclose"]], on="open_time_ms", how="inner")
    mt = merged["open_time_ms"].to_numpy(dtype="int64")
    ppo = merged["open"].to_numpy(dtype=float)      # perp open
    ppc = merged["close"].to_numpy(dtype=float)     # perp close
    pso = merged["sopen"].to_numpy(dtype=float)     # spot open
    psc = merged["sclose"].to_numpy(dtype=float)    # spot close

    # daily basis (perp_close - spot_close) aligned to the perp daily index
    spd = sm.copy()
    spd["day_ms"] = (spd["open_time_ms"] // MS_PER_DAY) * MS_PER_DAY
    spot_daily_close = spd.groupby("day_ms")["sclose"].last()
    perp_daily_close = sd.daily["close"]
    perp_day_ms = sd.daily["day_ms"].to_numpy(dtype="int64")
    spot_dc = spot_daily_close.reindex(perp_day_ms).to_numpy(dtype=float)
    daily_basis = pd.Series(perp_daily_close.to_numpy(dtype=float) - spot_dc, index=sd.daily.index)
    return mt, ppo, ppc, pso, psc, daily_basis


def _mark_daily_carry(daily_pnl, daily_basis, qty, basis_entry, basis_exit,
                      entry_day, exit_day, entry_cost, exit_cost,
                      fund, entry_ms, exit_ms, perp_entry_notional):
    """Distribute pair P&L across days: basis MTM (telescopes) + funding + costs.
    entry_cost / exit_cost are the total $ cost booked on the entry day / exit day (any split
    of perp/spot fees, spreads, impact, legging slippage) -- passed in so the cost model can be
    as detailed as needed while the daily-MTM invariant (sum == trade net) stays trivially true."""
    idx = daily_basis.index
    d0 = idx.searchsorted(entry_day)
    d1 = idx.searchsorted(exit_day)
    for d in range(d0, d1 + 1):
        if d == d0 and d == d1:
            px = qty * (basis_entry - basis_exit)
        elif d == d0:
            px = qty * (basis_entry - float(daily_basis.iloc[d]))
        elif d == d1:
            px = qty * (float(daily_basis.iloc[d - 1]) - basis_exit)
        else:
            px = qty * (float(daily_basis.iloc[d - 1]) - float(daily_basis.iloc[d]))
        daily_pnl.iloc[d] += px
    # costs: entry legs booked on d0, exit legs on d1
    daily_pnl.iloc[d0] += -entry_cost
    daily_pnl.iloc[d1] += -exit_cost
    # funding (perp short receives when rate>0): -(-1)*rate = +rate on perp notional
    fts, frates = fund.settlements_in(entry_ms, exit_ms)
    for ts, rate in zip(fts, frates):
        day_ms = (int(ts) // MS_PER_DAY) * MS_PER_DAY
        day = pd.Timestamp(day_ms, unit="ms", tz="UTC")
        dpos = idx.searchsorted(day)
        if 0 <= dpos < len(idx):
            daily_pnl.iloc[dpos] += rate * perp_entry_notional   # short receives +rate


def run_symbol_carry(sd: SymbolData, spot_min: pd.DataFrame, variant: VariantCarry,
                     consts: ConstantsCarry, filters, costs_cfg: CostsCarry,
                     ref_equity: float, tbl: pd.DataFrame, aligned=None):
    from .strategy_carry import raw_signal_carry
    p = variant.params
    enter = raw_signal_carry(tbl, p).to_numpy()
    dt = tbl["dt_ms"].to_numpy(dtype="int64")
    f_now = tbl["f_now"].to_numpy(dtype=float)
    pp_t = tbl["pp"].to_numpy(dtype=float)
    ps_t = tbl["ps"].to_numpy(dtype=float)
    adv_t = tbl["adv_usd"].to_numpy(dtype=float)
    dvol_t = tbl["daily_vol"].to_numpy(dtype=float)

    if aligned is None:
        aligned = build_aligned(sd, spot_min)
    mt, ppo, ppc, pso, psc, daily_basis = aligned

    fund = FundingModel(sd.funding)
    # ported √-impact cost model; per-leg fractional cost = round_trip/2 at the leg's participation
    impact = ImpactCostModel(commission_bps=costs_cfg.TAKER_FEE_BPS,
                             half_spread_bps=costs_cfg.SLIPPAGE_BPS,
                             impact_coef=costs_cfg.IMPACT_COEF, stress_mult=costs_cfg.STRESS_MULT)
    flat_leg = (costs_cfg.TAKER_FEE_BPS + costs_cfg.SLIPPAGE_BPS) * costs_cfg.STRESS_MULT * BPS
    # #38 asymmetric spot-leg params (Binance spot taker 10bps = 2x perp; + legging slippage)
    asym = getattr(costs_cfg, "SPOT_ASYMMETRIC", False)
    smult = costs_cfg.STRESS_MULT
    spot_fee = getattr(costs_cfg, "SPOT_FEE_BPS", costs_cfg.TAKER_FEE_BPS)
    spot_spread = getattr(costs_cfg, "SPOT_SLIPPAGE_BPS", costs_cfg.SLIPPAGE_BPS)
    spot_adv_ratio = getattr(costs_cfg, "SPOT_ADV_RATIO", 1.0)
    # legging slippage is part of the #38 realism upgrade -> only when the asymmetric model is on
    legging_frac = (getattr(costs_cfg, "LEGGING_SLIP_BPS", 0.0) * smult * BPS) if asym else 0.0
    exit_fund = p.EXIT_FUND_BPS * BPS
    basis_stop = p.BASIS_STOP_BPS * BPS
    max_hold_ms = consts.MAX_HOLD_DAYS * MS_PER_DAY

    daily_pnl = pd.Series(0.0, index=sd.daily.index)
    trades: list[Trade] = []
    n = dt.size
    k = 0
    while k < n:
        if not enter[k]:
            k += 1
            continue
        pp_e, ps_e = pp_t[k], ps_t[k]
        if not (np.isfinite(pp_e) and np.isfinite(ps_e) and pp_e > 0 and ps_e > 0):
            k += 1
            continue
        entry_ms = int(dt[k])
        # sizing: perp notional = NOTIONAL_FRAC * equity, capped by gross leverage
        perp_notional = p.NOTIONAL_FRAC * ref_equity
        perp_notional = min(perp_notional, consts.MAX_LEV * ref_equity / 2.0)  # gross = 2x perp
        qty = perp_notional / pp_e
        if qty <= 0:
            k += 1
            continue
        basis_entry = pp_e - ps_e
        cap_ms = entry_ms + max_hold_ms

        # funding-decay exit: first settlement > entry with funding <= EXIT_FUND
        dec_ms, dec_reason = None, None
        j = k + 1
        while j < n and dt[j] <= cap_ms:
            if np.isfinite(f_now[j]) and f_now[j] <= exit_fund:
                dec_ms, dec_reason = int(dt[j]), "funding_decay"
                break
            j += 1

        # basis stop intrabar within [entry, min(cap, dec)]
        horizon = cap_ms if dec_ms is None else min(cap_ms, dec_ms)
        lo = int(np.searchsorted(mt, entry_ms, side="left"))
        hi = int(np.searchsorted(mt, horizon, side="right"))
        stop_ms, stop_pp, stop_ps = None, None, None
        if hi > lo + 1:
            seg_basis = ppc[lo:hi] - psc[lo:hi]
            # short perp/long spot loses when basis WIDENS: (basis - basis_entry)/ps_e >= stop
            adverse = (seg_basis - basis_entry) / ps_e
            adverse[0] = -np.inf  # not on entry bar
            hit = adverse >= basis_stop
            if hit.any():
                bi = lo + int(np.argmax(hit))
                stop_ms = int(mt[bi]); stop_pp = float(ppo[bi]); stop_ps = float(pso[bi])

        # choose earliest exit
        cands = []
        if stop_ms is not None:
            cands.append((stop_ms, stop_pp, stop_ps, "basis_stop"))
        if dec_ms is not None:
            fpos = int(np.searchsorted(mt, dec_ms, side="left"))
            if fpos < mt.size and mt[fpos] == dec_ms:
                cands.append((dec_ms, float(ppo[fpos]), float(pso[fpos]), dec_reason))
        cpos = min(int(np.searchsorted(mt, cap_ms, side="left")), mt.size - 1)
        cands.append((int(mt[cpos]), float(ppo[cpos]), float(pso[cpos]), "time_cap"))
        exit_ms, pp_x, ps_x, reason = min(cands, key=lambda x: x[0])

        basis_exit = pp_x - ps_x
        price_pnl = qty * (basis_entry - basis_exit)                 # two-leg net (delta-neutral)
        funding_pnl = fund.funding_pnl_frac(-1, entry_ms, exit_ms) * perp_notional  # short receives
        en_p, en_s = qty * pp_e, qty * ps_e
        ex_p, ex_s = qty * pp_x, qty * ps_x
        # per-leg cost via the √-impact model, at this entry's participation & vol (fallback flat)
        adv, dvol = adv_t[k], dvol_t[k]
        have_impact = np.isfinite(adv) and adv > 0 and np.isfinite(dvol) and dvol > 0
        if not asym:
            # legacy symmetric model: one leg fraction for all 4 legs, perp ADV
            if have_impact:
                leg_frac = impact.round_trip_bps(perp_notional / adv, dvol) / 2.0 * BPS
            else:
                leg_frac = flat_leg
            perp_leg, spot_leg = leg_frac, leg_frac
        else:
            # #38 asymmetric: spot leg (10bps fee, spot ADV) costs ~2x the perp leg (5bps, perp ADV)
            vol_bps = (dvol * 1e4) if have_impact else 0.0
            perp_imp = costs_cfg.IMPACT_COEF * vol_bps * np.sqrt(perp_notional / adv) if have_impact else 0.0
            spot_adv = adv * spot_adv_ratio
            spot_imp = (costs_cfg.IMPACT_COEF * vol_bps * np.sqrt(perp_notional / spot_adv)
                        if have_impact and spot_adv > 0 else 0.0)
            perp_leg = (costs_cfg.TAKER_FEE_BPS + costs_cfg.SLIPPAGE_BPS + perp_imp) * smult * BPS
            spot_leg = (spot_fee + spot_spread + spot_imp) * smult * BPS
        # legging slippage booked once per pair establishment (entry and exit), on the pair notional
        entry_cost = perp_leg * en_p + spot_leg * en_s + legging_frac * perp_notional
        exit_cost = perp_leg * ex_p + spot_leg * ex_s + legging_frac * perp_notional
        cost = entry_cost + exit_cost
        net = price_pnl + funding_pnl - cost

        entry_day = pd.Timestamp((entry_ms // MS_PER_DAY) * MS_PER_DAY, unit="ms", tz="UTC")
        exit_day = pd.Timestamp((exit_ms // MS_PER_DAY) * MS_PER_DAY, unit="ms", tz="UTC")
        trades.append(Trade(
            symbol=sd.symbol, side=-1, entry_ms=entry_ms, exit_ms=exit_ms,
            entry_day=entry_day, exit_day=exit_day, entry_px=pp_e, exit_px=pp_x,
            qty=qty, notional=perp_notional, price_pnl=price_pnl, funding_pnl=funding_pnl,
            cost=cost, net_pnl=net, reason=reason))
        _mark_daily_carry(daily_pnl, daily_basis, qty, basis_entry, basis_exit,
                          entry_day, exit_day, entry_cost, exit_cost,
                          fund, entry_ms, exit_ms, perp_notional)

        exit_k = int(np.searchsorted(dt, exit_ms, side="right"))
        k = max(k + 1, exit_k)

    return trades, daily_pnl
