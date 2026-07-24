# Review-Driven Improvements — findings log

## Scorecard — all 20 review points

| # | Item | Status |
|---|---|---|
| 18 | Economic decomposition | ✅ done — funding ~100% of edge, basis ≈0, cost ~50% drag |
| 19 | Generalization (per-year, per-symbol) | ✅ done — **key finding: regime-dependent & decaying** (0 trades 2022 & 2025) |
| 6 | Tail-stress scenarios | ✅ done — full cascade −23%; cross-margin is the critical control |
| 5 | Exchange/liquidation model | ✅ done (within #6) — isolated-margin liquidation is the dominant tail |
| 9 | Capacity analysis | ✅ done — retail fine; ~$500M impact ceiling; opportunity-count is the real limit |
| 14 | Adversarial data sims | ✅ done — accounting invariant holds under corrupt/missing/delayed/NaN data |
| 16 | Literature review | ✅ done — `LITERATURE.md`, real cites (incl. Crypto-Carry paper confirming #19 decay) |
| 1,7,15 | Data-gated (L2, cross-exchange, options/on-chain) | ✅ roadmap done — `DATA_ROADMAP.md` (do: CVD free, cross-venue funding free, Deribit skew) |
| 3,10,20 | Funding **prediction**/persistence + "why is funding high" | ✅ done — **measured negative for point-forecast; only the squeeze RISK gate survives** |
| 2 | Regime classifier | ⏳ pending (HMM already ported) |
| 13 | Better exit logic (forecast/OI/vol) | ⏳ pending (depends on #3) |
| 4 | Spot-leg execution realism | ⏳ pending |
| 8,11 | Dynamic sizing / portfolio optimization | ⏳ pending |
| 17 | Confidence intervals / param stability | ⏳ pending (quick) |
| 12 | Stablecoin / depeg risk | ⏳ pending (discussion + scenario) |

Done this pass: **8 of the substantive items + the data roadmap**, all committed with real measured
results. The headline conceptual upgrade **#3/#10/#20 (predict funding instead of react)** is now
built and **measured — and the answer is honest and mostly negative**: point-forecasting funding
does not beat the naive threshold at the entry decision, and the exogenous "why is funding high"
features are symbol-unstable (overfitting). The only piece that survives is the **squeeze-rejection
RISK gate**, kept as measured tail insurance (near-zero in-sample cost), not as a return edge.



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

## #3 / #10 / #20 Funding prediction + "why is funding high" — DONE (measured, and mostly negative)

This was billed as "the headline conceptual upgrade": stop *reacting* to high funding and start
*predicting* it. I built the leak-free study myself (`funding_predict.py`) rather than delegate,
because leakage is the #1 way to manufacture a fake predictive edge. The verdict is honest and
mostly negative — the naive threshold the strategy already uses is close to optimal.

### The prior question first: is funding forecastable *beyond its own autocorrelation?*

Funding is near-random-walk persistent (literature: AR(1) ≈ 0.97–0.998; confirmed here — a pure
persistence baseline "next-K funding == funding now" already scores **OOS R² ≈ 0.46–0.47** on
BTC/ETH). So the ONLY forecast that matters is one that beats persistence. Walk-forward, leak-free
(in-fold standardization, embargo, target strictly forward), 5,000+ / 4,000+ OOS test points:

| symbol | R² persist | R² ridge (all feats) | **incremental R²** |
|---|---|---|---|
| BTCUSDT | 0.471 | 0.569 | **+0.098** |
| ETHUSDT | 0.458 | 0.557 | **+0.100** |

A feature model adds ~+0.10 R² on the *point forecast*. But two tests strip that of its shine:

**Ablation — does the EXOGENOUS "why is funding high" story (OI/vol) add anything?**

| symbol | persist | funding-only | oi+vol-only | all | **exog gain (all − funding)** |
|---|---|---|---|---|---|
| BTCUSDT | 0.471 | **0.603** | −1.899 | 0.569 | **−0.035** |
| ETHUSDT | 0.458 | 0.457 | −0.189 | 0.557 | **+0.100** |

The exogenous features are **inconsistent and not robust**: on BTC, funding-autocorrelation *alone*
(R²=0.603) **beats** the full model — adding OI/vol *hurts*. On ETH they help (+0.10). Standalone,
OI/vol are pure noise (negative R² on both). Helping one symbol, hurting the other, useless alone —
that is the overfitting signature the literature warned of, not a real driver. The honest read:
whatever point-forecast power exists is **better use of the funding autocorrelation**, which the
naive threshold already exploits.

**Decision-level test — does a forecast gate collect more realized funding at the entry threshold?**

| symbol | gate | select % | realized fwd funding (bps) | hit % |
|---|---|---|---|---|
| BTC | current (naive) | 6.8% | **2.88** | 100% |
| BTC | forecast (ridge) | 7.9% | 2.50 | 96.7% |
| ETH | current (naive) | 6.3% | **2.86** | 100% |
| ETH | forecast (ridge) | 5.5% | 2.93 | 100% |

At the actual carry entry threshold the forecast gate does **not** beat the naive current-funding
gate (BTC slightly worse, ETH a tie). The +0.10 R² lives in the *middle* of the funding
distribution, not at the *high tail* where carry enters — exactly where it would need to help.

**Conclusion for #3/#10:** do NOT build a funding return-predictor. It does not beat the threshold
out-of-sample on the decision that matters, and its apparent point-forecast edge is symbol-unstable.
This is the measured, negative answer — and it's more valuable than a shiny model that overfits.

### #20 "Why is funding high" — collapsed to one actionable RISK gate

Research (2 streams) + my measurement converge: the 7-way causal taxonomy (ETF demand / retail FOMO
/ short squeeze / MM hedging / illiquidity / listing / cross-venue) is a **strong overfitting
magnet** on noisy free OI. The one economically-grounded, leak-safe signal is the **squeeze
tell**: elevated funding + **price rising while OI falls** = short covering, a funding spike about
to invert. Implemented as an optional entry gate (`USE_OI_GATE`, default off) and **measured on the
real carry** (`squeeze_gate.py`), 2× stressed cost:

| symbol | gate | trades | rejected | net | Sharpe |
|---|---|---|---|---|---|
| BTC | OFF | 27 | — | +704 | 4.19 |
| BTC | **ON** | 25 | 2 | +672 | **4.33** |
| ETH | OFF | 29 | — | +773 | 3.64 |
| ETH | **ON** | 28 | 1 | +741 | 3.63 |

Nearly neutral in-sample: it removes ~4% of net, nudges BTC Sharpe up (4.19→4.33), leaves ETH flat.
501/357 decisions were squeeze-flagged in the feed but only 2/1 coincided with a high-funding entry
— the squeeze→flip event **rarely overlaps an entry in the calm sample**. So, exactly like the
tail-stress finding: this is **cheap insurance against a tail the backtest underweights**, justified
by mechanism, not by an in-sample edge. It is NOT presented as a Sharpe improvement — it is a risk
filter with a measured (near-zero) in-sample cost.

Leakage is pinned by `test_funding_predict.py`: a walk-forward fed **pure-noise features** must
score OOS R² ≈ 0 — if the pipeline peeked at the future it couldn't. It scores < 0.05. ✅

---

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
