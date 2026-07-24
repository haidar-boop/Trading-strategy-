# Data-Gated Roadmap — Crypto Cash-and-Carry Review Items

*Scope: what each data type beyond free Binance klines/funding/OI would add, where to get it, cost/feasibility, historical depth, and integration difficulty. Assessed for a retail cash-and-carry (basis/funding-harvest) book at ~$10k notional. Prices verified July 2026 via web search; treat exact numbers as directional — vendor tiers change.*

---

## 1. Order-book depth / L2 imbalance — reviews #1, #15

**What it adds.** Real execution-cost modeling instead of a flat fee/slippage assumption. Lets you (a) size legs against actual top-of-book depth so backtested basis P&L isn't overstated, (b) build an L2 imbalance signal (bid/ask depth ratio) that leads short-horizon price and can time leg entry, and (c) detect thin-book regimes where the carry unwind would be expensive. This is the single biggest source of backtest overstatement for a two-leg spread trade.

**Sources.**
- **Tardis.dev** — incremental L2 book updates + snapshots (top 25 / top 5) for Binance, Bybit, OKX, Deribit. The canonical historical L2 source.
- **Kaiko / Amberdata** — institutional-grade L2, order-by-order in some products. Enterprise pricing, effectively out of retail range.
- **Self-recording via WebSocket** — subscribe to Binance `@depth` diff stream, persist to Parquet. Free but **forward-only** (you get data from the day you start, no history).

**Cost / feasibility.** Tardis subscription ~$50–$900/mo depending on symbol/venue/depth breadth; the useful multi-venue L2 tier sits in the mid-hundreds. Self-recording is $0 in fees but costs a always-on VPS (~$5–20/mo) plus storage — L2 diffs are large (GBs/day for a handful of symbols).

**Historical depth.** Tardis: deep history (Deribit back to 2019; major perps multiple years). Self-recording: **none** — starts at t=0.

**Integration difficulty.** **High.** Reconstructing a book from incremental updates (sequence-number gap handling, snapshot resync) is fiddly and easy to get subtly wrong. Storage and query engineering is real work. This is the highest-effort item on the list.

---

## 2. Liquidations feed — review #15

**What it adds.** A stress/regime flag. Liquidation cascades are exactly when basis blows out and funding spikes — a live liq-intensity signal helps you (a) avoid entering a leg into a cascade, (b) opportunistically *harvest* the funding spike a cascade creates, and (c) size a stop/risk overlay. As a carry-timing input it's a "when is funding about to spike/mean-revert" predictor.

**Sources.**
- **Binance liquidation WS stream** (`@forceOrder`) — free and live, but **officially throttled**: Binance emits at most one liquidation event per symbol per second, so during a cascade you see a *sampled* fraction of true liquidations. Aggregate totals are undercounted.
- **Coinglass / Coinalyze** — cross-exchange aggregated liquidations (30+ venues) and a modeled liquidation *heatmap* (inferred position clusters, not raw fills).
- **Tardis.dev** — historical `liquidations` channel per venue.

**Historical completeness caveats.** Because of the exchange-side throttle, *no* provider has truly complete tick-level liquidation history — Coinglass, Tardis, and self-recorded streams all inherit the same sampled feed. Treat liquidation *magnitudes* as a relative index, not an exact dollar total. The heatmap is a model, not measured data.

**Cost / feasibility.** Binance WS: free. Coinglass API: no free tier — ~$79/mo (Startup) for strategy dev, ~$299/mo (Standard) for commercial use / deeper history. Tardis: bundled in subscription.

**Integration difficulty.** **Low–medium.** The WS stream is a trivial subscribe-and-log. Coinglass is a plain REST pull. The hard part is interpretation, not plumbing.

---

## 3. Options IV / skew / gamma — review #15

**What it adds.** The most information-rich *new* signal for a funding-carry trade, and cheap to obtain.
- **Skew (25-delta put/call) as a funding predictor** — put skew reflects demand for downside hedges; it co-moves with and often leads perp funding/basis stress. A skew term is a genuinely orthogonal feature to your existing funding/OI panel.
- **DVOL / IV level** — forward vol regime; high IV ≈ wider basis and higher unwind risk.
- **Dealer gamma positioning** — when dealers are short gamma, spot pins/whips harder near large strikes, which bleeds into perp basis behavior around expiries and around the monthly/quarterly roll.

