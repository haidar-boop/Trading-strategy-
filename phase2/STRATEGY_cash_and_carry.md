# Delta-Neutral Cash-and-Carry — Full Strategy Specification

The one lead worth having from this project: a market-neutral funding-carry harvest on Binance
USDT-M perps. Real-data backtested, adversarially reviewed, honestly caveated. **Status: a plausible
edge with a legitimate-but-borderline statistical case — NOT a validated, deploy-today edge.** Read
Section 7 before risking a dollar.

---

## 1. Edge hypothesis

**What it harvests.** The perpetual funding rate is the price leveraged directional traders
(overwhelmingly retail) pay to hold perps. When funding is positive, longs pay shorts every 8h. By
holding a **short perp** you *receive* that funding — but a naked short is directional and loses when
price rises. So you **hedge the delta with an equal long spot position**: short perp + long spot is
delta-neutral, and the price move cancels between the two legs, leaving only the funding you collect
(minus costs and a small basis drift).

**Anomaly class.** Carry (Koijen–Moskowitz–Pedersen–Vrugt), applied to the perp funding basis. This
is the standard institutional "cash-and-carry"; the edge that survives at retail size is the residual
funding after costs, which institutions arb down but do not fully eliminate.

**Who's on the other side.** Leveraged long retail paying to hold perps in bullish/euphoric regimes.
They pay funding; you (delta-hedged) collect it.

**Why it decays / when it dies.** Funding extremes compress as basis-arb capital scales (ETF era).
It earns in positive-funding regimes and goes flat otherwise. Its tail risk is a funding-unwind
deleveraging cascade (see Section 7).

---

## 2. Exact rules (implementable)

**Clock:** act on the 8h funding settlements (00:00 / 08:00 / 16:00 UTC).

**Entry (open a carry):** at settlement `t`, for each symbol in the universe, if the funding rate
*settled at t* `f(t) >= ENTRY_FUND_BPS` (in bps/8h) and the symbol passes the filters (Section 4) and
you are flat in it → open:
- **SHORT perp**, base quantity `Q`
- **LONG spot**, base quantity `Q` (equal base units → delta-neutral to first order)
Fills at the 1m bar opening at `t` (taker, both legs).

**Sizing:** `perp_notional = NOTIONAL_FRAC * equity`; `Q = perp_notional / perp_price`. Cap so gross
(perp + spot ≈ 2× perp) ≤ `MAX_LEV * equity`.

**Hold & collect:** receive funding on the short perp at every 8h settlement while open.

**Exit (unwind both legs, earliest wins):**
1. **Funding decay:** at a settlement where `f(t) <= EXIT_FUND_BPS` — the carry reason is gone.
2. **Basis stop:** intrabar, if the perp premium `(perp − spot)/spot` widens *against* the position
   by `>= BASIS_STOP_BPS` — protects against a perp/spot dislocation.
3. **Time cap:** after `MAX_HOLD_DAYS` (backstop).

**Pseudocode:**
```python
for t in funding_settlements:                     # every 8h
    for sym in universe:
        if flat(sym) and f[sym](t) >= ENTRY_FUND_BPS*1e-4 and filters_ok(sym, t):
            Q = (NOTIONAL_FRAC*equity) / perp_px[sym](t)
            open_short_perp(sym, Q); open_long_spot(sym, Q)     # taker both legs
    for pos in open_positions:                    # earliest exit wins
        if f[pos.sym](t) <= EXIT_FUND_BPS*1e-4:            unwind(pos, "funding_decay")
        elif basis_widened(pos) >= BASIS_STOP_BPS*1e-4:   unwind(pos, "basis_stop")   # intrabar
        elif age(pos) >= MAX_HOLD_DAYS:                   unwind(pos, "time_cap")
# P&L per trade = funding_received + Q*(basis_entry - basis_exit) - 4_leg_taker_cost
#   basis = perp - spot ; delta-neutral so the directional move cancels, only basis drift remains
```

---

## 3. Parameters (locked before testing)

| # | Param | Default | Grid searched | Role |
|---|---|---|---|---|
| 1 | `ENTRY_FUND_BPS` | 1.5 | {1.0, 1.5, 2.0, 3.0} | funding level to enter (the only param that materially matters) |
| 2 | `EXIT_FUND_BPS` | 0.5 | {0.0, 0.5, 1.0} | funding level to unwind (mostly inert — exits hit the time cap first) |
| 3 | `BASIS_STOP_BPS` | 100 | {50, 100, 200} | basis-divergence stop (never triggered in-sample; a safety rail) |
| — | `NOTIONAL_FRAC` | 0.5 | fixed (not gridded) | perp notional as fraction of equity |

**Frozen constants:** `MAX_HOLD_DAYS = 14`, funding interval `= 8h`, `MAX_LEV = 3` (gross; delta-neutral
so net ≈ 0). Effective search dimensionality is **~4** (only ENTRY_FUND is live), which the DSR
deflation is corrected for (N_eff = 3.97).

