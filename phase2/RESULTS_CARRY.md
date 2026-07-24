# Phase 2c — Delta-Neutral Cash-and-Carry Results (expanded universe, stressed costs)

> ### ⚠️ UPDATE (#38 spot-execution correction) — the "near-miss" was too optimistic
>
> The numbers below the banner were computed with a **symmetric** per-leg cost that under-charged
> the spot leg. After modeling spot execution honestly (#4/#38: Binance **spot taker is 2× the perp
> taker**, plus ~2 bps legging slippage per side — see `RESULTS_EXECUTION.md`), the verdict gets
> **worse and cleaner**:
>
> | metric (10-symbol OOS, stressed 2×) | old (symmetric cost) | **corrected (#38)** |
> |---|---|---|
> | OOS net P&L | +$732 | **+$270** (funding +1,677 · basis +108 · **cost −1,515**) |
> | OOS profit factor | 21.8 | **2.90** |
> | per-trade Sharpe | +0.949 | **+0.350** |
> | **per-trade DSR (effective-N)** | **0.962 (borderline PASS)** | **0.001 (clear FAIL)** |
> | daily DSR | 0.000 | 0.000 |
> | PBO / CSCV | 0.001 | **0.001** (still not overfit) |
> | verdict | near-miss (5/8) | **FAIL — DSR, MinTRL, per-trade DSR all fail** |
>
> **The single borderline "pass" this strategy ever had (per-trade DSR at effective-N = 0.962) was
> resting on the under-charged spot leg.** With realistic costs, cost rises to ~73% of gross funding
> and the risk-adjusted edge no longer clears the deflation bar on ANY ruler. What survives: it is
> still net-positive, still not overfit (PBO 0.001), still cost-*robust in sign* — but it is now an
> unambiguous FAIL on the pre-registered bar, not a near-miss. The honest headline is: **more
> realistic execution modeling turned a near-miss into a clear no.** Everything below is retained for
> the record but is superseded by this correction.

---

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

## Effective-N deflation — a legitimate correction, and a borderline pass (read the caveats)

The DSR deflation was over-inflated because the 33-config grid is highly correlated. The evidence
is concrete: **34 of 35 exits are `time_cap`, `basis_stop` never fires, `funding_decay` fires once**
— so two of the three gridded parameters (BASIS_STOP, EXIT_FUND) are **inert**; only ENTRY_FUND's 4
values is a real search dimension. The eigenvalue participation ratio agrees: **N_eff = 3.97**. So
my "33 configs" were genuinely ~4 distinct strategies, and deflating by 33 (let alone 1000) was
wrong. This correction is legitimate, not gaming — I'd defend N_eff≈4 to any reviewer.

Applying it:

| Ruler | Raw-N (33) | Effective-N (4) | Passes? |
|---|---|---|---|
| **Daily DSR** (pre-registered primary) | 0.000 | **0.199** | ❌ still fails |
| **Per-trade DSR** (fair low-frequency ruler) | 0.007 | **0.962** | ✅ (MinTRL 30 ≤ 35 available) |

**The honest read — and I am flagging the risk on myself:**
- **N_eff=4 is a clean, justified correction.** No dispute.
- **But the pass is on the *per-trade* ruler, and the pre-registered *daily* ruler still fails**
  (0.199). Switching to the ruler that passes *after* the primary failed is exactly the
  motivated-reasoning pattern this project warns against. The per-trade ruler is defensible for a
  low-frequency strategy, but it ignores idle-capital time, and I chose it after seeing daily fail.
- **The pass is borderline on every threshold:** DSR 0.962 vs the 0.95 bar; MinTRL 30 vs 35 trades.
  A result sitting on the knife-edge of every gate, reached under the most favorable defensible
  assumptions, is a "maybe, barely," not a robust "yes."
- **The tail is still untested** (next section) — even a clean statistical pass would not make it
  safe to deploy.

So I will **not** call this validated. The honest status upgrade is: **from "promising lead" to
"plausible edge with a legitimate but borderline statistical case."** Before it earns "validated," it
needs (1) an *independent* reviewer to bless the per-trade + effective-N methodology as the right
ruler rather than the flattering one, and (2) the tail stress test below. 6 of 9 gates pass; the
three fails (daily DSR, daily MinTRL, MC envelope) are the ones telling me to stay skeptical.

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
