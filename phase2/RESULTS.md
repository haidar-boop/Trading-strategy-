# Phase 2 — Coil-Break Backtest Results

**Verdict: INSUFFICIENT EVIDENCE — do not deploy.** On real Binance USDT-M data (BTCUSDT +
ETHUSDT, 2020-01 → 2025-12), the Coil-Break strategy, run exactly as specified in Phase 1
through a purged walk-forward, produces **46 out-of-sample trades — below its own pre-registered
60-trade floor.** Below that floor no statistical claim is made. And even setting the floor aside,
the point estimates show **no edge**: the OOS record is unprofitable.

This is not a failure of the implementation — it is the implementation doing its job. Phase 1
explicitly named low trade count as Coil-Break's binding risk ("OOS trade count will be
structurally low… the MinTRL/60-trade floor will likely bind here first"). It bound. The honest
answer the protocol was built to deliver is "the sample cannot support deployment," and that is
the answer.

## Measured OOS results (all numbers are measured, none invented)

| Metric | Value | Gate | Pass? |
|---|---|---|---|
| OOS trades (pooled, both symbols) | **46** | ≥ 60 | ❌ |
| OOS Sharpe (annualized) | **−0.48** | > 0 | ❌ |
| Probabilistic Sharpe PSR(0) | 0.17 | — | — |
| Deflated Sharpe (DSR), N=1000 | **0.0005** | ≥ 0.95 | ❌ |
| — deflation benchmark SR\* | 0.0615 /√bar | — | — |
| Minimum Track Record Length | **∞** | ≤ 1461 OOS days | ❌ |
| OOS profit factor | **0.79** | ≥ 1.3 | ❌ |
| MC block-bootstrap envelope | real 0.985 vs p5 0.958 | stay above p5 | ✅ (weak, see below) |
| MC entry-timing jitter (median vs base) | −31.9 vs −44.3 | median ≥ 0.5×base | ❌ |
| Corr to BTC buy-and-hold | 0.24 | (beta check) | — |

Window: 2020-01-01 → 2025-12-31. 320-variant grid, 8 walk-forward folds, 1461 OOS days.
Full machine-readable output: `artifacts/phase2_result.json`; OOS equity: `artifacts/phase2_oos_equity.csv`.

## Why it fails

1. **Structurally too few trades.** The compression gate admits only ~Q_COMP% of days, breakouts
   fire on a fraction of those, holds run days, and the universe is two instruments. Over four
   OOS years that is ~6 trades/year/symbol — 46 total. The per-fold optimizer reaches for the
   *loosest* compression (Q_COMP=35) in almost every fold, confirming trade count is the binding
   constraint, not edge quality.
2. **No positive edge in-sample-selected → OOS.** The deployed OOS Sharpe is negative and PF < 1.
   The walk-forward selected a variant each fold on IS Sharpe; those selections did not carry a
   real edge into OOS (classic thin-sample selection noise). DSR ≈ 0 against a deflation benchmark
   of just 0.06/√bar — the strategy does not clear even a very modest data-mining hurdle.
3. **Fragile to entry timing.** The jitter test (fills re-derived ±30 min from 1m data) leaves the
   median terminal below the (already negative) base — the little P&L there is depends on exact
   entry bars, which a 1-second live bot does not own.

## Trustworthiness of these numbers

The correctness-critical code was adversarially reviewed by four independent passes (stats
formulas, look-ahead/causality, cost & funding accounting, validation methodology). Their verdict:
the core is **sound** — formulas match Bailey & López de Prado, the causal guards (channel shift,
`close[t-1]` denominator, funding/OI alignment, next-open fills) are correct, funding signs and
settlement boundaries are right, the walk-forward is properly purged/embargoed and non-overlapping.

Real defects they found were **fixed and the backtest re-run**:
- daily P&L was attributed to the signal day instead of the fill day (one-day mis-timing of the
  daily-return series — totals were always correct); re-run numbers above are post-fix and
  essentially unchanged, confirming the verdict is not an artifact;
- the portfolio jitter aggregation summed per-symbol medians (meaningless) — rewritten to a proper
  shared-path portfolio replay;
- stats degenerate-input guards now fail **closed** (nan/inf) instead of clamping to a spurious pass;
- profit-factor = ∞ (all-winners) now passes its gate; N is clamped/reported consistently.

Unit tests (23, all passing) cover the stats formulas on synthetic data with known properties,
funding-sign and cost arithmetic, feature causality (future data cannot change past features), and
the engine's daily-MTM ⇔ trade-P&L accounting invariant.

## Documented conservatism / limitations (not hidden)

- **DSR trial dispersion V** is estimated from the 320 correlated grid variants, which understates
  the true dispersion and thus *under*-deflates (flatters DSR). This is intentionally offset by
  fixing N to the shared-ledger 1000. It does not affect this verdict — DSR is ~0 regardless.
- **MC block-bootstrap envelope** is a weak test (resamples of the same returns center on the real
  drift), which is why it "passes" even on a losing record; the jitter test and the DSR carry the
  real power here. A max-drawdown or terminal-Sharpe bootstrap would add power — noted for future.
- **CPI dates** omitted from the event filter (FOMC-only; dates not fabricated); **spread filter**
  live-only per spec; **stop fills** assume `min(stop, open)` (real cascade slippage is worse).
- **Sizing** uses a constant reference sleeve (non-compounding) for stationary daily returns.

## Recommendation

As specified, Coil-Break **does not validate** on the available sample — it cannot generate enough
independent OOS trades to support a deployment claim, and what it does generate shows no edge. Do
not proceed to Phase 3 (live-ops) for this candidate as-is. Options, in order of my preference:

1. **Test the runner-up (Funding-Extreme Fade) instead.** It is also fully backtestable on free
   full-history data and has a real per-trade cash-flow (funding receipt), which may clear the
   trade-count/edge bar where a pure breakout does not. The entire Phase-2 harness here
   (cost/funding model, walk-forward, DSR/PSR/MinTRL, Monte Carlo, data layer) is strategy-agnostic
   and reused directly — only `strategy.py`/`config.py` change.
2. **Broaden Coil-Break's universe** (more top-10 perps that pass the liquidity floor) to lift the
   trade count above the floor — but this changes the pre-registered design and must be re-locked
   and re-counted in the DSR ledger before it means anything.
3. **Abandon Coil-Break.** A defensible outcome: the design's own falsification protocol rejected it.

My recommendation is **(1)** — point the same harness at Funding-Extreme Fade. Say the word and I'll
wire it in.
