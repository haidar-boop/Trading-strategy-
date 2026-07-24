"""
Delta-neutral cash-and-carry (spot-hedged funding capture) — the delta-hedged
variant motivated by the FEF finding (funding carry is real; the loss was the naked delta).

Mechanism: when perp funding is positive (longs pay shorts), SHORT the perp (receive
funding) and simultaneously BUY the equivalent spot (hedge the delta). The position is
delta-neutral, so the directional bleed that killed FEF is removed; the net price P&L
reduces to the change in basis (perp - spot). Collect funding until it normalizes, then
unwind. The open question the backtest answers: does the carry survive the 4-leg cost?

Deliberately few free parameters (3 gridded + 1 sizing) — a small search space is the
right call for a strategy that might actually pass, since it minimizes overfitting risk.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParamsCarry:
    ENTRY_FUND_BPS: float = 1.5   # enter when funding settled at t >= this (bps/8h); grid {1,1.5,2,3}
    EXIT_FUND_BPS: float = 0.5    # unwind when funding decays to <= this (bps/8h); grid {0,0.5,1}
    BASIS_STOP_BPS: float = 100.0 # unwind if basis widens against us by >= this (bps); grid {50,100,200}
    NOTIONAL_FRAC: float = 0.5    # perp notional as fraction of equity (delta-neutral); NOT gridded


@dataclass(frozen=True)
class ConstantsCarry:
    MAX_HOLD_DAYS: int = 14           # time-exit backstop
    FUNDING_INTERVAL_HOURS: int = 8
    MAX_LEV: float = 3.0              # gross-leverage cap (perp + spot); delta-neutral so net ~0
    UNIVERSE: tuple = ("BTCUSDT", "ETHUSDT")


@dataclass(frozen=True)
class FiltersCarry:
    LIQ_FLOOR_USD: float = 1_000_000_000.0   # 30d median daily perp volume >= $1B (BTC/ETH pass)
    EVENT_EXCL_MINUTES: float = 30.0


@dataclass(frozen=True)
class CostsCarry:
    # 4 taker legs per round trip (short perp + buy spot in; buy perp + sell spot out).
    # Cost model = ported ImpactCostModel: fee + half-spread + impact_coef*vol_bps*sqrt(part),
    # all x STRESS_MULT. At retail size (participation ~5e-6 on a $1B-ADV symbol) the impact
    # term is ~0.2 bps, so the binding stress is the multiplier on fee+spread. The pass/fail
    # run uses STRESS_MULT=2.0 (the ~2x-cost regime the carry survived in sensitivity testing).
    TAKER_FEE_BPS: float = 5.0
    SLIPPAGE_BPS: float = 2.0        # treated as the half-spread in the impact model
    IMPACT_COEF: float = 0.5
    STRESS_MULT: float = 2.0         # stressed pass/fail cost; set 1.0 for the base (unstressed) view


@dataclass(frozen=True)
class ValidationCarry:
    DSR_CONF: float = 0.95
    TRIAL_COUNT_N: int = 1000        # shared conservative ledger (over-deflates a 36-trial search)
    OOS_PF_MIN: float = 1.3
    OOS_MIN_TRADES: int = 30
    MINTRL_CONF: float = 0.95
    IS_MONTHS: int = 24
    OOS_MONTHS: int = 6
    STEP_MONTHS: int = 6
    PURGE_DAYS: int = 14
    EMBARGO_DAYS: int = 28
    MC_PATHS: int = 1000
    MC_BLOCK_TRADES: int = 5
    MC_JITTER_MINUTES: int = 5
    MC_FAIL_TERMINAL_FRAC: float = 0.5
    MC_ENVELOPE_PCTILE: float = 5.0
    # grid (36 combos)
    ENTRY_FUND_GRID: tuple = (1.0, 1.5, 2.0, 3.0)
    EXIT_FUND_GRID: tuple = (0.0, 0.5, 1.0)
    BASIS_STOP_GRID: tuple = (50.0, 100.0, 200.0)


@dataclass(frozen=True)
class VariantCarry:
    params: ParamsCarry

    def label(self) -> str:
        p = self.params
        return f"EF{p.ENTRY_FUND_BPS:g}_XF{p.EXIT_FUND_BPS:g}_BS{int(p.BASIS_STOP_BPS)}"


def full_grid_carry(spec: ValidationCarry, notional_frac: float = 0.5) -> list[VariantCarry]:
    out = []
    for ef in spec.ENTRY_FUND_GRID:
        for xf in spec.EXIT_FUND_GRID:
            for bs in spec.BASIS_STOP_GRID:
                if xf >= ef:
                    continue  # exit threshold must be below entry threshold
                out.append(VariantCarry(ParamsCarry(ENTRY_FUND_BPS=ef, EXIT_FUND_BPS=xf,
                                                    BASIS_STOP_BPS=bs, NOTIONAL_FRAC=notional_frac)))
    return out
