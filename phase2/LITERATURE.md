# Literature Review: Delta-Neutral Crypto Perpetual-Futures Cash-and-Carry (Funding Harvest)

*Compiled 2026-07-24. Every citation below was checked against a primary or authoritative secondary source (journal page, NBER/SSRN/arXiv landing, or publisher record). Where a venue, page range, or issue could not be pinned down with confidence, this is stated explicitly. Nothing here is invented; where the crypto-specific evidence is thin or non-peer-reviewed, that is flagged.*

---

## 1. Carry as an Asset-Pricing Factor

The strategy harvests a *carry* — income earned for holding a position when prices are unchanged. This connects directly to a mature asset-pricing literature.

- **Koijen, R. S. J., Moskowitz, T. J., Pedersen, L. H., & Vrugt, E. B. (2018). "Carry." *Journal of Financial Economics*, 127(2), 197–225.** (DOI: 10.1016/j.jfineco.2017.11.002; NBER WP 19325, 2013.) — The anchor reference. Defines carry model-free as the return if prices do not move, and shows it predicts returns both cross-sectionally and in time series across equities, bonds, commodities, currencies, and options. Directly generalizes the concept our strategy exploits to a new asset (crypto perps).

- **Fama, E. F. (1984). "Forward and Spot Exchange Rates." *Journal of Monetary Economics*, 14(3), 319–338.** — Origin of the "forward premium puzzle": interest-rate differentials predict currency returns in the "wrong" direction for UIP, i.e. carry is compensated. Note the venue is *JME*, not *JFE* — the "Fama-French" label is often loosely attached; the FX-carry root is this Fama (1984) regression, distinct from the Fama-French (1993, *JFE*) equity three-factor model.

- **Lustig, H., Roussanov, N., & Verdelhan, A. (2011). "Common Risk Factors in Currency Markets." *Review of Financial Studies*, 24(11), 3731–3777.** (NBER WP 14082.) — Builds the HML-FX / "slope" factor for currency carry and ties carry returns to a global-volatility/risk factor. Relevance: establishes carry as *risk-compensated* rather than free money, which is the honest framing for any funding-harvest pitch.

*Honest note:* This literature is equities/FX/commodities. It gives the theoretical scaffolding (carry is a priced, crash-exposed factor) but says nothing crypto-specific — that is Section 2.

---

## 2. Crypto-Specific Perpetual Funding and the Cash-and-Carry Basis

This is the area most relevant to the mechanics of the strategy, and also where **peer-reviewed work is genuinely thin** — the strongest pieces are recent working papers, a few now reaching journals.

- **Schmeling, M., Schrimpf, A., & Todorov, K. "Crypto Carry."** Circulated as **BIS Working Paper No. 1087 (2023, rev. 2025)** and **CEPR DP 20719**; SSRN 4268371. **Forthcoming/published in *Management Science* (2024/2025; DOI 10.1287/mnsc.2024.05069).** — The single most directly relevant paper. Documents crypto carry (futures–spot / funding) reaching >40% p.a., and traces it to (i) leverage demand from smaller trend-chasing investors and (ii) limited arbitrage capital due to margin/regulatory frictions. Uses the CME micro-contract and spot-ETF launch as natural experiments (carry compressed after each). This is the empirical backbone for "who pays funding" and "funding as a leverage-demand premium." *Caveat:* verify the final *Management Science* volume/pages before formal citation — the journal record was in the "online first" stage at time of search.

- **He, S., Manela, A., Ross, O., & von Wachter, V. (2022). "Fundamentals of Perpetual Futures." arXiv:2212.06888; SSRN 4301150.** — Working paper (not yet peer-reviewed at time of search). Derives no-arbitrage bounds linking the funding rate to the perp–spot gap and to expected spot returns, with BTC empirics across exchanges (Jan 2020–Dec 2022), including the FTX-collapse episode of large negative funding. Relevance: theoretical justification that funding ≈ basis and is arbitrageable, plus a caution that funding can invert sharply in stress.

