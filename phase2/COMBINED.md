# Combined Platform — phase2 harness × uploaded quant_system

This merges the two systems into **one research platform**: the real-data phase2 harness
(real Binance data, real-venue costs, the Coil-Break / FEF engines, DSR/PSR/MinTRL, purged
walk-forward, Monte Carlo) now carries the machinery it lacked, ported from the uploaded
`quant_system` sandbox.

> **What "combine" means here — and what it does not.** This combines the *testing machinery*,
> not two winning strategies (there are none). More validation tooling makes strategies *harder*
> to pass, not easier — it is a stricter filter, not an alpha generator. The payoff is that the
> platform now tells you, faster and more honestly, whether a real-data edge survives.

## What was ported (attribution: uploaded quant_system)

Under `phase2/coilbt/quantlib/`:

| Module | Capability | Why it matters |
|---|---|---|
| `pbo.py` | **PBO / CSCV** — Probability of Backtest Overfitting (Bailey-Borwein-LdP-Zhu) | The one big test phase2 lacked. Wired onto the **real-data grid**: for every grid config's OOS return stream, how often is the in-sample-best config below the OOS median. |
| `allocation.py` | **HRP / ERC / IVP / min-variance** | Robust multi-stream portfolio construction (no matrix inversion) for when a sleeve ever passes. |
| `metrics.py` | Sortino / Calmar / MaxDD / Ulcer / VaR / CVaR / tail / Omega | Richer risk picture than Sharpe alone; reported on every deployed OOS record. |
| `impact_costs.py` | **√-law market-impact** cost model + stress multiplier | More realistic than flat fee+slippage; for capacity/stress analysis. |
| `regime.py` | **Gaussian HMM** (Baum-Welch, Viterbi) with causal `filter()` vs look-ahead `smooth()` | Regime-conditioning of entries; the causal/look-ahead split is a built-in leakage guard. |
| `sizing_lib.py` | EWMA vol, vol-targeting, fractional Kelly, ADV caps | Portfolio-level risk scaling. |

## What changed in the runners

Both `run_fef.py` and `run_phase2.py` now compute and report, on **real OOS data**:

- **PBO / CSCV** over the full grid — a new pass/fail check (`pbo_pass = pbo < 0.5`), alongside DSR.
  This is the capability neither system had on its own: a real-data overfitting-probability read.
- **Rich metrics** (Sortino, Calmar, MaxDD, Ulcer, CVaR) on the deployed OOS equity.

So a strategy now has to clear **two independent overfitting screens** — DSR (deflation vs the
trial count) *and* PBO (selection-stability across time splits) — not one.

## The honest read on the combined FEF result

Running FEF through the combined battery does not change its verdict (it was never going to —
better tools don't add edge). It adds a second, independent confirmation: the DSR already said the
selected config's Sharpe doesn't beat the data-mining hurdle; PBO now independently reports how
overfit-prone the selection is. Two screens, same conclusion, more confidence in it. See
`RESULTS_FEF.md` (updated with the PBO line) and `artifacts/fef_result.json`.

## Run

```bash
python -m phase2.coilbt.run_fef     --start 2020-01-01 --end 2025-12-31   # FEF + DSR + PBO
python -m phase2.coilbt.run_phase2  --start 2020-01-01 --end 2025-12-31   # Coil + DSR + PBO
python -m pytest phase2/tests/ -q                                          # 36 tests
```

## What this unlocks next (all now one-import away)

1. **Delta-hedged carry** through DSR **and** PBO with **√-impact stressed costs** — the one
   hypothesis the data motivates (FEF proved the funding carry is real).
2. **Regime-conditioned entries** via the causal HMM `filter()`.
3. **HRP portfolio** across any sleeves that individually survive both screens.

Attribution: the ported algorithms are from the user-supplied `quant_system` sandbox; this work
integrates them onto real data and the phase2 walk-forward. Education/engineering only — not
investment advice, and still **no validated edge**.
