# Review-Driven Improvements — findings log

Working through the 20-point review. Buildable-now items first (by impact × feasibility);
data-gated items (#1 order-book, #7 cross-exchange, #15 options/L2/on-chain) flagged separately.

---

## #19 Generalization + #18 Economic decomposition — DONE (and it's the most revealing test yet)

Default config, 2× stressed cost, all measured.

**By calendar year (all 10 symbols):**

| Year | trades | funding | basis | cost | NET | Sharpe |
|---|---|---|---|---|---|---|
| 2021 (bull) | 64 | +4,509 | −47 | −1,926 | **+2,536** | 7.22 |
| **2022 (bear/LUNA/FTX)** | **0** | — | — | — | **0** | — |
| 2023 (recovery) | 13 | +462 | +41 | −396 | +107 | 1.92 |
| 2024 (ETF) | 36 | +1,544 | +43 | −1,082 | +504 | 4.01 |
| **2025 (compression)** | **0** | — | — | — | **0** | — |

**By symbol subset (full period):**

| Subset | trades | funding | basis | cost | NET | Sharpe |
|---|---|---|---|---|---|---|
| BTC only | 27 | +1,482 | **0** | −778 | +704 | 4.19 |
| ETH only | 29 | +1,728 | −97 | −858 | +773 | 3.64 |
| BTC+ETH | 56 | +3,210 | −96 | −1,636 | +1,478 | 4.20 |
| all 10 | 113 | +6,515 | +37 | −3,404 | **+3,147** | 5.58 |

### What this exposes (honest)

1. **The edge is regime-dependent and appears to be DECAYING.** Every dollar was earned in
   high-funding bull/recovery regimes (2021 ≫ 2024 > 2023). In **2022 (the bear) it made zero
   trades**, and in **2025 it also made zero** — funding never cleared the 1.5 bps entry bar. This
   is the funding-compression decay Phase 1 predicted (ETF/basis-arb capital scaling), now visible:
   the biggest year (2021) is largely the in-sample warmup, and the most recent year (2025) is a
   blank. The strategy does not *lose* in bad regimes — it correctly goes flat — but it only *earns*
   in euphoric ones, and that opportunity is shrinking.
2. **It DOES generalize across instruments.** BTC-only (+$704, Sharpe 4.2) and ETH-only (+$773,
   Sharpe 3.6) are both solidly positive on their own — it is not an artifact of one weird alt.
3. **Economic decomposition is clean: funding is ~100% of the edge, basis ≈ 0, cost ≈ 50% drag.**
   Gross funding +$6,515; basis +$37 (the delta hedge works essentially perfectly — the directional
   move is neutralized); cost −$3,404 (roughly half the funding). So this is a pure funding-harvest
   whose main enemy is transaction cost, exactly as designed — no hidden directional bet.

### The sober takeaway

The aggregate "+$732 net, Sharpe 1.89" understates how *concentrated in time* the edge is. It is a
**bull-market funding harvester**: strong when leverage demand is high (2021, 2024), dormant
otherwise, and the most recent full year produced nothing. Any deployment plan must assume it earns
in bursts and sits flat — often for a year or more — and that the funding-extreme opportunity is
structurally compressing. This is not a steady-income strategy; it is episodic and decaying.

---

## #6 Tail-stress scenario engine + #5 exchange/liquidation — DONE (the biggest missing test)

Analytical stress of a representative position (equity $10k, perp $5k, gross $10k). P&L as % of equity:

| Scenario | P&L % equity |
|---|---|
| Funding flips −3bps/8h for 72h | −0.14% |
| Basis blowout +8%, stop executes cleanly (1%) | −0.57% |
| **Basis blowout +8%, GAPS through the stop** | **−4.07%** |
| Spot illiquid on exit (−3%) | −1.50% |
| Exchange halt 3 days (adverse funding + basis) | −1.09% |
| Perp liquidation, **CROSS** margin | **−0.07%** |
| Perp liquidation, **ISOLATED 3× margin** | **−17.17%** |
| **FULL CASCADE (all stacked, isolated margin)** | **−22.92%** |

**Findings:**
- The backtest's −0.9% max drawdown is fantasy: the in-sample period saw **none** of these. A real
  deleveraging cascade on the naive (isolated-margin) implementation can lose **~23% of equity**.
- **The single most important risk control: CROSS / portfolio margin.** It collapses the perp-
  liquidation loss from −17% to −0.07%, because the spot collateral supports the perp short and the
  hedge stays intact. Isolated margin breaks the hedge and is the dominant tail.
- The second: a **gap-aware basis stop** — a stop at 1% does not save you if the basis gaps to 8%
  (−4%); size `notional_frac` so a gapped blowout is survivable.

## #9 Capacity — DONE

Execution-impact crossover (funding ~115 bps/trade gross, BTC ADV ~$20B, 2× stressed base cost):

| Notional/trade | net bps | | Notional/trade | net bps |
|---|---|---|---|---|
| $10k | +86.6 | | $50M | +57.0 |
| $1M | +82.8 | | $100M | +44.6 |
| $10M | +73.6 | | $500M | **−7.9** |

- At **retail size ($10k–$1M) execution impact is negligible** (~85 bps/trade net).
- Execution-impact ceiling ~$500M/trade — but the honest limit is **lower**: deploying size at the
  funding extreme *compresses the funding you're collecting* (you become the arb). At retail the
  binding constraint is the **number** of (decaying) opportunities, not capacity.