- **Ackerer, D., Hugonnier, J., & Jermann, U. "Perpetual Futures Pricing."** NBER WP 32936; **forthcoming *Mathematical Finance* (2026; DOI 10.1111/mafi.70018).** — Formal continuous-time pricing of the perpetual contract and its funding mechanism. Relevance: the most rigorous pricing treatment; useful for modeling funding as the state variable we harvest. *Caveat:* the *Mathematical Finance* record shows a 2026 online date — treat as forthcoming.

- **Makarov, I., & Schoar, A. (2020). "Trading and Arbitrage in Cryptocurrency Markets." *Journal of Financial Economics*, 135(2), 293–319.** — Peer-reviewed. Not about perps per se, but documents persistent cross-exchange/cross-country price deviations and the capital-control and market-segmentation frictions that let arbitrage spreads persist. Relevance: explains structurally *why* the basis/funding premium is not immediately competed away — the limits-of-arbitrage story specialized to crypto.

*Honest note:* Beyond Makarov-Schoar, most of this section is working-paper or just-published material, and much practitioner knowledge (exchange funding formulas, clamp mechanics, retail-long skew) lives in exchange docs and blogs rather than refereed journals. A claim like "retail systematically pays funding" is *supported* by Schmeling-Schrimpf-Todorov's leverage-demand evidence but should be presented as an empirically-motivated hypothesis, not settled theory.

---

## 3. Backtest-Overfitting and Sharpe-Statistics Methodology

These are the tools we rely on to keep the funding-harvest backtest honest. This literature is mature and well-cited.

- **Bailey, D. H., & López de Prado, M. (2012). "The Sharpe Ratio Efficient Frontier." *Journal of Risk*, 15(2), 3–44.** — Introduces the **Probabilistic Sharpe Ratio (PSR)**: the probability that a track record's true SR exceeds a benchmark, correcting for track-record length, skew, and kurtosis. Relevance: our reported SR is short-sample and non-normal (funding harvest has fat left tails) — PSR is the right significance statistic. *Caveat:* the exact issue/pages of the *Journal of Risk* version I could not fully re-verify; the SSRN version is authoritative.

- **Bailey, D. H., & López de Prado, M. (2014). "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality." *Journal of Portfolio Management*, 40(5), 94–107 (SSRN 2460551).** — **DSR** deflates the observed SR for the *number of trials* tried (multiple-testing selection bias). Relevance: essential given we sweep parameters (funding thresholds, rebalance frequency, universe) — DSR is the headline number to report, not the naive SR.

- **Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2014). "Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance." *Notices of the American Mathematical Society*, 61(5), 458–471.** — Shows how few trials are needed to manufacture a spuriously high in-sample SR, and that overfit strategies can have *negative* OOS returns. Relevance: the conceptual warning that motivates our whole validation protocol.

- **Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2017). "The Probability of Backtest Overfitting." *Journal of Computational Finance*, 20(4), 39–69 (SSRN 2326253).** — Formalizes **PBO** via **Combinatorially Symmetric Cross-Validation (CSCV)**: estimates the probability the in-sample-best config underperforms the median OOS. Relevance: this is the specific overfitting metric we run on the parameter sweep.

- **López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley.** — Source for **purged k-fold cross-validation** and the **embargo** (Ch. 7), which remove look-ahead leakage from overlapping/serially-correlated labels — exactly the failure mode in funding time series. Also popularizes CPCV. Relevance: our train/test splitting protocol.

- **Lo, A. W. (2002). "The Statistics of Sharpe Ratios." *Financial Analysts Journal*, 58(4), 36–52.** — Asymptotic distribution of the SR under IID and under serial correlation; shows autocorrelation can inflate annualized SR by ~65%. Relevance: funding-harvest returns are highly autocorrelated (smooth funding accrual punctuated by jumps) — Lo's correction is needed before annualizing or comparing SRs.

- **Politis, D. N., & Romano, J. P. (1994). "The Stationary Bootstrap." *Journal of the American Statistical Association*, 89(428), 1303–1313.** — Block bootstrap with random (geometric) block lengths preserving weak dependence and stationarity. Relevance: the appropriate resampling scheme for confidence intervals on SR/drawdown of a serially-dependent funding-return series.

