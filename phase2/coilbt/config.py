"""
Coil-Break configuration: 4 free params, frozen constants, filters, cost model,
and the validation spec. Values are locked to the Phase-1 spec (STRATEGY_DESIGN.md,
Candidate 1). Nothing here is tuned inside the backtest except the gridded params.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Params:
    """The 4 free parameters. F_RISK is a parameter but is NOT gridded (fixed a priori)."""
    L: int = 20              # channel lookback (days); grid {10,15,20,30,40}
    Q_COMP: float = 25.0     # compression percentile; grid {10,20,25,35}
    K_ATR: float = 3.0       # shared initial + trailing ATR multiple; grid {2,3,4,5}
    F_RISK: float = 0.005    # equity fraction risked to the initial stop; fixed


@dataclass(frozen=True)
class Constants:
    ATR_N: int = 14                     # Wilder ATR period (days)
    PCTL_WIN: int = 365                 # compression percentile trailing window (days)
    MAX_HOLD_DAYS: int = 14             # hard holding cap
    MAX_LEV: float = 3.0                # leverage cap (portfolio budget across bots)
    FUND_GATE: float = 0.0005           # per-8h funding veto (5x the 0.01% baseline); frozen
    PER_SYMBOL_SPLIT: float = 0.5       # 50/50 BTC/ETH sleeves
    FUNDING_BUDGET_STOP_BPS: float = 25.0
    UNIVERSE: tuple = ("BTCUSDT", "ETHUSDT")
    # Percentile interpolation method — FROZEN (a hidden DOF; must not vary across the grid).
    PCTL_METHOD: str = "linear"


@dataclass(frozen=True)
class Filters:
    LIQ_FLOOR_USD: float = 500_000.0    # 30d median 1m dollar volume
    SPREAD_CEIL_BPS: float = 2.0        # LIVE-only; backtest assume-pass
    VOL_BAND_LOW: float = 0.005         # atr14/close lower bound
    VOL_BAND_HIGH: float = 0.10         # atr14/close upper bound
    EVENT_EXCL_HOURS: float = 24.0      # before FOMC decision / US CPI
    OI_GAP_MAX_HOURS: float = 1.0
    MISSING_1M_MAX: int = 0             # over the last L days
    LIQ_CAP_FRAC: float = 0.05          # clip <= 5% of 30d median 1m dollar volume
    LIVE: bool = False                  # backtest => spread filter assume-pass


@dataclass(frozen=True)
class Costs:
    TAKER_FEE_BPS: float = 5.0
    MAKER_FEE_BPS: float = 2.0          # deferred; base spec is taker-only
    SLIPPAGE_BPS: float = 2.0
    FUNDING_INTERVAL_HOURS: int = 8
    MAKER_PATH_ENABLED: bool = False


@dataclass(frozen=True)
class ValidationSpec:
    # thresholds (all after full costs, on concatenated OOS)
    DSR_MIN: float = 0.0                # DSR is a probability; "DSR>0 at 95%" => DSR >= 0.95
    DSR_CONF: float = 0.95
    TRIAL_COUNT_N: int = 1000           # shared batch ledger (NOT 320)
    OOS_PF_MIN: float = 1.3
    OOS_MIN_TRADES: int = 60
    MINTRL_CONF: float = 0.95
    # walk-forward
    IS_MONTHS: int = 24
    OOS_MONTHS: int = 6
    STEP_MONTHS: int = 6
    PURGE_DAYS: int = 14                # = max hold
    EMBARGO_DAYS: int = 15             # max(14d, ~1% of span)
    # Monte Carlo
    MC_PATHS: int = 2000
    MC_BLOCK_TRADES: int = 5
    MC_JITTER_MINUTES: int = 30
    MC_FAIL_TERMINAL_FRAC: float = 0.5
    MC_ENVELOPE_PCTILE: float = 5.0
    # grid
    L_GRID: tuple = (10, 15, 20, 30, 40)
    Q_COMP_GRID: tuple = (10.0, 20.0, 25.0, 35.0)
    K_ATR_GRID: tuple = (2.0, 3.0, 4.0, 5.0)
    OI_VARIANTS: tuple = ("on", "off")
    SIDE_VARIANTS: tuple = ("both", "long_only")


@dataclass(frozen=True)
class Variant:
    """One backtest configuration = params + the two structural variants."""
    params: Params
    oi_on: bool
    side_mode: str  # "both" or "long_only"

    def label(self) -> str:
        oi = "oiON" if self.oi_on else "oiOFF"
        return f"L{self.params.L}_Q{int(self.params.Q_COMP)}_K{self.params.K_ATR:g}_{oi}_{self.side_mode}"


def full_grid(spec: ValidationSpec, f_risk: float = 0.005) -> list[Variant]:
    """The 320-trial Coil-Break grid: 5*4*4 params x 2 OI x 2 side."""
    out = []
    for L in spec.L_GRID:
        for q in spec.Q_COMP_GRID:
            for k in spec.K_ATR_GRID:
                p = Params(L=L, Q_COMP=q, K_ATR=k, F_RISK=f_risk)
                for oi_on in (True, False):
                    for side in spec.SIDE_VARIANTS:
                        out.append(Variant(params=p, oi_on=oi_on, side_mode=side))
    return out
