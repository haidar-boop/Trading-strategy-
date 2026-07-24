# The Strategy — Delta-Neutral Crypto Funding Carry (+ an optional variance sleeve)

*Definitive, current, self-contained spec. Supersedes earlier drafts. Every number here is measured
on real Binance/Deribit data with honest (stressed) costs, or explicitly labeled. Nothing is
invented.*

---

## 0. The one-paragraph truth

This is a **delta-neutral funding-carry** strategy: short a perpetual future, buy the equal amount of
spot, and collect the funding that leveraged longs pay to shorts — with the price direction hedged
out. It is **real, cost-robust in sign, and not overfit** (PBO 0.001). It is also, under honest
execution costs, **not strong enough to clear the deflated-Sharpe bar** — it is an episodic,
regime-concentrated, decaying premium, not a steady alpha. I built an entire redesign to find
something better and **found no independent alpha that survives** — only one modest, un-leverable
variance-premium *insurance* sleeve. This document tells you exactly what to run, what it earns, and
where it breaks — without dressing any of it up.

---

## 1. Base strategy — delta-neutral cash-and-carry

### Mechanism (why the edge exists)
Perpetual futures use a **funding rate** to peg the perp to spot: when leveraged longs dominate
(the persistent state in crypto bull phases), funding is **positive** and longs pay shorts every 8h.
If you **short the perp** you receive that funding; if you simultaneously **buy the equal quantity of
spot**, your net price exposure is ~zero (delta-neutral), so you keep the funding minus the change in
basis (perp − spot) and minus transaction cost. The structural payer is the **behaviorally-sticky,
over-leveraged long crowd** (documented in Schmeling-Schrimpf-Todorov, *Crypto Carry*, BIS WP 1087) —
they overpay for leverage and keep doing it. It is not fully arbitraged because deploying size at the
funding extreme compresses the very funding you collect, and the premium is regime-concentrated and
decaying as basis-arb capital scales in.

### Exact rules
- **Universe:** liquid Binance USDT-M perps with a spot pair and 30-day median volume ≥ $1B. In
  practice: BTC, ETH, SOL, XRP, DOGE, BNB, ADA, LINK, AVAX, LTC (10 names).
- **Entry (per 8h funding settlement, per symbol):** open the carry (short perp + long spot, equal
  base qty) when the settled funding `f_now ≥ 1.5 bps/8h` **and** liquidity/event/mechanical filters
  pass. Positive-carry side only (short perp) — reverse carry needs spot borrow, out of scope.
- **Exit (earliest wins):** (a) funding decays to `≤ 0.5 bps/8h`; (b) basis stop — perp premium
  widens against you by ≥ 100 bps intrabar; (c) time cap — 14 days.
- **Sizing:** perp notional = 0.5 × equity (gross ≈ 1× equity, delta-neutral), gross-leverage cap 3×.
- **Only 4 free parameters** (entry 1.5, exit 0.5, basis-stop 100, notional-frac 0.5) — deliberately
  small to limit overfitting.

### Costs (this is where realism bites — #4 correction)
Four taker legs per round trip (short perp + buy spot in; buy perp + sell spot out), modeled
**asymmetrically** because **Binance spot taker (10 bps) is 2× the perp taker (5 bps)**, plus a
**legging-slippage** term (the two legs fill on separate matching engines 1–3 s apart):
- perp leg ≈ 5 + 0.5 bps; spot leg ≈ 10 + 1 bps (spot ADV ≈ perp/6.5); legging ≈ 2 bps per side.
- **Realistic round trip ≈ 37 bps; the pass/fail run uses 2× stress ≈ 59 bps.**
- Cost is now **~73% of gross funding** (was mis-stated at ~50% before the spot leg was corrected).

### Honest measured performance (10-symbol, 8-fold walk-forward, 2× stressed cost)
| metric | value | verdict |
|---|---|---|
| OOS trades | 35 | clears the ≥30 floor |
| OOS net P&L | **+$270** (funding +1,677 · basis +108 · **cost −1,515**) | positive but thin |
| OOS profit factor | 2.90 | ✅ |
| PBO / CSCV (overfitting) | **0.001** | ✅ not overfit |
| per-trade Sharpe | +0.35 | — |
| **Deflated Sharpe (daily)** | **0.00** | ❌ the blocker |
| **Per-trade DSR (effective-N)** | **0.001** | ❌ fails |
| MinTRL | ∞ (need more trades) | ❌ |

**Confidence intervals** (default config, BTC+ETH, 56 trades): net **+$771, 90% CI [+$229, +$1,362],
P(net>0) = 99.4%**; per-trade Sharpe 0.286, CI [0.118, 0.440]. → **The sign is robust; the magnitude
is not** (~6× CI).

**Generalization** (by year, all measured): 2021 +$1,662 · 2022 **$0 (flat)** · 2023 **−$64** · 2024
+$29 · 2025 **$0**. The edge is **regime-concentrated in bull/euphoria and decaying** — it earns in
bursts and sits flat (often a year+) otherwise.

