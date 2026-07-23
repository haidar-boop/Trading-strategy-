"""
Cost model for the Coil-Break backtest, exactly per the stated constraints.

Per side:
  taker fee     = 5 bps
  maker fee     = 2 bps   (maker path deferred; base spec is taker-only)
  slippage      = 2 bps   (marketable orders on BTC/ETH at <= $25k notional)

Round trips:
  taker+taker   = 2*(5+2) = 14 bps   (the pass/fail cost model for base spec)
  maker+taker   = (2) + (5+2) = 9 bps (upside, not assumed)

Funding:
  charged on position notional at each 8h settlement (00:00/08:00/16:00 UTC)
  ONLY when the position is held across that timestamp.
  Sign convention (Binance): funding_rate > 0  =>  longs PAY shorts.
    long  P&L from funding at settlement = -rate * notional
    short P&L from funding at settlement = +rate * notional
  "Adverse funding" for the funding-budget stop = cumulative funding PAID (a positive cost).

All bps are on notional. 1 bp = 1e-4.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

BPS = 1e-4


@dataclass(frozen=True)
class CostModel:
    taker_fee_bps: float = 5.0
    maker_fee_bps: float = 2.0
    slippage_bps: float = 2.0

    def entry_cost_frac(self, maker: bool = False) -> float:
        """Fractional cost of one entry fill (fee + slippage), on notional."""
        fee = self.maker_fee_bps if maker else self.taker_fee_bps
        slip = 0.0 if maker else self.slippage_bps
        return (fee + slip) * BPS

    def exit_cost_frac(self, maker: bool = False) -> float:
        fee = self.maker_fee_bps if maker else self.taker_fee_bps
        slip = 0.0 if maker else self.slippage_bps
        return (fee + slip) * BPS

    def round_trip_frac(self, entry_maker: bool = False, exit_maker: bool = False) -> float:
        return self.entry_cost_frac(entry_maker) + self.exit_cost_frac(exit_maker)


class FundingModel:
    """Indexes the 8h funding series and accrues funding cash flows for held positions.

    funding_df columns: calc_time[ms], last_funding_rate  (settlement timestamp + realized rate).
    """

    def __init__(self, funding_df: pd.DataFrame):
        f = funding_df.sort_values("calc_time").reset_index(drop=True)
        self._ts = f["calc_time"].to_numpy(dtype="int64")
        self._rate = f["last_funding_rate"].to_numpy(dtype="float64")

    def settlements_in(self, start_ms: int, end_ms: int) -> tuple[np.ndarray, np.ndarray]:
        """Funding (timestamps, rates) with start_ms < ts <= end_ms.

        A position entered at start_ms and exited at end_ms pays/receives funding at
        every settlement strictly after entry and at/through exit (held ACROSS the stamp).
        """
        lo = np.searchsorted(self._ts, start_ms, side="right")
        hi = np.searchsorted(self._ts, end_ms, side="right")
        return self._ts[lo:hi], self._rate[lo:hi]

    def funding_pnl_frac(self, side: int, start_ms: int, end_ms: int) -> float:
        """Signed funding P&L as a fraction of (constant) notional over [start, end].

        side = +1 long, -1 short. Positive = credit to the position.
        Assumes notional roughly constant over the hold (position sizing is fixed at entry);
        the engine applies this to the entry notional, matching how a bot without
        rebalancing actually accrues.
        """
        _, rates = self.settlements_in(start_ms, end_ms)
        if rates.size == 0:
            return 0.0
        # long pays when rate>0  => pnl = -side*rate summed
        return float(-side * rates.sum())

    def adverse_funding_frac(self, side: int, start_ms: int, now_ms: int) -> float:
        """Cumulative funding PAID (>=0) by the position from entry to now.

        Used by the funding-budget stop (force-exit at >= 25 bps adverse).
        """
        pnl = self.funding_pnl_frac(side, start_ms, now_ms)
        return max(0.0, -pnl)
