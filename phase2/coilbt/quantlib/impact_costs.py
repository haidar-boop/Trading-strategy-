"""
Square-root market-impact cost model. Adapted from the uploaded quant_system.

More realistic than the flat fee+slippage model in phase2/coilbt/costs.py: impact
scales with the square root of participation (traded notional / ADV), per the
empirical square-root law, and a stress multiplier lets validation re-charge costs
at 2-3x to confirm an edge is not just unpaid transaction cost.

    cost_frac = |dw| * (commission + half_spread) + |dw| * impact_coef*vol_bps*sqrt(participation)

This complements (does not replace) the venue-calibrated flat model; the phase2
engines use the flat taker model by default, and this is available for capacity /
stress analysis and for the portfolio layer.
"""
from __future__ import annotations

import numpy as np


class ImpactCostModel:
    def __init__(self, commission_bps: float = 1.0, half_spread_bps: float = 2.0,
                 impact_coef: float = 0.5, stress_mult: float = 1.0):
        self.commission_bps = commission_bps
        self.half_spread_bps = half_spread_bps
        self.impact_coef = impact_coef
        self.stress_mult = stress_mult

    def cost_fraction(self, dw: np.ndarray, daily_vol: np.ndarray,
                      participation: np.ndarray) -> float:
        """Total cost as a fraction of equity for a rebalance.

        dw            : absolute weight changes (fraction of equity), per asset
        daily_vol     : per-asset daily vol as a fraction (e.g. 0.012)
        participation : traded notional / ADV notional, per asset (>=0)
        """
        dw = np.abs(np.asarray(dw, float))
        vol_bps = np.asarray(daily_vol, float) * 1e4
        part = np.clip(np.asarray(participation, float), 0, None)
        linear = dw * (self.commission_bps + self.half_spread_bps) * 1e-4
        impact = dw * (self.impact_coef * vol_bps * np.sqrt(part)) * 1e-4
        return float((linear + impact).sum() * self.stress_mult)

    def round_trip_bps(self, participation: float, daily_vol: float) -> float:
        """Convenience: implied round-trip cost (bps) at a given participation."""
        vol_bps = daily_vol * 1e4
        one_side = (self.commission_bps + self.half_spread_bps
                    + self.impact_coef * vol_bps * np.sqrt(max(participation, 0.0)))
        return float(2.0 * one_side * self.stress_mult)