*Honest note:* This methodology is asset-class-agnostic and solid, but it does not *rescue* a thin-sample crypto backtest — crypto perps have only ~2017–present of usable, regime-shifting data (multiple hacks, FTX, an ETF launch). Even a strong DSR/PBO should be read against that short, non-stationary sample.

---

## 4. Market-Neutral / Carry-Crash Risk ("Picking Pennies in Front of a Steamroller")

A delta-neutral funding harvest is *not* riskless: it carries basis-blowout, deleveraging, exchange-solvency, and liquidation risk. The relevant literature is limits-of-arbitrage and carry-crash.

- **Shleifer, A., & Vishny, R. W. (1997). "The Limits of Arbitrage." *Journal of Finance*, 52(1), 35–55.** — Arbitrage requires capital and is risky; adverse price moves can force *arbitrageurs* to liquidate at the worst time (performance-based capital withdrawal). Relevance: our carry trade can be right on fundamentals yet be margin-called out before convergence — the core structural risk.

- **Brunnermeier, M. K., & Pedersen, L. H. (2009). "Market Liquidity and Funding Liquidity." *Review of Financial Studies*, 22(6), 2201–2238.** (NBER WP 12939.) — Models liquidity spirals: margins rise as volatility rises, forcing deleveraging that further impairs liquidity. Relevance: describes exactly the crypto-cascade mechanism (rising vol → higher exchange margin → forced unwind → basis dislocation) that turns a benign carry into a tail loss.

- **Brunnermeier, M. K., Nagel, S., & Pedersen, L. H. (2009). "Carry Trades and Currency Crashes." *NBER Macroeconomics Annual 2008*, 23, 313–347.** (NBER WP 14473.) — Empirically, carry returns are negatively skewed: "go up by the stairs, down by the elevator." Unwinds cluster when funding liquidity dries up. Relevance: the canonical "pennies in front of a steamroller" evidence; the crypto funding harvest should be expected to inherit this negative-skew/crash profile.

- *(Supporting, mechanism-specific)* **Makarov & Schoar (2020)** (cited in §2) and **Shleifer, A., & Vishny, R. W. (1992). "Liquidation Values and Debt Capacity: A Market Equilibrium Approach." *Journal of Finance*, 47(4), 1343–1366** — the fire-sale foundation (asset-specific buyers are constrained exactly when sellers must sell). Relevance to a leveraged, cross-exchange carry book facing forced liquidation into a thin market.

*Honest note:* The carry-crash evidence is FX/equity; there is (to my knowledge at time of search) **no peer-reviewed paper cleanly documenting the skewness of a crypto perp funding-harvest strategy after realistic costs, liquidation, and exchange-counterparty risk.** The FX analogy is strong but is an *analogy*. FTX (Nov 2022) is the obvious reminder that crypto adds a counterparty/venue-failure tail absent from the FX literature.

---

## Summary of Honesty Caveats

- **Strongest, peer-reviewed:** the carry factor (§1), the overfitting/Sharpe statistics toolkit (§3), and the crash-risk/limits-of-arbitrage theory (§4). These are mature and citable with confidence.
- **Thinnest:** crypto-specific perpetual-funding economics (§2). The best work (Schmeling-Schrimpf-Todorov *Crypto Carry*; He et al.; Ackerer et al.) is recent and partly still working-paper or "forthcoming"; verify final venue/pages before formal citation. Makarov-Schoar (2020, *JFE*) is the one firmly peer-reviewed crypto-arbitrage anchor.
- **Not fabricated, but flagged for double-check:** exact issue/pages for the PSR (*Journal of Risk* 2012) and DSR (*JPM* 2014) papers, and the final published venue of *Crypto Carry* and *Perpetual Futures Pricing*. SSRN/NBER/arXiv IDs given are reliable.
- **Data-honesty:** the crypto sample is short (~2017–present) and regime-shifting; no statistical toolkit converts that into a long, stationary track record. Present funding harvest as a *risk-compensated, negatively-skewed carry trade with venue/counterparty tail risk*, not as an arbitrage.