# Phase 2c — Delta-Neutral Cash-and-Carry Results (expanded universe, stressed costs)

**Verdict: NOT validated — but the strongest, most robust, non-overfit result in the project, and
a genuine near-miss.** On a 10-symbol universe, under **stressed 2× √-impact costs**, over 8
walk-forward folds, the delta-neutral carry **clears 5 of 8 gates** — including the trade-count
floor it previously missed and *both* overfitting screens — while **failing the Deflated Sharpe
Ratio**, the single strictest test. It is a real, positive, cost-robust, not-overfit carry whose
*risk-adjusted* return is not strong enough to clear the demanding DSR bar. Do not deploy on this
evidence.

## Measured OOS results (10 symbols, stressed 2× costs, all measured)

Universe: BTC · ETH · SOL · XRP · DOGE · BNB · ADA · LINK · AVAX · LTC (admitted by the $1B floor
where liquid). Window 2020-01-01 → 2025-12-31; 33-variant grid; 8 folds; 1461 OOS days.

| Gate | Value | Threshold | Pass? |
|---|---|---|---|
| **OOS trades** | **35** | ≥ 30 | ✅ (was 18 on 2 symbols) |
| **NET P&L (stressed 2× cost)** | **+$732** (funding +$1,677 · basis +$108 · cost −$1,053) | — | — |
| OOS profit factor | **21.8** | ≥ 1.3 | ✅ |
| **PBO / CSCV** | **0.001** | < 0.5 | ✅ **not overfit** |
| Single-best-month excision | positive ex-best | ex-best > 0 | ✅ |
| MC entry-timing jitter (two-leg) | median ≈ base | median ≥ 0.5×base | ✅ |
| **Deflated Sharpe (DSR)** | **0.000** (benchmark 0.368 vs per-bar Sharpe **0.099**) | ≥ 0.95 | ❌ **the blocker** |
| — DSR at honest own-search N=33 | **0.000** | ≥ 0.95 | ❌ (fails even un-inflated) |
| MinTRL | ∞ | ≤ 1461 | ❌ |
| MC block-bootstrap envelope | breached | above p5 | ❌ (weak on sparse returns) |
| OOS Sharpe (ann.) / Sortino / Calmar / MaxDD | +1.89 / +1.05 / +1.99 / **−0.9%** | — | — |

**5 of 8 gates pass.** `artifacts/carry_result.json`, `artifacts/carry_oos_equity.csv`.

## What the expansion proved

- **The universe fix worked.** 18 → 35 OOS trades: the carry now clears the evidence floor. Adding
  liquid perps scaled the opportunity exactly as expected.
- **It is cost-robust at scale.** Under the ported √-impact model stressed 2×, the carry still nets
  **+$732** — the funding gross (+$1,677) absorbs a doubled cost (−$1,053). Not an artifact of
  optimistic costs.
- **It is not overfit.** PBO/CSCV = 0.001 across 33 configs — the in-sample-best config reliably
  stays best out-of-sample. The two overfitting screens (DSR's deflation *and* PBO) disagree here,
  and that disagreement is informative (below).

## Why it still fails — read this honestly

The deciding failure is **DSR**, and it fails cleanly even at the honest own-search N=33 (not just
the conservative N=1000). The reason: the deployed **per-bar Sharpe is 0.099**, and the
multiple-testing-deflated benchmark is **0.368** — the risk-adjusted return does not clear the bar.

Two things are true at once and I won't hide either:
1. **PBO passes but DSR fails — genuinely, not contradictorily.** PBO tests *selection stability*
   (does the best config generalize — yes). DSR tests *magnitude vs the search* (is the Sharpe
   level beyond what the config spread could produce by luck — no). A strategy can have stable,
   non-overfit selection *and* a Sharpe too modest to clear the deflation bar. This one does.
2. **The daily-return Sharpe understates a low-frequency strategy** — 35 trades over 1461 mostly-flat
   days makes the daily-Sharpe small even though profit factor is 21.8 and MaxDD is −0.9%. That is a
   real limitation of the metric, **but it is not an excuse**: the pre-registered bar is DSR on the
   deployed return stream, and it is not cleared. I am not going to relabel a fail as a pass.

## Per-trade re-score (the fair ruler for a low-frequency strategy)

The daily-Sharpe fail is partly a metric artifact (35 trades diluted across ~1,400 flat days), so we
re-scored on a **per-trade** basis — the correct ruler for a low-frequency strategy — and reported it
**alongside** the daily numbers (not instead of them; swapping to the flattering metric would be the
Sharpe-inflation this project exists to prevent):

| Ruler | Sharpe | PSR(0) | DSR (own-N) | MinTRL |
|---|---|---|---|---|
| Daily returns (n=1461 days) | 0.099/bar (1.89 ann) | — | 0.000 | ∞ |
| **Per-trade (n=35 trades)** | **+0.949** | **1.000** | **0.007** | **∞ → NEED MORE trades** |

What this tells us, cleanly:
- **The bets are genuinely good.** Per-trade Sharpe 0.949 with PSR(0)=1.000 — the trade-level edge is
  real and confidently positive. The 10× jump from the daily number is legitimate (it removes the
  idle-day dilution), not a trick.
- **The fair ruler still fails — and names the real barrier.** Even per-trade, DSR is 0.007 and MinTRL
  is infinite: **the binding constraint is trade *count*, not bet quality.** 35 trades cannot prove
  the edge isn't luck given the config search and the heterogeneous grid dispersion. No choice of
  ruler fixes that — **only more data does** (more instruments, longer history, or higher frequency).

This is the honest payoff of doing it right: we gave the strategy the fairest possible measurement,
and it confirmed the edge is real per-bet **but** told us plainly we do not yet have enough trades to
claim it. You cannot measure your way to significance — you need more evidence.

## The caveat that matters most

**34 of 35 exits are `time_cap`, and MaxDD is −0.9%.** As with the 2-symbol run, the strategy held
through calm sustained-funding regimes and **the sample still largely dodged a funding-unwind
cascade** — carry's signature tail. The pristine drawdown is a property of a benign sample, not
proof of safety, and **perp liquidation is still unmodeled**. A carry that looks this clean has, by
construction, not yet been shown the steamroller.

## Honest bottom line

Across the whole project — three Phase-1 designs, three real-data backtests, a combined platform,
and this expansion — the delta-neutral cash-and-carry is **the only strategy that is simultaneously
positive, cost-robust (2×), not overfit (PBO), and past the trade floor.** It is the best lead by a
wide margin. **But it is not validated:** its risk-adjusted return does not clear the Deflated
Sharpe bar, and its tail (a leverage-flush cascade with perp liquidation) is untested. The honest
status is **"a real, promising, well-behaved carry edge that has cleared more screens than anything
else here, but is not — on this evidence — a deployable, statistically-proven edge."**

What would settle it, in order:
1. **A denser / longer sample or a per-trade DSR construction** to fairly measure a low-frequency
   strategy's risk-adjusted return (the daily-Sharpe penalty is the proximate cause of the DSR fail).
2. **A modeled funding-unwind cascade with perp liquidation** in-sample — the real test of whether
   the −0.9% drawdown survives contact with the tail.
3. If it clears DSR under (1) *and* survives (2), it is the first deployable edge in the project.

*Not investment advice. No validated edge — the strongest, most robust, non-overfit lead, short of
the strictest bar.*