**Sources.**
- **Deribit public API** — free, live, no key required for market data (order book, mark IV, DVOL index). Dominant BTC/ETH options venue, so it *is* the market.
- **Deribit historical CSVs** — first-of-each-month files downloadable free without an API key, back to 2019-03-30 (good enough for monthly-resolution research).
- **Tardis.dev** — `markprice.options` IV stream since 2019-10-01, full continuous history (paid, but Deribit has a partnership giving some free historical access).
- **Amberdata** — polished derivatives/IV analytics and DVOL endpoints back to April 2019 (enterprise pricing).

**Cost / feasibility.** Live signal is **free** (Deribit public API). Continuous history is free-ish (first-of-month CSVs) or paid via Tardis for tick history. Amberdata is out of retail budget.

**Historical depth.** Excellent — 2019→present via Deribit/Tardis.

**Integration difficulty.** **Medium.** Live pull is easy; the work is computing a clean skew/term-structure surface (delta bucketing, interpolation) from the option chain. Gamma-exposure estimation is more involved and lower-priority for a $10k book.

---

## 4. ETF flows — review #15

**What it adds.** A slow macro-demand overlay. Sustained positive spot-ETF inflows correlate with persistent positive funding (structural long demand you're getting paid to provide via the short-perp leg); heavy outflows precede funding normalization/inversion. Useful as a *regime tilt* on how aggressively to run the carry, not as an entry trigger.

**Sources.**
- **Farside Investors** — `farside.co.uk/btc/` and `/bitcoin-etf-flow-all-data/`, free web tables, per-issuer daily flows, history from Jan 2024 (BTC; ETH and SOL also covered). Scrape-friendly HTML. An unofficial Parse.bot API wraps it (paid) but scraping the table directly is free.
- **Issuer disclosures** — authoritative but scattered across fund websites; only worth it for reconciliation.
- **Bloomberg** — gold standard, irrelevant at retail cost.

**Cost / feasibility.** **Free** via Farside scrape.

**Historical depth / granularity.** **Daily only**, from Jan 2024 (spot ETFs didn't exist before). This is inherently a low-frequency, ~2-year series — fine as a slow overlay, useless for intraday and too short to be statistically strong on its own.

**Integration difficulty.** **Low.** One daily HTML scrape + parse. The main risk is layout changes breaking the scraper.

---

## 5. Stablecoin issuance / on-chain flows / whale transfers — reviews #12, #15

**What it adds.** A liquidity/demand backdrop. Net stablecoin *issuance* (USDT/USDC supply expansion) is dry powder entering the system and loosely leads risk-on funding regimes; large exchange-inflow whale transfers can precede volatility. For a carry trade this is a *second-order regime tilt*, weaker and noisier than options skew or funding itself.

**Sources.**
- **Artemis** — stablecoin supply, transfer volume, active addresses, chain breakdown. **Free tier covers most of this**; Pro ~$588/yr.
- **Glassnode** — stablecoin supply + exchange net-flow metrics; Free tier exists but meaningful metrics/resolution/alerting sit behind tiers up to ~$999/mo.
- **Nansen** — smart-money wallet / whale tracking; strong but subscription-priced and aimed at token trading, not basis.
- **Chain RPC (self-serve)** — read stablecoin contract `Transfer` events / `totalSupply` directly via a free public RPC or a free-tier node provider. Zero data cost, all engineering cost.

**Cost / feasibility.** Free path exists (Artemis free tier for aggregate supply; raw RPC for issuance). Nansen and upper Glassnode tiers are not justified at $10k.

**Historical depth.** Deep (multi-year) on Glassnode/Artemis; RPC gives full chain history but you must backfill it yourself.

**Integration difficulty.** Artemis free tier: **low** (dashboard/CSV). Raw RPC decoding of transfers + whale labeling: **high**. For this book, take the aggregate stablecoin-supply series only and skip whale-level tracking.

---

## 6. Cross-exchange data — review #7

**What it adds.** Directly enables the review-#7 idea: a **multi-venue funding panel** (Binance vs Bybit vs OKX vs Deribit perps) to (a) route each carry leg to the venue paying the best funding, (b) run cross-venue funding-dispersion as a signal, and (c) sanity-check that a Binance-only funding series isn't idiosyncratic. High relevance-to-effort for a carry strategy specifically.

**Do the public dumps exist? Yes.**
- **Bybit** — `public.bybit.com` free bulk CSV dumps, no registration, spot + USDT/inverse perps; primarily **tick trade** files. Funding history is available via the Bybit v5 REST API (`/v5/market/funding/history`).
- **OKX** — official historical-data page provides trades, candles, order book, and **funding-rate** history; also a REST funding-history endpoint. Community tools (`okx-dump`, crypto-crawler downloaders) automate it.
- **Deribit** — free public API for perp funding + options; first-of-month historical CSVs.
- **CoinAPI** (fallback) — unified historical funding across Binance/Bybit/OKX back to ~2021 (paid) if you want one clean panel without per-venue plumbing.

**Cost / feasibility.** **Free** via each exchange's public dumps/APIs. Rate limits are the only friction; a nightly batch job stays well within them.

**Historical depth.** Multi-year funding history on all three major perp venues via their APIs.

**Integration difficulty.** **Medium.** No single format — each venue has its own schema, timestamp convention, and funding-interval quirk (8h standard but some symbols differ), so the work is a per-venue adapter layer normalizing into one funding panel. Once built, it's the highest-value free upgrade for review #7.

---

## 7. CVD / trade tape — review #15 — **THIS ONE IS FREE**

**What it adds.** Cumulative Volume Delta (signed aggressor flow) as an order-flow signal: divergence between price and CVD flags exhaustion/absorption and helps time leg entries; aggressive-flow bursts front-run funding pressure. A genuinely useful microstructure feature at zero data cost.

**Source.** **`data.binance.vision`** — `aggTrades` dumps **exist free** for both spot and USDⓈ-M / COIN-M **futures**, daily and monthly CSV/ZIP, no key, multi-year history. `aggTrades` includes the `isBuyerMaker` flag, which is all you need to sign each trade and build CVD. (Bybit/OKX trade dumps from item #6 give the same for other venues.)

**Cost / feasibility.** **$0.** This is the clearest win on the list — the data is already sitting in the same free Binance archive you're using for klines.

**Historical depth.** Deep — years, matching kline coverage.

**Integration difficulty.** **Low.** Download ZIPs, sign by `isBuyerMaker`, cumulative-sum into CVD, resample. A day of work. It slots directly into your existing Binance-archive ingestion.

---

## Prioritized Recommendation

### Build these 2–3 first — most edge per unit of integration effort

1. **CVD / trade tape (#7 above, review #15) — do it now.** Free, already in the Binance archive you ingest, one day of work, and it adds a real microstructure signal plus better fill-timing. Zero reason not to. **Effort: low. Cost: $0.**

2. **Multi-venue funding panel (#6, review #7) — highest strategic fit.** Free from Bybit/OKX/Deribit public dumps + APIs. Directly answers "which venue do I run the carry on and is Binance funding representative," which is the core lever of a cash-and-carry book. **Effort: medium (per-venue adapters). Cost: $0.**

3. **Deribit options skew/IV (#3, review #15) — best *new* signal.** Free live via Deribit's public API, free-ish history via first-of-month CSVs. Skew is orthogonal to your funding/OI features and is a credible funding-stress leading indicator. Take skew + DVOL first; defer dealer-gamma. **Effort: medium (surface construction). Cost: ~$0.**

*Honorable mention, near-free:* **Farside ETF flows (#4)** and **Artemis stablecoin supply (#5, free tier)** — both are cheap daily scrapes that give a slow macro regime tilt. Add them as low-priority overlays once the top 3 are in; neither is strong enough to prioritize over the above.

### Not worth it at $10k retail size

- **Historical L2 depth via Tardis / Kaiko / Amberdata (#1)** — mid-hundreds to enterprise pricing and the single hardest integration (book reconstruction). At $10k notional your fills barely move top-of-book; a calibrated flat slippage/fee haircut in the backtest captures 90% of the value. Revisit only if you scale to size where depth genuinely constrains execution. **Self-recording L2** is free but forward-only and high-effort — skip unless/until you commit to a long recording horizon.
- **Coinglass Standard ($299/mo) and paid Glassnode/Nansen tiers (#2, #5)** — the free Binance liquidation stream and Artemis/Glassnode free tiers already give you the regime flags; the paid uplift (heatmaps, smart-money labels) doesn't convert to enough carry edge to justify recurring cost at this size.
- **Amberdata / Kaiko / Bloomberg anywhere they appear** — institutional pricing, not retail-rational.
- **Whale-level / labeled on-chain tracking (#5)** — high engineering cost (RPC decoding + labeling) for a weak, noisy second-order signal. Take only the aggregate stablecoin-supply series from Artemis's free tier.

**Bottom line:** every high-value upgrade for this strategy is either already free (CVD, cross-venue funding) or near-free (Deribit skew, ETF/stablecoin overlays). The paid feeds mostly buy execution-microstructure and entity-level detail that a $10k carry book cannot monetize. Spend the effort budget on integration, not subscriptions.