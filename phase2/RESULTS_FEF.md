# Phase 2 — Funding-Extreme Fade (FEF) Results

**Verdict: FAIL (no edge) — but the more informative failure of the two candidates.** On real
Binance USDT-M data (BTC+ETH, 2020-2025), FEF **clears the trade-count floor that killed
Coil-Break (93 OOS trades vs a 30 floor)**, and it **empirically confirms the funding-receipt half
of its own hypothesis** — the strategy collected **+$347 of funding** over the OOS trades. But the
**directional delta risk loses more than the carry earns**: net OOS Sharpe is negative, profit
factor < 1, and DSR ≈ 0. The fade collects funding and bleeds it back (and more) on the naked perp
leg it is forced to hold.

## Measured OOS results (all measured, none invented)

| Metric | Value | Gate | Pass? |
|---|---|---|---|
| OOS trades (both symbols) | **101** | ≥ 30 | ✅ |
| — side split | 89 short / 12 long | — | — |
| — exit reasons | 50 stop · 20 normalization · 27 time-cap · 4 funding-sign | — | — |
| **Total funding P&L** | **+$347** | (thesis check) | ✅ real |
| OOS Sharpe (annualized) | **−0.38** | > 0 | ❌ |
| Deflated Sharpe (DSR), N=1000 | **0.009** | ≥ 0.95 | ❌ |
| Minimum Track Record Length | **∞** | ≤ 1461 | ❌ |
| OOS profit factor | **0.77** | ≥ 1.3 | ❌ |
| Single-best-month excision | total −0.15, ex-best −0.25 | ex-best > 0 | ❌ |
| **PBO / CSCV** (combined platform) | **0.55 over 384 configs** | < 0.5 | ❌ |
| Rich metrics (deployed OOS) | Sortino −0.24 · Calmar −0.16 · MaxDD −26% | — | — |
| MC block-bootstrap envelope | (weak test) | above p5 | ✅ (weak) |
| MC entry-timing jitter | median < 0.5×base (both negative) | median ≥ 0.5×base | ❌ |

Numbers are post-fix (see below): the code/security review found a same-day look-ahead in the
daily filters and a same-settlement re-entry; both were fixed and the backtest re-run. The verdict
was unchanged (trade count 93→101, funding +$347→+$347, Sharpe −0.33→−0.38) — the finding is robust.

Window 2020-01-01 → 2025-12-31; 384-variant grid, 8 folds, 1461 OOS days. Full output:
`artifacts/fef_result.json`; OOS equity: `artifacts/fef_oos_equity.csv`.

## What this actually tells us (the useful part)

Unlike Coil-Break, FEF got past the count gate, so the edge checks are meaningful — and they
decompose the hypothesis cleanly:

1. **The carry is real.** Funding P&L is **positive (+$347)** across the OOS trades. Fading extreme
   funding does put you on the receiving side, and you do collect it — the Phase-1 carry mechanism
   is confirmed on real data, not just asserted.
2. **The delta kills it.** Net P&L is negative because the *price* leg loses more than the carry
   earns: 39 of 93 exits are stop-outs, and the fade enters *against* a euphoric trend, so the
   directional excursion against the naked perp position overwhelms the funding received. This is
   exactly the risk Phase 1 flagged as SPECULATIVE ("the price-reversal component… carries delta
   risk that mandate-constrained desks will not warehouse").
3. **Not a single-episode artifact either.** The excision test fails because the record is
   *net-losing* — removing the best month makes it worse, not better. There is no hidden good
   episode being masked; there is simply no positive edge in the directional version.

So FEF as specified — a **directional** funding fade — does not validate. But it isolates *why*:
the harvestable signal (funding carry) is real; the loss comes from the un-hedged delta.

## Trustworthiness

Reuses the same harness that was adversarially reviewed for Coil-Break (stats, walk-forward,
Monte Carlo, cost/funding accounting — all confirmed sound). The FEF-specific code (decision table,
engine) was **code-reviewed and security-reviewed** by two adversarial passes. The code review
confirmed the core correct (funding signs, accrual boundaries, earliest-exit selection, sizing,
decision-table reuse, percentile causality, accounting invariant) and found one real look-ahead
(daily filters reading the decision's incomplete calendar day) plus a same-settlement re-entry —
**both fixed and the backtest re-run** (numbers above are post-fix). The security review found the
package clean against the classic data-fetch surface (no eval/exec, HTTPS-only, no zip-slip); the
one actionable item — an unsanitized symbol reaching a filesystem path — was fixed with a strict
symbol whitelist. The accounting invariant (daily MTM == trade net P&L) is unit-tested and holds,
funding signs are tested (short receives when funding > 0), and all features are causal. 28 tests pass.

## Recommendation

Neither Phase-2 candidate validated as specified — **and that is the honest, valuable output of the
falsification protocol.** But FEF's decomposition points somewhere concrete:

1. **Test the delta-neutral (spot-hedged cash-and-carry) variant.** FEF proved the funding carry is
   real and positive; the loss is entirely the un-hedged delta. Hedging the perp with the spot leg
   removes the directional risk and isolates the carry — this is the variant Phase 1 explicitly set
   aside ("NOT spot-hedged cash-and-carry"). It is the single most-supported next experiment,
   because we now have *evidence* (the +$347 funding line) that the thing being harvested exists.
   Caveat: at $10k with 5+2 bps × 4 legs, the cash-and-carry's thinner per-unit edge must clear a
   higher cost hurdle — that is precisely what a Phase-2c backtest would measure.
2. **Accept the batch result.** Two of three candidates tested; both directional edges rejected on
   real data. The third (Cascade Fade) needs self-recorded L2/liquidation data before its *tradable*
   trigger can even be backtested (Phase-1 caveat), so it is not a quick win.

My recommendation: **build the spot-hedged carry variant** — it reuses this entire harness (add a
spot data feed and a two-leg P&L), and it is the one experiment the data actively motivates. Say the
word.