### Verdict on the base strategy
**Real, not overfit, positive-in-sign — but does NOT clear the pre-registered deflated-Sharpe bar
under honest costs, and it is decaying.** Deploy only with eyes open: it is an episodic funding
harvester, not steady income.

---

## 2. Risk — the part the backtest hides

The backtest's −1.6% max drawdown is a benign-sample artifact. Analytical tail-stress of the naive
implementation:

| scenario | P&L % equity |
|---|---|
| Funding flips −3 bps/8h for 72h | −0.14% |
| Basis blowout +8%, **gaps through the stop** | −4.07% |
| Perp liquidation, **isolated margin** | **−17%** |
| **Full deleveraging cascade (isolated margin)** | **−23%** |
| Perp liquidation, **cross / portfolio margin** | −0.07% |

**The single most important control: use CROSS / portfolio margin** — the spot collateral supports
the perp short and the hedge stays intact (turns −17% into −0.07%). Second: a **gap-aware basis stop**
and small `notional_frac` so a gapped blowout is survivable. Capacity: fine at retail ($10k–$1M);
execution-impact ceiling ~$500M/trade, but the real limit is the **number** of (decaying)
opportunities, not size.

---

## 3. Optional sleeve — ATM variance-risk premium (insurance, not alpha)

The one idea from a 7-candidate redesign that survived both economic screening and empirical
falsification. Sell 30-day ATM implied vol (Deribit), delta-hedged; harvest the gap between implied
and subsequent realized vol (IV−RV). It is a **different risk factor** than carry (second-moment vs
leverage-demand) and is **empirically uncorrelated** with the carry (Spearman ~0), including in the
carry's bad months.

**But — after correcting my own initial over-scoring** (I had inflated it via an overlapping-window
smoother and linear accounting; an adversarial review caught it):
- BTC: gross ~8 vol pts/month, positive every year — but tradeable, variance-space **Sharpe ~1.0,
  DSR 0.88–0.92 (fails the 0.95 bar)**.
- **The tail is savage:** a real COVID-scale vol month is **≈ −298 vol points** in variance space —
  a single such month exceeds the entire multi-year accumulated premium and turns the Sharpe negative.
- ETH: not viable (Sharpe ~0).

**Verdict: real, structural, carry-independent — but a *compensated crash-risk premium*, i.e.
positive-EV short-convexity insurance, NOT leverable alpha.** If used at all: **small, hard-stopped,
un-levered**, sized as insurance, never against its in-sample Sharpe. Pre-capital checks still owed:
a true delta-hedged path simulation (hedge-error variance) and a stressed-tape spread sample.

---

## 4. What was rejected, and why (so you don't chase it)

All rejected on **economics**, not backtest:
- **Funding point-prediction** — funding is near-random-walk; a feature model does not beat the naive
  "enter when funding is high" threshold at the entry decision (measured).
- **Funding-flip / stablecoin de-risk overlays** — the flip/stress they target is a rare tail the
  sample barely contains, and the carry's funding threshold already keeps it flat during those events
  (both falsified empirically).
- **Calendar basis, cross-exchange funding dispersion, liquidation-cascade fade, OI crowding fade** —
  all are either the *same leverage-demand factor re-expressed*, or competed-to-zero / negative-EV for
  a retail bot on free data. (Cross-sectional funding was actually built and measured: gross +$962 vs
  turnover −$11,571 — a clear loss.)

**The deep reason:** nearly every durable crypto edge is a slice of the same over-leveraged-long
short-skew imbalance, so they co-crash and don't diversify each other. **Beta-neutral crypto alpha
that is genuinely independent of the carry factor is structurally hard.**

---

## 5. If you deploy — the honest checklist
1. **Cross / portfolio margin, always.** This is the difference between a −0.07% and a −17% tail.
2. Size so a **gapped basis blowout (+8%)** is survivable; hard basis stop; small notional fraction.
3. Expect **long flat stretches** (a year+). This is episodic, not income. Don't lower thresholds to
   force trades — the sub-1.5 bps cells are net-negative after honest cost (measured).
4. Treat any VRP sleeve as **insurance sized small**, not a return engine.
5. Re-measure funding compression periodically — the premium is decaying; the strategy could go to
   permanent-flat as basis-arb capital scales.
6. **Paper-trade first** to validate real fills vs the modeled 37–59 bps round-trip cost — the whole
   edge lives or dies on execution cost, and my cost model, while honest, is not your fill log.

---

*Code: `phase2/coilbt/` (carry engine `backtest_carry.py`, `strategy_carry.py`, `config_carry.py`;
costs `costs.py` + `quantlib/impact_costs.py`; validation `run_carry.py`, `robustness_carry.py`;
tail `tailstress.py`; VRP `vrp_test.py`/`vrp_book.py`). Full write-ups: `RESULTS_CARRY.md`,
`RESULTS_IMPROVEMENTS.md`, `RESULTS_EXECUTION.md`, `STRATEGY_REDESIGN.md`. 70 tests pass.*
