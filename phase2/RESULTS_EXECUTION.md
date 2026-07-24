# Spot-leg execution realism (#4) — cost model correction

The cash-and-carry cost model originally applied **one symmetric per-leg cost** (perp fee + spread,
perp ADV) to all four legs. That is wrong by construction: the spot leg is materially more expensive
than the perp leg, and non-simultaneous fills add a legging cost the model ignored entirely. This
note records the real, cited parameters used in the corrected `SPOT_ASYMMETRIC` model.

## Cited fee schedule (Binance, VIP 0 / retail)

| leg | taker fee | with token discount | source |
|---|---|---|---|
| **SPOT** | **10.0 bps** (0.1000%) | 7.5 bps (BNB −25%) | Binance Spot Trading Fee page; corroborated by CoinSpot Binance Fees 2025 guide |
| **PERP** (USDT-M) | **5.0 bps** (0.0500%) | 4.5 bps (BNB −10%) | Binance Futures Fee page; TradersUnion & Bitdegree fee guides |

**The spot taker fee is 2× the perp taker fee.** A symmetric per-leg cost understates the true cost
of the delta-neutral pair, because half the legs (the spot buy on entry, the spot sell on exit) are
charged at twice the assumed rate.

## Estimated components (reasoned, labeled estimates — not live ticks)

- **Spot half-spread:** BTC/USDT ~0.5–1.0 bp, ETH/USDT ~1.0–1.5 bp (anchored to Binance tick sizes
  and Kaiko/Glassnode depth research that BTC/ETH USDT pairs carry the tightest books). Default 1.0 bp.
- **Perp half-spread:** ~0.5 bp.
- **Spot ADV vs perp ADV:** the perp is ~5–10× more liquid (documented Binance BTC perp:spot daily
  volume ratio 6.3–9.1). Modeled as `spot ADV ≈ perp ADV × 0.15`. At retail size ($5k–25k) impact on
  either leg is <0.5 bp, but the asymmetry is encoded so the model scales correctly with size.
- **Legging slippage:** the two legs fill on two matching engines (Futures vs Spot) 1–3 s apart; the
  price drift in between lands directly in the entry basis (execution-basis slippage), one-sided in
  expectation (you chase the second leg + cross a second half-spread). BTC ~50–60% annualized vol ⇒
  ~1 bp/second ⇒ **~2 bps typical per pair-establishment** (entry and again exit); ~8 bps stressed.

## Corrected per-trade cost

| | realistic (1×) | stressed (2×, the pass/fail default) |
|---|---|---|
| open the pair | perp ~5.6 + spot ~11 + legging 2 = **~18.6 bps** | ~29.5 bps |
| round trip | **~37 bps (~0.37%)** | ~59 bps (~0.59%) |

(Previously the model implied ~28 bps round trip at 2× stress — the spot leg was under-charged.)

## Measured effect

Net roughly **halves** and the marginal years go to break-even — see `RESULTS_IMPROVEMENTS.md`
(#4 section). Cost rises from ~50% to ~73% of gross funding. This is the largest downward revision in
the project and it comes purely from modeling the spot leg honestly.

## Honest caveats (from the research)

- Personal futures fee tiers are login-gated; the 0.02%/0.05% USDT-M base + BNB discounts are
  confirmed via multiple third-party guides consistent with Binance's standing schedule, not read off
  a logged-in page.
- Spot spreads and legging slippage are **reasoned estimates** (tick size + published vol + depth
  research), not live order-book snapshots. Treat as design defaults; recalibrate against real fill
  logs before trusting the magnitude.
- Paying fees in BNB (spot −25%, futures −10%) would lower these; the model uses the no-discount VIP0
  rows as the conservative default.

Implementation: `config_carry.CostsCarry` (SPOT_* fields), `backtest_carry.run_symbol_carry`
(asymmetric branch). `SPOT_ASYMMETRIC=False` recovers the legacy symmetric model. Both paths are
covered by `test_carry.py::test_symmetric_fallback_four_leg_cost` and `::test_asymmetric_spot_cost_is_higher`.
