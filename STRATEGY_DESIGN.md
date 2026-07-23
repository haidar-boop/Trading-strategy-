# Quantitative Strategy Design — 3 Testable Candidates for Crypto Perpetual Futures

**Status: design only.** These are falsifiable hypotheses and unambiguous specifications, not a finished edge. There is **no market data and no backtest here**, so no performance number in this document is measured — every quantity labeled "hypothesis" is an order-of-magnitude implication of a mechanism, never an estimate of results. Win rate, Sharpe, drawdown, annual return, and trade frequency are deliberately **not** stated anywhere; producing them is the job of Phase 2.

This document was produced by three independent designer passes (one per anomaly class) followed by an adversarial verification pass whose job was to hunt for prohibition violations — invented metrics, unmeasurable rule language, undercounted parameters, dishonest trial accounting, and cost-arithmetic errors. Every finding it raised has been applied; the parameter budgets, the funding-cost conventions, and the multiple-testing ledger below are the corrected versions.

---

## Fixed constraints (all three strategies are designed within these)

| Constraint | Value used |
|---|---|
| **Venue / market** | Binance USDT-margined perpetual futures (Bybit as fallback venue) |
| **Universe** | BTCUSDT and ETHUSDT by default; other top-10-by-volume perps admissible only if the strategy's liquidity filter passes |
| **Capital** | $10,000 working assumption; every design must remain valid across $5k–$25k |
| **Costs (stated, because you left them blank)** | Taker fee **5 bps/side**, maker fee **2 bps/side** (Binance USDT-M VIP0, no BNB discount); expected slippage **2 bps/side** for marketable orders on BTC/ETH at ≤$25k notional. **Round trip:** taker+taker ≈ **14 bps**; maker-entry + taker-exit ≈ **9 bps**. Maker fills trade slippage risk for adverse-selection and non-fill risk. Funding is charged bar-by-bar at its realized sign in every cost model. |
| **Max leverage** | 3× (stated assumption; you left it blank) — enforced as a **portfolio** budget across all bots, not 3× per bot |
| **Max holding period** | Per-strategy, hard cap **14 days** |
| **Execution** | Automated bot via exchange WS/REST, ~1 s decision-to-order latency |
| **Data available** | 1m OHLCV (multi-year); 8h funding rates (full history); 5m open interest (multi-year via exchange/aggregators); L2 order-book depth and liquidation events (self-recorded going forward; historical only partial/paid). **Any rule depending on L2 or liquidation history carries an explicit limited-history caveat in its validation section.** |

**Costs — where the margin sits, in one line each.** The stated 9–14 bps round trip leaves realistic margin for all three *hypothesised* gross edges (tens to low-hundreds of bps); it is thinnest for the liquidation-reversion strategy (fastest horizon, most execution-sensitive) and most comfortable for the funding fade (funding receipt is a cash flow, not just price reversion). None of the three survives if effective round-trip cost reaches the 25–50 bps range, and each states its own kill line.

---


# Candidate 1 — Coil-Break (recommended: test first)

# Coil-Break: Volatility-Compression Breakout with Positioning Confirmation

Instrument universe: BTCUSDT, ETHUSDT USDT-M perps (Binance primary, Bybit fallback). Daily decision cadence on bars aggregated from 1m OHLCV at 00:00 UTC. Holding period: days, hard cap 14 days. Automated execution, ~1s latency.

---

### 1. Edge hypothesis

**Inefficiency and anomaly class.** Two documented anomaly classes, composed:

1. **Time-series momentum / post-breakout continuation** (Moskowitz–Ooi–Pedersen 2012; the broader trend-following literature). Prices exhibit positive autocorrelation at multi-day horizons after directional shocks, consistent with initial underreaction followed by continuation.
2. **Volatility clustering** (Engle/GARCH family; well documented in crypto). Low-volatility episodes are persistent but terminate in high-volatility episodes; a range contraction is a measurable precursor state to a volatility expansion. Note honestly: volatility clustering predicts the *magnitude* regime, not direction. The directional content of this strategy comes entirely from the breakout/TSMOM component; compression is a *conditioning* filter intended to select breakouts that occur from a low-noise base (where a channel violation is more informative relative to noise), not an independent alpha source.
3. **Open-interest confirmation — labeled SPECULATIVE.** The interpretation "breakout with rising OI = new-money conviction and further continuation; breakout with falling OI = position-closing (short-covering / long liquidation) and likely fade" is standard futures-market folklore with some support in commodity-futures positioning studies, but crypto-perp-specific evidence is thin and mostly practitioner-grade. It is implemented as a binary sign filter only, it is one of the explicitly counted backtest variants (on/off), and the strategy must not depend on it to pass validation.
4. **Funding as a crowding gate — partially supported.** Extreme positive funding as a proxy for crowded longs connects to the carry/crowding literature (perp funding as the cost leveraged longs pay); using it to *veto* entries in the crowded direction is a risk filter, not an alpha claim.

**Who is on the other side and why they lose.**
- **Mean-reversion traders and grid bots** who have been profitably fading the edges of the compressed range for days/weeks. At the breakout they are short the move by construction, and their stop-outs and re-hedging supply continuation flow. That grid-bot liquidity on Binance perps is large and mechanically fades every move until the grid boundary breaks is **SPECULATIVE** (practitioner folklore; no citation or data) — it is a plausibility argument for the counterparty, not a validated premise.
- **Inattentive holders** (the underreaction channel): discretionary participants anchored to the prior range who update beliefs slowly after a regime shift, selling into the early stage of an up-move (or covering late in a down-move).
- **Range-selling option-like liquidity providers**: market makers who widened inventory during the quiet period and must reduce inventory into the expansion, paying the momentum.

These counterparties lose *systematically* only in the specific state we condition on (post-compression regime change); in choppy regimes they win and we pay them. That asymmetry is the bet, not a free lunch.

**Why it survives at $5k–25k but is not institutionally arbitraged away.** TSMOM in crypto *is* institutionally traded (crypto CTAs), which is why we should expect a compressed, not zero, edge. The residual case for a solo trader: (a) institutional trend programs run slower horizons and diversified multi-asset books — a 2-instrument, days-horizon breakout book at ≤$75k max notional (3x on $25k) is below any mandate's capacity floor and not worth dedicated infrastructure; (b) many mandates cannot touch offshore USDT-margined perps at all; (c) at this size, taker execution has effectively zero market impact on BTC/ETH perps, so the small trader's cost structure is genuinely competitive with institutions for this trade shape. This is a "too small to bother" edge, not a hidden one.

**Decay profile.** Behavioral + regime-dependent, not structural. Requires regimes with volatility clustering and multi-day trends (2020–21, 2023–24 style). Killed by: sustained choppy/mean-reverting regimes (repeated false breakouts), volatility death (institutionalization compressing the expansion cycle), and crowding of short-horizon crypto trend itself. Because the directional component is behavioral, expect slow decay with regime-dependent long droughts rather than a sharp structural break.

---

### 2. Full specification (Python pseudocode)

**Free parameters (4 of 5 allowed — honest count).** The verifier correctly flagged that `FUND_GATE` cannot be both a "structural anchor" and a searched on/off variant. Resolution: `FUND_GATE` is **pre-registered frozen** at 5× the exchange baseline and **removed from the search space entirely** (it is a pure risk veto, always on, never tuned — see constants and §5). With that, the 5th slot is genuinely unused and the count below is honest.

| # | Param | Default | A-priori range | Economic reason |
|---|-------|---------|----------------|-----------------|
| 1 | `L` (lookback, days) | 20 | 10–40 | Defines the range that mean-reversion counterparties defend and the horizon of underreaction. Below 10d the channel is noise; above 40d holding-cap conflicts. |
| 2 | `Q_COMP` (compression percentile) | 25 | 10–35 | How quiet the market must be, relative to its own trailing year, before a breakout is treated as a regime change rather than routine noise. |
| 3 | `K_ATR` (stop/trail ATR multiple) | 3.0 | 2.0–5.0 | Noise scale separating a failed breakout from continuation; used for both initial and trailing stop (deliberately shared to save a parameter). |
| 4 | `F_RISK` (fraction of equity risked per trade at initial stop) | 0.005 | 0.0025–0.010 | Sizing. Fractional-Kelly stand-in: true Kelly is unestimable pre-data, so fixed-fractional risk with a hard cap is the explicitly justified alternative. `F_RISK` is fixed a priori and **excluded from any optimization grid** (it scales P&L, it does not create edge). |

**Hard-coded constants (one-line justifications):**
- `ATR_N = 14` days — Wilder convention, deliberately not tuned.
- `PCTL_WIN = 365` days — one year of trailing distribution for the compression percentile; spans at least one full vol cycle.
- `MAX_HOLD = 14` days — mandate constraint, not a choice.
- `MAX_LEV = 3` — mandate constraint.
- OI confirmation is **sign-only** (`ΔOI > 0` over the breakout day) — a sign test avoids introducing a tunable threshold; SPECULATIVE alpha-ish filter, legitimately tested as an on/off variant (it is a candidate edge source whose contribution we want to isolate).
- `FUND_GATE = 0.0005` per 8h (0.05%) = 5× the exchange's 0.01% baseline — **pre-registered frozen and never searched.** It is a one-directional risk veto (blocks entries into the crowded/expensive-funding side), not an alpha knob; the 5× line is a judgment call fixed before any testing, so it consumes no parameter slot and appears in no grid. Unlike the OI filter, it is **not** run as an on/off variant.
- Per-symbol capital split 50/50 BTC/ETH; one position per symbol; no pyramiding.
- Re-entry after any exit requires a **new compression episode** (compression condition must go false then true again) — mechanical cooldown, no new constant.
- **No profit target — hard-coded absence, justified:** a trend-continuation hypothesis has no ex-ante price objective (the whole bet is that the move runs further than the range implies); capping it at a fixed target would truncate exactly the right tail the edge lives in. The trailing chandelier stop (`K_ATR`) is the harvest mechanism, and the 14-day cap is the backstop. Adding a target would introduce a parameter with no mechanism behind it.
- Fills modeled: taker at next 1m open after signal, +2 bps slippage per side, 5 bps taker fee per side, funding accrued every 8h while holding, all per the stated cost constraints.

