"""
Tail-stress scenario engine for the delta-neutral cash-and-carry (#6, #5).

The backtest's -0.9% max drawdown is a benign-sample artifact: 34/35 exits were the calm
time-cap and no funding-unwind cascade occurred in-sample. This module STRESSES the position
against the specific adverse scenarios that actually kill carry trades, computed analytically on
a representative position so the loss is explicit and auditable.

Representative position (default sizing): equity E; perp notional = NOTIONAL_FRAC*E; short perp +
long spot of equal base quantity; gross = 2*perp notional. Delta-neutral, so the P&L shock in each
scenario is driven by basis moves, funding sign flips, execution frictions, or a broken hedge
(perp liquidation), NOT by the underlying price direction.

All outputs are P&L as a fraction of EQUITY (negative = loss). This is a stress analysis, not a
probability estimate — it answers "if this happens, how much do I lose?", which the backtest cannot.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Position:
    equity: float = 10_000.0
    notional_frac: float = 0.5      # perp notional = 0.5 * equity ; gross = 1.0 * equity
    perp_leverage: float = 3.0      # margin used on the perp leg if ISOLATED margin
    taker_bps: float = 5.0
    slippage_bps: float = 2.0

    @property
    def perp_notional(self):
        return self.notional_frac * self.equity

    @property
    def perp_margin_isolated(self):
        return self.perp_notional / self.perp_leverage


def _frac(pnl_dollars, pos):
    return pnl_dollars / pos.equity


def scenario_funding_flip(pos: Position, rate_bps=-3.0, settlements=9):
    """Funding flips negative and stays there (e.g. -3 bps/8h for 72h = 9 settlements).
    A short perp PAYS negative funding. Loss = |rate| * settlements * perp_notional."""
    loss = (rate_bps * 1e-4) * settlements * pos.perp_notional   # rate<0 -> short pays -> loss<0
    return _frac(loss, pos)


def scenario_basis_blowout(pos: Position, blowout_bps=800.0, basis_stop_bps=100.0, gaps=True):
    """Perp premium blows out (perp trades far above spot). Short-perp/long-spot LOSES the basis
    widening. If the basis stop executes cleanly you cap the loss near the stop; if it GAPS through
    (illiquid / one-tick move), you eat the full blowout."""
    realized = blowout_bps if gaps else basis_stop_bps
    loss = -(realized * 1e-4) * pos.perp_notional
    # plus a taker exit on both legs
    loss -= 2 * (pos.taker_bps + pos.slippage_bps) * 1e-4 * pos.perp_notional
    return _frac(loss, pos)


def scenario_spot_illiquid(pos: Position, spot_haircut_bps=300.0):
    """Spot leg cannot be sold at fair value on unwind (thin book) -> extra slippage on exit."""
    loss = -(spot_haircut_bps * 1e-4) * pos.perp_notional
    return _frac(loss, pos)


def scenario_exchange_halt(pos: Position, halt_days=3.0, adverse_funding_bps=-2.0,
                           adverse_basis_bps=200.0):
    """Exchange halts trading: you cannot exit. Funding keeps accruing (assume adverse) and the
    basis drifts against you; you exit at the worse level once trading resumes."""
    settlements = int(halt_days * 3)
    funding = (adverse_funding_bps * 1e-4) * settlements * pos.perp_notional
    basis = -(adverse_basis_bps * 1e-4) * pos.perp_notional
    return _frac(funding + basis, pos)


def scenario_perp_liquidation(pos: Position, rally_pct=40.0, cross_margin=True):
    """Sharp rally. Short perp loses; long spot gains the same (delta-neutral).
    * CROSS margin: the spot collateral supports the perp, no liquidation -> net ~0 (basis only).
    * ISOLATED margin: if rally > 1/leverage, the perp short is LIQUIDATED at a loss of the perp
      margin, the hedge BREAKS (you are left naked long spot), and you realize the perp loss while
      the spot gain is unrealized/at-risk if price reverses. Models the realized liquidation loss +
      a liquidation penalty."""
    if cross_margin:
        # perp loss and spot gain offset; only a small basis/fee residual
        residual = -2 * (pos.taker_bps + pos.slippage_bps) * 1e-4 * pos.perp_notional
        return _frac(residual, pos)
    liq_threshold = 1.0 / pos.perp_leverage
    if rally_pct / 100.0 < liq_threshold:
        # not liquidated; perp unrealized loss offset by spot gain
        return _frac(-2 * (pos.taker_bps + pos.slippage_bps) * 1e-4 * pos.perp_notional, pos)
    # liquidated: lose the perp margin + a ~1% liquidation penalty; hedge broken
    loss = -pos.perp_margin_isolated - 0.01 * pos.perp_notional
    return _frac(loss, pos)


def scenario_full_cascade(pos: Position):
    """A realistic deleveraging cascade stacks several: funding flips negative, basis blows out and
    gaps through the stop, spot is illiquid, and (isolated margin) the perp liquidates."""
    total = 0.0
    total += scenario_funding_flip(pos, rate_bps=-4.0, settlements=9)
    total += scenario_basis_blowout(pos, blowout_bps=800.0, gaps=True)
    total += scenario_spot_illiquid(pos, spot_haircut_bps=300.0)
    total += scenario_perp_liquidation(pos, rally_pct=40.0, cross_margin=False)
    return total


def capacity_sweep(funding_gross_bps=115.0, adv_usd=20e9, daily_vol=0.03,
                   impact_coef=0.5, base_cost_bps=28.0):
    """Capacity (#9): as deployed notional grows, the √-impact cost grows ~notional^1.5 and
    eventually eats the (linear) funding edge. Sweep notional per trade and find where net -> 0.

    funding_gross_bps : gross funding collected per round trip (from the backtest, ~115 bps/trade)
    adv_usd           : average daily $ volume of the venue (BTC ~ $20B)
    base_cost_bps     : the linear 4-leg fee+slippage round trip (28 bps at 2x stress)
    NOTE: this models only EXECUTION impact. It does NOT model the bigger real limit -- that
    deploying size at the funding extreme COMPRESSES the funding you are trying to collect (you
    become the arb). True capacity is therefore LOWER than the execution-impact crossover below.
    """
    print("\n" + "=" * 72)
    print("CAPACITY (#9) — execution-impact crossover (funding gross ~%.0f bps/trade, ADV $%.0fB)"
          % (funding_gross_bps, adv_usd / 1e9))
    print("=" * 72)
    print(f"{'notional/trade':>16}{'participation':>15}{'impact bps(4leg)':>18}{'net bps':>10}")
    print("-" * 72)
    vol_bps = daily_vol * 1e4
    crossover = None
    for notional in [1e4, 1e5, 1e6, 1e7, 5e7, 1e8, 5e8, 1e9]:
        part = notional / adv_usd
        impact_bps = 4 * impact_coef * vol_bps * (part ** 0.5)   # 4 legs
        net_bps = funding_gross_bps - base_cost_bps - impact_bps
        if net_bps <= 0 and crossover is None:
            crossover = notional
        print(f"${notional:>14,.0f}{part:>15.2e}{impact_bps:>18.1f}{net_bps:>10.1f}")
    print("-" * 72)
    msg = f"~${crossover:,.0f}/trade on this venue" if crossover else ">$1B/trade (impact only)"
    print(f"Execution-impact capacity ceiling: {msg}")
    print("BUT true capacity is much lower: your own flow compresses the funding at the extreme.")
    print("At $10k-$1M retail size, execution impact is negligible; the binding limit is the")
    print("NUMBER of funding-extreme opportunities (decaying, per #19), not size.")
    print("=" * 72)


def run(pos: Position | None = None):
    pos = pos or Position()
    rows = [
        ("Funding flips -3bps/8h for 72h", scenario_funding_flip(pos)),
        ("Basis blowout +8%, stop executes (1%)", scenario_basis_blowout(pos, gaps=False)),
        ("Basis blowout +8%, GAPS through stop", scenario_basis_blowout(pos, gaps=True)),
        ("Spot illiquid on exit (-3%)", scenario_spot_illiquid(pos)),
        ("Exchange halt 3 days (adverse)", scenario_exchange_halt(pos)),
        ("Perp liquidation, CROSS margin", scenario_perp_liquidation(pos, cross_margin=True)),
        ("Perp liquidation, ISOLATED 3x", scenario_perp_liquidation(pos, cross_margin=False)),
        ("FULL CASCADE (all stacked, isolated)", scenario_full_cascade(pos)),
    ]
    print("=" * 72)
    print("TAIL-STRESS SCENARIOS — delta-neutral cash-and-carry")
    print(f"equity=${pos.equity:,.0f}  perp_notional=${pos.perp_notional:,.0f} "
          f"(gross ${2*pos.perp_notional:,.0f})  perp_leverage(isolated)={pos.perp_leverage:g}x")
    print("=" * 72)
    print(f"{'scenario':<42}{'P&L % equity':>14}{'$ on equity':>16}")
    print("-" * 72)
    for name, frac in rows:
        print(f"{name:<42}{frac*100:>13.2f}%{frac*pos.equity:>15.0f}")
    print("-" * 72)
    print("Backtest in-sample max drawdown was -0.9% -> the sample never saw ANY of these.")
    print("Key defenses: (1) CROSS/portfolio margin (spot collateral prevents perp liquidation and")
    print("keeps the hedge intact); (2) hard basis stop with gap-aware sizing; (3) small notional_frac")
    print("so a gapped basis blowout is survivable; (4) avoid holding through scheduled-halt risk.")
    print("=" * 72)
    return rows


if __name__ == "__main__":
    run()
    capacity_sweep()
