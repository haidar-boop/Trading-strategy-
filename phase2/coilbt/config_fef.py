"""
Funding-Extreme Fade (FEF) configuration — Candidate 2 from STRATEGY_DESIGN.md.

Directional funding-fade on Binance USDT-M perps: at each 8h funding settlement, if
funding is in its extreme tail AND open interest has recently expanded, take the side
that RECEIVES funding (fade the crowd). 5 free params (RISK_FRAC not gridded); the rest
pre-registered frozen. Grid = 192 param combos x 2 structural variants = 384; shared
DSR ledger N = 1000. Validation floor is 30 OOS trades (FEF-specific, lower than Coil's 60).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParamsFEF:
    ENTRY_PCT: float = 97.5    # extreme-funding percentile; grid {95, 96.5, 97.5, 99}
    OI_Z_MIN: float = 1.0      # OI-expansion z-score floor; grid {0.5, 1.0, 1.5, 2.0}
    STOP_ATR_MULT: float = 2.5 # stop distance in 4h-ATR units; grid {1.5, 2.5, 3.5}
    EXIT_PCT: float = 80.0     # funding-normalization exit percentile; grid {50, 65, 80, 90}
    RISK_FRAC: float = 0.01    # equity fraction risked to the stop; NOT gridded


@dataclass(frozen=True)
class ConstantsFEF:
    PCT_LOOKBACK_DAYS: int = 365      # funding-percentile trailing window
    OI_LOOKBACK_DAYS: int = 90        # z-score baseline window for 24h OI changes
    OI_CHANGE_HOURS: int = 24         # OI change window (= 3 funding intervals)
    ATR_PERIOD: int = 14              # Wilder ATR on 4h bars
    BAR_HOURS: int = 4                # ATR bar size
    MAX_HOLD_DAYS: int = 7            # time-exit backstop (= 21 funding intervals)
    PER_POS_LEV: float = 1.5          # per-position leverage cap
    TOTAL_LEV: float = 3.0            # portfolio leverage cap
    FUNDING_INTERVAL_HOURS: int = 8   # required funding interval (ok_mech)
    UNIVERSE: tuple = ("BTCUSDT", "ETHUSDT")
    PCT_MIN_HISTORY: int = 200        # min funding prints before a percentile is trusted


@dataclass(frozen=True)
class FiltersFEF:
    LIQ_FLOOR_USD: float = 1_000_000_000.0   # 30d median DAILY perp volume >= $1B
    SPREAD_CEIL_BPS: float = 2.0             # LIVE-only; backtest assume-pass
    VOL_HI_24H: float = 0.15                 # |close/close_24h_ago - 1| must be <= 15%
    VOL_LO_ANN: float = 0.20                 # 30d annualized realized vol must be >= 20%
    EVENT_EXCL_MINUTES: float = 30.0         # +/-30 min around FOMC/CPI
    MAKER_PATH_ENABLED: bool = False         # backtest fills at taker (conservative)


@dataclass(frozen=True)
class CostsFEF:
    TAKER_FEE_BPS: float = 5.0
    MAKER_FEE_BPS: float = 2.0
    SLIPPAGE_BPS: float = 2.0


@dataclass(frozen=True)
class ValidationFEF:
    DSR_CONF: float = 0.95
    TRIAL_COUNT_N: int = 1000
    OOS_PF_MIN: float = 1.3
    OOS_MIN_TRADES: int = 30          # FEF floor (tail-gated => low count expected)
    MINTRL_CONF: float = 0.95
    IS_MONTHS: int = 24
    OOS_MONTHS: int = 6
    STEP_MONTHS: int = 6
    PURGE_DAYS: int = 7               # = max hold
    EMBARGO_DAYS: int = 28           # 2x the 14-day cap, per spec
    MC_PATHS: int = 1000
    MC_BLOCK_TRADES: int = 5
    MC_JITTER_MINUTES: int = 5        # +/-5 min execution jitter on fill
    MC_FAIL_TERMINAL_FRAC: float = 0.5
    MC_ENVELOPE_PCTILE: float = 5.0
    # grid
    ENTRY_PCT_GRID: tuple = (95.0, 96.5, 97.5, 99.0)
    OI_Z_GRID: tuple = (0.5, 1.0, 1.5, 2.0)
    STOP_ATR_GRID: tuple = (1.5, 2.5, 3.5)
    EXIT_PCT_GRID: tuple = (50.0, 65.0, 80.0, 90.0)
    SIDE_VARIANTS: tuple = ("symmetric", "positive_only")


@dataclass(frozen=True)
class VariantFEF:
    params: ParamsFEF
    side_mode: str  # "symmetric" (fade both tails) or "positive_only" (short high funding only)

    def label(self) -> str:
        p = self.params
        return (f"E{p.ENTRY_PCT:g}_Z{p.OI_Z_MIN:g}_S{p.STOP_ATR_MULT:g}"
                f"_X{int(p.EXIT_PCT)}_{self.side_mode}")


def full_grid_fef(spec: ValidationFEF, risk_frac: float = 0.01) -> list[VariantFEF]:
    out = []
    for e in spec.ENTRY_PCT_GRID:
        for z in spec.OI_Z_GRID:
            for s in spec.STOP_ATR_GRID:
                for x in spec.EXIT_PCT_GRID:
                    p = ParamsFEF(ENTRY_PCT=e, OI_Z_MIN=z, STOP_ATR_MULT=s, EXIT_PCT=x,
                                  RISK_FRAC=risk_frac)
                    for side in spec.SIDE_VARIANTS:
                        out.append(VariantFEF(params=p, side_mode=side))
    return out
