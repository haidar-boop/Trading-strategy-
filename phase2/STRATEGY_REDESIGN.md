# Edge Redesign — Hypothesis Portfolio (design first, no implementation yet)

Mandate: stop optimizing the funding-carry backtest; increase the **economic edge**. Design new
hypotheses, justify *why they should exist* and *why they are not fully arbitraged away*, and reject
anything that only improves a backtest. This document is the design deliverable — nothing here is
implemented yet. Seven candidate sleeves were each given a deep economic-rationale pass and an
adversarial "it's already arbitraged away" rebuttal; the synthesis below ranks the survivors and
rejects the rest **on economics, not backtest**.

## The one structural fact that drives every verdict

**Nearly every durable crypto "edge" traces to the same root:** a behaviorally-sticky,
price-insensitive, over-leveraged long crowd that pays to be levered and gets *mechanically*
liquidated. Funding carry, calendar basis, cross-venue dispersion, cascade fades, crowding fades,
and even the fat tail of the options variance premium are all different *slices of that one
imbalance* — and they all **short the same negative skew**, so they **co-crash together**. This is
why "just add more sleeves" mostly *concentrates* the left tail instead of diversifying it. Genuine
diversification requires (a) an edge with an *orthogonal factor*, and (b) explicit hedges for the
tail that edge still shares with carry.

## Verdicts

### ✅ Survive (1 candidate independent alpha + 2 risk overlays)