```python
# ---------- feature construction (daily bars from 1m OHLCV, 00:00 UTC) ----------
def features(sym, t):                      # t = daily close timestamp
    d = daily_bars(sym)                    # aggregated from 1m
    atr    = wilder_atr(d, ATR_N)[t]                     # in price units
    hh     = max(d.high[t-L : t])                        # PRIOR L days, excludes bar t
    ll     = min(d.low [t-L : t])
    # compression measured on bars up to t-1 so the breakout bar
    # cannot inflate its own range (look-ahead guard)
    rw     = (max(d.high[t-L : t]) - min(d.low[t-L : t])) / d.close[t-1]
    rw_hist = [range_width(s) for s in daily_range(t-PCTL_WIN, t)]
    compressed = rw <= percentile(rw_hist, Q_COMP)
    oi_up   = oi_5m(sym, t) > oi_5m(sym, t - 1_day)      # SPECULATIVE sign filter
    oi_down = oi_5m(sym, t) < oi_5m(sym, t - 1_day)
    fr      = last_settled_funding_rate(sym, t)          # known at t, no look-ahead
    return d, atr, hh, ll, compressed, oi_up, oi_down, fr

# ---------- entry (evaluated once per day at 00:00 UTC close) ----------
def entry_signal(sym, t):
    d, atr, hh, ll, compressed, oi_up, oi_down, fr = features(sym, t)
    if not compressed:                 return None
    if not filters_pass(sym, t):      return None       # section 3
    if d.close[t] > hh and oi_up  and fr <  FUND_GATE:  return "LONG"
    if d.close[t] < ll and oi_down and fr > -FUND_GATE: return "SHORT"
    return None
    # note: SHORT requires oi_down (long liquidation / new shorts pressing) —
    # the symmetric-sign OI reading is the most SPECULATIVE piece; the
    # oi-filter-off variant treats both sides unconditionally.

# ---------- sizing: fixed-fractional risk (explicit Kelly alternative) ----------
def size(sym, t, equity, atr, entry_px):
    per_sym_equity = 0.5 * equity
    stop_dist  = K_ATR * atr
    qty        = (F_RISK * per_sym_equity) / stop_dist   # risk F_RISK of sleeve to stop
    qty        = min(qty, MAX_LEV * per_sym_equity / entry_px)   # leverage cap
    qty        = min(qty, liquidity_cap_qty(sym, t))             # section 3
    return qty

# ---------- position management (checked every 1m bar) ----------
def manage(pos, bar_1m, t_now):
    atr = pos.atr_at_entry                      # frozen at entry; no stop widening
    if pos.side == "LONG":
        pos.trail = max(pos.trail, highest_close_since_entry(pos) - K_ATR * atr)
        hard_stop = pos.entry_px - K_ATR * atr
        stop_px   = max(hard_stop, pos.trail)   # chandelier ratchet
        if bar_1m.low <= stop_px:  exit_taker(pos, "stop")
    else:  # SHORT, mirrored
        pos.trail = min(pos.trail, lowest_close_since_entry(pos) + K_ATR * atr)
        hard_stop = pos.entry_px + K_ATR * atr
        stop_px   = min(hard_stop, pos.trail)
        if bar_1m.high >= stop_px: exit_taker(pos, "stop")
    if t_now - pos.entry_time >= 14 * DAY:      exit_taker(pos, "time_cap")
    # funding-budget stop: cap adverse carry at 25 bps (half the ~50 bps kill line); uses only the
    # settled-funding series, fixed fraction, no new free parameter.
    if accrued_adverse_funding_bps(pos) >= 25:  exit_taker(pos, "funding_budget")

# ---------- execution ----------
# Entry: market (taker) at first 1m bar after signal close; ~1s latency.
# Exits: stop-market (taker). No maker orders in the base spec — breakout entries
# chase momentum, where maker fills are adversely selected; the maker-entry
# variant is deferred until live L2 data exists to model non-fill risk.
```

---

### 3. Filters (code conditions, not prose)

All thresholds hard-coded constants (justified inline); none consume a free parameter.

```python
def filters_pass(sym, t):
    # Liquidity floor: 30d median 1m dollar volume >= $500k  =>  our max clip
    # ($75k notional) is < 15% of a median MINUTE. Trivially true for BTC/ETH;
    # this is the admission gate for any other top-10 perp.
    ok_liq   = median(dollar_vol_1m(sym, t-30*DAY, t)) >= 500_000

    # Spread ceiling (LIVE ONLY — needs self-recorded L2; see section 7):
    # 1h median top-of-book spread <= 2 bps, else block entries.
    ok_sprd  = live_median_spread_bps(sym, 1*HOUR) <= 2.0 if LIVE else True

    # Volatility band: ATR14/close in [0.5%, 10%].
    # Below 0.5%: stop distance so tight that fees+slippage dominate risk.
    # Above 10%: cascade regime; stop-market fill quality unmodelable.
    ok_vol   = 0.005 <= atr14(sym, t) / close(sym, t) <= 0.10

    # Scheduled-event exclusion: no NEW entries in the 24h before FOMC rate
    # decisions and US CPI releases (public calendars, fully computable).
    # Existing positions are managed normally.
    ok_event = not within(24*HOUR, next_event({"FOMC_DECISION", "US_CPI"}), t)

    # Data-integrity gates: skip entry if OI feed has a gap > 1h in the last
    # 24h, or the 1m OHLCV feed has any missing bar in the last L days.
    ok_data  = oi_gap_hours(sym, t-1*DAY, t) <= 1 and n_missing_1m(sym, t-L*DAY, t) == 0

    # No session/time-of-day exclusion: 24/7 market, daily cadence already
    # fixes decision time at 00:00 UTC.
    return ok_liq and ok_sprd and ok_vol and ok_event and ok_data

def liquidity_cap_qty(sym, t):
    # Clip <= 5% of 30d median 1m dollar volume: at $500k floor => $25k cap,
    # matching the stated slippage assumption's validity domain.
    return 0.05 * median(dollar_vol_1m(sym, t-30*DAY, t)) / close(sym, t)
```

---

### 4. Cost sensitivity

**Gross edge the hypothesis implies — hypothesis, not estimate.** The hypothesis is that post-compression breakouts capture a move on the order of 1–3× ATR14 net of the losing trades' ~1× `K_ATR`·ATR stops, over days. Taking ATR14/close to be of order low-single-digit percent for BTC/ETH — an **unverified working assumption to be confirmed from downloaded data before validation, not a measured fact** — that puts the *hypothesized* average gross edge per trade in the **tens to low hundreds of bps** (order of magnitude: ~50–200 bps). This is what the anomaly class would have to deliver to exist at all at this horizon; it is not a measured number.

**All-in round-trip cost accounting (taker/taker base case):**
- Fees: 5 + 5 = 10 bps
- Slippage: 2 + 2 = 4 bps
- Funding carry: at the 0.01%/8h baseline, ~3 bps/day against a long; 14-day worst-case hold ≈ 42 bps; typical multi-day hold ~10–20 bps, sign depends on side and regime. The `FUND_GATE` veto caps entries into the most adverse carry.
- **Total: ~14 bps fees+slip, ~25–55 bps all-in including adverse funding on longer holds.**

**Dead threshold.** A days-horizon breakout strategy with hypothesized gross edge of ~50–200 bps/trade is plausibly dead when all-in round-trip cost reaches **~50 bps** — that consumes the entire lower bound of the hypothesized edge before the win/loss asymmetry is even tested. Fees+slippage alone at ≥25 bps/side (e.g., losing maker/VIP status AND slippage regime doubling) would also flag death.

**Do stated costs leave realistic margin? Conditional yes — with one explicit exception.** Arithmetic: 14 bps fees+slip against a ≥50 bps lower-bound hypothesized edge is ≤28% of gross, comfortable. But the ~55 bps worst-case all-in (max-duration 14-day hold paying adverse funding) **sits above the ~50 bps kill line** — so the honest answer is "yes for typical holds, no for max-duration adverse-funding holds." Two pre-registered mitigations keep the base case clear of the kill line rather than hand-waving the contradiction: (i) the `FUND_GATE` veto blocks entries into the most adverse carry side, capping the funding a new position can pay; (ii) any position whose *accrued* adverse funding since entry exceeds 25 bps is force-exited (a funding-budget stop, using only the settled-funding series — no new parameter, a fixed fraction of the kill line). With those, the realistic all-in stays in the ~14–35 bps band; the >50 bps tail is truncated by rule, not assumed away. Validation charges bar-by-bar funding at its realized sign so the backtest sees this directly. Maker-entry (9 bps RT) is not assumed; it is upside deferred until non-fill risk is measurable from live L2 (section 7).

---

### 5. Validation protocol (pass/fail thresholds, no predicted metrics)

**Minimum data.** BTCUSDT perp from 2019-09 (contract launch) and ETHUSDT perp from 2019-11, through present: 1m OHLCV (exchange-native), full funding history (exchange-native), OI at 5m from earliest aggregator availability (~2020; vendor-spliced — the OI variant must therefore also be evaluated with the OI filter OFF over the full sample, and ON only over the OI-covered subsample). This span contains ≥5 distinct regimes: **COVID crash (Mar 2020), 2020–21 leverage bull, May 2021 leverage flush, 2022 bear (LUNA/3AC/FTX), 2023 recovery, 2024–25 ETF era** — including both regimes the edge needs (trending, vol-clustered) and regimes designed to kill it (2022 chop-down, range-bound stretches of 2023).

**Walk-forward.** Rolling 24-month IS window → select params on IS only → trade next 6-month OOS block → step 6 months. **Purge** any trade whose holding window crosses an IS/OOS boundary; **embargo = 14 days** (equal to max holding period) between IS end and OOS start so no label leakage through open positions or overlapping ATR/percentile state. All OOS blocks are concatenated into one OOS record; per-fold statistics are reported but not used as pass/fail (per-fold trade counts will be too small to test — see below).

**The low-trade-count problem, confronted.** The compression gate mechanically restricts eligible entry days to ≤ `Q_COMP`% of days per instrument (arithmetic consequence of the rule, not a performance forecast), holds last days, and there are only 2 instruments. OOS trade count will therefore be structurally low. Consequences adopted:
1. **Hard floor: ≥ 60 concatenated OOS trades** (pooled across symbols and folds). Below 60, the verdict is **"insufficient evidence — do not deploy"** regardless of how good the point estimates look. No exceptions.
2. DSR/PSR are computed on **daily OOS returns** (autocorrelation- and non-normality-adjusted per Bailey–López de Prado), not per-trade returns, to use the full sample length.
3. **MinTRL test:** compute Minimum Track Record Length at 95% confidence against SR* = 0 from the concatenated OOS moments. **Fail if MinTRL > actual concatenated OOS length.** This is the honest version of "the sample may simply be too short to know," and it is an expected failure mode for this, the slowest sibling.

