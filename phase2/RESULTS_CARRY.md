# Phase 2c — Delta-Neutral Cash-and-Carry Results

**Verdict: INSUFFICIENT EVIDENCE (18 OOS trades < 30 floor) — but the strongest, most
promising, and only non-overfit positive result in the entire project.** The delta-hedged
carry does what FEF's decomposition predicted: it isolates the real funding carry, hedges out
the delta that killed the directional fade, **passes the overfitting screen**, and **survives
2-3× cost stress** — yet on two symbols it does not generate enough out-of-sample trades to make
the statistical claim at the pre-registered confidence.

## Measured OOS results (walk-forward, all measured)

| Metric | Value | Gate | Pass? |
|---|---|---|---|
| OOS trades | **18** | ≥ 30 | ❌ (the blocker) |
| P&L decomposition | **funding +$825 · basis +$43 · cost −$258 · NET +$610** | — | — |
| OOS Sharpe (annualized) | **+3.20** | > 0 | ✅ |
| OOS profit factor | **∞** (no OOS losers) | ≥ 1.3 | ✅ |
| **PBO / CSCV** | **0.064** over 33 configs | < 0.5 | ✅ **(not overfit)** |
| Single-best-month excision | positive ex-best | ex-best > 0 | ✅ |
| Sortino / Calmar / MaxDD | +1.57 / +6.73 / **−0.2%** | — | — |
| Deflated Sharpe (DSR), N=1000 | 0.0001 | ≥ 0.95 | ❌ |
| MinTRL | ∞ | ≤ 1461 | ❌ |
| MC envelope / jitter | breached / below | — | ❌ (low-power at n=18) |

Window 2020-01-01 → 2025-12-31; 33-variant grid, 8 folds, 1461 OOS days. All 18 exits were
`time_cap` (held the full 14 days). `artifacts/carry_result.json`, `artifacts/carry_oos_equity.csv`.

## Why this one is different

FEF proved the funding carry is real (+$347) but bled it back on the naked-perp delta. This
variant **shorts the perp and buys the equivalent spot** — delta-neutral — so the net price P&L
reduces to the basis change (+$43, negligible, exactly as a hedge should) and only the carry
minus 4-leg cost remains. The result:

- **The carry dominates and clears costs.** Funding +$825 vs 4-leg cost −$258 → net +$610.
- **It is not overfit.** PBO/CSCV = 0.064 (the ported screen) — the in-sample-best config stays
  best OOS. This is the first strategy in the project to pass PBO.
- **It survives realistic cost stress.** On the full sample (56 trades), net stays positive at
  **2× cost (+$1,509)** and **3× cost (+$707)** — the funding gross ($3,210) is big enough to
  absorb slippage/impact stress. The edge is not an artifact of optimistic costs.

## Verification (self-audited — this is a positive result, so scrutinized hard)

- **P&L is correct, not a bug.** Leg-by-leg recompute matches: funding equals an independent
  FundingModel calc (no double-count between trade P&L and daily MTM), the sign is right (short
  perp *receives* positive funding), and cost is ~4 taker legs (2 perp + 2 spot). The daily-MTM
  accounting invariant holds (unit-tested).
- **No look-ahead.** Every entry lands exactly on a funding settlement (contemporaneous fill at
  that minute's open, not a future bar); exits are causal; the daily filters use the last
  *completed* day. 5 carry unit tests (delta-neutrality, funding sign, 4-leg cost, invariant,
  entry gating), 41 total, all passing.

## The honest caveats (why it is not "validated")

1. **18 OOS trades < 30.** Below the floor, no statistical claim is made. This is a coverage
   problem, not an edge problem — the full sample has 56 trades; the walk-forward splits them thin.
2. **The pristine −0.2% drawdown is a warning, not a trophy.** Carry is "picking up pennies in
   front of a steamroller": steady gains, then a deleveraging cascade. All 18 exits are `time_cap`
   in calm sustained-positive-funding regimes — the OOS window largely **dodged a funding-spike-then-crash**.
   The clean drawdown likely reflects a benign sample, not absence of tail risk.
3. **Perp liquidation is not modeled.** The spot hedge offsets the perp short, but a sharp rally
   can liquidate an under-margined perp leg before the hedge is realized. At NOTIONAL_FRAC=0.5
   (2× gross) this risk is modest but real and unmodeled.
4. **Costs, though stress-tested, omit spot-leg borrow/transfer** and assume both legs fill; real
   execution in stress is worse than the flat model even at 3×.

## Recommendation — this is the one worth pursuing

Of everything tested, the delta-neutral carry is the **only strategy with a real, positive,
non-overfit, cost-robust edge signal**. It is blocked from a "validated" verdict by exactly one
thing — trade count — and that is fixable cleanly:

1. **Expand the universe** to the top perps that pass the $1B liquidity floor (not just BTC/ETH).
   Carry opportunities scale with the number of instruments; this is the direct path from 18 → 30+
   OOS trades. It changes the pre-registered universe, so it must be **re-locked and the DSR trial
   ledger re-counted** before the numbers mean anything.
2. **Stress the sample deliberately** — ensure the OOS window includes a funding-unwind cascade
   (e.g. a leverage-flush event), and add a perp-liquidation model, to price the steamroller.
3. **Charge √-impact stressed costs** (already ported in `quantlib/impact_costs.py`) as the pass/fail
   cost model, not the flat one.

If it still clears DSR **and** PBO with ≥30 OOS trades under stressed costs and a cascade in-sample,
that is a genuine, deployable edge — the first in this project. Until then: **promising, cost-robust,
not overfit — but unproven on sample size, and carrying an unmodeled tail.**

*Not investment advice. No validated edge yet — a strong lead that has cleared more screens than
anything else here.*
