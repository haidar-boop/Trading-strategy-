# Phase 2 — Coil-Break Backtest

Full backtest implementation of **Candidate 1 (Coil-Break)** from `STRATEGY_DESIGN.md`,
run on **real** Binance USDT-M perpetual-futures data. Vectorized feature construction,
event-driven (path-dependent) exit resolution, costs + slippage + funding modeled per the
Phase-1 constraints, and DSR / PSR / MinTRL reported on out-of-sample data.

> Every number the runner prints is **measured** on real data. Nothing is invented. Where
> the sample is too thin to conclude, the report says **"insufficient evidence"** — that is a
> legitimate verdict, and it is the one this strategy earns (see results).

## Data (free, no API keys)

All data comes from `data.binance.vision` (the public bulk-dump host; the `fapi.*` REST API
is geo-restricted and deliberately unused):

| Feed | Path | Used for |
|------|------|----------|
| 1m klines | `futures/um/monthly/klines/<SYM>/1m/` | daily bars + intrabar exit resolution |
| funding (8h) | `futures/um/monthly/fundingRate/<SYM>/` | funding accrual + funding gate/budget |
| metrics (5m OI) | `futures/um/daily/metrics/<SYM>/` | OI sign filter (2021+ only) |

Coverage: klines/funding from 2020, OI/metrics from 2021 (so the OI-ON variant is only
meaningful on the covered subsample — exactly as the spec requires).

## Layout

```
coilbt/
  config.py        # 4 free params, frozen constants, filters, costs, validation spec, the 320-variant grid
  data/download.py # threaded downloader (data.binance.vision -> parquet cache)
  data/loader.py   # 1m -> daily bars; causal funding/OI alignment; median 1m $-vol
  costs.py         # fee/slippage model + funding accrual (realized sign) + adverse-funding
  strategy.py      # vectorized, causal features + entry-signal logic (look-ahead guarded)
  backtest.py      # event-driven engine; vectorized hold resolution (trail/hard/time/funding stops)
  stats.py         # PSR, MinTRL, Deflated Sharpe, profit factor (Bailey & Lopez de Prado)
  walkforward.py   # purged/embargoed rolling walk-forward + per-fold grid selection
  montecarlo.py    # circular block bootstrap envelope + entry-timing jitter
  run_phase2.py    # orchestrator + pass/fail report
tests/             # stats, costs/funding, look-ahead, engine invariant  (pytest)
```

## Run

```bash
python -m venv .venv && source .venv/bin/activate     # or: uv venv
uv pip install numpy pandas scipy pyarrow requests matplotlib pytest

# 1) download (cached; ~290 MB for 2020-2025 both symbols)
python -m phase2.coilbt.data.download --symbols BTCUSDT ETHUSDT --start 2020-01-01 --end 2025-12-31

# 2) full backtest + validation report
python -m phase2.coilbt.run_phase2 --start 2020-01-01 --end 2025-12-31 --symbols BTCUSDT ETHUSDT

# 3) tests
python -m pytest phase2/tests/ -q
```

Outputs land in `phase2/artifacts/`: `phase2_result.json` (all metrics + checks + verdict) and
`phase2_oos_equity.csv` (concatenated OOS equity curve).

## Methodology (locked to Phase-1 spec)

- **Walk-forward:** rolling (fixed) 24m IS / 6m OOS / 6m step; selection uses IS returns only,
  with the last `max(purge=14d, embargo=15d)` of IS dropped; OOS blocks are non-overlapping.
- **DSR** computed once on the concatenated OOS record, deflated by E[max Sharpe] across the
  shared-ledger **N = 1000**; trial dispersion `V` estimated from all 320 fixed variants scored
  on the same OOS windows.
- **Monte Carlo:** circular block bootstrap (not IID) 5th-percentile envelope + entry-timing
  jitter (fills re-derived from 1m data).
- **Pass gates:** DSR ≥ 0.95, OOS PF ≥ 1.3, ≥ 60 OOS trades, MinTRL ≤ OOS length, MC envelope
  + jitter. Below 60 OOS trades the verdict is **"insufficient evidence — do not deploy."**

## Known limitations (documented, not hidden)

- **CPI dates** are omitted from the event filter (FOMC-only); exact BLS release dates were not
  fabricated. Minor: the filter removes ~1-day windows for a small set of days.
- **Spread filter** is live-only (assume-pass in backtest), per spec — real spread/impact needs
  self-recorded L2.
- **Stop fills** assume `min(stop_px, bar.open)`; true gap/queue slippage in cascades is worse
  and only measurable forward (the Phase-1 "what the backtest cannot tell us" caveat).
- **Sizing** uses a constant reference sleeve (non-compounding) so daily returns are stationary
  for DSR/PSR — a deliberate research-backtest convention.
