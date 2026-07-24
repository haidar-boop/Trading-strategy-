# "Make it better" — diversification + honest-deflation attempt

Goal: improve the delta-neutral carry toward a real verdict via (1) adding uncorrelated carry
sleeves and HRP-combining them (diversification, the one genuine free lunch), and (2) an
effective-N deflation correction. Deep-research-led, then built and measured. Honest outcome below.

## 1. Cross-sectional funding sleeve — built, and it FAILS (negative-expectancy at retail cost)

Market-neutral funding-dispersion harvest: at each 8h settlement, short the top-K funding perps /
long the bottom-K (both sides receive funding), dollar-neutral, rebalanced every 8h. Vectorized
causal panel backtest over the 10-symbol universe.

**Decomposition (4y, K=2, 2× stressed cost) — sign-verified, not a bug:**

| Component | P&L |
|---|---|
| Funding collected (both sides) | **+$962** ✅ real |
| Price (short-momentum / short-beta bleed) | −$2,213 |
| **Turnover cost (3 rebalances/day)** | **−$11,571** ← the killer |
| **Net** | **≈ −$13k (Sharpe ≈ −3)** |

The funding-dispersion edge is real but tiny (+$962), and **turnover cost is ~12× it**. Cross-sectional
funding is a low-margin, high-turnover strategy that **needs institutional (maker/near-zero) fees** to
work; at retail taker costs it is strongly negative-expectancy. It fails the pre-screen and would
*drag* an HRP book — so it cannot serve as the diversifying sleeve. (Exactly the turnover-killer the
research predicted.)

## 2. Calendar-basis sleeve — SKIPPED (weak diversifier)

Data exists on data.binance.vision (delivery/quarterly klines, both um and cm). But the research
showed it is driven by the **same** leverage-demand factor as the funding carry and is
**positively correlated** with it at the regime level — a weak diversifier, not the low-correlation
sleeve the thesis needs. Building it (multi-contract roll stitching, settlement mechanics) was not
worth it for little diversification benefit. Documented as a non-priority.

## 3. HRP-combine — not applicable

HRP-combining requires ≥2 positive-expectancy, low-correlation sleeves. We have exactly one working
sleeve (the single-name cash-and-carry); the cross-sectional sleeve is negative and the calendar
sleeve is correlated. **There is no viable second sleeve to combine**, so the diversification lever
— sound in theory — did not yield a combinable book here. The HRP machinery remains available in
`quantlib/allocation.py` for when a second working sleeve exists.

## 4. Effective-N deflation — legitimate, and it produces a borderline per-trade pass

The one lever that did move the needle. The carry's 33 configs are highly correlated (BASIS_STOP and
EXIT_FUND are inert — all `time_cap` exits), so the honest effective trial count is **N_eff = 3.97**,
not 33. Under this correct deflation, the **per-trade DSR reaches 0.962 (passes) with MinTRL 30 ≤ 35
trades** — the first DSR variant to clear the bar. But the **pre-registered daily DSR still fails**
(0.199), the pass is borderline, and it depends on choosing the per-trade ruler after daily failed.
See `RESULTS_CARRY.md` for the full, appropriately-skeptical treatment. Not declared validated.

## Net outcome

- **Diversification did not pan out** — no viable second sleeve (cross-sectional dies on turnover;
  calendar is correlated). An honest negative result, cleanly decomposed.
- **The effective-N correction is legitimate** and upgrades the single-name carry from "promising
  lead" to "plausible edge with a borderline statistical case" — pending an independent methodology
  review and the untested funding-cascade tail test.
- The single-name delta-neutral cash-and-carry remains the one and only lead worth pursuing.

*Not investment advice. Still no cleanly-validated edge — one plausible, borderline, tail-untested lead.*
