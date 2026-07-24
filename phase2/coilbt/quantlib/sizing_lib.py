# Adapted from the uploaded quant_system research sandbox (synthetic-data
# methodology toolkit); integrated verbatim-algorithm into the phase2 harness.
"""
sizing.py - Position sizing and risk scaling.

Two pillars:
  - Volatility targeting: leverage_t = clip(target_vol / realized_vol_t, 0, L_max)
    Stabilises portfolio risk far more reliably than tweaking signals.
  - Fractional Kelly: f* = mu / sigma^2 (growth-optimal), used at a fraction
    kappa ~ 0.25 because full Kelly is far too aggressive under estimation error.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

ANN = 252


def ewma_vol(returns: pd.Series | pd.DataFrame, halflife: int = 20,
             ann: int = ANN):
    """Annualised EWMA volatility."""
    var = returns.ewm(halflife=halflife, min_periods=halflife // 2).var()
    return np.sqrt(var) * np.sqrt(ann)


def vol_target_leverage(realized_ann_vol, target_ann_vol=0.10, l_max=2.0):
    lev = target_ann_vol / np.where(realized_ann_vol > 1e-9, realized_ann_vol, np.nan)
    return np.clip(lev, 0.0, l_max)


def fractional_kelly(mu_ann, sigma_ann, kappa=0.25, cap=1.0):
    """Growth-optimal fraction f* = mu/sigma^2, scaled by kappa and capped."""
    f_star = mu_ann / np.maximum(sigma_ann ** 2, 1e-9)
    return np.clip(kappa * f_star, -cap, cap)


def cap_by_adv(weights: np.ndarray, adv_frac: np.ndarray, max_participation=0.05):
    """
    Cap each weight so traded notional <= max_participation * ADV.
    adv_frac = ADV notional / portfolio equity (per asset).
    """
    max_w = max_participation * np.asarray(adv_frac, float)
    return np.clip(weights, -max_w, max_w)