**Pass thresholds (all after full costs: fees, slippage, funding accrual):**
- Deflated Sharpe Ratio > 0 at 95% confidence on concatenated OOS, with the trial count N below.
- OOS profit factor ≥ 1.3 (pooled trades) — raised from an earlier 1.15 to match both siblings; this is the *lowest*-trade-count sibling, so a thin PF is the most likely to be luck here, and it warrants the same floor, not a laxer one.
- OOS trade count ≥ 60 and MinTRL ≤ OOS length (above).
- Long-side and short-side evaluated separately: if only one side passes, only that side deploys and the variant count is charged accordingly.
- Sanity: OOS daily-return correlation to BTC buy-and-hold reported; if long-only equity is statistically indistinguishable from a vol-targeted BTC hold (paired test on daily returns), verdict is "beta in a costume — reject."

**Monte Carlo (2,000 paths each):**
- Trade-order reshuffle via block bootstrap on the OOS trade sequence (block = 5 trades to respect clustering).
- Entry-timing jitter: shift each entry execution uniformly ±30 minutes around the signal close, re-priced from 1m data (tests dependence on the exact 00:00 UTC print).
- **Fail** if the realized OOS equity path breaches the 5th-percentile envelope of the jittered/reshuffled paths at any point, or if the jittered median terminal equity falls below 0.5× the unjittered result (fragility to timing).

**Multiple-testing accounting (shared batch-wide ledger).** Parameter grid actually searched: `L` ∈ {10,15,20,30,40} × `Q_COMP` ∈ {10,20,25,35} × `K_ATR` ∈ {2,3,4,5} = 80 combinations (`F_RISK` counted as a parameter but excluded from the grid; `FUND_GATE` frozen and unsearched). Variants: OI filter {on, off} × side {long+short, long-only} = 4 (the funding-gate on/off variant is **removed** — the gate is now frozen). **80 × 4 = 320 trials for Coil-Break.**

The DSR trial count is **not** this figure multiplied by a sibling count — that is the double-count error the earlier draft made. There are **3** sibling strategies, and the shared ledger is the **sum** of the three declared grids: FEF 384 + Cascade Fade 162 + Coil-Break 320 = **866 nominal.** With a stated exploratory margin (iteration, range-widening) the shared trial count rounds to **N = 1,000**, cited identically across all three Section 5s and revised jointly whenever any sibling adds trials. This N feeds the DSR for Coil-Break. Because Coil-Break is the last sibling selected for deployment after seeing OOS results, the *selection* itself is an extra test DSR does not fully absorb (see §7).

---

### 6. Live degradation triggers

All computed daily by the bot; actions are automatic.

| Trigger | Measurable condition | Automatic action |
|---|---|---|
| Rolling PSR floor | PSR(SR*=0) on trailing 26 weeks of live daily returns < 0.50 | Halve `F_RISK` |
| Rolling PSR halt | Same window, PSR < 0.25 | Halt new entries; manage open exits only; manual review required to resume |
| MC envelope breach | Live equity drawdown (in R-multiples, at matching trade count) deeper than the 5th-percentile max-drawdown of the validation Monte Carlo envelope | Full halt; strategy returns to revalidation |
| Breakout-failure regime | ≥ 8 of the last 10 entries exited at the initial stop within 48h | Halve `F_RISK` until the ratio drops below 5/10 |
| Funding regime shift | 90d mean |funding| > 3× the full-backtest median |funding| | Disable entries on the side that would pay funding; log as structural-break candidate |
| Compression-distribution shift | Trailing 180d share of days passing the compression gate outside [0.5×, 2.5×] `Q_COMP`% | Flag distribution shift; halt new entries pending manual review (the conditioning variable itself has moved) |
| Spread regime shift | 30d median top-of-book spread (self-recorded L2) > 2× the first-90-days-live median, or > 4 bps absolute | Recompute all-in RT cost with observed spread; if ≥ 50 bps (section 4 dead threshold), halt |
| OI feed break | Exchange OI methodology change announcement, or feed gap > 24h | Disable OI confirmation (fall back to the validated oi-off variant if it passed; otherwise halt) |
| Venue/fee change | Announced taker fee or funding-interval change altering all-in RT by > 5 bps | Recompute section 4 arithmetic before next entry; halt if dead threshold crossed |

---

### 7. Failure modes

**Top 3 ways this is most likely a FALSE POSITIVE:**
1. **Survivor of a mined batch.** This is 1 of 3 sibling strategies drawn from a shared ledger of ~866 nominal trials (N = 1,000 with margin). Even with DSR at N = 1,000, the *selection of which sibling to deploy* after seeing OOS results is itself an additional test that DSR does not fully absorb. The compression gate (`Q_COMP`) is especially dangerous: percentile filters are flexible enough to quietly select the profitable subperiods of a trending sample.
2. **Regime luck masquerading as edge.** The available history is dominated by two structural bull runs. A long-biased breakout system can pass every threshold in section 5 while being repackaged crypto beta with extra fees; the short side may simply never accumulate enough trades to test (the MinTRL/60-trade floor will likely bind here first). The beta-in-a-costume test helps but cannot fully separate "trend edge" from "was long during bulls" on one asset class.
3. **Positioning-data look-ahead and splices.** Aggregator OI history is backfilled and vendor-spliced; revision timestamps are not the original publication timestamps, so the backtested OI filter may use information that was not available at the bar close. Funding alignment is a second trap: the settled rate is known in advance of the interval it applies to — misaligning it by one interval creates silent look-ahead in the funding gate. Both feeds get an explicit alignment audit before any backtest is trusted, and the OI variant is never allowed to be the difference between pass and fail.

**Market-structure changes that kill it outright:** taker-fee regime change of a few bps (section 4 margin arithmetic collapses); funding-interval or funding-cap changes altering the carry math mid-hold; secular volatility compression as crypto institutionalizes (the compression→expansion cycle itself dampens, removing the conditioning event); regulatory loss of access to offshore USDT-M perps; a durable shift of counterparty mix away from grid/mean-reversion flow (fewer stop-outs to fuel continuation).