| Rank | Sleeve | Independent factor? | After-cost edge | Role | Honest prior |
|---|---|---|---|---|---|
| 1 | **ATM variance-risk premium** (Deribit, delta-hedged, ATM/near-ATM only — **wings excluded**) | **Yes — genuinely.** Second-moment (variance/jump) premium vs carry's first-moment (leverage-demand) premium. Different Greek, different DGP (IV−RV vs perp-spot basis). The *only* candidate whose edge source is not the leverage-demand root. | Thin, cost-hostile. DOV/structured-product sellers have compressed ATM VRP; Deribit vol-point spreads + continuous delta-hedge bleed eat most of gross. Survives only as a small, disciplined book. | **Candidate independent alpha** (pilot-gated satellite) | ~0.30 |
| 2 | **Stablecoin de-risk gate** (USDT/USDC premium + mint/burn flows) | Strong independence *logic* (dollar-liquidity factor), but converges with carry in the depeg tail. | Near-zero as standalone (endogenous, slow, thin gross eaten by taker cost). | **Overlay only** — de-risk gate on carry; value is *avoided drawdown*, not alpha. | overlay |
| 3 | **Funding-flip hazard overlay** (regime *duration/survival*, not level) | **Negatively** correlated with carry *in the left tail* — a genuine tail-hedge cousin, though same factor family. | N/A as alpha (it's negative-carry insurance); cheap as a low-turnover de-risk trigger. | **Overlay only** — carry tail hedge. | overlay |

Key point on the redesign's diversification: **VRP decorrelates the *body* of the distribution; the
two overlays decorrelate the shared *crash*.** Neither overlay gets standalone capital — they
modulate the carry book's on/off state and are validated only by drawdown reduction.

### ❌ Rejected (on economics)

- **Calendar basis (quarterly futures) — not an independent factor.** The dated basis and perp
  funding are two pricings of *one* latent object: the term structure of crypto leverage demand.
  Near-cointegrated by no-arbitrage, same behavioral payer, widen in the same euphoric regimes. A
  lower-frequency *re-expression* of carry (and more competed by ETF/CME basis desks post-Jan-2024),
  not a diversifier. If run at all it should *replace* part of carry, not add to it.
- **Cross-exchange funding dispersion — competed to zero where capturable; uncapturable where not.**
  Steady-state major-venue dispersion is one of the most crowded arbs in crypto, and it is this
  repo's own already-dead cross-sectional cousin (measured gross +$962 vs turnover ~$11.5k) with
  *strictly worse* economics (4 order-book crossings on 2 venues' thinner books). The only uncompeted
  residual (captive-geography rent) forces full unnettable collateral on both venues and the exact
  withdrawal-latency/ADL friction that makes convergence unrealizable in stress — paid a premium for
  a risk you cannot warehouse.
- **Liquidation-cascade fade — fully competed at the only latency a retail bot can occupy.** The
  overshoot is faded by colocated HFT in the microseconds *before* Binance's throttled (~1/sym/sec),
  delayed public `forceOrder` stream even reports it. As a taker you're the HFTs' exit liquidity; as
  a maker you're adversely selected — filled preferentially on the cascades that *don't* revert
  (LUNA/FTX/2020-03-12). The residual is negatively-skewed and adversely-selected — a loss.
- **OI crowding fade (standalone directional) — direction is commoditized; the scarce part isn't
  independent.** "Fade extreme funding + rising OI + liquidations" is the explicit thesis of every
  liquidation-hunter bot and free Coinglass heatmap. The only scarce piece (ex-ante exhaustion
  *timing*) is fragile negative-skew crash insurance carried by a handful of 2021-style cascades, and
  it co-moves *with* carry on the blow-off-then-crash — doubling the exact tail it claims to hedge.

(`funding_persistence` and `stablecoin_flow` are rejected *as standalone alpha* for the same
reasons, but retained as overlays above.)

## Recommended structure — 1 base + 1 satellite + 2 shared overlays

1. **Carry (base, existing).** Kept as the most-validated book and the benchmark the redesign must
   beat — even though it fails DSR standalone. The overlays exist to fix its fatal tail.
2. **ATM VRP (satellite, new, pilot-gated).** The one orthogonal factor; diversifies carry in the
   *body*. Sized to its *capacity ceiling*, not its point-estimate Sharpe (~20–30% of risk budget,
   only if it clears its pilot).
3. **Stablecoin gate + funding-flip hazard (overlays, 0% standalone capital).** Neutralize the
   negative-skew crash that carry and VRP *share*.

Rough risk split: carry ~70–80%, VRP ~20–30% iff it passes its pilot, overlays 0% (risk-reducers).
Capacity-and-independence-tilted, **not** return-weighted.

## Build order — each gated on a pre-registered falsification test (cheapest-strongest first)

**1. Stablecoin de-risk overlay** (cheapest: free data, ~zero turnover).
   *Falsify:* does gating carry OFF on a stablecoin-stress z-score reduce OOS MaxDD / left-tail CVaR
   on the LUNA/FTX/SVB episodes **without** materially cutting net return? If no drawdown reduction →
   drop it (signal is coincident, not leading).

**2. Funding-flip hazard overlay** (cheap: BTC+ETH data in hand).
   *Falsify:* does a state-conditioned hazard model (OI z-score, OI accel, realized vol, funding
   slope) beat the **naive empirical survival curve / fixed time-cap** OOS on BTC+ETH? The strong
   adjacent null: it does *not* (the level-forecast already showed ~0 incremental OOS R² from these
   same crowdedness features). If it can't beat naive → nothing to build; holding-to-median is
   optimal.

**3. ATM VRP sleeve** (hardest, but the only independent alpha).
   *Falsify (both must pass):* (a) does a delta-hedged **ATM/near-ATM** DVOL−RV carry clear
   net-of-cost using free DVOL+RV under an *honest stressed* assumption (cross the full quoted
   vol-point spread twice per roll + continuous hedge bleed)? **and** (b) does its return show
   **Spearman < 0.5 vs carry in the body** (excluding shared crash days)? Guardrail: if it only works
   with the **wings** included, reject — the wing premium is tail-correlated carry in a variance
   costume, and its costs are unmodelable on free history anyway.

## The honest bottom line (do not oversell)

The redesign plausibly produces a **modestly** stronger *after-cost, tail-aware* book than the single
carry sleeve — **but mainly by fixing carry's tail, not by stacking new alpha.** Seven candidates in:
four are hard economic rejects (same leverage-demand factor re-expressed, or negative-EV/uncapturable
for a retail bot on free data); two survive only as overlays (drawdown reducers, no new return
stream); exactly **one** has a genuinely orthogonal factor (ATM VRP) and even it is compromised — the
fat, easily-harvested part (the wings) is both tail-correlated with carry *and* unmodelable on free
data, so the independent-and-feasible construction is a thin, capacity-capped, cost-hostile ATM book
that a retail taker may not clear. Its prior is ~0.30 — more likely to fail than not.

**Beta-neutral crypto alpha genuinely independent of funding carry is structurally hard**, because
the durable edges nearly all short the same crowd's negative skew. The legitimate deliverable is:
run three cheap, pre-registered falsification tests in order; expect the two overlays to earn their
keep as drawdown reducers; treat ATM VRP as the single real shot at an independent return stream,
funded small and only if its pilot passes with independence coming from the *body*, not the wings.
Deploy nothing on the strength of a backtest — deploy on the strength of the pre-registered tests
surviving.