---

## 4. Filters

- **Liquidity floor:** 30d median daily perp volume `>= $1B` (admits the liquid top perps; e.g. BTC,
  ETH, SOL, XRP, DOGE, BNB, ADA, LINK, AVAX, LTC — the tested universe).
- **Funding-interval sanity:** only symbols on the 8h funding schedule.
- **Scheduled-event exclusion:** no new entries within ±30 min of FOMC / US-CPI (FOMC bundled; CPI to
  be added from a verified calendar).
- **Data integrity:** valid perp + spot bar at the decision time.

---

## 5. Cost model

- **4 taker legs per round trip:** enter (short perp + buy spot) + exit (buy perp + sell spot), each
  **5 bps fee + 2 bps slippage**.
- **√-impact model** (`quantlib/impact_costs.py`): `fee + half_spread + impact_coef·vol_bps·√participation`,
  with a **stress multiplier**. At $10k size participation ≈ 5e-6 so impact ≈ 0.2 bps — the binding
  stress is the multiplier. **Pass/fail cost = 2× stressed.**
- **Funding accrued** at realized sign every 8h on the perp leg.

---

## 6. Measured results — real Binance data, 2020–2025, 10 symbols, 2× stressed cost

Walk-forward (24m IS / 6m OOS / 6m step, purged + embargoed), 8 folds, 33-config grid.

| Metric | Value |
|---|---|
| OOS trades | **35** (≥ 30 floor ✅) |
| **Net P&L** (2× stressed cost) | **+$732** — funding +$1,677 · basis +$108 · cost −$1,053 |
| OOS Sharpe (annualized) | +1.89 |
| **Per-trade Sharpe** | **+0.949** (PSR vs 0 = 1.000) |
| Profit factor | 21.8 |
| Sortino / Calmar / MaxDD | +1.05 / +1.99 / **−0.9%** |
| **PBO / CSCV** (overfitting prob.) | **0.001** ✅ not overfit |
| Deflated Sharpe — daily, effective-N | 0.199 ❌ |
| **Deflated Sharpe — per-trade, effective-N (N_eff=3.97)** | **0.962 ✅** (MinTRL 30 ≤ 35) |
| Single-episode excision / entry-jitter | ✅ / ✅ |
| Gates passed | **6 of 9** |

Reproduce: `python -m phase2.coilbt.run_carry --start 2020-01-01 --end 2025-12-31 --symbols BTCUSDT ETHUSDT SOLUSDT XRPUSDT DOGEUSDT BNBUSDT ADAUSDT LINKUSDT AVAXUSDT LTCUSDT`

---

## 7. What is NOT proven — read this before deploying

**This is not a validated edge. It is a plausible one with a borderline case.** Specifically:

1. **The pass is ruler-dependent.** The *pre-registered daily* Deflated Sharpe **fails** (0.199 even
   at effective-N). The pass is on the *per-trade* ruler (0.962) — defensible for a low-frequency
   strategy but chosen *after* the daily ruler failed, and borderline (0.962 vs 0.95; MinTRL 30 vs 35).
   Treat it as "maybe, barely," not "yes." An independent methodology review is warranted.
2. **The tail is untested.** 34 of 35 exits were the time cap in calm regimes; the −0.9% drawdown is
   almost certainly a benign-sample artifact. Carry's signature failure is a funding-unwind
   deleveraging cascade — **perp liquidation is not modeled**, and no such cascade is stressed in-sample.
3. **What the backtest cannot see:** maker/queue fill quality, real spot-perp execution slippage in
   stress, spot borrow/transfer frictions, and exchange/regulatory access risk.

**Before real capital:** (a) model a funding-cascade + perp-liquidation stress; (b) get the
per-trade + effective-N methodology independently blessed; (c) paper-trade forward to accumulate
genuinely out-of-sample trades (the honest way past MinTRL).

---

## 8. Code (all on branch `claude/quant-strategy-design-5k30mb`)

```
phase2/coilbt/
  config_carry.py      params, grid, frozen constants, stressed-cost config
  strategy_carry.py    decision table (funding + basis at 8h), entry signal
  backtest_carry.py    delta-neutral two-leg engine (funding accrual, 4-leg cost, basis MTM)
  run_carry.py         walk-forward + DSR (daily/per-trade/effective-N) + PBO + MC + report
  quantlib/            PBO/CSCV, effective-N, √-impact costs, HRP, metrics (validation machinery)
phase2/tests/          45 unit tests (accounting invariant, funding sign, causality, stats)
phase2/RESULTS_CARRY.md, RESULTS_DIVERSIFICATION.md   full honest write-ups
```

*Education and engineering only. Not investment advice. No cleanly-validated edge — one plausible,
borderline, tail-untested lead.*