**What the backtest cannot tell us (specific to this strategy's taker/stop-market order types):**
- **Entry slippage in expansion.** We buy breakouts with market orders at exactly the moment depth thins and the book leans against us; the flat 2 bps assumption is calibrated to normal conditions and is optimistic at signal time. Unmeasurable historically without L2; self-recorded live spread/impact data feeds the section 6 spread trigger instead.
- **Stop-market fills in cascades.** Liquidation cascades gap through stop prices; the backtest fills at the stop level +2 bps, reality can be materially worse precisely in the largest losers. Historical liquidation data is partial (aggregator/paid-vendor only), so this tail is validated only forward, from self-recorded WS liquidation and fill data.
- **Maker-variant unknowables.** The 9 bps maker-entry improvement carries non-fill risk (missing the exact breakouts that work) and adverse selection (filling on the ones that fail) — neither is estimable from OHLCV. The maker variant is therefore excluded from the spec until ≥ 90 days of self-recorded L2 exists.
- **Queue position and partial fills** are second-order at ≤ $25k clips on BTC/ETH but not zero during the high-ATR windows this strategy deliberately selects into — which is exactly when the backtest's fill model is least trustworthy.


# Candidate 2 — Funding-Extreme Fade

# Funding-Extreme Fade (FEF) — directional funding-fade on Binance USDT-M perps

**Class chosen:** directional funding-fade (NOT spot-hedged cash-and-carry). The position is a single perp leg taken against the crowded side, so it always sits on the funding-receiving side while open. Delta risk is accepted and managed with stops; it is not hedged.

---

### 1. Edge hypothesis

**Inefficiency.** The perpetual funding rate is the price of leverage demand. In normal regimes it hovers near the interest-rate baseline (Binance baseline 0.01%/8h). Episodically it spikes to multiples of that baseline because leveraged directional traders — overwhelmingly retail and momentum-chasing funds using the perp as their only access instrument — bid up one side of the book faster than arbitrage capital re-anchors the perp to spot. Two documented anomaly classes support fading this:

1. **Carry** (Koijen, Moskowitz, Pedersen, Vrugt, "Carry", JFE 2018): assets with high carry earn it on average; in perps, the funding-receiving side is the carry-long side. Funding as a vol-risk/leverage premium is documented in the crypto-specific literature (e.g. work on perp basis and funding as a speculative-demand index; Kyle-style leverage-demand pricing).
2. **Crowded-trade unwind** (crowding/deleveraging literature: Stein 2009, Khandani-Lo 2007 quant unwind; in crypto, the well-documented long-liquidation cascades of 2021): when positioning is one-sided AND leveraged, small adverse moves force mechanical liquidations in the direction opposite the crowd, producing short-horizon mean reversion of price alongside normalization of funding.

The **combined bet**: when funding is in its extreme tail AND open interest has recently expanded (new leveraged positioning, not stale positioning), take the opposite side. You are paid funding every 8h while waiting, and the price-reversal component is optionality on a forced unwind. The funding-receipt component is literature-anchored carry; the price-reversal component is anchored in the unwind literature but its magnitude in this specific market is **SPECULATIVE** until backtested.

**Who pays, and why they systematically lose.** The counterparty is the leveraged directional trader (mostly retail on Binance perps, per exchange disclosures and academic studies of perp user composition) who (a) pays 3-10x the baseline funding rate because the perp is their only leverage venue — no portfolio margin, no CME access, no spot-margin infrastructure; (b) is momentum-entering after a move, i.e. buying leverage at its most expensive; (c) holds liquidation-prone positions, so their exit is partly involuntary and clusters against them. They "pay" twice: the explicit funding transfer and the implicit unwind slippage. Forced hedgers (miners, desks hedging structured products) also pay extreme funding at times, but they are a minority of flow on Binance USDT-M.

**Why it survives at $5k-25k but is not institutionally arbitraged away.** The pure spot-perp basis IS institutionally arbitraged (that is the delta-neutral cash-and-carry trade), which is exactly why funding rarely stays extreme for weeks. But the *directional fade* is not a riskless arb: it carries delta risk that mandate-constrained arb desks will not warehouse, and its capacity in the tail episodes is small relative to institutional size — the working hypothesis (unvalidated: episode frequency and per-episode capacity are exactly what the backtest must measure) is that the edge concentrates in rare episodes whose capacity is far below institutional relevance, because taker entry at size would move the very unwind the trade bets on. A $10k account is noise-level. Additionally the strategy requires tolerating multi-day adverse excursions against a euphoric trend, which is a career-risk trade for institutions and merely a stop-loss for a solo trader.

**Decay profile: regime-dependent + slowly structural.** Needs: regimes with episodic retail leverage euphoria (2020-21, 2023-24 memecoin/ETF waves). Killed or dormant in: (a) prolonged apathy regimes where funding never reaches the tail (mid-2022 post-FTX chop) — strategy correctly goes flat, opportunity cost only; (b) structurally, the growth of ETF-linked basis arb capital (post Jan-2024) compresses funding extremes — this is a measurable, monitorable decay channel (Section 6), not a silent one. The behavioral driver (retail chasing leverage) is persistent; the structural ceiling on how extreme funding gets is falling over time.

---

### 2. Full specification (Python pseudocode)

**Free parameters (exactly 5):**

| # | Name | Default | Range (a-priori) | Economic reason |
|---|------|---------|------------------|-----------------|
| 1 | `ENTRY_PCT` | 97.5 | 95.0–99.0 | Defines "extreme" funding: tail of the rolling funding distribution. Too low = fading normal carry (no crowding); too high = near-zero trade count. |
| 2 | `OI_Z_MIN` | 1.0 | 0.5–2.0 | Crowding confirmation: requires OI expansion, distinguishing fresh leveraged positioning (unwindable) from stale funding drift. |
| 3 | `STOP_ATR_MULT` | 2.5 | 1.5–3.5 | Stop distance in ATR units. The fade enters against a trend; stop must sit outside routine noise but inside account-ruin territory. |
| 4 | `EXIT_PCT` | 80.0 | 50.0–90.0 | Funding-normalization exit: when the crowding premium has decayed to this percentile, the carry reason to hold is gone. |
| 5 | `RISK_FRAC` | 0.01 | 0.005–0.02 | Fraction of equity risked to the stop per trade. Explicit alternative to fractional Kelly, justified below. |

**Sizing justification (alternative to Kelly):** fractional Kelly requires edge and variance estimates we do not have pre-validation; plugging invented numbers into Kelly launders fiction into a formula. Fixed-fractional risk (risk `RISK_FRAC` of equity to the stop) is the standard conservative substitute, is monotone in the same quantities once estimated, and can be replaced by fractional Kelly post-validation using OOS trade statistics. `RISK_FRAC` occupies one of the 5 parameter slots.

**Pre-registered frozen constants.** The verifier's honest recount is correct that several of these are potential degrees of freedom, not laws of nature. They are therefore **pre-registered here, before any testing, as frozen and never-to-be-varied**; no sensitivity analysis will be run on them, and if any is ever changed, every value tried multiplies the batch trial ledger (Section 5) before the DSR is recomputed:

- `PCT_LOOKBACK = 365 days` of realized 8h funding prints — one full annual cycle (1,095 funding intervals) so the percentile is not dominated by a single quarter. **Frozen.**
- `OI_LOOKBACK = 90 days` for the OI-change z-score — one calendar quarter; OI levels drift secularly and 90d localizes the crowding baseline. **Frozen.**
- `OI_CHANGE_WINDOW = 24h` = exactly 3 funding intervals — one full funding day; positioning built inside a single funding cycle is the fresh, liquidation-prone kind. **Frozen.**
- `ATR_PERIOD = 14` bars on `BAR = 4h` bars (built from 1m OHLCV) — Wilder convention, deliberately not tuned; 4h matches the holding horizon. **Frozen.**
- `MAX_HOLD = 7 days` = exactly 21 funding intervals. **Frozen.** Acknowledged as a judgment call, not a structural anchor: it is a backstop behind the `EXIT_PCT` normalization exit (which should fire first in the hypothesized mechanism), pre-registered so it can never be tuned into a hidden sixth parameter.
- `MAKER_WAIT = 300 s` — post a maker limit at best bid/ask first; escalate to taker if unfilled and signal persists, bounding non-fill risk at one 5-min re-check. **Frozen.**
- `PER_POS_LEV = 1.5x`, `TOTAL_LEV = 3.0x` — allows BTC and ETH positions simultaneously within the 3x account cap (and within the batch-wide portfolio budget, see cross-strategy rules). **Frozen.**
- `DECISION_TIMES` = funding timestamps 00:00/08:00/16:00 UTC — funding is the signal; decisions align to when it settles. **Signal convention (backtest and live, identical):** the signal uses the **realized funding print settled at decision time t** — the rate for the interval *ending* at t, which is fixed by the premium-TWAP up to t and is in the exchange's historical realized series. This makes the backtest signal fully computable from the constraint-listed data and removes any dependence on Binance's live "predicted rate" field, which has no reconstructible history. Using the print for the interval ending at t+8h would be look-ahead and is forbidden.
- No profit target and no trailing stop — hard-coded absence, justified: the exit thesis is funding normalization (`EXIT_PCT`), not a price level; adding price targets adds parameters without a mechanism.

```python
# ---- state built ONLY from constraint-listed data ----
# funding[sym]        : realized 8h funding history (full); funding[sym].settled_at(t)
#                       is the print for the interval ENDING at t (knowable at t)
# oi_5m[sym]          : open interest, 5m granularity
# bars_4h[sym]        : 4h OHLCV aggregated from 1m
# equity              : current account equity

def signal(sym, t):                      # t in DECISION_TIMES
    hist   = funding[sym].last_days(365)               # PCT_LOOKBACK
    f_now  = funding[sym].settled_at(t)                # realized print settled at t; no look-ahead
    pct    = percentile_rank(hist, f_now)              # 0..100, two-sided distribution
    d_oi   = oi_5m[sym].at(t) - oi_5m[sym].at(t - 24h) # OI_CHANGE_WINDOW
    oi_z   = zscore(d_oi, oi_5m[sym].rolling_24h_changes(days=90))
    if pct >= ENTRY_PCT       and oi_z >= OI_Z_MIN:  return SHORT   # crowd is long; short receives funding
    if pct <= 100 - ENTRY_PCT and oi_z >= OI_Z_MIN:  return LONG    # crowd is short; long receives funding
    return None

def enter(sym, side, t):
    if not filters_pass(sym, t): return                # Section 3
    atr  = ATR(bars_4h[sym], 14)
    px   = last_trade_price(sym)
    stop_dist = STOP_ATR_MULT * atr
    notional  = RISK_FRAC * equity / (stop_dist / px)
    notional  = min(notional, PER_POS_LEV * equity,
                    TOTAL_LEV * equity - open_gross_notional())
    if notional < MIN_NOTIONAL_EXCH: return
    oid = post_limit(sym, side, price=best_quote(sym, side), qty=notional/px)
    wait(300)                                          # MAKER_WAIT
    if unfilled(oid):
        cancel(oid)
        if signal(sym, now()) == side:                 # re-check before paying taker
            market_order(sym, side, notional/px)
    set_stop_market(sym, stop=entry_price -/+ stop_dist)   # reduce-only, taker

def manage(pos, t):                       # every DECISION_TIME + on stop trigger via WS
    if stop_hit(pos):                     return exit_taker(pos)          # STOP
    if now() - pos.entry_time >= 7*DAY:   return exit_taker(pos)          # TIME EXIT (MAX_HOLD)
    f_now   = funding[pos.sym].settled_at(t)                  # realized print settled at t
    # Funding-sign exit: if funding has flipped to a sign we now PAY, the carry reason to
    # hold is gone regardless of percentile — do not warehouse an adverse-funding position.
    pays_funding = (f_now > 0) if pos.side == LONG else (f_now < 0)
    if pays_funding:                      return exit_maker_then_taker(pos, wait=300)  # FUNDING-SIGN EXIT
    pct_now = percentile_rank(funding[pos.sym].last_days(365), f_now)
    normalized = (pct_now <= EXIT_PCT) if pos.side == SHORT \
            else (pct_now >= 100 - EXIT_PCT)
    if normalized:                        return exit_maker_then_taker(pos, wait=300)  # NORMALIZATION EXIT
    # else hold; funding accrues to us at each t while pct stays extreme and sign is favorable
```

---

### 3. Filters (code conditions, not prose)

All constants hard-coded; none consume a free-parameter slot.

```python
def filters_pass(sym, t):
    # Liquidity floor: universe admission (BTC/ETH pass by construction; gates any other top-10 perp)
    ok_liq   = median_daily_perp_volume_usd(sym, days=30) >= 1_000_000_000      # $1B: position <0.003% of ADV at $25k*1.5x

    # Spread ceiling: LIVE check only (no historical L2). Backtest assumption for BTC/ETH documented in Sec. 5/7.
    ok_sprd  = live_top_of_book_spread_bps(sym) <= 2.0                          # matches the 2 bps slippage assumption

    # Volatility band: refuse entry inside an active dislocation (the cascade you want has ALREADY happened)
    ok_vol_hi = abs(close_1m(t) / close_1m(t - 24h) - 1) <= 0.15               # 15%/24h: entering mid-cascade = catching knives
    ok_vol_lo = realized_vol_annualized(bars_1m, days=30) >= 0.20              # <20% ann. vol: ATR-based stops degenerate, edge dormant

    # Funding-mechanism sanity: skip symbols whose funding interval != 8h (Binance moved some alts to 4h/1h)
    ok_mech  = funding_interval(sym) == 8 * HOUR

    # Scheduled macro events: no NEW entries in [release - 30min, release + 30min] for US CPI and FOMC statements
    ok_event = not within_minutes(t, macro_calendar(['CPI','FOMC']), 30)       # manually maintained calendar file

    # Signal staleness: the signal must still fire on the SAME side between signal calc and order submission
    ok_fresh = signal(sym, now()) == intended_side

    return all([ok_liq, ok_sprd, ok_vol_hi, ok_vol_lo, ok_mech, ok_event, ok_fresh])
```

Session/time exclusions beyond the macro calendar: none — crypto perps trade 24/7 and funding timestamps are the natural clock; adding session filters would be an uncompensated parameter.

---

### 4. Cost sensitivity

**Gross edge the hypothesis implies (hypothesis, not estimate).** Mechanism arithmetic only: Binance baseline funding is 0.01%/8h (1 bp). The 97.5th-percentile entry gate, by construction, targets episodes where predicted funding is a multiple of baseline; the funding clamp and historical public commentary put tail episodes in the several-bps-per-8h range. If an episode pays on the order of 5 bps/8h and decays toward baseline over a holding period of 1-7 days (3-21 accruals), funding receipt alone is of order **15-100 bps per trade**, before any price-reversal contribution (sign-positive under the unwind hypothesis, magnitude unknown) and before losses on stopped-out trades. This is the hypothesis the backtest exists to test, not an estimate of performance.

**Round-trip cost at which the strategy is plausibly dead.** Costs per trade: entry (maker-first, taker fallback) + exit (maker-first on normalization, taker on stop/time) → between 9 bps (maker+taker RT per stated schedule) and 14 bps (taker+taker). Stops fire during cascades where slippage is worse than stated on **both** legs of a taker exit; doubling the stated 2 bps slippage on the taker exit side alone gives ~16 bps RT worst case (14 + 2), and if entry-side slippage also doubles, ~18 bps. The strategy is plausibly dead if effective RT cost exceeds **~40-50 bps**, i.e. the point where costs consume the low end of the hypothesized funding receipt alone, leaving the trade dependent entirely on the speculative price-reversal leg.

**Do stated costs leave realistic margin? Yes.** Arithmetic: hypothesized gross of order 15-100 bps/trade vs 9-18 bps RT cost → the low-end hypothesis covers costs at roughly 1x-2x, the central hypothesis at 3x-6x. Margin exists but is NOT comfortable at the low end: if validation shows median funding receipt per trade below ~25 bps, the edge is a cost-line rounding error and the strategy fails Section 5 regardless of statistical significance. **Funding-sign caveat (correcting an earlier overclaim):** the fade side is the funding-*receiving* side *at entry*, but decisions occur only at 8h timestamps and the normalization exit fires at the `EXIT_PCT` (80th) percentile, not at zero — so funding can cross the median and flip against the position for one or more 8h intervals before an exit rule triggers. Funding is therefore a revenue line *in expectation while the signal holds*, not "never a cost line"; the backtest charges realized funding bar-by-bar with its actual sign, and `manage()` books the adverse funding when the sign flips (see the funding-sign check added to the exit logic).

---

### 5. Validation protocol (pass/fail, no predicted metrics)

**Minimum data.** BTCUSDT and ETHUSDT perps: 1m OHLCV, full realized funding history, and 5m OI, from 2019-09 (start of Binance USDT-M funding history) to present (~6.8 years). This spans >=4 distinct regimes: the 2020 COVID crash and recovery, the 2021 retail-leverage mania and May-2021 leverage flush, the 2022 deleveraging bear (LUNA, FTX), the 2023-24 recovery, and the 2024-25 ETF era (the funding-compression regime the strategy must survive). OI history from aggregators (e.g. Coinalyze) where exchange history is short — timestamp alignment audited (Sec. 7). No L2 or liquidation history is required by any rule (the spread filter is live-only); this avoids the limited-history problem by design, at the cost of backtesting entry fills under a documented assumption: **backtest fills BTC/ETH entries at taker with the stated 5+2 bps, never assuming maker fills** — conservative by construction.

**IS/OOS and walk-forward.** Anchored walk-forward: initial training window 24 months, test window 6 months, step 6 months, re-fitting only the 5 parameters on the grid below each step. Purge: trades whose holding window crosses a fold boundary are dropped from training. Embargo: **28 days** between train end and test start (= 2x the 14-day max holding cap) so no funding-percentile lookback or open trade leaks across the boundary. Final reserved OOS: the most recent 12 months are never touched during any development iteration.

**Pass thresholds (all after costs, on concatenated OOS trades only):**
- Deflated Sharpe Ratio > 0 at 95% confidence, with trial count N from the multiple-testing accounting below.
- OOS profit factor >= 1.3 (floor chosen above 1.0 because the strategy's trade count will be low — tail-gated entries — and a thin PF on few trades is indistinguishable from luck).
- Minimum Track Record Length (Bailey-Lopez de Prado) at 95% confidence must be <= the available OOS sample length; if MinTRL exceeds the OOS window, verdict is "insufficient evidence", not "pass".
- >= 30 OOS trades total across both symbols; below that, no statistical claim is made and the strategy is shelved, not deployed.
- Edge must not be single-episode: removing the single best OOS calendar month must leave OOS PnL > 0. (Funding extremes cluster; this is the specific overfit channel here.)

**Monte Carlo.** 1,000 runs of (a) trade-order reshuffle of OOS trades and (b) entry-timing jitter: shift each entry decision by one full funding period (+/-8h, re-evaluating the signal — trades that vanish, vanish) plus execution jitter of +/-5 minutes on fill price using 1m bars. Fail if the actual OOS equity path breaches the 5th-percentile envelope of the jittered ensemble, or if the median jittered run is unprofitable (which would mean the edge lives in timing precision the 1-second bot cannot own).

**Multiple-testing accounting (shared batch-wide ledger).** This strategy's own grid: ENTRY_PCT{95, 96.5, 97.5, 99} x OI_Z_MIN{0.5, 1.0, 1.5, 2.0} x STOP_ATR_MULT{1.5, 2.5, 3.5} x EXIT_PCT{50, 65, 80, 90} = 192 combinations (RISK_FRAC excluded from the grid: it scales but does not reorder signal-level Sharpe), x 2 structural variants entertained (symmetric fade vs positive-funding-only) = **384 trials for FEF**.

The trial count fed to the DSR is **not** this number multiplied by a sibling count — that is a double-count error. There are **3** sibling strategies in this batch, and the correct shared ledger is the **sum** of the three declared grids, because the deploy decision searches across all of them: FEF 384 + Cascade Fade 162 + Coil-Break 320 = **866 nominal trials**. Adding a stated exploratory margin (iterations, range widenings) rounds the shared trial count to **N = 1,000**, cited identically in all three Section 5s and revised jointly whenever any sibling adds trials. This N feeds the DSR for FEF.

---

### 6. Live degradation triggers

- **Rolling PSR floor:** Probabilistic Sharpe Ratio (benchmark SR* = 0) computed over the trailing 40 closed trades or 6 months, whichever fills first. PSR < 0.50 → halve `RISK_FRAC`; PSR < 0.30 → halt new entries, manage exits only.
- **Drawdown vs Monte Carlo envelope:** live equity (marked daily, including open positions and accrued funding) breaching the 5th-percentile OOS Monte Carlo drawdown envelope at the equivalent trade count → full halt, no new entries, existing positions exit on their normal rules; restart requires a fresh validation pass on data including the drawdown period.
- **Funding-regime shift (edge-specific):** two-sample KS test, monthly, of the trailing 90d funding distribution vs the training-period distribution; p < 0.01 for 2 consecutive months → recalibrate percentile lookback and re-run validation before further entries. Separately: if the count of 8h periods per quarter with funding above the frozen training-era 97.5th-percentile level falls by more than half vs the training-era quarterly median → edge-compression flag, halve size (this is the ETF-arb decay channel made measurable).
- **Mechanism change:** Binance changes funding interval, clamp, or fee schedule on a traded symbol → immediate halt on that symbol pending respec (the `ok_mech` filter catches interval changes automatically).
- **Participation change:** 30d median perp volume or median OI on a traded symbol falls below 50% of its trailing 1y median → drop symbol from universe.
- **Spread-regime shift:** live spread filter (`<= 2.0 bps`) rejecting > 20% of attempted entries over a rolling 30 days → cost model is stale; halt and re-measure slippage assumptions from self-recorded L2.

Each trigger's action is automatic (bot-enforced); manual override requires writing down the reason before resizing, not after.

---

### 7. Failure modes

**Top 3 ways this is most likely a FALSE POSITIVE:**
1. **Episode concentration masquerading as edge.** Tail-gated entries mean OOS PnL is plausibly dominated by 2-3 unwind episodes (May 2021, LUNA, FTX). A backtest can pass every aggregate threshold while being a bet that specific historical cascades recur on schedule. Mitigation is the single-best-month excision test and the >=30-trade floor, but with honest eyes: the effective sample of independent episodes may be closer to 10 than to the nominal trade count.
2. **Percentile-threshold mining.** ENTRY_PCT/EXIT_PCT are exactly the kind of parameters that overfit smoothly — every value "works" on the episodes it was tuned around. The 192-point grid is declared and fed into the DSR, but DSR corrects for search breadth, not for the fact that all grid points share the same few episodes (correlated trials deflate less than independent ones — the correction is optimistic by construction).
3. **Look-ahead and alignment defects in the two non-price feeds.** (a) The signal uses the realized funding print for the interval *ending* at decision time t (fixed by the premium-TWAP up to t, so knowable at t and not look-ahead). The trap to avoid is keying the decision at t to the print stamped at t+8h (the interval *ending* at t+8h), which settles in the future — that would be look-ahead flattering exactly the extreme prints this strategy trades. The backtest must assert `funding_timestamp <= decision_timestamp` on every signal evaluation. (b) Aggregator OI history carries vendor-side timestamp lag; a 5-15 minute misalignment can convert post-cascade OI collapse into a phantom pre-entry crowding signal. Both require an explicit alignment audit against self-recorded live data before any pass verdict is trusted.

**Market-structure changes that kill it outright:** permanent funding-extreme compression as ETF/CME basis-arb capital scales (the tail simply stops occurring — strategy goes structurally flat, then dead); Binance moving BTC/ETH to shorter funding intervals or tighter clamps (respec required, historical percentiles void); exchange-level position or leverage caps on retail (removes the counterparty); regulatory exclusion of the operator from Binance and Bybit both (venue death); a funding-formula change decoupling funding from positioning imbalance.

**What the backtest cannot tell us (specific to these order types):** maker entry fill probability and adverse selection — the backtest conservatively assumes taker entries, but live maker fills during funding extremes are precisely the fills most likely to be adversely selected (filled because the move continued against us); stop-market slippage during liquidation cascades — stops fire at the worst liquidity moments this market produces, and 1m OHLCV cannot bound intra-bar sweep depth, so the 2 bps slippage assumption is a floor, not an expectation, on stop exits; partial fills near the exchange minimum-notional at the $5k end of the capital range; and queue position on the maker-first exit, where non-fill converts a 2 bps cost into a 7 bps cost plus 5 minutes of unwanted delta during normalization. Self-recorded L2 and liquidation streams, accumulated from day one of paper trading, are the only remedy — and they only measure the future, not the sample the pass verdict was earned on.


# Candidate 3 — Cascade Fade

# Cascade Fade — mean reversion after liquidation cascades (BTC/ETH USDT-M perps)

### 1. Edge hypothesis

**Inefficiency.** Transient price pressure from forced, non-informational order flow: when leveraged perp positions are liquidated in a cluster, the exchange's liquidation engine sends marketable orders that demand immediacy at any price. The resulting displacement contains a component unrelated to fundamental information, which partially reverts once the forced flow is exhausted. Anomaly class: **forced-flow anticipation / liquidity provision**, anchored in the fire-sale and price-pressure literature (Shleifer–Vishny fire sales; Coval–Stafford mutual-fund fire-sale reversals; flash-crash reversion studies, e.g. the 2010 equity flash crash post-mortems; Nagel's "Evaporating Liquidity" on short-horizon reversal as compensation for liquidity provision). The specific application to crypto perp liquidation cascades has supporting practitioner and academic evidence (liquidation-driven price impact and reversal on BTC perps) but the exact retrace magnitude/half-life on Binance USDT-M is **SPECULATIVE** until measured — the *existence* of pressure-then-reversal is the documented part; the *tradability net of costs at this size* is the hypothesis under test.

**Who is on the other side and why they lose.** The counterparty is the liquidated trader — mechanically, the exchange liquidation engine closing their position with orders that have zero price sensitivity and zero patience. This is the cleanest form of a systematically losing counterparty: they are not expressing a view; their order timing and direction are dictated by margin arithmetic, and clustering is mechanical (stop-out prices stack at round leverage levels, and each fill pushes price into the next tranche's bankruptcy price). Secondary losers: momentum-chasing retail who market-sell into the hole after the move has already happened.

**Why it survives at $5k–25k but not institutional size.** (a) **Capacity:** the edge is a few tens of bps captured on the passive side of a book that has been momentarily emptied; the profitable size is bounded by post-cascade depth, which is smallest exactly when the signal fires. A fund deploying $50M+ would move its own entry and destroy the retrace. (b) **Infrastructure economics:** professional liquidity providers *do* fade cascades, but they compete at microsecond latency on the first bounce; this strategy trades the slower, minutes-scale residual reversion after flow exhaustion, where 1-second latency is adequate and the dollar edge per event is hypothesized to be too small to fund an institutional desk (event frequency and per-event capacity are unvalidated — exactly what the backtest must measure — but the mechanism caps profitable size at post-cascade book depth, which is smallest precisely when the signal fires). (c) **Mandate:** institutions face venue/custody constraints on retail perp venues and cannot warehouse the tail risk of catching falling knives with meaningful AUM.

**Decay profile.** **Behavioral/structural hybrid, regime-dependent.** Needs: a leveraged retail participant base (nonzero open interest churn, periodic |funding| spikes) and episodic volatility that produces cascades. Killed by: (i) prolonged low-vol, low-leverage regimes (no events — starvation, not losses); (ii) HFT market-maker saturation that compresses the retrace below costs (structural decay — the liquidity-provision premium erodes as competition for it rises); (iii) exchange changes to the liquidation engine (auction-style liquidation, ADL changes) that eliminate the marketable-order fire-sale mechanism.

### 2. Full specification (Python pseudocode)

**Free parameters (exactly 5).** The verifier's honest recount (true count was 10) is accepted and the budget is re-drawn: the four highest-impact, least-anchored knobs — two entry gates and the two pieces of exit geometry — are the free params; the sizing fraction is the fifth (counted, but excluded from the optimization grid, matching both siblings); everything else is pre-registered frozen (next block).

| # | Param | Default | Range (a-priori) | Economic reason |
|---|---|---|---|---|
| 1 | `LIQ_MULT` | 1.0 | 0.5–2.0 | Cascade trigger scale: multiple of the trailing 30-day **frozen** 99th-percentile 5-min liquidation notional (`LIQ_REF_Q` folded in as a frozen tail definition, so this is one crowding knob, not two). Separates forced-flow clusters from background liquidation noise. |
| 2 | `DISP_Z` | 4.0 | 3.0–6.0 | Minimum price displacement (5-min return in units of 1-min EWMA vol × √5). Ensures the forced flow actually moved price enough that a partial retrace clears costs. |
| 3 | `RETRACE_FRAC` | 0.33 | 0.20–0.50 | Profit target as fraction of the cascade leg. Encodes the hypothesis that only part of the displacement is non-informational. |
| 4 | `STOP_EXT` | 0.25 | 0.15–0.50 | Stop distance: fraction of the cascade leg beyond the extreme at which the reversion hypothesis is declared void (fresh forced flow). A first-order tunable risk knob (the sibling FEF spends a slot on exactly this), now honestly counted. |
| 5 | `F_RISK` | 0.005 | 0.0025–0.010 | Fixed-fractional risk per trade to the stop. **Counted as a parameter but excluded from the optimization grid** (it scales P&L, it does not reorder signal Sharpe), identically to siblings FEF (`RISK_FRAC`) and Coil-Break (`F_RISK`). Replaces the earlier fractional-Kelly-on-live-stats sizing, which could not be both grid-searched and called "not fitted." |

All numbers below are **pre-registered frozen constants** — never varied, never sensitivity-analyzed; if any is ever changed, each value tried multiplies the batch trial ledger (§5) before the DSR is recomputed.

```python
# ---------- PRE-REGISTERED FROZEN CONSTANTS (never tuned, never sensitivity-analyzed) ----------
BAR = "1m"
VOL_SPAN = 1440           # 1-day EWMA of 1m log returns: baseline vol scale, standard daily window
LIQ_REF_WIN_D = 30        # trailing window for liquidation-notional reference quantile
LIQ_REF_Q = 0.99          # 99th pct of 5-min liq notional: FROZEN tail definition of "cascade-sized"
                          # flow; folded into the free param LIQ_MULT (one crowding knob, not two)
OI_DROP_MIN = 0.005       # 0.5% OI drop over 15m: FROZEN deleveraging-confirmation gate and the
                          # OHLCV+OI backtest proxy. Structural anchor: any positive OI drop confirms
                          # net position CLOSING; 0.5% is a de-minimis floor above feed noise, not a tuned edge.
EXHAUST_FRAC = 0.10       # FROZEN mechanism gate: enter only after the 1m liq bucket falls to <=10% of
                          # the cascade's peak 1m bucket. This is a definition of "forced flow is over"
                          # (fading DURING peak flow is knife-catching), pre-registered, not optimized.
DEPTH_MULT = 20           # L2 gate: passive-side depth within 25 bps must be >= 20x our order notional
DEPTH_BAND_BPS = 25
SPREAD_MAX_BPS = 2.0      # spread ceiling; matches the 2 bps slippage assumption. NOTE: the "normal"
                          # BTC/ETH spread level is an UNVERIFIED working assumption to be confirmed from
                          # self-recorded bookTicker before live sizing (no market data available here).
ENTRY_TTL_S = 300         # cancel unfilled entries 5 min after signal: edge decays in minutes
REPRICE_S = 60            # reprice post-only order every 60s while signal valid, max 3 times
MAX_REPRICE = 3
T_MAX_MIN = 120           # FROZEN time backstop (2h): the pressure-reversal half-life hypothesis. A
                          # judgment call, pre-registered so it cannot become a hidden sixth parameter.
COOLDOWN_MIN = 60         # FROZEN: no re-entry on a symbol for 60 min after a stop-out (don't re-fade a
                          # resuming trend). Structural anchor: ~1 reversal-half-life backstop.
MAX_CONCURRENT = 2        # BTC + ETH cascades are correlated; cap portfolio event exposure
MAX_LEV = 3.0             # constraint
RISK_FLOOR = 0.0025       # cold-start floor if F_RISK is ever set below it; also the deploy-day size

# ---------- state per symbol, updated each 1m bar ----------
sigma_1m = ewma_std(log_returns_1m, span=VOL_SPAN)
liq_1m_long, liq_1m_short = bucket_liq_ws_notional(side, window="1m")   # self-recorded WS feed
liq_5m_side = rolling_sum(liq_1m_side, 5)                               # side = side being LIQUIDATED
ref_liq = rolling_quantile(liq_5m_both_sides, q=LIQ_REF_Q, window_days=LIQ_REF_WIN_D)
oi_drop_15m = (oi[t - 15] - oi[t]) / oi[t - 15]                         # 5m OI series, ffilled to 1m
r_5m = log(close[t] / close[t - 5])
disp_z = r_5m / (sigma_1m * sqrt(5))

# ---------- signal ----------
def cascade_signal(t):
    # long-liquidation cascade -> price fell -> we BUY (mirror for shorts liquidated -> SELL)
    side_liq = "long" if disp_z <= -DISP_Z else ("short" if disp_z >= DISP_Z else None)
    if side_liq is None: return None
    if liq_5m[side_liq] < LIQ_MULT * ref_liq: return None
    if oi_drop_15m < OI_DROP_MIN: return None
    # flow exhaustion: current 1m liq bucket has collapsed vs cascade peak
    peak_1m = max(liq_1m[side_liq] over last 5 bars)
    if liq_1m[side_liq][t] > EXHAUST_FRAC * peak_1m: return None
    if not filters_pass(t): return None                      # section 3
    ref_price = close[t - 15]                                # pre-cascade reference (15m ago, matches OI window)
    extreme = min(low[t-5:t]) if side_liq == "long" else max(high[t-5:t])
    leg = abs(ref_price - extreme)
    return dict(direction=("buy" if side_liq == "long" else "sell"),
                extreme=extreme, leg=leg)

# ---------- entry (maker-first) ----------
def enter(sig):
    px = best_bid if sig.direction == "buy" else best_ask     # post-only at touch
    order = post_only_limit(sig.direction, px, size=position_size(sig))
    # reprice to new touch every REPRICE_S while cascade_signal still valid, max MAX_REPRICE times;
    # cancel at ENTRY_TTL_S; if a NEW cascade trigger fires beyond STOP_EXT extension, cancel (regime resumed)

# ---------- exits ----------
def manage(pos, sig):
    if pos.direction == "buy":
        target = pos.entry_px + RETRACE_FRAC * sig.leg        # resting maker limit
        stop   = sig.extreme - STOP_EXT * sig.leg             # taker stop-market on breach
    else:
        target = pos.entry_px - RETRACE_FRAC * sig.leg
        stop   = sig.extreme + STOP_EXT * sig.leg
    if breach(stop): exit_taker()                             # hypothesis falsified for this event
    if age(pos) >= T_MAX_MIN: exit_taker()                    # time stop; no trailing (retrace is one-shot,
                                                              # a trailing stop adds a parameter with no
                                                              # mechanism behind it)

# ---------- sizing: fixed-fractional risk (explicit Kelly alternative, matches siblings) ----------
def position_size(sig):
    # fractional Kelly needs edge/variance estimates we do not have pre-validation; plugging invented
    # numbers into Kelly launders fiction into a formula. Fixed-fractional risk is the conservative
    # substitute, replaceable by fractional Kelly POST-validation from OOS trade stats.
    stop_dist = abs(sig.entry_ref - (sig.extreme -/+ STOP_EXT * sig.leg)) / sig.entry_ref
    risk_frac = max(RISK_FLOOR, F_RISK)                       # F_RISK fixed a priori, not grid-searched
    notional  = (risk_frac * equity) / stop_dist
    return min(notional, MAX_LEV * equity, 25_000)            # leverage cap and stated capacity cap
```

### 3. Filters (code conditions, not prose)

```python
def filters_pass(t):
    return all([
        # liquidity floor (universe admission; BTC/ETH pass by construction)
        median_daily_quote_volume(symbol, 30) >= 1_000_000_000,   # $1B/day: top-10 perp scale
        # spread ceiling at signal time (self-recorded bookTicker)
        time_avg_spread_bps(last="5m") <= SPREAD_MAX_BPS,          # 2 bps; wider book = MM withdrawal, stale quotes
        # L2 depth gate (self-recorded depth snapshots; see §5 for history caveat)
        depth_notional(side=passive_side, band_bps=DEPTH_BAND_BPS) >= DEPTH_MULT * intended_notional,
        # volatility band: annualized EWMA 1m vol
        0.15 <= sigma_1m * sqrt(525600) <= 2.00,
        #   floor 15%: below it a 4-sigma leg is too small in bps to clear costs
        #   ceiling 200%: above it stop execution risk dominates (gaps through stop levels)
        # scheduled-event exclusion: static calendar, no entries in the window
        not within(event_calendar(["FOMC_statement", "US_CPI_release"]), minus_min=15, plus_min=45),
        # exchange operational state
        exchange_status == "normal",                                # no entries during reduce-only/maintenance
        # portfolio state
        open_positions_count() < MAX_CONCURRENT,
        minutes_since_last_stopout(symbol) >= COOLDOWN_MIN,
    ])
```

All thresholds above are hard-coded constants; none are tuned in validation (they are frozen before backtesting, and only the 5 parameters in §2 enter the search grid).

### 4. Cost sensitivity

- **Gross edge the hypothesis implies (hypothesis, not estimate):** the trigger requires a ≥4σ 5-min displacement while annualized 1m vol is ≥15%. Arithmetic on the trigger geometry only (no data, no win rate): at the vol floor, σ_1m ≈ 2.1 bps, so the minimum qualifying 5-min leg is ≈ 4 × √5 × 2.1 ≈ 19 bps, and the 15-min leg used for the target is larger; in the mid-range vol regimes where cascades actually occur, qualifying legs are geometrically in the 50–300 bps range. The **winner's** gross target is `RETRACE_FRAC = 1/3` of the leg ≈ **20–100 bps captured**; the **loser** is capped near `STOP_EXT` × leg + entry distance ≈ **tens of bps**. Deliberately **no net-expectancy number is stated**: combining a winner magnitude and a loser magnitude into a per-trade expectancy requires the win rate, which is prohibited to estimate and is exactly what the backtest exists to measure. The tradable claim is only that the per-winner gross magnitude sits well above round-trip cost; whether the hit rate makes expectancy positive is unknown until validated.
- **Round-trip cost at which the strategy is plausibly dead:** because the winner's gross is order 20–100 bps, once all-in RT cost approaches ~**20–25 bps** it consumes the low end of the *winner* magnitude before any losing trades are netted; treat ≥25 bps RT as presumptively fatal.
- **Cost accounting (per side, plus funding):** fees maker 2 / taker 5 bps; slippage 2 bps/side. Intended winner path = maker entry (2) + maker target exit (2) = **4 bps RT**; loser path = maker entry (2) + taker stop/time exit (5 + 2 slippage) = **9 bps RT**. **Funding line (was missing):** `T_MAX_MIN` ≤ 120 min and long entries follow long-liquidation cascades, which occur in high positive-funding regimes (see §6's own high-funding flag) — a hold that crosses an 8h funding timestamp pays funding *against* the position by construction. Worst case one 8h interval at an elevated regime rate (order 5–10 bps) is charged to the loser/time-stop path, taking it to ~**14–19 bps RT**. The pass/fail cost model in §5 therefore prices **all** fills at taker/taker (14 bps) **plus** bar-by-bar funding accrual at its realized sign.
- **Do stated costs leave margin?** **Yes, conditionally.** The winner's 20–100 bps gross sits above even the funding-loaded taker/taker RT; the low end (20 bps gross vs ~14–19 bps RT) is thin, so a strategy that only clears costs at the low leg-magnitude tail fails §5 regardless of statistical significance. If the edge survives only with maker fills (4–9 bps RT), that is a fill-rate assumption the backtest cannot verify (§7) and the strategy is graded on the taker/taker+funding model.

### 5. Validation protocol (pass/fail thresholds, no predicted metrics)

**Data-history honesty — what can be validated where.** The trigger has two implementations: (a) **live trigger** using the liquidation WS feed + L2 depth gate; (b) **proxy trigger** using only OHLCV + 5m OI (`disp_z` + `oi_drop_15m`), which is computable over multi-year history. Binance's liquidation WS has been throttled (order-of one message/sec/symbol since 2021), so even "full" liquidation history undercounts notional; aggregator/vendor history (Coinalyze, Tardis) is partial and possibly backfilled. Therefore: **backtest = proxy trigger, no depth gate, taker/taker costs** (validatable claims: existence/magnitude/half-life of post-cascade reversion, time-stop behavior, regime dependence). **Forward validation = ≥6 months of self-recorded WS liquidations + L2 depth**, measuring (i) proxy-vs-live trigger agreement — **fail if <70% of live triggers are matched by proxy triggers within ±5 min** (else the backtest tested a different strategy), and (ii) maker fill attainment on signals — recorded, and the cost model is switched to measured fill mix only after this period. Optionally buy 1–2 years of Tardis book/liq data to extend (b)-vs-(a) agreement testing backward; this refines but does not replace the proxy backtest.

- **Minimum data:** BTCUSDT + ETHUSDT, 1m OHLCV and 5m OI, **2020-01 → present**, spanning ≥4 distinct regimes: Mar-2020 COVID flush, Apr/May-2021 leverage flush, 2022 bear (LUNA, FTX), 2023–24 recovery, 2024–25 ETF era. Rationale: the edge is event-driven and regime-dependent; a sample missing both a leverage-flush regime and a low-vol regime cannot falsify starvation or knife-catching failure modes. **OI-source fallback:** exchange-native 5m OI does not reach back to 2020 on all symbols; where it is absent the backtest uses aggregator OI (Coinalyze/Tardis) **only after** a timestamp-alignment audit against the exchange-native period they overlap (fail the audit → drop that pre-native span rather than trust spliced data). The `oi_drop_15m` proxy is the sole OI dependency, so a bounded early-period gap degrades sample size, not signal validity.
- **Walk-forward:** IS 18 months / OOS 6 months, step 6 months, **rolling (fixed 18-month window, not anchored/expanding** — one scheme, stated unambiguously). **Purge 1 day, embargo 1 day** around each IS/OOS boundary — the actual max hold is `T_MAX_MIN` = 2h, so a 1-day purge/embargo is already ~12× the holding horizon and covers intraday feature overlap; the 30-day rolling liquidation-reference quantile is recomputed strictly from pre-boundary data so it cannot leak.
- **Pass thresholds (all on concatenated OOS, taker/taker 14 bps cost model):**
  - Deflated Sharpe Ratio > 0 at 95% confidence given trial count N below;
  - OOS profit factor ≥ 1.3 after costs;
  - ≥150 OOS trades total and ≥10 OOS trades in ≥3 of the named regimes (else verdict = "insufficient sample", not pass);
  - Minimum Track Record Length (at the observed OOS moments, benchmark SR = 0) must fit within the available OOS span; if MinTRL exceeds it, verdict = "unproven", not pass.
- **Monte Carlo:** 10,000 runs of (i) trade-order reshuffle and (ii) entry-timing jitter of **±1 bar (1 min)** with re-derived fills plus fill-price jitter uniform in [0, +3 bps] adverse. Fail if the realized OOS equity path breaches the 5th-percentile envelope at any point, or if the jittered-entry mean P&L falls below 50% of the unjittered mean (a signal that thin should not survive 1-second-latency execution).
- **Multiple-testing accounting (shared batch-wide ledger):** the gridded params are the **4** signal-shaping knobs only — `LIQ_MULT` × `DISP_Z` × `RETRACE_FRAC` × `STOP_EXT` at 3 values each = 81 (`F_RISK` is counted as a parameter but excluded from the grid, matching siblings) — × 2 execution variants (maker-first vs taker-only) = **162 trials for Cascade Fade.** The DSR trial count is **not** this figure times a sibling count (that double-counts). There are **3** sibling strategies; the shared ledger is the **sum** of the three declared grids — FEF 384 + Cascade 162 + Coil-Break 320 = **866 nominal**, rounded to **N = 1,000** with an exploratory margin, cited identically across all three Section 5s and revised jointly when any sibling adds trials. This N feeds the DSR for Cascade Fade. Any parameter-range widening increments the shared ledger before the DSR is recomputed.

### 6. Live degradation triggers

- **Rolling PSR floor:** PSR(SR*=0) over the last 60 closed trades; **< 0.60 → halve `F_RISK` sizing; < 0.40 → halt entries** until a full re-validation on data including the halt period passes.
- **Drawdown vs Monte Carlo envelope:** live equity (marked per closed trade) below the OOS Monte Carlo 5th-percentile envelope at the matching trade count → **halt entries**, run post-mortem; resume only if the cause is identified as execution (fixable) rather than edge decay.
- **Structural-break indicators (edge-specific, each measurable):**
  - *Participation/engine change:* 30-day count of live cascade triggers < 20% of the backtest-period per-30-day average across comparable vol regimes (vol-band-matched) → starvation or liquidation-engine change → **halt**. Any documented change to Binance's liquidation/ADL mechanism or liq-WS schema → **halt until re-mapped**.
  - *Spread regime shift:* 30-day median spread > 2× trailing-180-day median → maker economics changed → **force taker-only cost model in sizing; if that model's expectancy per §4 goes ≤0, halt**.
  - *Funding regime shift:* 30-day mean |funding| > the 90th percentile of full-history 30-day mean |funding| → **halve size** (cascades in one-sided funding regimes continue rather than revert more often, per the stop-out clustering mechanism). The trigger is the single quantified condition; no qualitative descriptor is attached to it.
  - *Retrace-half-life drift:* rolling median time-to-target of the last 30 winners > 2× the backtest OOS median → the reversal is slowing (competition gone or mechanism changed) → **halve size, flag for re-validation**.
- Every halt is automatic (bot flat + no new entries); manual restart requires a written cause analysis.

### 7. Failure modes

**Top 3 ways this is most likely a FALSE POSITIVE:**
1. **Event-count illusion / regime luck:** cascades are rare and P&L is concentrated in a handful of flush episodes (May-2021, LUNA, FTX). A DSR computed on ~150–300 trades where 10 events carry the expectancy is fragile; the per-regime trade-count floor in §5 mitigates but does not eliminate this. If the 2022 events are removed and the edge vanishes, it was a bet on one regime.
2. **Proxy-trigger look-ahead and data artifacts:** 5m OI timestamps from aggregators may be end-of-interval stamped at start (silent 5-min look-ahead that flatters a minutes-scale signal); backfilled liquidation history from vendors may be survivorship-cleaned. The backtest must use exchange-native OI with verified timestamp convention, and any vendor liq data is used for agreement testing only, never for the tested trigger.
3. **Fill fantasy at the extreme:** the backtest marks maker fills at the touch after exhaustion; in reality passive bids near a cascade low fill preferentially when the cascade *continues through them* (adverse selection) and miss when the bounce is real (non-fill). The taker/taker cost model in §5 partially immunizes the pass decision, but the *maker-based* live economics remain unverified until the forward-recorded period — a strategy that only passes with assumed maker fills is unproven, not validated.

**Market-structure changes that kill it outright:** Binance moving to auction/RFQ-style liquidations or materially expanding insurance-fund internalization (no marketable fire-sale flow reaches the book); liquidation feed discontinued (live trigger degraded to the proxy, which was never live-validated); sub-second HFT liquidity provision compressing the residual retrace below 10 bps; migration of leveraged retail to venues/instruments outside the universe (event starvation); fee-tier or rebate changes that flip the maker/taker economics in §4.

**What the backtest cannot tell us (specific to these order types):** post-only queue position at the touch after a cascade (fills modeled as certain are actually probabilistic and adversely selected); market impact of our own stop-market exits into a just-thinned book (2 bps slippage is a normal-book number; post-cascade taker slippage on stops is strictly worse and unmeasured); partial fills on the resting target limit leaving residual inventory at the time stop; the depth gate's true pass rate at signal times (no historical L2 → the gate's selectivity is unknown until ≥6 months of self-recorded book data exist); and latency interaction — whether the 1-second decision loop systematically arrives after faster faders have already taken the touch, leaving only the toxic remainder.


---

# Final ranking

Ranked by **(edge durability × implementability at $5k–25k) ÷ implementation complexity**. This ranks *which to test first for a trustworthy pass/fail signal* — it is not a claim about which will ultimately be most profitable.

| Rank | Strategy | Edge durability | Implementability at my size | Complexity | Why here |
|---|---|---|---|---|---|
| **1** | **Coil-Break** (vol-compression momentum) | Med–High — TSMOM is the most literature-backed of the three; behavioral decay is slow, not a sharp structural break | **High** — signal is fully computable on multi-year *free* data (OHLCV + funding + 5m OI); daily cadence; taker execution has ~zero impact at ≤$25k | **Low** — daily breakout + chandelier trail; no maker-timing, no self-recorded-data dependency for the signal | Best (durability × implementability) ÷ complexity. Cleanest, most trustworthy backtest. **Binding risk is validation, not implementation:** low trade count may trip the MinTRL / 60-trade floor. |
| **2** | **Funding-Extreme Fade** (carry / crowded-positioning) | Med — behavioral driver (retail overpaying for leverage) is persistent, but the funding *tail* is structurally compressing as ETF/CME basis-arb capital scales (a monitored decay channel) | **High** — signal fully backtestable on full-history funding + OI + OHLCV; no L2/liquidation history needed | **Medium** — funding-sign exit logic, two-feed percentile tracking with alignment audits, maker-first execution | Strong second. The most attractive *per-trade economics* (funding receipt is a realized cash flow), but rarer episodes and an eroding tail pull durability below Coil-Break. |
| **3** | **Cascade Fade** (liquidation reversion) | Med — forced-flow reversion is well-documented, but HFT liquidity provision compresses the residual, and it depends on the liquidation mechanism staying marketable | **Med–Low** — the *tradable* trigger needs self-recorded liquidation WS + L2 depth; only a **proxy** is backtestable on history, so a backtest pass does not validate the deployed strategy without 6+ months of forward recording | **High** — fastest horizon, most execution-sensitive (queue position, adverse selection, stop slippage into a thinned book), proxy-vs-live agreement testing | Best counterparty story in the batch (a mechanically price-insensitive forced loser), but the least trustworthy backtest and the highest execution risk. Test **last**, and only after forward L2/liq data exists. |

**Recommendation: test Coil-Break first.** Not because it has the strongest edge — the funding fade arguably has cleaner per-trade economics and the cascade fade has the cleanest counterparty — but because it is the only candidate whose *entire* signal is computable on multi-year free data with no self-recorded-data dependency, so its pass/fail verdict is the most trustworthy per unit of effort. Its one serious weakness (structurally low trade count) is known upfront and handled honestly by the MinTRL gate and the hard ≥60-OOS-trade floor: if the sample can't support a conclusion, the protocol returns "insufficient evidence," not a false pass. Run FEF second (also fully backtestable, better per-trade edge, watch the eroding tail); run Cascade last, after you have recorded enough live L2/liquidation data to validate the real trigger rather than a proxy.

---

# Portfolio-level rules (these three are NOT independent — the verifier flagged this)

Deploying more than one of these simultaneously requires an overlay, because the edges and their evidence overlap:

1. **FEF and Cascade Fade monetize the same flush episodes.** Funding extremes precede and accompany liquidation cascades; both strategies fade the same crowd in the same direction during the same handful of events (May-2021, LUNA, FTX — the exact episodes both name as concentration risk). Their OOS evidence is correlated and their live P&L will be correlated. **Rule:** treat them as one "flush-fade" sleeve — at most one may hold a position in a given symbol during the same cascade window, and the shared DSR ledger already counts their trials jointly. Do not double-count their combined backtest as two independent confirmations.
2. **Coil-Break and Cascade Fade can fire on the same symbol in opposite directions** (a breakout that turns into a cascade). **Rule:** positions net at the account level, and the **3× leverage cap is a single portfolio budget across all bots**, not 3× per strategy. A portfolio governor enforces total gross notional ≤ 3× equity and reconciles opposing signals (net, don't gross up).
3. **Shared blind spots correlate false-positive risk across the batch.** All three lean on the same aggregator-spliced 5m OI history (one vendor timestamp defect fails all three), validate on the *same* regime list (so "spans ≥2 regimes" is one sample cited three times, not three independent samples), and inherit the same 2 bps spread/slippage assumption pending live L2. **Rule:** a batch-wide pass is *less* independent than three separate passes — weight it accordingly, cross-check OI against a second source, and treat regime luck as a joint failure mode.

---

# Strategy-independent, reusable components

Build these **once**; all three strategies (and Phase 2/3) share them:

- **Cost model** — fee schedule (maker/taker), slippage assumption, and a **funding-accrual engine that charges funding bar-by-bar at its realized sign**. Identical across all three (same venue, same constants). The single most reused component.
- **Risk daemon / sizing** — fixed-fractional risk-to-stop, per-position leverage cap, and the **portfolio leverage governor** (rule 2 above). Identical formula across all three; only the per-trade risk fraction differs (and each is a counted, grid-excluded parameter).
- **Degradation monitor** — rolling Probabilistic Sharpe Ratio floor with tiered de-risk/halt actions, and the drawdown-vs-Monte-Carlo-envelope halt. Identical framework; only the *edge-specific structural-break indicators* (funding-regime KS test, cascade-frequency starvation, compression-distribution shift) are swapped per strategy.
- **Validation harness** — walk-forward with purge/embargo, Deflated Sharpe Ratio against the **shared trial ledger (N ≈ 1,000)**, Probabilistic Sharpe and Minimum Track Record Length, and the Monte Carlo reshuffle + entry-timing-jitter engine. Identical methodology; only window sizes and the trade-count floors differ.
- **Data-integrity layer** — the OI timestamp-alignment audit and the `funding_timestamp ≤ decision_timestamp` look-ahead assertion. A shared hazard, so a shared tool.

The cost model, the risk daemon, and the degradation monitor are the three the brief calls out — and all three are genuinely strategy-independent here.

---

# Follow-up phases (awaiting your go-ahead — not produced now)

- **Phase 2** — full backtest implementation of the chosen candidate (recommended: **Coil-Break**): vectorized where possible, event-driven where path-dependence (trailing stop, funding accrual) demands it; costs and slippage per the constraints above; DSR / PSR / MinTRL reported on out-of-sample data against the shared N.
- **Phase 3** — live-ops spec: shadow/paper parity harness, execution checklist, monitoring dashboard, and operator-discipline rules (skip conditions, halt-after-N-losses, no manual overrides mid-session).

Tell me which candidate to take into Phase 2 — my recommendation is Coil-Break first, FEF second — and I'll build it.
