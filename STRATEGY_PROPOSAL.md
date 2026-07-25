# Charging-Lien Leakage

## Queue-rationed trustee capacity as an exogenous, unpriced determinant of realised recovery

---

## 1. Strategy name

**Charging-Lien Leakage (CLL).**

Full descriptive name: *Queue-rationed indenture-trustee capacity as an exogenous, unpriced determinant of realised recovery on defaulted corporate debt.*

The document has been restructured following adversarial review. The single largest change is that the **latency term has been split into two economically distinct objects**, only one of which is tradable:

- **CLL-F** — the *baseline* fee component (`F₀ / SeriesSize`), retained as a covariate, **not** as the thesis. Conceded prior art (LoPucki & Doherty), relabelled to series level.
- **CLL-Q** — the **congestion-driven fee *quantum*** component: queue-rationed trustee capacity causes *more billed trustee and trustee's-counsel work to be charged against a given series under the charging lien*. This is a **cash deduction**, not a discount factor. It survives at `r = 0`. **This is the thesis and the sole source of claimed originality as a position.**
- **CLL-D** — the **float/discounting** component (`R · (1 − e^{−rL})`): the time value of the distribution queue. **This is withdrawn from the traded estimand.** Written as a position it is long a claim settling at T1 and short an economically identical claim on the same estate settling at T2 > T1, collecting the interest between them. That is a calendar / delivery-date basis position and it is carry. It is on the permanently-closed list and it is not traded. It is deliberately **hedged to zero** (Section 8.1) and retained only as an input to the forecasting product (Section 14.5).

Why the split is a repair and not a retreat: the mechanism — queue-rationed capacity at a shared administrative intermediary, congested by *unrelated issuers' defaults* — is unchanged. What changed is which of its two consequences is monetised. Congestion does two things: it makes cash arrive later (a financing payoff, banned) and it makes the workout cost more per series (a cash payoff, tradable). The document now trades only the second.

The strategy trades a **cross-sectional structure in realised cash**, not a level view on distressed credit. Its central object is not a claim's economic terms — not seniority, not collateral, not coupon — but **the claim's position in a rationing queue whose congestion is determined by other people's bankruptcies**.

**Bottom line, stated at the top because the arithmetic in Sections 7, 9 and 11 now says so:** on the parameters this document is willing to defend, the *position* has negative expected value at the stated transaction and borrow costs, and the honest primary deliverable is the forecasting product in Section 14.5. The position specification below is retained in full, but as a **conditional** that is reinstated only if the pre-registered magnitude gate (Test 1C) returns a wedge materially larger than the one assumed here.

---

## 2. Economic thesis

### 2.1 The object

A corporate bond is not a claim on an issuer. It is a claim **routed through a fixed administrative chain**: indenture trustee → paying agent → DTC → DTC participant → beneficial holder. Cash reaches the holder only by traversing every node, in order, with no bypass.

The first node — the indenture trustee — holds a **contractual charging lien**: a first-priority claim on all distributions payable to holders of that series, covering the trustee's own compensation and its counsel's fees, and **senior to the holders it nominally serves**. It is not a claim against the estate. It is a **toll levied at the terminal node, after every number the pricing apparatus measures has already been fixed**.

Realised cash to a holder is:

```
RealisedCash  =  ModelledRecovery  −  F(Cong)/SeriesSize  −  r × Latency
                                      └── traded (CLL-F + CLL-Q) ──┘   └─ NOT traded (CLL-D) ─┘
```

where `F(Cong)` is the per-indenture fee net of any successful holder objection — **and is itself increasing in the trustee's queue congestion**, which is the thesis — and `Latency` is the elapsed time from plan effective date to actual receipt of cash.

**The critical structural point about `F(Cong)`.** Trustee and trustee's-counsel compensation in a workout is time-and-materials, not a fixed retainer: hourly billing for status reporting, holder communications, claim reconciliation, distribution mechanics, court appearances and fee-application defence. A congested workout desk does not do *less* work per series; it does *more*, because congestion produces re-work, duplicated status reporting, longer engagement of outside counsel per unit of distribution, additional interim fee applications, and a longer period over which the engagement bills at all. The queue therefore converts into **billed dollars charged against the series under the charging lien**, not merely into a later payment date.

This is the mechanism by which the congestion story produces a payoff that does not vanish when the short rate does.

### 2.2 Why the edge exists — the rationing argument

The *baseline* fee component (`F₀/SeriesSize`) is **largely prior art** at the estate level (LoPucki & Doherty 2011; Warner 1977; Ang-Chua-McConnell 1982; Weiss 1990). It is retained only as a covariate. **The thesis rests on the congestion sensitivity of the fee quantum — `∂F/∂Cong` — and specifically on why it cannot be competed away.**

A corporate trustee's workout function is a small number of named workout officers plus a panel of outside counsel. That capacity is:

1. **Inelastically supplied in the short run.** A trustee cannot hire and train a restructuring workout officer inside the horizon of a single Chapter 11 case. Panel counsel capacity is similarly fixed within a 12–24 month window.
2. **Shared across all of that trustee's concurrently defaulted mandates**, which are unrelated estates with unrelated issuers.
3. **Legally barred from clearing by price.** This is the load-bearing point. The trustee *cannot* charge a congestion premium to move a series to the front of the distribution queue, because:
   - (a) its fees are set by the indenture and constrained by *ex post* reasonableness review, not by scarcity;
   - (b) the charging lien is capped in practice by court supervision and by holder objection;
   - (c) holders have **no legal mechanism to bid for queue priority** — there is no market in distribution sequence, no auction, no side payment that a court would sanction.

A resource that is inelastically supplied, allocated by queue, and legally prevented from clearing at a price **must** produce a congestion externality. Because the price channel is closed, the externality cannot show up as a higher unit fee; it shows up as **more units of billed work per series and a later date** — the first is cash and is traded, the second is float and is not.

That cost is imposed on you by issuers you have never analysed and could not have analysed.

### 2.3 Who pays

**Correction to the naive answer.** Index funds and insurance general accounts hold every index-eligible CUSIP unconditionally and cannot select on chain topology (trustee identity is not a field in any index vendor's or terminal's security master). But **they are ejected by mandate at or shortly after default, before the toll is levied.** They are therefore *harmed at issuance* but are **not** the marginal price-setter at trade entry. Asserting otherwise was the single largest defect in the original formulation and is withdrawn.

The marginal price-setter once a name is in default is the **distressed specialist and the ad hoc group**. They pay their own counsel. They *do* model the estate's professional-fee waterfall, because estate-level administrative expense is a public, docketed, estate-wide number.

The narrow, falsifiable informational claim on which the entire wedge now rests has been **narrowed further** in response to the Moody's-URD objection (Section 4.6):

> Distressed specialists, and the historical recovery datasets they calibrate to, produce recovery estimates at **class level**. They therefore embed the **population-average and estate-average toll** by construction. What they do not and structurally cannot produce is a **within-class, series-level** toll estimate, because that requires (a) a prospectus-derived trustee-identity map at CUSIP level and (b) a cross-case panel of each trustee's concurrent mandate load. Neither exists as a field anywhere.

The value is captured by **the trustee and disproportionately by the trustee's counsel**, neither of whom is a market participant.

### 2.4 Why they cannot stop

Every constraint is contractual, statutory, or capacity-based — none is behavioural.

- The charging lien cannot be renegotiated *ex post* without the trustee's consent.
- Removing a trustee mid-workout requires a holder majority **plus** a willing successor **plus** court process — unattainable for a dispersed, index-held series.
- The trustee will not act without indemnity, which requires organising holders who are structurally hard to organise.
- Distributions must legally pass through the trustee and paying agent. **There is no path around the node.**
- Trustee workout capacity is fixed in the short run and cannot be cleared by price; queue position is not purchasable at any price.

### 2.5 Why professional firms have not arbitraged it

No agent holds both the information and the incentive:

| Agent | Holds information? | Bears cost? | Can act? |
|---|---|---|---|
| Underwriter / issuer's counsel (selects trustee) | Yes | **No** — zero default-state cost; new-issue spread does not move 1bp on trustee identity | Yes but no reason to |
| Index funds / insurance GAs (bear cost at issuance) | **No** — trustee identity not in security master | Yes, but exit before default resolution | **No** — mandate forbids selection |
| Trustee + trustee's counsel (capture value) | Yes | No | **Not a market participant** |
| Distressed specialist (sets price at entry) | Estate/class-level yes; **series-level and cross-case congestion, no** | Yes | Yes — if they had the map |
| Rating agencies / recovery vendors | Define recovery at plan effectiveness, at **class** level — upstream of, and averaged across, the toll | No | Cannot redefine without destroying multi-decade series comparability |

The congestion component is uniquely **unknowable from the issuer's own file**, however deep the diligence. That is why deep single-name work does not surface it.

### 2.6 What risk is compensated

**Legal-process variance, not enterprise variance.** Specifically:

- The risk that a plan converts the charging lien into an estate-paid administrative expense (mutualisation).
- The risk that an ad hoc group wins §503(b)(5) substantial-contribution status and shifts the burden.
- The risk that a prepack converts to free-fall and the queue lengthens unpredictably.
- The risk that a successful fee objection collapses the toll.
- The illiquidity of holding matched distressed positions through emergence.
- **Short-leg financing and corporate-action risk** through plan effectiveness (Section 6.5) — which, on the arithmetic in Section 9.4, is larger than the wedge.

Explicitly **not** compensated, because explicitly not taken: the float/discounting differential between the two legs' settlement dates. That is hedged out (Section 8.1).

### 2.7 Why it survives for years

No regulator is closing it. There has been **no SEC concept release, no Trust Indenture Act rulemaking, and no exchange consultation** on trustee compensation or charging-lien transparency since the Trust Indenture Reform Act of 1990. TIA §316(b) litigation (*Marblegate*) concerns payment rights, not the toll.

This cuts both ways and must be stated honestly: **the mechanism is old and openly tolerated, which means any wedge that were large and easy would already have been arbitraged by the distressed community.** The defensible position is that the wedge is *small, structured, and unmeasured* — not that it is large. Sections 9 and 11 now show that "small" is small enough to be below the cost of trading it.

---

## 3. Market structure explanation

### 3.1 The chain, node by node

| Node | Governing instrument | Clause that creates the toll or the queue |
|---|---|---|
| Indenture trustee | Trust indenture, qualified under Trust Indenture Act of 1939 (15 U.S.C. §§77aaa–77bbbb) | Standard Article VII compensation-and-indemnity section: trustee has a **lien prior to the Securities** on all money or property held for payment, to secure compensation, expenses, disbursements and advances, **including counsel fees**. This is the charging lien, and it is time-and-materials, which is why congestion enters it as **quantum**. |
| Paying agent | Same indenture / separate paying agency agreement | Distributions must be made through the paying agent; funds held in non-interest-passing deposit accounts, so **holders bear the time value of the queue** and the float accrues to the paying-agent bank. **This is the CLL-D channel and it is not traded** — trading it is trading a float differential, which is carry. |
| DTC | DTC Operational Arrangements; Rules & Procedures | Distributions to beneficial holders flow only via DTC participant positions; the trustee is the sole authorised source of a distribution instruction on the CUSIP. Also the mechanism by which a shorted CUSIP is cancelled at effectiveness — see Section 6.5. |
| Participant / prime broker | Customer agreements | Sub-allocation; adds days, not the mechanism. Determines whether a short can be carried through a plan corporate action at all. |

### 3.2 The statutory mutualisation channels — the thing that can kill the traded components

These are the routes by which the toll is shifted from holders to the estate. Because the traded estimand is now **entirely a fee-quantum object**, mutualisation zeroes *all* of it — which is what makes the disbursing-agent control in Test 2A a genuine off-switch rather than a partial one. Their base rate is the **go/no-go gate** in Section 15.

- **11 U.S.C. §503(b)(5)** — indenture trustee substantial-contribution administrative expense. Estate-borne.
- **11 U.S.C. §506(b)** — an **oversecured** creditor's contractual fees, costs and reasonable attorneys' fees are added to the secured claim. Estate-borne. **This applies precisely to the oversecured secured-notes population.** Note that oversecurity is a *valuation ruling*, not a document fact — see U3 in Section 5.1.
- **Plan-negotiated administrative expense** — standard modern plan boilerplate reads approximately: *"Indenture Trustee Fees shall be paid in Cash by the Debtors on the Effective Date … and upon such payment the Indenture Trustee shall be deemed to have released its Charging Lien."* Practitioner sources describe this as having *become standard practice.*
- **Plan-appointed disbursing agent whose fees are an estate-paid administrative expense.** This is the mechanism's **natural off-switch** for the traded components: it mutualises the fee quantum while leaving every fundamental, seniority, collateral, liquidity and holder-composition variable unchanged. It does **not** switch off the queue — cash still arrives on some date through some intermediary — which is precisely why Test 2 has been split (Section 15).

### 3.3 The documented quantum of the toll

The evidentiary record is real, docketed, and — awkwardly for the thesis — consists of cases where organised holders **objected and won**:

- **Nortel** — trustee asserted ~$8.1m; plan capped estate payment at $4.25m; court permitted recovery **above the cap** against noteholder distributions via the charging lien. This is the "capped with lien preserved above cap" form.
- **Tribune Media** — $29,790,038.61 asserted; $3m allowed. A ~90% reduction.

Both are *level* observations. Neither speaks to the **congestion sensitivity** of the quantum, which is the thesis and which no published source measures.

### 3.4 Participants who matter

**Trustees:** BNY Mellon, Computershare/Wilmington Trust, UMB Bank, Citibank N.A., Deutsche Bank Trust Company Americas, GLAS. Six names carry the overwhelming majority of large US corporate indentures. This concentration is what makes a congestion panel tractable — and what makes trustee mandate share correlated with market segment, and makes trustee congestion close to (market share × aggregate default volume), which is a serious threat to identification and is why the placebo horse race in Section 15 Test 1A is now mandatory.

**Venues for the resulting position:** OTC distressed bonds (TRACE-disseminated for registered and 144A-with-registration-rights issues), bankruptcy trade claims, and matched-tenor OIS/interest-rate swaps (hedge only). **Single-name CDS and CDX are no longer used** — see Section 9.1.

### 3.5 The adjacent market where the identical toll *is* priced

Trustee and paying-agent fees sit at the **top of every ABS/CMBS/CLO waterfall**, are disclosed in Form 424H shelf prospectuses, and are modelled line-by-line by standard cashflow engines (Intex). This supports the persistence story — the market internalises the terminal-node toll **whenever it appears in a machine-readable field** — but it confirms that the *concept* is not novel. Only its absence from the corporate cross-section is.

---

## 4. Mathematical intuition

### 4.1 Notation

For estate `i`, series `s`, held to plan effectiveness:

- `R_i` — modelled recovery on the class, as a fraction of allowed claim, at plan effectiveness. Produced by rating agencies, recovery vendors and distressed models **at class level**.
- `N_{i,s}` — allowed claim amount of series `s` (dollars).
- `F_{i,s}` — indenture trustee fees + trustee's counsel fees charged against series `s` distributions, net of successful objection (dollars). Decomposed as `F_{i,s} = F₀_{i,s} + φ · Cong_{k,t}` — a baseline per-indenture cost plus a congestion-driven increment.
- `L_{i,s}` — latency in years: days from plan effective date to **first holder distribution**, /365. Forecast, reported, and used in the data product; **not** an input to the traded payoff.
- `r_t` — risk-free short rate at effective date (OIS, matched tenor). Enters only the hedge.
- `m_{i,s} ∈ {0,1}` — mutualisation indicator: 1 if plan treatment of *that series'* trustee fees is estate-paid admin expense / §503(b)(5) / §506(b) add-on / disbursing agent; 0 if the charging lien is preserved and exercised (categories (d) and (e) in Section 15). **Defined at series level, not estate level.**
- `Cong_{k,t}` — congestion at trustee `k` at time `t`. **Primary measure is a flow, not a stock:** aggregate allowed claim value of **new large Chapter 11 mandate arrivals** at trustee `k` in the trailing 12 months, **leave-one-out** (excluding estate `i`). The stock measure (concurrently active mandates) is retained as a robustness check only. The switch to arrivals is what makes the instrument simultaneously T-0 observable and immune to the reverse-causality channel (Section 4.5.4).
- `P_{i,s}` — market price of series `s` at trade entry, per 100 of claim.

### 4.2 Estimand

The **traded per-claim toll**, in points of claim:

```
τ_{i,s}  =  100 · (1 − m_{i,s}) · [ F₀_{i,s} + φ · Cong_{k,t} ] / N_{i,s}
            └──── CLL-F (covariate) ────┘   └──── CLL-Q (thesis) ────┘
```

Note that `(1 − m)` multiplies **both** terms, because both are fee quantum. This is a change from the previous draft, in which the mutualisation indicator multiplied only the fee term while the latency term ran free — an inconsistency that made the stated off-switch false on the document's own equation.

The **untraded** component, retained for the forecasting product and hedged to zero in any position:

```
τ^D_{i,s}  =  100 · R_i · ( 1 − e^{−r_t · L_{i,s}} )
```

`τ^D` is a discount factor. A long/short in `τ^D` between two claims on the same estate is a delivery-date basis position and is not taken.

The **wedge** is the estimand of interest, and it is defined on the *within-estate deviation*, because that is what is traded (Section 4.6):

```
τ̃_{i,s}  =  τ_{i,s}  −  ( Σ_{s'∈i} N_{i,s'} τ_{i,s'} ) / ( Σ_{s'∈i} N_{i,s'} )

W_{i,s}  =  ( P_{i,s} − P̄_i )  −  E[ − τ̃_{i,s} | Ω_entry ]
```

i.e. the *relative* price of a series within its estate, minus the *relative* net-of-toll cash it will actually deliver. The claim is `E[W] > 0` for above-average-`τ̃` series and `< 0` for below-average, and — critically — that `∂(P − P̄)/∂τ̃ ≈ 0` in the within-estate cross-section.

Defining the wedge on the deviation rather than the level is not cosmetic. It is what makes Section 4.6's signing argument apply to the object that is actually traded, and it is what allows estate fixed effects to absorb `R_i` in the price regression (Section 4.3, Stage 3).

### 4.3 Estimator

**Stage 1 — the congestion regression on the fee quantum (this is the publish-or-kill gate).**

```
100 · F_{i,s} / N_{i,s}  =  α  +  β_Q · Cong_{k(i,s),t_i}^{(−i)}  +  γ' X_{i,s}  +  δ_k  +  θ_year  +  ε_{i,s}
```

run **with estate fixed effects wherever two or more series in the same estate are observed**, which is the specification the strategy actually trades.

Controls `X_{i,s}`, **all of which must be observable at T-0** (this is a correction; the previous control list contained terminal, case-lifetime quantities and was a look-ahead — see Section 4.7):

- log allowed claim value of estate; log allowed claim of the series
- number of distinct classes; number of distinct indentures
- prepack/prearranged/free-fall indicator
- **elapsed days from petition date to T-0** (replaces "case duration to effective date")
- **docket entries filed to date** and **contested matters filed to date** (replace "number of contested matters", which was a case-lifetime total)
- DIP facility maturity date and milestone schedule, as the market's own T-0 forecast of case length
- aggregate US speculative-grade default rate in month t
- court-district docket load in month t
- issuer SIC sector

`δ_k` = trustee fixed effect. Inference: **wild cluster bootstrap-t with clustering at the trustee level**, plus randomisation-inference p-values from permuting the congestion series across trustees (Section 4.8).

**Mandatory placebo horse race.** `Cong` at the case's **claims agent** (Kroll / Epiq / Stretto / Verita) and at its **debtor-counsel firm** and its **financial advisor**, each constructed identically and leave-one-out, are entered **simultaneously** with trustee congestion. The mechanism survives only if `β_Q` on trustee congestion retains its magnitude and significance in the joint specification. This is required because the shared-bottleneck rival predicts the same coefficient from a different causal node — one that is not mapped at CUSIP level and is not tradable via the trustee-identity map.

**Stage 1B — the latency regression (data product only, not a deployment gate).**

```
L_{i,s}  =  α_L  +  β_L · Cong_{k,t_i}^{(−i)}  +  γ' X_{i,s}  +  δ_k  +  θ_year  +  ε^L_{i,s}
```

Same controls, same inference. Reported as a **reduced-form latency result**. No cash-magnitude claim is attached to it and no position is derived from it.

**Stage 2 — the cash regression, within estate.**

```
ΔNetCash_{i,s,s'} / N  =  a  +  b_Q · Δ(Fitted fee quantum)  +  c · ΔIndentureCount  +  u
```

taken in **differences between pari passu series of the same estate**, so that `R_i`, enterprise value, plan structure, class treatment and the credit cycle are differenced out. Prediction: `b_Q ≈ −1` — a dollar of charged fee is a dollar of lost cash. This is a cash-accounting identity and is the least contestable claim in the document.

The previous draft ran Stage 2 as an across-estate 2SLS with `Cong` instrumenting for `L`, and predicted `b ≈ −R·r`. **That specification is withdrawn.** Its exclusion restriction was never stated on the second-stage error, and it is not defensible: congestion is driven by the credit cycle, the credit cycle moves realised recovery directly, and `R` was not among the Stage-2 controls, so congestion had an open channel to net cash that did not run through latency (Section 4.4).

**Stage 3 — the price regression (does price embed the within-estate deviation?).**

```
(P_{i,s} − P̄_i)  =  a'  +  b' · τ̃^⊥_{i,s}  +  φ · ΔLiquidity_{i,s}  +  ψ · ΔSeriesSize  +  η_i  +  v_{i,s}
```

with **estate fixed effects `η_i`** and with the regressor **`τ̃^⊥` = the within-estate toll deviation orthogonalised against `R̂_i` and against `R̂_i · r_t · L̂`** before entry.

This is a substantive correction. The previous specification regressed the *level* of price on the *level* of `τ̂` without `R` among the controls, while `τ̂` was mechanically proportional to `R̂` by construction. Under the null that price fully embeds the toll (`P = 100R − τ`), that regression returns `Cov(P,τ) = 100·Cov(R,τ) − Var(τ)`; with `sd(R) ≈ 0.3` across distressed names the first term is an order of magnitude larger than the second and drives `b̂'` positive, i.e. into or above the stated pass band regardless of the truth. The test could not reject its own null.

Two independent fixes are applied and both are required: (i) estate fixed effects, which absorb `R_i` entirely, since the legs are pari passu with identical collateral, guarantors and §506(b) status and therefore share `R`; and (ii) explicit orthogonalisation of the regressor against `R̂` and against the float term, so that any residual series-level recovery variation cannot load on `τ̃`.

Interpretation on the **residualised, within-estate** specification:
- `b' = 0` — price ignores the within-estate toll deviation; tradable wedge is `τ̃`.
- `b' = −1` — price fully embeds it; real but untradable.
- `b' ∈ (−1, 0)` — partial embedding; tradable wedge is `(1 + b')·τ̃`.
- **`b' > 0.1`** — price is *higher* for higher-toll series. Under the residualised within-estate specification this cannot be produced by the recovery channel, so it indicates either a remaining omitted variable correlated with both (hold-up rent and odd-lot liquidity are the two candidates) or that `τ̃` is measured with error correlated with price. **This is a specification failure, not a trading signal.** Branch: re-specify, do not trade. If it survives re-specification, the toll model is wrong.

### 4.4 Identifying assumption

Two distinct restrictions are required and were previously conflated. The document states both.

**IA-1 (Stage 1, reduced form).** Conditional on `X_{i,s}`, `δ_k` and `θ_year`, the defaulting behaviour of trustee `k`'s **other** clients is uncorrelated with the determinants of estate `i`'s own charged fee quantum:

```
Cov( Cong_{k,t}^{(−i)} , ε_{i,s} | X, δ_k, θ_year )  =  0
```

**IA-2 (the exclusion restriction, which the previous draft never stated).** For any two-stage use of `Cong`, the requirement is on the **second-stage** error `u`:

```
Cov( Cong_{k,t}^{(−i)} , u_{i,s} | X )  =  0
```

i.e. congestion affects net cash **only** through the trustee-side channel and not through any other route.

**IA-2 is not defensible across estates and the document does not claim it.** Credit cycles congest trustees and simultaneously move realised recovery; recovery is not among the second-stage controls and cannot be, because it is the outcome variable's dominant component. That is why (i) the across-estate 2SLS has been withdrawn, (ii) Stage 1B is presented as reduced form only, and (iii) Stage 2 is run **within estate in differences**, where `R_i` and the cycle are differenced out and IA-2 reduces to the far weaker requirement that congestion at trustee `k` is uncorrelated with the *within-estate, cross-series* determinants of net cash other than fees. That is the only version of the exclusion restriction this document is prepared to defend.

The exogeneity comes from a hard structural fact: *your trustee's other clients defaulted for reasons that have nothing to do with your issuer.* That property is real and is the design's central identification device. It is **not**, however, a property that no rival can reproduce — see Section 4.5.5 and Test 1A's placebo horse race.

### 4.5 What would violate identification

Stated plainly, ranked by seriousness:

1. **Common credit-cycle shock.** A recession congests trustees, court districts, restructuring counsel and financial advisors *simultaneously*. Mitigated by the aggregate-default-rate and district-docket-load controls, by year fixed effects, and by the within-estate differencing in Stage 2, but **cannot be fully separated** from economy-wide professional scarcity. This is the primary threat and it is not fully solved.
2. **Trustee specialisation.** If trustee `k` concentrates in a sector, its clients default together *and* that sector has structurally slower and costlier plans. Mitigated by `δ_k` + sector controls; residual risk remains because trustee mandate share is correlated with market segment and hence with issuer type.
3. **Selection at issuance.** If issuers with higher default probability systematically choose particular trustees, `Cong` is correlated with issuer quality. Testable: regress trustee choice at issuance on issuer credit metrics; the prior (Amihud, Garbade & Kahan 1999) is that selection is driven by underwriter convenience and fee quotes, not by issuer credit.
4. **Reverse causality.** Slow, expensive estates keep a trustee "active" longer, mechanically inflating a *stock* measure of congestion. **Fixed by using new-mandate arrivals in the trailing 12 months as the primary measure**, leave-one-out. Arrivals at trustee `k` cannot be inflated by the duration of estate `i`'s own case. This replaces the previous fix — measuring the stock *at the effective date* — which was incompatible with a T-0 tradable signal (Section 4.7) and has been abandoned.
5. **Shared non-trustee bottleneck.** Large cases at the same trustee are disproportionately administered by the same claims agents, the same restructuring counsel and the same financial advisors. Congestion at any of those nodes slows and inflates distributions and is mechanically correlated with the trustee's mandate load. **This rival predicts the same coefficient sign and magnitude as CLL while implying a different causal node — one that is not mapped at CUSIP level and not tradable via the trustee-identity map.** It is addressed only by the placebo horse race in Test 1A, and until that horse race is run the attribution is unresolved. The previous draft's claim that "no competing explanation can pass Test 1" was false and has been deleted throughout.
6. **Default clustering / market share.** Because six trustees carry most large indentures, `Cong_{k,t}` ≈ trustee-k market share × aggregate default volume. Year fixed effects reduce but do not eliminate this, because market share is time-varying and segment-correlated. Partially addressed by standardising congestion within trustee (Section 5.2) and by the randomisation-inference test that permutes congestion across trustees within year.

### 4.6 Why the wedge is *signed* — and why the signing argument applies to the deviation, not the level

This was the weakest joint in the previous draft and it has been rebuilt. The previous version signed a **level** and traded a **deviation**. A claim-weighted demeaned variable sums to zero by construction, so a one-sided-omitted-variable argument about the level does not survive the demeaning. The argument below signs the deviation directly.

**Step 1 — concede the level.** `F ≥ 0` always, so `E[RealisedCash] ≤ ModelledRecovery` as a cash identity. But the *level* of the toll is **not** a tradable pricing error, because history-calibrated recovery datasets embed it mechanically. Moody's URD pairs **price at default with settlement value at resolution** — settlement value is realised, net-of-toll cash. Any recovery model fitted to that history therefore has the **average toll baked into its intercept**. The level is priced. **The claim that price is systematically too high in the level is withdrawn as a trading claim** and retained only as a statement about the cash identity.

**Step 2 — the calibration is at class level, and that is the whole trade.** Recovery vendors, rating-agency recovery ratings and distressed models produce estimates for a **class** — "senior secured notes of estate i" — not for individual CUSIPs within that class. Where a class contains multiple pari passu series under distinct indentures, the calibrated model assigns them **the same** net-of-toll recovery. It does so not by oversight but by construction: the historical settlement values it was fitted to are themselves reported at class level, and the input that would distinguish the series (trustee identity, and that trustee's queue) is not a field in any security master.

**Step 3 — therefore the pricing error equals the deviation, with the right sign on both sides.** Let `τ̄_i` be the estate/class-average toll and `τ_{i,s}` the series-specific toll. The calibrated model prices every series in the class at `100·R_i − τ̄_i`. Realised cash is `100·R_i − τ_{i,s}`. The error is exactly:

```
Price_{i,s} − RealisedCash_{i,s}  =  τ_{i,s} − τ̄_i  =  τ̃_{i,s}
```

which is **positive for the above-average series and negative for the below-average series**, with a slope of exactly +1 in the deviation. The pricing error is not merely nonzero on the deviation; it is *monotone in the deviation with a known coefficient*. That is precisely what a within-estate long/short needs, and it is a stronger statement than the level argument it replaces, because it does not require the price-setter to be ignorant of the toll — only to be ignorant of its **within-class dispersion**.

**Step 4 — what this now requires, which is falsifiable.** The argument rests on an empirical proposition about the *granularity* of other people's models, not their existence: **no commercially available recovery estimate is produced at series level within a pari passu class.** This is directly checkable and Test 8 has been extended to check it. If any vendor produces series-level, as opposed to class-level, net-of-toll recovery estimates, Step 2 fails and the deviation is priced along with the level.

**The honest qualifier, unchanged in force:** the *cash* wedge is a cash-accounting identity and is not contestable. The *price* wedge requires `b' > −1` in the residualised, within-estate Stage 3 — i.e. that relative price within an estate does not already embed the relative toll. That is contestable, and it is the subject of Test 5.

### 4.7 The look-ahead problem, stated and fixed

The previous draft fixed the decision point at T-0 (disclosure statement or plan supplement docketed) and then computed the signal from inputs that do not exist at T-0. Three specific violations, all now fixed:

1. **"Case duration to effective date"** appeared in the Stage-1 control list. The effective date has not occurred at T-0. **Replaced** by elapsed days from petition to T-0, docket entries to date, and the DIP milestone schedule.
2. **"Number of contested matters"** scaled the fee forecast. That is a case-lifetime total, terminal and unobservable at T-0. **Replaced** by contested matters *filed to date*.
3. **Congestion timing.** Test 1's hypothesis measured congestion **at the effective date** (to fix reverse causality), while the deployed signal evaluated it at trade entry, 12–36 months earlier. The coefficient was therefore estimated on one regressor and deployed on another. **Fixed by switching the congestion measure to trailing-12-month new-mandate arrivals**, which is (a) observable at T-0, (b) immune to reverse causality from the subject case's own duration, and therefore (c) usable with the **same timing convention in estimation and deployment**. Estimation and deployment both use the T-0 value. The effective-date stock measure is retained only as a robustness check and is never used to form a tradable signal.

Any statistic that cannot be computed from the docket and the reference data as they stood at T-0 is excluded from the signal, without exception.

### 4.8 Inference, and what the sample can actually support

The regressor `Cong` varies at exactly the trustee × time level, which was also the previous draft's clustering level. That is the textbook setting in which cluster-robust standard errors are severely downward-biased with few clusters. With `≥ 4` trustees and trustee fixed effects absorbing most of the cross-trustee variation, the effective number of independent clusters is 4–6, far below the ~40 rule of thumb. A 1%-level result under those conditions is more likely an artefact of the variance estimator than evidence. The previous draft's stated pass criterion was therefore not attainable at its stated sample.

Corrections, pre-registered:

- Inference is by **wild cluster bootstrap-t** (Rademacher weights, 9,999 replications) with clustering at the **trustee** level, and separately by **randomisation inference** permuting the congestion series across trustees within year (9,999 draws).
- The **number of effective clusters is reported** with every coefficient.
- Minimum trustee count is raised from 4 to **8** (the six majors plus any trustee with ≥ 5 large mandates in the trailing 36 months), and the significance criterion is replaced by a **randomisation-inference p-value < 0.05**, which does not rely on asymptotics in the number of clusters.
- **Minimum detectable effect must be reported before the coefficient is.** At `n = 120` case-series observations, 8 trustee clusters and the control set above, the MDE on `β_Q` is approximately **0.6–0.8 standard deviations of the fee-quantum outcome per standard deviation of congestion**. That is a large effect. The test has essentially no power against a true effect of 0.2 SD or less, which is well within the range of magnitudes the mechanism might plausibly produce. **A null result at n = 120 is therefore weak evidence of absence, and a significant result at n = 120 implies an effect large enough that its absence from practitioner models becomes harder, not easier, to believe.** Both directions of that tension are stated because both are real.

---

## 5. Exact entry rules

### 5.1 Universe

An estate enters the candidate set at the moment **all** of the following are true:

- **U1.** US Chapter 11 filing (or an out-of-court restructuring with a filed disclosure-type solicitation), allowed claim value of funded debt ≥ **$500m** (assumption: threshold chosen to match the "large case" definition in the LoPucki-Doherty sample and to ensure docket and prospectus availability).
- **U2.** At least **two** pari passu bond series under **distinct indentures** with **distinct trustees**. Verified from prospectus/OM trustee-identity field.
- **U3.** Both series share collateral package and guarantor set (verified from the intercreditor agreement and the security-agreement schedules), **and have the same forecast §506(b) status**.
  **Restated as a forecast, because it is not a document fact.** §506(b) status is an *oversecurity determination* — a function of collateral value versus claim, adjudicated by a valuation ruling that in most cases post-dates T-0. The previous draft presented it as a verified document field while Section 6.3 simultaneously provided an exit for discovering it *after a valuation ruling*; that was a direct contradiction. At T-0 the strategy therefore computes `π^506_{i,s}` = probability the series is oversecured, from the disclosure statement's valuation range and the class's position in the waterfall, and requires **|π^506_s − π^506_{s'}| ≤ 0.15** for the legs to be treated as matched. The residual uncertainty is propagated into `m̂` (Section 5.2) and into a **sizing haircut of `1 − 2·max(π^506·(1−π^506))`**, which is at its most punitive when the valuation is a coin flip.
  **Alternative universe, offered as the cleaner but smaller option:** restrict to cases where a valuation ruling has already been entered before T-0. This removes the forecast entirely. It also removes roughly two thirds of candidates and moves T-0 materially later, and the funnel in Section 11.2 is reported both ways.
- **U4.** *(Restated at series level — the previous estate-level version was internally contradictory.)* Plan treatment of trustee fees, as disclosed in the disclosure statement or plan supplement, is classified **per series**, not per estate, into categories (a)–(e) of Test 0. The requirement depends on which component is being expressed:

  | Component | Long leg requires | Short leg requires |
  |---|---|---|
  | **CLL-Q** (thesis: congestion-driven quantum) | (d) or (e) — lien preserved, *uncongested* trustee | (d) or (e) — lien preserved, *congested* trustee |
  | **CLL-F** (covariate: baseline fee level) | (a), (b) or (c) — mutualised | (d) or (e) — lien preserved |

  The previous draft's U4 excluded categories (a)/(b)/(c) outright at estate level, while Section 9.2 defined the long leg as a series under a plan providing *estate payment* of trustee fees — i.e. category (a), which U4 had just excluded — and Section 11.2 then applied the gate as a hard ×0.25 filter in one row and dropped it to "a probability weight rather than a filter" in the next. The gate was simultaneously a hard exclusion, satisfied only by the short leg, and not a filter. **All three readings are replaced by the table above**, and Section 11.2 is rebuilt on the joint requirement, which is strictly harder than either gate alone.
- **U5.** Trustee identity for both series maps to a trustee in the congestion panel (the six majors plus any trustee with ≥ 5 large mandates in the trailing 36 months).
- **U6.** *(New — see Section 6.5.)* The prime broker has confirmed **in writing, before entry**, that it will carry the short position through plan effectiveness and settle it by delivery of the plan consideration on the corporate action. If it will not, the position would have to be covered at market before cancellation, which converts the short leg into a price-convergence trade. **No confirmation, no trade.**

### 5.2 Signal construction

**Congestion score.** For trustee `k` at date `t`, using arrivals (Section 4.1):

```
Cong_{k,t}  =  Σ_{j ∈ NewMandates(k, t−12m → t), j ≠ i}  AllowedClaim_j          (dollars)
CongZ_{k,t} =  ( Cong_{k,t} − μ_k ) / σ_k          (z-score vs trustee k's own trailing 5-year distribution)
```

Using the trustee's *own* history for standardisation removes cross-trustee scale differences and leaves only within-trustee time-series congestion, which is the exogenous part. All quantities are evaluated at **T-0**, the same convention used in estimation.

**Predicted fee quantum** (the thesis component), in points of claim:

```
q̂_{i,s}  =  100 · (1 − m̂_{i,s}) · β̂_Q · Cong_{k,t_0}^{(−i)} / N_{i,s}
```

**Predicted baseline fee burden** (the covariate), in points of claim:

```
f̂_{i,s}  =  100 · (1 − m̂_{i,s}) · F̂₀_k / N_{i,s}
```

where `F̂₀_k` is the trustee-specific median per-indenture baseline fee from the docket panel, scaled by **T-0-observable** case-intensity proxies only: elapsed days since petition, docket entries to date, contested matters filed to date, and the DIP milestone schedule. (The previous draft scaled it by case duration to the effective date and by total contested matters — both terminal quantities, both look-ahead. Both are removed.)

`m̂` is the fitted probability of mutualisation **for that series** from a logit on: number of distinct indentures, prepack indicator, presence of an ad hoc group with counsel of record on that series, district (SDTX/SDNY/DE dummies), `π^506` from U3, and `CongZ`.

**Total predicted traded toll:**

```
τ̂_{i,s}  =  f̂_{i,s}  +  q̂_{i,s}          (points of claim)
```

The float term `100 · R̂ · r · L̂` is **not** in `τ̂`. It is computed separately, reported in the data product, and used to size the OIS hedge that removes it from the position (Section 8.1).

**Signal — the relative toll within an estate:**

```
S_{i,s}  =  τ̂_{i,s}  −  ( Σ_{s'∈i} N_{i,s'} τ̂_{i,s'} ) / ( Σ_{s'∈i} N_{i,s'} )
```

Positive `S` = rich series (short). Negative `S` = cheap series (long). The signing argument for this demeaned object is Section 4.6, Steps 2–3; it is not inherited from the level.

### 5.3 Thresholds

The minimum-signal gate is **no longer a constant**. The previous draft set it at 1.5 points, described as "~1.5× the estimated round-trip cost on the *liquid* leg", and then admitted positions with negative expected edge: at `|S| = 1.5`, tilt cost 1.2, and `P(d or e) = 0.65` implied by the `m̂ ≤ 0.35` gate, Section 7.1 returns `E = 0.65 × 1.5 − 1.2 = −0.22` points at the *most favourable* `b' = 0`. The pair expression, at 3.5 points round trip, was being admitted at a threshold well below its own transaction cost. The gate is now derived from the sizing formula:

```
|S_{i,s}|  ≥  ( c_j  +  borrow_j  +  margin )  /  [ ( 1 + b̂' ) · P(d or e)_j ]
```

with `margin = 1.0` point, and `borrow_j` the modelled borrow accrual over the expected hold (Section 9.4).

| Gate | Threshold | Basis |
|---|---|---|
| Minimum absolute signal | Formula above. **At current parameters this evaluates to ≈ 5.7 points (pair, cheap borrow) and ≈ 10.3 points (pair, typical borrow)** | Derived from `E_j > 0` with margin, not from one leg's half-spread |
| Minimum congestion dispersion within estate | `|CongZ_k − CongZ_k'| ≥ 0.75σ` | Assumption. Below this, the quantum differential is inside the standard error of `β̂_Q` |
| Mutualisation probability | `m̂ ≤ 0.35` on the short leg; `m̂ ≥ 0.65` on the long leg for the CLL-F expression | Assumption; calibrated to the Test 0 base rate |
| §506(b) status match | `|π^506_s − π^506_{s'}| ≤ 0.15`, with sizing haircut per U3 | Forecast, not a document field |
| First-stage strength | Randomisation-inference p < 0.05 on `β_Q` in the live rolling estimation, with effective cluster count reported | Replaces the F ≥ 10 criterion, which is not meaningful with 6–8 clusters |
| Rate regime | **Removed as a gate.** | The traded estimand no longer contains `r`. This is the point of the CLL-D withdrawal: the thesis component pays the same at `r = 0` as at `r = 5%`. Rates now enter only through the hedge |
| Both-legs-borrowable | Locate confirmed, **borrow ≤ 50bp**, size ≥ 2× intended, **and PB written confirmation per U6** | Tightened from 300bp. At 300bp over an 18–36 month hold the borrow alone costs 4.5–9 points, which exceeds any plausible wedge (Section 9.4) |

### 5.4 Timing — the precise observable that triggers

The trigger is a **docket event**, not a price.

**T-0: Disclosure statement or plan supplement is docketed** (PACER/CM-ECF, or a docket feed). This document discloses plan treatment of indenture trustee fees **per series**. This is the moment `m` becomes observable and it is **before** the effective date — the screen is *ex ante*, not hindsight. Every input to `S` is evaluated as of T-0 (Section 4.7).

Operational sequence, US Eastern time:

- **07:00 ET daily** — automated docket sweep of the candidate estate list; new filings parsed for the per-series trustee-fee treatment clause and the disbursing-agent provision.
- **By 09:30 ET** — analyst confirms category (a)–(e) **for each series separately** by reading the actual plan article; the classifier is a screen, never the final word. Signal `S` recomputed with the now-observed `m`.
- **Same day** — prime broker written confirmation on corporate-action handling of the short leg (U6). **Execution does not begin without it.**
- **10:30–15:00 ET, day T-0 or T+1** — execution window. Distressed bonds trade OTC; the window excludes the first 60 minutes after the 09:30 open and the last 60 minutes before 16:00, when dealer quotes are widest and TRACE prints thinnest.
- **Build over 3–10 sessions**, never in one day (Section 9).

**Secondary trigger, congestion-driven, no docket event required:** at each **month-end**, the congestion panel is refreshed. Any estate already in the universe whose `S` crosses the derived threshold because of a *change in the trustee's other mandates* becomes eligible. This is the purest expression of the mechanism — a position initiated because someone *else* went bankrupt.

---

## 6. Exact exit rules

### 6.1 Thesis-realisation exits

| Trigger | Action | Threshold |
|---|---|---|
| Plan effective date + first holder distribution received on both legs | Full exit; the wedge is realised in cash | n/a — terminal |
| Confirmation order entered moving trustee fees to estate-paid administrative expense **on the short leg** | Exit that leg within 5 business days | Any movement from category (d)/(e) → (a)/(b)/(c) |
| Court approves a plan-appointed disbursing agent paid as an estate admin expense | **Full exit of the CLL-F and CLL-Q legs of that estate.** Under Section 4.2, `(1 − m)` multiplies both traded terms, so the **traded** toll is zero once the lien is released | Binary |

**Correction retained deliberately.** The previous draft called the disbursing agent "the mechanism's off-switch; the wedge is definitionally zero", which was false on its own equation: `(1 − m)` multiplied only the fee term, so the queue — and the holder's exposure to `R·r·L` — survived the disbursing agent untouched, having merely moved to a different intermediary. That inconsistency is resolved not by weakening the exit but by **removing the float term from the traded estimand entirely**. The exit above is now exactly true *of what is traded*. It remains **false of the queue**, and the document says so: appointing an estate-paid disbursing agent does not shorten the queue, and the latency object in the data product does not switch off. That is why Test 2 is split.

### 6.2 Thesis-invalidation exits

| Trigger | Threshold | Action |
|---|---|---|
| Rolling `β̂_Q` (fee quantum on congestion) | Randomisation-inference p > 0.10 for two consecutive quarterly re-estimations, or sign flip | Halt all new CLL-Q entries; run down existing book. **This is the publish-or-kill coefficient** |
| Trustee congestion coefficient in the placebo horse race | `β̂_Q` falls below 50% of its single-instrument magnitude when claims-agent, debtor-counsel and FA congestion are entered simultaneously | Halt; the causal node is not the trustee |
| Realised `b_Q` (cash on fee quantum) in Stage 2 | `b_Q > −0.5` over a rolling 20-case window | Halve all CLL-Q sizing |
| Claim-weighted base rate of plan categories (d)+(e) | Falls below **20%** on a trailing 24-month docket sample | Terminate CLL-F entirely; CLL-Q may continue only where both legs are in (d)/(e) |
| Stage-3 `b'` (relative price on residualised relative toll) | `b' < −0.75` on a trailing 30-estate sample | Terminate the position; convert to the data product (Section 14.5) |
| Stage-3 `b'` | `b' > 0.1` and survives re-specification | Terminate the position; the toll model is misspecified |

### 6.3 Adverse-selection exits

The dangerous state is being long a series that is cheap **for a reason the model does not see**.

| Trigger | Threshold | Action |
|---|---|---|
| An ad hoc group forms on **one leg only**, or an RSA is amended so the two legs are no longer co-signatories | Any occurrence | Exit within 3 business days. Coalition matching was the entire control for hold-up rent; once it breaks, the position is a bet on creditor-on-creditor violence, which is 5–40 points and swamps a 1–3 point wedge |
| Non-pro-rata exchange, uptier, drop-down, or priming transaction proposed affecting either leg | Any occurrence | Immediate full exit of the estate |
| Valuation ruling entered that separates the legs' §506(b) status by more than the U3 tolerance | Any occurrence | Exit — §506(b) mutualises the toll on the oversecured leg only, so the matching is broken. **Expected, not exceptional:** U3 is a forecast, and this is the branch where the forecast was wrong |
| Substantial-contribution motion filed under §503(b)(5) by either trustee | Any occurrence | Reassess `m̂` within 48h; exit if `m̂` rises above 0.5 on the short leg |
| Adverse price move on the short leg without any docket event | −4 points vs the long leg over 10 sessions | **Halve the position. This is a risk-reduction rule triggered by suspected information arrival, not a convergence or profit-taking rule** — see Section 13.2. It may only ever *reduce* exposure; there is no corresponding rule that adds to a position on a favourable price move, and no exit anywhere in Section 6 is taken because price has moved *toward* fair value |

### 6.4 Time-based exits

| Condition | Threshold | Action |
|---|---|---|
| Elapsed time from entry with no plan confirmation | **30 months** | Exit regardless of P&L. Beyond this the case has converted to a workout the model did not underwrite |
| Case converts from Chapter 11 to Chapter 7 | Immediate | Exit. Liquidation distributions run through a trustee under a different fee regime (§326 statutory caps), not the indenture charging lien |
| Rate hedge roll | Quarterly | Re-struck to the current expected differential time-to-cash, so that the float differential stays neutralised (Section 8.1) |

### 6.5 Short-leg financing and corporate-action exits *(new — the previous draft had none)*

The dominant operational risk in the position had no exit rule, no limit and no cost reserve. The short leg is held 18–36 months in a name whose borrow is 100–400bp and "frequently no locate at all", through a plan effectiveness at which the shorted CUSIP is **cancelled** and replaced by plan consideration.

| Trigger | Threshold | Action |
|---|---|---|
| Borrow recall on the short leg | Any occurrence | Attempt re-locate within 1 business day; if unavailable, **close both legs**. A recalled short leaves a naked long distressed bond, which is not this strategy |
| Borrow rate rises above the entry gate | > 100bp annualised, or > 2× entry rate | Re-run `E_j` at the new rate. If `E_j < 0`, close both legs |
| Cumulative borrow accrual since entry | Exceeds **40% of `|S|`** | Close both legs. The financing cost is consuming the thesis |
| Prime broker withdraws the U6 corporate-action confirmation | Any occurrence | Close the short leg immediately, then the long leg |
| Confirmation order entered (T minus ~30–45 days to effectiveness) | Scheduled | **Decision point.** If the PB will settle the short by delivery of plan consideration on the corporate action, carry to cash. If not, the short must be covered at market pre-cancellation — in which case the short leg is monetised at *price*, not at *cash*, the cash-settlement logic of Section 13.2 no longer protects it, and the position is closed rather than converted |
| Forced buy-in | Any occurrence | Accept; record as a realised cost against the strategy's borrow reserve |

**Borrow reserve.** A reserve equal to the modelled full-holding-period borrow accrual on every open short leg, at the *entry* rate plus 200bp, is held against NAV and is not available for new positions.

---

## 7. Position sizing

### 7.1 Formula

Per-estate expected edge, in points of claim:

```
E_j  =  ( 1 + b̂' ) · P(category d or e)_j · H^506_j · |S_j|   −   c_j   −   borrow_j
```

where `c_j` is the modelled round-trip bid-ask cost, `borrow_j` is modelled borrow accrual over the expected holding period, `H^506_j` is the U3 valuation haircut, and `(1 + b̂')` is the fraction of the within-estate toll deviation **not** already in relative price, from the residualised Stage 3.

**Entry requires `E_j ≥ 1.0 point`**, which is what generates the derived `|S|` gate in Section 5.3. The previous draft's fixed 1.5-point gate admitted positions with `E_j = −0.22`; that is corrected at the root, in the gate, not by a caveat.

Notional weight:

```
w_j  =  min(  κ · E_j / σ_j² ,   L_j ,   C_j ,   W_max  )
```

- `κ` = **0.15** (fractional-Kelly multiplier; assumption, set deliberately low because `E_j` is an estimate from a small sample and the estimation error is likely larger than the estimate).
- `σ_j` = realised annualised volatility of the *leg spread*, not of either leg. For matched pari passu series this is typically 3–6 points annualised (assumption).
- `L_j` = **liquidity cap** = 4% of the outstanding claim amount of the **smaller leg**, applied to **both** legs, so that the position is claim-matched. At the Section 9.4 orphan-series float of $100–300m this is **$4–12m per leg**. *(Section 11.3 previously applied this 4% to the $400m–$2.0bn large leg and reported $16–80m; that was the larger leg, not the smaller, and contradicted this line. Corrected.)*
- `C_j` = **concentration cap** = 10% of strategy NAV per estate.
- `W_max` = 3% of strategy NAV per single CUSIP. **This binds below `L_j` for any NAV under ~$400m**, and the binding cap is the smaller of the two in every case — see Section 11.3.

### 7.2 What it scales with

- **Increasing** in `|S_j|` — the relative toll. Linear.
- **Increasing** in congestion dispersion between the two trustees.
- **Independent of `r_t`.** This is the direct consequence of withdrawing CLL-D. The previous draft's "the strategy shrinks toward zero at low short rates by construction" was a concession that its payoff was a financing payoff; the traded estimand no longer contains `r`, and rates now enter only through the hedge that removes the float differential.
- **Decreasing** in `m̂` uncertainty — sizing is multiplied by `P(d or e)`.
- **Decreasing** in `π^506` uncertainty — via `H^506_j`.
- **Decreasing** in borrow cost, directly and through the `E_j` gate.

### 7.3 Caps

| Cap | Level | Basis |
|---|---|---|
| Per CUSIP | 3% NAV | Assumption; single-name gap risk. **Binds before the 4%-of-smaller-leg liquidity cap at any NAV below ~$400m** |
| Per estate | 10% NAV | Assumption |
| Per trustee (congestion factor exposure) | 25% NAV | **The whole book loads on the same congestion factor.** If a credit cycle congests all trustees at once, the diversification is illusory |
| Total gross | 150% NAV | Assumption; the strategy is capital-inefficient because both legs are cash bonds |
| Borrow reserve | Full-period accrual at entry rate + 200bp on every open short | Section 6.5 |
| Illiquid (non-TRACE, no borrow) exposure | **0%** | Changed from 15%. Without borrow there is no short leg and therefore no position (Section 9.2) |

---

## 8. Risk management

### 8.1 Unwanted exposures and their neutralisation

**Rate exposure — the hedge now removes a *payoff*, not merely a risk.** The two legs settle on different dates, so the position mechanically contains a discount-factor differential. In the previous draft that differential *was the thesis* (`r × Latency`), and Section 8.1 conceded "a long/short in time-to-cash is a duration position by construction" while Section 13.3 denied it was carry. Both cannot be true.

The resolution is structural: **the float differential is hedged to zero and is not a source of P&L.** For each estate, compute expected differential time-to-cash `ΔL̂ = L̂_short − L̂_long` and the claim-weighted notional at risk, and enter a matched-tenor OIS/swap of DV01:

```
DV01_hedge  =  Notional × R̂ × ΔL̂ × (∂PV/∂r)
```

struck at the weighted-average expected receipt date, and **sized to offset the full `100·R·(1 − e^{−rL})` differential, not merely its rate sensitivity**. The intended realised P&L therefore contains no financing differential between the two settlement dates. If the hedge cannot be put on — no liquid matched-tenor OIS, or a notional too small to be worth a swap line — **the position is not taken**, because an unhedged version of it is a calendar basis trade.

**Residual rate exposure after hedge is stated and monitored, not asserted away** — the hedge is against a *forecast* latency differential, and forecast error in `ΔL̂` is unhedged. Limit: residual DV01 ≤ 2% of the DV01 of a 2-year matched-notional swap. Forecast error in `ΔL̂` is the one channel through which float still touches the P&L, and it is a *risk*, not an edge: its expectation is zero by construction.

**Estate / enterprise-value exposure.** Neutralised **by construction, with a second cash claim on the same estate** — the two legs are pari passu claims on the same estate with identical collateral, guarantors and forecast §506(b) status, so enterprise value nets. **Single-name CDS is no longer used as an estate hedge and single-name CDS is no longer used at all.** The previous draft's default expression was long a defaulted cash bond versus single-name CDS protection carried 14–20 months, which is a cash-CDS basis position: over that horizon, cheapest-to-deliver dynamics, auction settlement and the cash-versus-CDS recovery gap move in tens of points against a stated 1–3 point wedge, and a hedge held that long, at a size chosen to neutralise estate exposure, becomes the dominant P&L driver precisely *because* the strategy has no view on it. Any estate-neutral expression on a single estate is necessarily a **two-cash-leg pair**; that is now the only expression (Section 9.2).

**Credit beta.** With both legs cash claims on the same defaulted estate, matched by claim amount, broad-market credit beta is second-order and is **not separately hedged**. CDX HY protection has been removed for the same reason single-name CDS was: an index hedge held 18–36 months against a sub-point wedge is a larger position than the strategy. Residual |β_CDX| is measured and reported; if it exceeds 0.15 the position is reduced, not hedged.

**Hold-up rent / coalition exposure — the largest confound.** Not hedged; *controlled by construction* via the within-coalition matching requirement (both legs RSA co-signatories or represented by the same ad hoc group). If the matching breaks, the position is exited (Section 6.3), not hedged.

**Short-leg financing and corporate-action exposure.** Not hedgeable. Reserved against, gated at entry (U6, borrow ≤ 50bp), exited on the triggers in Section 6.5, and — on the arithmetic in Section 9.4 — **larger than the wedge at any borrow rate above roughly 50–70bp**. This is the single largest reason the position expression fails its own economics.

**Liquidity exposure.** Not hedgeable. Priced into `c_j`.

### 8.2 Limits

| Limit | Level |
|---|---|
| Max drawdown before mandatory strategy review | 12% of allocated capital |
| Max drawdown before forced 50% de-gross | 18% |
| Max single-estate loss | 4% NAV |
| Max positions in one court district | 30% NAV (district docket load is a confound *and* a correlated risk) |
| Max positions with the same ad hoc group counsel | 25% NAV |
| Max positions sharing a claims agent | 30% NAV (added: the placebo rival in Section 4.5.5 is also a correlated risk, not only an identification threat) |
| Min cash buffer | 15% NAV (distressed positions cannot be liquidated to meet margin) |

### 8.3 Kill criteria

The **position** is terminated — not resized — if any of the following. Note that none of these kills the **data product**, which is the primary deliverable (Section 14.5).

1. **`β̂_Q` (fee quantum on congestion) is not distinguishable from zero** in the pre-registered Test 1A. This kills CLL-Q, which is the thesis. What remains is LoPucki-Doherty applied at series level, which is not original enough to justify the programme as a position.
2. **`β̂_Q` does not survive the placebo horse race** against claims-agent, debtor-counsel and FA congestion. The causal node is not the trustee, the trustee-identity map is not the right map, and nothing tradable follows.
3. **Claim-weighted base rate of plan categories (d)+(e) < 20%.** Kills CLL-F and severely restricts CLL-Q.
4. **Stage-3 `b' < −0.75`** (real and untradable) **or `b' > 0.1` surviving re-specification** (model wrong).
5. **The within-coalition wedge (Test 4) is indistinguishable from zero.** The original construction was hold-up-rent shorting in a lab coat.
6. **Test 1C returns a within-estate `|S|` distribution whose 90th percentile is below the derived entry gate of Section 5.3.** The wedge is real but smaller than the cost of trading it. *On the priors stated in Section 9.4, this is the expected outcome.*
7. **Realised round-trip cost plus borrow on the median position exceeds 60% of `|S|`** over a 20-position sample.

---

## 9. Execution model

### 9.1 Instruments

| Instrument | Role | Venue |
|---|---|---|
| CUSIP-level distressed corporate bonds | **Both legs.** Long and short, claim-matched, same estate | OTC dealer market; TRACE-disseminated |
| Matched-tenor OIS / interest-rate swaps | Neutralises the float differential so it is not a payoff (Section 8.1) | Cleared (LCH/CME) |
| Bankruptcy trade claims | Opportunistic, where a bond leg is unavailable **and** the claim can be assigned on both sides | Bilateral assignment |

**Prohibited instruments.**

- **Single-name CDS — removed.** Long a defaulted cash bond versus single-name protection for 14–20 months is a cash-CDS basis position, and the strategy holds no view on the basis. A hedge with no view, held that long, sized larger than the alpha, is the position.
- **CDX HY — removed**, for the same reason at index level.
- **LSTA loan assignments — removed** as a hedge for the same reason; they were never a leg.

**Deleted leg (a):** long senior secured term loan vs short pari passu secured notes is **removed**. Credit agreements universally place administrative agent fees, expenses, indemnity and agent's counsel at the top of the payment waterfall, so both chains carry a toll; and the residual is dominated by the published loan-vs-bond recovery differential of 20–30 points. It was a levered bet on a known factor in the costume of a new one.

**Deleted leg (b):** naive flagship-vs-orphan without coalition matching is **removed** for collinearity with hold-up rent.

### 9.2 The only expression — the two-cash-leg, same-estate pair

Within a matched-fundamentals candidate set: **long** the pari passu series whose predicted traded toll is below the estate's claim-weighted average; **short** the pari passu series whose predicted traded toll is above it. Both legs are cash claims on the same estate, claim-matched, so estate exposure nets by construction and no third instrument is required to neutralise it.

**"Underweight or avoid" has been deleted as an expression.** The previous draft's default was to overweight the low-toll series and "underweight or avoid" the high-toll one, with residual estate exposure hedged in CDS. Avoidance captures no toll differential whatsoever: a long-only position in the low-toll series is a long distressed bond, and the entire signal content of the strategy is the *difference* between two series. **If the high-toll leg cannot be shorted, there is no position.** That is a capacity cost and it is accepted rather than argued around.

Conditions, all required: both legs borrowable at ≤ 50bp with size ≥ 2× intended; U6 prime-broker corporate-action confirmation in hand; both share collateral, guarantors and forecast §506(b) status within tolerance; both are RSA co-signatories or represented by the same ad hoc group; OIS hedge executable. **Expected count: on the funnel in Section 11.2, well under one estate per year. The capacity constraint is a fact about the strategy, not a defect to be argued away.**

### 9.3 What is no longer claimed

The previous draft described the CDS-hedged tilt as "the honest expression" and concluded that "the pair expression is marginal by construction and the tilt is the default", with tilt capacity of 8–12 estates/yr against pair capacity of ~1/yr. That was the load-bearing capacity claim in the document, and it rested on an expression that is a banned basis trade and on a universe gate applied inconsistently (Section 5.1, U4). **Both the tilt and its capacity are withdrawn.** The strategy's honest capacity is the pair's.

### 9.4 Order handling, slippage, and the cost arithmetic that decides the question

Distressed bonds do not trade on a lit book. Execution is voice/Bloomberg-chat RFQ against 4–8 dealers with distressed desks.

- **Never** show both legs to the same dealer in the same conversation. The pair *is* the signal.
- Long leg and short leg worked through **disjoint dealer sets**, separated by **≥ 2 business days**.
- Build in **3–10 sessions**, max 25% of daily TRACE volume in the CUSIP per session; for non-TRACE names, max 20% of the dealer's shown axe.
- Use **odd-lot sizing deliberately** on the orphan leg.
- No resting orders, no algorithmic execution, no participation in BWICs where the list composition would reveal the pairing.

**Expected slippage (assumptions, with basis):**

| Leg type | Bid-ask, points | Basis |
|---|---|---|
| Large liquid distressed series ($1bn+, TRACE-active) | 0.5–1.5 | Typical distressed IG-fallen-angel dealer quote |
| Small orphan series ($100–300m, sporadic prints) | 2.0–5.0 | Typical distressed odd-lot/orphan quote |
| OIS hedge | < 0.5bp | Cleared |
| Borrow cost on orphan short | 100–400bp annualised, frequently **no locate at all** | Practical |

**Modelled round-trip cost `c_j` (pair): ≈ 3.5 points.**

**Modelled borrow cost `borrow_j`:** at the Section 5.3 entry gate of 50bp over an 18–36 month hold, **0.75–1.5 points** on the short notional. At the *typical* market rate of 100–400bp, **1.5–12 points** — which is why the gate was tightened from 300bp, and why most candidates fail it.

**The magnitude arithmetic, stated before any price work is done.** This is the number that decides whether a position exists:

- The traded wedge is a **within-estate deviation in fee quantum**, not a level. The relevant quantity is the *difference* in charging-lien fees between two series distributed under the same plan, from the same effective date, on the same estate.
- Trustee-plus-counsel fees on a large case run roughly $2–30m at estate level, of which a single indenture's share is roughly $0.5–8m. On a $100–300m orphan series that is **0.5–3 points** of *baseline* toll (CLL-F) and near-zero on a $1bn+ series.
- The **congestion-driven increment** — CLL-Q, the thesis — is a fraction of that baseline. A plausible prior, pending Test 1A, is 20–40% of the baseline on the congested leg, i.e. **0.2–1.0 points** on the small leg and effectively nil on the large one.
- Against `c_j ≈ 3.5` points and `borrow_j ≈ 0.75–1.5` points at the *best available* borrow rate, and a derived entry gate of ≈ 5.7–10.3 points (Section 5.3).

**Consequence, stated plainly:** the thesis component alone almost certainly does not clear the gate. Even the fee component (CLL-F), at 0.5–3 points of within-estate deviation, clears it only in the upper tail and only where the two series' plan treatments differ. **The previous draft's 1.5-point gate could in practice only ever be tripped by CLL-F — the component conceded to be prior art — which means the original component would never have traded.** Test 1C is pre-registered specifically to measure this before any price work, and Kill Criterion 6 acts on it.

### 9.5 How the position is built without revealing itself

The signal's inputs are the position's disguise: entry is triggered by a **docket event on the estate** or by a **congestion change at an unrelated trustee**. Neither produces an observable order-flow pattern that a competitor can reverse-engineer, because the second input is not a variable anyone else is watching. The main disclosure risk is **not** order flow — it is Rule 2019 ad hoc group disclosure and the organisational process itself, which is why positions are held below 4% of a series and why the strategy does not join ad hoc groups.

---

## 10. Expected holding period

One payoff date, not two. The previous draft claimed two, and the claim was internally inconsistent.

| Component | Payoff event | Expected elapsed time from entry |
|---|---|---|
| **CLL-F (baseline fee)** | **Cash at distribution.** | 18–36 months |
| **CLL-Q (congestion quantum, thesis)** | **Cash at distribution.** Cannot be accelerated | 18–36 months |
| **CLL-D (float)** | Not traded; hedged to zero | n/a |

**Why the previous "dated event" repair is withdrawn.** Section 13.13 asserts — and the document still asserts — that **price never responds to the toll, because the variable is not in anyone's dataset**. If that is true, then the public, discrete resolution of the fee-mutualisation binary at the disclosure-statement date produces **no mark and no P&L**. Resolution of uncertainty is not a payoff. The previous draft's claim that splitting the payoff "converts part of a 1–3 year unhedgeable hold into a dated event" and thereby "removes the information-arrives-after-the-trade objection" therefore does not survive alongside 13.13, and the two could not both be kept. **13.13 is kept; the dated-event repair is deleted.** The information-arrives-late objection stands unrepaired and is recorded in Section 12A.

**Blended expected holding period: 22–30 months, median ~24** (up from the previously stated 14–20, which was understated by exactly the amount the deleted repair was assumed to save). There is **no interim mark-to-market convergence** — the position is carried at marks that do not reflect the wedge until cash arrives. This is a poor fit for any mandate with monthly liquidity and must be stated as such. It also lengthens the borrow accrual in Section 9.4, which is why that number is quoted over 18–36 months.

---

## 11. Capacity estimate

### 11.1 Binding constraint

**The binding constraint is the count of qualifying estates per year, not dollar liquidity.** Dollar liquidity binds second, within the qualifying estates. Both are now materially smaller than the previous draft stated.

### 11.2 Arithmetic — rebuilt on the joint series-level gate

The previous funnel applied the (d)/(e) gate as a hard ×0.25 filter in one row ("this is the killer") and then dropped it "to a probability weight rather than a filter" in the next row to reach 8–12/yr for the tilt. The gate cannot be both. Section 5.1 U4 now states the requirement **per leg**, and the funnel below applies it jointly. The joint requirement is strictly harder than either gate alone.

| Step | Count | Basis |
|---|---|---|
| Large US Chapter 11 filings, funded debt ≥ $500m | **45–65/yr** | Typical annual count in a normal-to-elevated default year; 100+ in 2009/2020, ~30 in a benign year |
| …with public bonds and retrievable indentures | ×0.75 → **34–49** | Some are loan-only / sponsor-owned |
| …with ≥2 pari passu series under **distinct indentures with distinct trustees** | ×0.35 → **12–17** | Most capital structures consolidate series under one indenture per priority tier |

**Branch Q (thesis: congestion-driven quantum).** Requires **both** legs in category (d)/(e) — lien preserved on both — with congestion dispersion between their trustees.

| Step | Count | Basis |
|---|---|---|
| Both legs in (d)/(e) | ×0.25 → **3.0–4.3** | Test 0 base-rate prior; plan treatment is usually uniform across series within an estate, so the joint probability is close to the marginal |
| Congestion dispersion ≥ 0.75σ | ×0.6 → **1.8–2.6** | Assumption |
| Both legs borrowable **and** U6 PB confirmation obtainable | ×0.30 → **0.5–0.8** | Tightened: PB willingness to carry a short through a plan corporate action is not routine |
| Borrow ≤ 50bp (the economic condition, Section 9.4) | ×0.25 → **0.13–0.20** | Most orphan distressed borrow is 100–400bp |

**Branch F (covariate: baseline fee level).** Requires **split** treatment — long leg in (a)/(b)/(c), short leg in (d)/(e), within the same estate.

| Step | Count | Basis |
|---|---|---|
| Split treatment across series within estate | ×0.10 → **1.2–1.7** | Harder than the marginal base rate, because plan treatment is usually uniform across series |
| Both legs borrowable + U6 | ×0.30 → **0.36–0.51** | As above |
| Borrow ≤ 50bp | ×0.25 → **0.09–0.13** | As above |

**Union, allowing overlap: ≈ 0.2–0.3 qualifying estates per year** under the full economic gates, and **≈ 0.9–1.3 per year** if the borrow-cost condition is relaxed to the previous 300bp — at which point the borrow alone costs 4.5–9 points and the positions lose money by construction.

Under the alternative U3 universe (post-valuation-ruling cases only) every line falls by roughly a further two thirds, to **≈ 0.07–0.10 estates/yr**, in exchange for removing the §506(b) forecast error.

**This is not a business. It is stated as the honest output of the stated gates.**

### 11.3 Dollar capacity

Per estate, corrected per Section 7.1:
- Smaller (orphan) leg float: **$100–300m** allowed claim (Section 9.4).
- Liquidity cap `L_j` = 4% of the **smaller** leg → **$4–12m per leg**, median **$8m**. *(The previous draft applied 4% to the $400m–$2.0bn large leg and reported $16–80m / $40m median, which contradicted its own definition of `L_j`.)*
- The 3%-NAV-per-CUSIP cap `W_max` binds below `L_j` for any NAV under ~$400m. At a NAV of $50m, `W_max` = $1.5m and is the binding cap; at $270m the two caps coincide at $8m.
- Gross per estate = 2 legs × $8m = **$16m** at the liquidity cap.

At 0.25 estates/yr and a 24-month hold, the steady-state book is roughly **$8m gross**. At the relaxed-borrow count of ~1.1 estates/yr it is roughly **$35m gross**.

**Round-number capacity: the position expression cannot responsibly absorb more than $25–50m NAV**, and at that NAV the per-CUSIP cap, not liquidity, is what binds. The previous draft's "$300–400m NAV" figure was a consequence of the withdrawn tilt expression and the mis-applied liquidity cap, and is withdrawn.

### 11.4 Expected gross revenue — corrected, and negative

Recomputed with execution cost expressed in **points applied to gross notional** rather than the previous unexplained "$1.2m", with the corrected liquidity cap, and with borrow included.

Per qualifying estate, at the *optimistic* end (`|S| = 3` points, which Section 9.4 says CLL-Q alone does not reach; `P(d or e) = 0.65`, from the `m̂ ≤ 0.35` gate; `b' = 0`; `H^506 = 0.9`):

```
Gross edge   =  0.03 × $16m gross × 0.65 × 0.9        ≈  $281k
Bid-ask      =  3.5 points × $16m gross               ≈  $560k
Borrow       =  1.0 point   × $8m  short              ≈  $80k
                                                       ─────────
Net per estate                                        ≈  −$359k
```

At 0.25 estates/yr: **≈ −$90k per year.** At the relaxed-borrow count of ~1.1 estates/yr, with borrow at 250bp over 24 months (5 points on the short): **≈ −$0.9m per year.**

**At the `|S|` that CLL-Q alone plausibly generates (0.2–1.0 points, Section 9.4), gross edge per estate falls to $19–94k against $640k of cost — a loss of roughly 85–97% of the transaction cost incurred.**

**The "≈ 70bp" headline in the previous draft is withdrawn.** It was built from a $40m median position (wrong leg), a $1.2m execution cost (not the stated 1.2 points on gross), a ~50% hit rate on the mutualisation binary (the `m̂ ≤ 0.35` gate implies ≥ 65%, and the two figures were never reconciled), and a 10-estate-per-year count that came from the withdrawn tilt. Every one of those inputs has been corrected and the corrected figure is negative.

**The honest conclusion follows from the arithmetic, not from modesty: on the parameters this document defends, the position expression loses money, and the deliverable is Section 14.5.** The position specification is retained in full because it becomes live again — and only becomes live again — if Test 1C returns a within-estate `|S|` distribution materially larger than assumed here.

---

## 12. Failure modes

Ranked by probability × impact.

### F-1. The wedge is smaller than the cost of trading it. *(Highest probability — promoted from F-7)*
The traded quantity is a **within-estate deviation**, not a level. Section 9.4's magnitude arithmetic puts CLL-Q at 0.2–1.0 points and CLL-F at 0.5–3 points against a 3.5-point round trip, 0.75–12 points of borrow, and a derived entry gate of 5.7–10.3 points.
**Leading indicator:** Test 1C, the pre-registered `|S|` distribution measured before any price work.

### F-2. The go/no-go gate fails: fee mutualisation is modal.
Multiple independent practitioner sources state that negotiating debtor/estate payment of indenture trustee fees as an administrative expense **has become standard practice**. §503(b)(5) and §506(b) provide statutory mutualisation channels, the latter applying precisely to the oversecured secured-notes population.
**Leading indicator:** rolling 24-month claim-weighted share of plan categories (d)+(e). Below 20% → CLL-F dead and CLL-Q severely restricted.

### F-3. Congestion does not predict the fee quantum.
If `β̂_Q ≈ 0`, the thesis is fiction and only the baseline fee cross-section remains — LoPucki-Doherty applied at series level, not original enough to justify the programme as a position.
**Leading indicator:** Test 1A. This is the publish-or-kill coefficient.

### F-4. The causal node is not the trustee. *(New)*
Claims agents, debtor counsel and financial advisors are shared across the same cases and congest simultaneously with the trustee. That rival predicts the same coefficient sign and magnitude while implying a node that is not mapped at CUSIP level and not tradable via the trustee-identity map.
**Leading indicator:** the placebo horse race in Test 1A.

### F-5. The toll is already in the relative price.
Small orphan series already trade at a liquidity/odd-lot discount. If that discount exceeds the toll deviation, the toll is embedded and the wedge is unidentified.
**Leading indicator:** residualised, within-estate Stage-3 `b'`. Below −0.75 → terminate the position and ship the data product. Above +0.1 → the model is misspecified.

### F-6. Hold-up rent contamination.
Every variable that selects the short leg — small, orphaned, dispersed, unorganised, no ad hoc group — is the textbook definition of the excluded creditor in a coordination game. That effect is 5–40 points versus a sub-point-to-3-point toll.
**Leading indicator:** any RSA amendment or ad hoc group formation that breaks the coalition matching; within-coalition wedge (Test 4) indistinguishable from the unmatched wedge.

### F-7. Congestion exogeneity failure.
Credit cycles congest trustees, court districts, restructuring counsel and financial advisors simultaneously. Controls cannot fully separate trustee-specific capacity from economy-wide professional scarcity. Compounded by the fact that six trustees carry most indentures, so congestion ≈ market share × aggregate default volume.
**Leading indicator:** `β̂_Q` within-trustee with year FE versus pooled; randomisation-inference p-value.

### F-8. Borrow and corporate-action mechanics on the short leg.
Borrow at 100–400bp over an 18–36 month hold costs 1.5–12 points against a sub-point-to-3-point wedge; locate frequently does not exist; and at plan effectiveness the shorted CUSIP is cancelled, requiring a prime broker willing to settle the short by delivery of plan consideration. If it will not, the short must be covered at market pre-cancellation and the cash-settlement logic fails.
**Leading indicator:** realised borrow accrual as a fraction of `|S|`; U6 confirmation refusal rate.

### F-9. Statistical power and data availability.
The intersection of the gates leaves a low single-digit number of usable pairs per decade, and the dependent variable of the latency test is not reliably reconstructable historically (Section 14.2C).
**Leading indicator:** cumulative count of qualifying estates in the Test 0 hand-coding sample; historically reconstructable `n` for Test 1B.

### F-10. Low-rate regime. *(Demoted — no longer applies to the thesis)*
This was previously a first-order failure mode: `r × Latency` was the entire congestion payoff, so at 1% short rates a twelve-month queue was worth ~1 point rather than ~5. **That exposure has been removed with CLL-D.** The traded estimand is a fee quantum and is rate-independent. The residual is that the *hedge* becomes cheaper to run and the float forecast error smaller — both benign. **This item is retained only to record that the previous draft's most-cited magnitude figures ("4–5 points per incremental year", "~1 point at 1% rates") described the withdrawn component, applied to the level rather than the traded deviation, and assumed `R ≈ 1` when defaulted-debt recovery is typically 0.3–0.6. All three errors compounded in the favourable direction.**

### F-11. A live version already exists.
Reorg/Octus and 9fin plan-waterfall models sit behind paywalls that the prior-art search could not read.
**Leading indicator:** the wedge compresses on new cases without any change in the mechanism's inputs; or a vendor ships a trustee-identity field or a **series-level** recovery estimate (which would also break Section 4.6 Step 2).

### F-12. Case conversion.
Chapter 11 → Chapter 7 changes the fee regime entirely (§326 statutory caps replace the indenture charging lien).
**Leading indicator:** motion to convert on the docket.

---

### 12A. Honest caveats — residual weaknesses that survive every repair

These are stated plainly and are not softened. Every item from the previous draft is retained; items 14–20 are new and record defects that could **not** be repaired without destroying the mechanism.

1. **Prior art on the agency structure is complete and unrepaired.** The agent-and-constraint description — passive, liability-minimising trustee that will not act without indemnity, selected by issuer/underwriter who bear no default-state cost, not priced in the new-issue spread, serving holders too dispersed to remove or direct it — is stated almost line for line in Amihud, Garbade & Kahan, *A New Governance Structure for Corporate Bonds*, 51 Stan. L. Rev. 447 (1999); the companion JACF piece (SSRN 255587); and Kahan, *Rethinking Corporate Bonds*, 77 N.Y.U. L. Rev. 1040 (2002). **The economics is prior art; only the pricing expression and the congestion instrument are not.**

2. **Prior art on the fee-scaling prediction is complete and unrepaired.** "`F/SeriesSize`, additive in the number of distinct counsel engagements" is LoPucki & Doherty's professional-fee model (OUP 2011; SSRN 419280, 906184) relabelled from estate level to series level, on a regularity documented since Warner (1977), Ang-Chua-McConnell (1982) and Weiss (1990). Confining the test to within-estate variation narrows but does not eliminate the overlap.

3. **The go/no-go gate is more likely than not to fail.** See F-2.

4. **The marginal-price-setter claim is asserted, not measured.** The repaired mechanism rests on the proposition that recovery estimates are produced at class level and never at series level within a pari passu class. **That is a claim about the contents and granularity of other people's models.** Test 5 is an indirect check and Test 8 has been extended to attack it directly; no direct evidence has yet been gathered. Document-driven distressed funds (Aurelius, Elliott, Attestor, Farallon, Silver Point) occupy exactly the docket-technicality niche the original claimed was empty.

5. **The evidentiary record of the toll consists of organised holders defeating it.** Nortel and Tribune Media are known *because* holders objected and won. Treating objection capacity as a covariate mitigates but does not remove the tension between the equilibrium's premise and its own proof of existence.

6. **Statistical power is a serious risk.** See F-9 and Section 4.8: at `n = 120` the minimum detectable effect is 0.6–0.8 SD, so a null result is weak evidence of absence.

7. **Congestion exogeneity is imperfect.** See F-7. Trustee mandate share is correlated with market segment and therefore with issuer type, and with six trustees dominating, congestion is close to market share × aggregate default volume.

8. **The mechanism's most conspicuous consequence — the queue itself — is not tradable.** CLL-D is withdrawn because a long/short in time-to-cash between two claims on the same estate is a delivery-date basis position, i.e. carry. The queue remains real, remains caused by unrelated issuers, and remains unmeasured; it simply cannot be monetised as a position without taking a banned payoff. **The strongest and most novel part of the mechanism therefore lives only in the data product.**

9. **Transaction costs and borrow exceed the wedge at the stated magnitudes.** See F-1 and F-8. This is not mitigated anywhere; it is the reason Section 11.4 is negative.

10. **The same toll is fully priced in an adjacent market.** ABS/CMBS/CLO waterfalls model trustee and paying-agent fees line-by-line (Intex, Form 424H). This supports persistence but confirms the concept is not novel — only its absence from the corporate cross-section is.

11. **A live version may already exist and could not be ruled out.** The negative search on trustee congestion is **weak evidence of novelty, not proof of it.**

12. **Holding period and mandate fit are poor, and worse than previously stated.** 22–30 months with no interim mark-to-market convergence, negative carry on borrow, and an exit at the mercy of the same illiquidity that creates the opportunity.

13. **No regulator is closing this, which is both the persistence argument and a warning.** Any wedge that were large and easy would likely already have been arbitraged. The defensible position is that it is small, structured and unmeasured — not that it is large.

14. **The information-arrives-after-the-trade objection is unrepaired.** *(New; the previous draft claimed a repair that did not exist.)* The document holds, in Section 13.13, that price never responds to the toll because the variable is not in anyone's dataset. That is incompatible with monetising the fee-mutualisation binary at its public resolution date, because a variable to which price never responds produces no mark when it resolves. The two-payoff-date structure is therefore deleted and the objection stands: **all information relevant to the position arrives at or after the point at which the trade must be placed, and nothing is monetised until cash at distribution.** What would resolve it: a docket-date event study showing that relative prices of series within an estate move on the docketing of differential trustee-fee treatment. If such a move exists, 13.13 is wrong, the strategy has an event-drift component, and Stage 3 should be re-estimated around the disclosure-statement date. That study has not been run.

15. **The disbursing-agent control is not exogenous for latency.** *(New)* Plans that appoint a disbursing agent are plausibly the better-organised, faster, more professionally administered cases. The subsample therefore differs in latency for reasons unrelated to the charging lien. Test 2 has been split so that the fee-component test (2A), which is valid because mutualisation zeroes the fee by construction, is separated from the latency test (2B), which is **not** identified by the disbursing-agent indicator and is reported as descriptive only. **No instrument for queue length that is orthogonal to plan quality has been found.** What would resolve it: an instrument for distribution timing driven by trustee-side operational capacity and not by case quality — trustee back-office system migrations, office relocations, or workout-officer departures would qualify if they could be dated. None is currently observable.

16. **The originality of the surviving position rests entirely on one coefficient.** *(New)* With CLL-D withdrawn, the traded object is a fee-quantum model. Its distinction from conceded prior art (item 2) is *only* that the predictor is cross-issuer trustee congestion and the level of aggregation is the series. **If `β̂_Q` is zero, or if it does not survive the claims-agent/debtor-counsel placebo horse race, nothing original remains and the programme should stop.** This is a narrower base than the previous draft claimed and it is stated as such.

17. **The signing argument now depends on an empirical claim about vendor granularity.** *(New)* Section 4.6 concedes that history-calibrated recovery models embed the *average* toll — the Moody's URD objection is accepted, not deflected — and rests the trade on those models being **class-level** rather than series-level. That is falsifiable and is checked in Test 8, but it has not been checked. If any vendor produces series-level net-of-toll recovery estimates within a pari passu class, the deviation is priced along with the level and the wedge is zero.

18. **The publish-or-kill test may not be executable before deployment, and the ordering does not currently admit this.** *(New)* Section 14.2C states that first-distribution dates are not reliably reconstructable historically. The restructure improves this materially for the *traded* component — Test 1A's dependent variable is charged fee quantum, retrievable from docketed Rule 2016 statements and fee applications, with an estimated historically reconstructable **n ≈ 200–400 case-series observations** — but Test 1B's latency dependent variable remains prospective, with an estimated historically reconstructable **n ≈ 50–90**, below the previously stated minimum of 120. **Test 1B therefore cannot gate anything and is not in the stopping rule.** The latency arm of the research is a multi-year prospective data-collection exercise.

19. **The strategy has no institutional capacity.** *(New)* Section 11.3 puts the responsible NAV ceiling at $25–50m and Section 11.4 puts expected revenue below zero. There is no version of the position specification in this document that supports a fund. This is not a conservatism margin; it is the arithmetic.

20. **Test 7 has been rebuilt because its predicted sign was shared with the conceded prior art.** *(New)* A prepack → prearranged → free-fall gradient is predicted identically by LoPucki-Doherty's professional-fee model and by every generic bankruptcy-cost story, because free-fall cases are longer, more contested and more complex by definition. The previous version of the test could not contribute evidence to the attribution it claimed to establish. It is replaced (Section 15) by a within-case-type congestion gradient. The replacement is a weaker test in absolute power and the document accepts that in exchange for it discriminating at all.

---

## 13. Why this is fundamentally different from known strategies

### 13.0 The stripped-sentence test, applied to the position as it now stands

Before the item-by-item comparison, the position is written out as a single sentence with all narrative removed, because that is the form in which the previous draft's two collapses were visible and its prose was not.

> **I am long the pari passu series of estate `i` whose distributions will bear a smaller charging-lien fee deduction, and short the pari passu series of the same estate — same collateral, same guarantors, same forecast §506(b) status, same creditor coalition — whose distributions will bear a larger one; the size of each deduction is forecast from how many *unrelated* issuers recently defaulted onto each series' indenture trustee; I hold both to cash at distribution and I hedge the difference in settlement dates to zero.**

Checks against the closed categories:

- **Calendar / delivery-date basis, cash-and-carry:** the settlement-date differential is explicitly hedged to zero (Section 8.1) and is not a source of P&L. The payoff survives unchanged at `r = 0`. *This is the specific repair; the previous draft's CLL-L failed here, and the version of it that failed has been withdrawn rather than defended.*
- **Carry:** no premium is earned for holding risk over time; the payoff is a difference in a **cash quantum deducted**, realised at a single terminal event.
- **CDS / cash-CDS basis:** no CDS is used anywhere in the strategy (Section 9.1).
- **Mean reversion / value:** an anchor exists and is stated (Section 4.2). Convergence is not required and is never harvested — see 13.2.
- **Momentum, trend, seasonality, stat arb:** no price-path or return-series input anywhere in the signal.
- **Market making:** the strategy pays 3.5 points round trip and holds 24 months.
- **Volatility risk premium:** no optionality, no convexity.

**What the stripped sentence still concedes:** the payoff object is a professional-fee deduction, which is conceded prior art at estate level. The originality is confined to the predictor and the level of aggregation, and it stands or falls on `β̂_Q` (Section 12A, item 16).

---

Taken item by item. Each entry states the *specific* reason, not a rhetorical one.

**1. Cross-sectional / time-series momentum.** Momentum requires a price path as an input and a price move as the payoff. CLL's input is a docket event and a count of *unrelated* bankruptcies at a shared administrative agent; its payoff is a **cash difference at emergence**, which occurs even if neither leg's price ever moves. A position that pays off with zero price change is definitionally not momentum.

**2. Value / mean reversion.** *(Rewritten — the previous defence was false.)* The previous draft claimed "both require an anchor to which price reverts. CLL claims no such anchor." **That was wrong on the document's own equations:** Section 4.2 supplies an anchor, `E[100·R − τ]`, and the entry rule keys off distance from it. The correct argument is different and stronger: **the anchor exists, but convergence to it is never required and never harvested, because the position is carried to terminal cash settlement.** Every exit in Section 6.1 is a cash or docket event — first holder distribution, mutualisation of the lien, disbursing-agent approval — and not a normalisation of the signal. Stated explicitly: **any exit taken on price convergence before distribution would be a mean-reversion trade, and no such exit exists in Section 6.** The one price-triggered rule that remains (Section 6.3, −4 points versus the long leg over 10 sessions) is a risk-reduction rule on suspected adverse information; it may only ever reduce a position, never take profit, and it is explicitly not a convergence rule. If that rule were ever used to close a profitable position, the strategy would become mean reversion and the classification here would fail.

**3. Carry.** *(Rewritten — the previous defence argued from counterparty identity, which is irrelevant to what a position is.)* The previous draft conceded that CLL-L "looks superficially like a carry/time-value trade" and rebutted it by observing that the mirror side accrues to a trustee who is not a market participant. **Who receives the mirror leg says nothing about the structure of the payoff, and the rebuttal is withdrawn.** The correct treatment is structural: **the time-value component has been removed from the strategy.** The float differential between the two legs' settlement dates is hedged to zero (Section 8.1) precisely because, unhedged, it *would* be a calendar basis position and it *would* be carry — it vanishes at `r = 0`, which is the diagnostic. What remains is a difference in a **cash quantum deducted at the terminal node**, which does not vanish at `r = 0`, is not earned for the passage of time, and is not compensation for bearing a risk over an interval.

**4. Statistical arbitrage / pairs trading.** Stat arb requires a historical cointegrating relationship estimated from a return series. CLL's signal is estimated from **bankruptcy dockets and prospectus trustee-identity fields**, contains no price history, and the pre-registered falsification tests in Section 15 are all runnable **before any return series exists**.

**5. Merger arbitrage / deal-break risk.** Merger arb is a bet on the probability of a binary corporate event completing. CLL-F contains a binary (mutualisation), but the binary is about **who pays an administrative fee**, not whether a transaction closes; CLL-Q is a continuous quantum. Merger arb also has no analogue of a cross-issuer instrument.

**6. Capital structure arbitrage.** Cap-structure arb bets on relative *valuation* of claims with different priority or payoff convexity. CLL is explicitly constructed to hold **priority, collateral, guarantor set and forecast §506(b) status identical** across legs. The residual is topological, not seniority-based. The leg that *was* a cap-structure trade (loan vs pari passu notes) was **deleted** for precisely this reason.

**7. Convertible arbitrage.** No optionality, no volatility exposure, no delta hedge.

**8. Distressed debt / bankruptcy claims trading (the closest neighbour).** Classical distressed investing prices the **estate**: enterprise value, allowed claim pool, plan structure, class treatment. CLL takes the estate's valuation as **given and correctly priced** and trades the residual imposed *after* the estate valuation is fixed and *below* the level at which that valuation is produced. Its signature input — the trustee's *other* clients' defaults — is not in any distressed model. **Caveat, per Section 4.5.5: it is also not exclusively in CLL's model.** A shared claims-agent or debtor-counsel bottleneck would generate the same cross-issuer prediction from a different node. The horse race in Test 1A, not this paragraph, is what establishes the discrimination.

**9. Creditor-on-creditor violence / hold-up rent / LME-victim shorting.** The most dangerous confound and the reason the within-coalition design exists. The naive flagship-vs-orphan pair *is* hold-up-rent shorting and was **deleted** for collinearity. The surviving construction requires both legs to be **co-signatories to the same RSA or represented by the same ad hoc group**. Test 4 is the pre-registered test that, if failed, concedes the strategy was hold-up rent all along.

**10. Liquidity provision / market making.** A market maker earns the bid-ask for immediacy. CLL *pays* 3.5 points round trip and holds for 22–30 months. Further, a liquidity story predicts a **price gap that closes at emergence with no cash gap**; CLL predicts a **cash gap**. Test 6 separates them.

**11. Volatility risk premium / short vol.** No option positions, no variance exposure, no convexity.

**12. Index rebalance / inclusion effects.** Index effects operate through forced flow on a scheduled date. CLL's index-related claim is the opposite: index holders are *ejected before the toll is levied*, which is why the original "index funds pay" claim was **withdrawn**.

**13. Post-earnings-announcement drift / event drift.** PEAD requires a public information release and a slow price response. **CLL claims price never responds**, because the variable is not in anyone's dataset. A drift study would find no drift and the cash payoff would still occur. **This claim is retained, and Section 10 has been rewritten to be consistent with it:** because price never responds, nothing is monetised at the disclosure-statement date and both components pay only in cash at distribution. The previously claimed two-payoff-date structure was incompatible with this item and has been deleted rather than allowed to stand alongside it.

**14. Seasonality / calendar effects.** No date-of-year dependence.

**15. Trend following / managed futures.** No price-trend input; no futures.

**16. Risk parity / factor timing / low-vol / size / quality.** Loadings on priced systematic factors estimated from returns. CLL's signal is a legal-administrative variable with no return-series input. The one superficially size-like element (`F/SeriesSize`) is (a) demoted to a covariate, (b) tested only **within estate**, and (c) acknowledged as LoPucki-Doherty prior art.

**17. CDS basis / cash-CDS arbitrage.** *(Rewritten — the previous defence conceded the problem.)* The previous draft used single-name CDS as the estate hedge in what it called its default expression, and defended the classification by saying "the strategy makes no claim about the relationship between CDS and cash spreads." **That is the reason it collapsed, not the reason it did not:** a hedge held 22–30 months, sized to neutralise estate exposure, on which the strategy has no view, dominates a sub-3-point wedge by an order of magnitude. **CDS has been removed from the strategy entirely** (Section 9.1). Estate exposure is neutralised with a second cash claim on the same estate, which is what makes the expression a two-cash-leg pair and is what collapses the capacity to the number in Section 11.2.

**18. Recovery-rate trading.** Recovery trading takes a view on `R`. CLL takes `R` as given and trades `τ̃`, the **within-class deviation** in a deduction defined downstream of `R`. A vendor that improved its estimate of `R` to perfection would not close the wedge, because `R` is estimated at class level and `τ̃` varies *within* the class. **This is now the cleanest structural separation available and it is also the load-bearing empirical claim of Section 4.6, Step 2** — if any vendor moves to series-level recovery estimates, this separation and the wedge disappear together.

**19. Litigation finance / legal-outcome betting.** Litigation finance bets on the merits of a claim. CLL bets on a **queue position and a billing quantum at an administrative intermediary**, which is not adjudicated and has no merits.

**20. Professional-fee / bankruptcy-cost research (LoPucki-Doherty).** This is a **partial and now larger** overlap, conceded rather than denied. With CLL-D withdrawn, the traded object *is* a professional-fee object. LoPucki-Doherty predicts **estate-level** fee variation from case characteristics; CLL predicts **series-level, within-estate** variation from **cross-issuer congestion at a shared trustee**, which is not a variable in their model or in any successor. The estate fixed effect makes the two orthogonal in specification. **But the overlap is now the strategy's whole payoff object, and the originality is confined to the predictor.** See Section 12A, item 16.

**The single property no item on this list shares:** every strategy above derives its signal from the traded instrument's own issuer, its own price history, or a systematic factor. CLL derives its primary signal from **a congestion externality at a shared administrative intermediary, caused by issuers the position has no exposure to.** That property is genuinely unusual — and Section 4.5.5 records that it is *not* unique to the trustee node, which is why the placebo horse race is mandatory before the property is claimed as discriminating.

---

## 14. Data required

### 14.1 Exists today, point-in-time available

| Data | Vendor / source | Fields | Frequency | History | PIT? |
|---|---|---|---|---|---|
| Chapter 11 dockets | PACER / CM-ECF; Docket Alarm, CourtListener/RECAP | Full filings incl. disclosure statements, plan supplements, trustee fee applications, **Rule 2016 statements**, confirmation orders | Continuous | Electronic filing from ~2001, patchy before | Yes — filings are timestamped |
| Large-case dataset | UCLA-LoPucki Bankruptcy Research Database (BRD) | Case size, duration, district, prepack flag, outcome | Case-level | 1980– | Yes |
| Bond reference / indenture identity | Prospectuses & OMs via SEC EDGAR (424B, S-1, S-4); Bloomberg DES; Refinitiv | **Trustee name**, indenture date, series size, collateral, guarantors | Issuance | 1996– (EDGAR full text) | Yes, by filing date |
| Bond prices | TRACE (FINRA); Bloomberg BVAL; ICE; Markit | Price, yield, volume | Daily/intraday | TRACE 2002– | Yes |
| Recovery data | Moody's Ultimate Recovery Database / Default & Recovery Database | **Price at default paired with settlement value at resolution**, at **class** level | Case | 1987– | Yes |
| Index membership | Bloomberg/Barclays, ICE BofA | Eligibility flags | Monthly | 1990s– | Yes |
| Rates | Bloomberg, LCH | OIS curve | Daily | Long | Yes |
| District docket load | Administrative Office of US Courts, Table F | Filings by district | Quarterly | Long | Yes |
| Aggregate default rate | Moody's / S&P | Trailing 12m spec-grade default rate | Monthly | Long | Yes |
| Claims agent / debtor counsel / FA identity per case | Docket first-day filings; retention applications | Firm identity, retention date | Case | 2001– | Yes |

**Note, correcting an earlier claim, and note what it now implies.** The assertion that "the price-versus-realised-cash dataset does not exist" is **withdrawn**. Moody's URD pairs price at default with settlement value at resolution and has been commercially available for two decades. **This is not merely a narrowing of the data-moat claim; it is load-bearing against the strategy and Section 4.6 has been rebuilt around it.** Because settlement value is realised, net-of-toll cash, any recovery model calibrated to URD embeds the **average** toll mechanically. The level is therefore priced, and the only tradable object is the **within-class deviation**, which URD does not resolve because its settlement values are reported at class level. The data moat claim is narrowed to the **trustee-identity and trustee-congestion mapping** and to **within-class dispersion**.

### 14.2 Does not exist — must be constructed

**A. CUSIP → indenture trustee map.** Trustee identity is **not a field in any index vendor's or terminal's security master**. Extracted from prospectus/OM text via EDGAR full-text search plus NLP extraction on the "Trustee" caption and the Article VII heading, with manual verification. Estimated 15,000–25,000 US corporate CUSIPs for a 20-year panel; ~2–4 analyst-months plus tooling, then maintained at issuance.

**B. Trustee concurrent-mandate congestion panel — the primary research object.** For each major corporate trustee, **monthly**, the count and aggregate allowed claim value of **new large Chapter 11 mandate arrivals in the trailing 12 months** (primary) and of concurrently active mandates (robustness). Constructed by joining (i) the docket universe, to (ii) the CUSIP→trustee map, to (iii) claim registers and plan class amounts. **This is the panel the prior-art audit could not find anywhere in print, in any product, or in any vendor field.** ~3–5 analyst-months for a 20-year history; thereafter maintained monthly.

**B2. Parallel congestion panels for claims agents, debtor-counsel firms and financial advisors.** *(New — required by the placebo horse race in Test 1A, without which the trustee attribution cannot be established.)* Same construction, keyed on retention applications rather than indentures. ~1.5–2.5 analyst-months. **This panel is not optional and is not a robustness check; Test 1A cannot be run without it.**

**C. Realised distribution latency.** Days from **plan effective date** to **first holder distribution**, plus count and timing of interim distributions. Sources: plan administrator reports, post-effective-date docket entries, DTC corporate-action records, trustee notices to holders. **Coverage is incomplete and inconsistent; estimated historically reconstructable n ≈ 50–90 case-series observations.** For a meaningful fraction of cases this must be **collected prospectively**. This is the largest data risk in the latency arm — and it is why the latency arm has been removed from the deployment stopping rule (Section 15) rather than left there as an unreachable terminal node.

**D. Trustee fee quantum actually charged against holder distributions — now the dependent variable of the publish-or-kill test.** From fee applications and Rule 2016 statements, net of objection outcomes. Docketed and free, but requires per-case reading. **Estimated historically reconstructable n ≈ 200–400 case-series observations** for post-2004 large cases. This is materially better coverage than (C), and moving the publish-or-kill test onto this variable is a direct consequence of moving the traded estimand onto fee quantum. ~3–4 analyst-months.

**E. Plan treatment classification (categories (a)–(e)), coded at series level.** Hand-coded from disclosure statements and plan supplements. **No vendor provides this.** 150–250 cases for the Test 0 gate; ~1.5 analyst-months. Series-level coding, not estate-level, because Section 5.1 U4 now requires it per leg.

**F. RSA / cooperation-agreement co-signatory rosters at series level.** Extracted from RSA exhibits and Rule 2019 statements. Partially machine-readable; substantially manual.

**G. Disclosure-statement valuation ranges, for the `π^506` oversecurity forecast.** Hand-extracted; required by U3.

### 14.3 Flagged for prospective collection

- **Realised distribution latency (C)** — the dependent variable of the latency arm. Historical coverage is the binding limitation; a forward-collection protocol must start on day one. **The latency arm is a multi-year prospective exercise and cannot gate anything before then.**
- **Trustee workout staffing levels** — not disclosed anywhere. Would strengthen the capacity story (it is the actual `S` in the supply curve) but is unobtainable. The congestion panel is the proxy.
- **Prime-broker willingness to carry distressed shorts through plan corporate actions** — not documented anywhere; must be established bilaterally per case (U6) and recorded, since the refusal rate is a direct input to Section 11.2.

### 14.4 Paywalled and uninspected

Reorg/Octus and 9fin plan-waterfall models. These are the most likely location of an undisclosed live version and could not be read. Subscriptions should be acquired before any capital deployment, specifically to check whether (i) trustee-fee treatment, (ii) distribution timing, and (iii) **series-level as opposed to class-level recovery estimates** are already modelled fields. Item (iii) is new and is decisive for Section 4.6.

### 14.5 The data product — now the primary deliverable, not the fallback

The deliverable is a **CUSIP-level net-of-toll recovery estimate**: modelled class recovery, minus predicted series-level baseline fee burden, minus predicted congestion-driven fee quantum, minus predicted congestion-driven latency cost. This is a correction to every published recovery series (Moody's URD, S&P LossStats, rating-agency recovery ratings) at a granularity none of them offers, and it is useful whether or not a position is expressible.

**This is stated as the primary output rather than an acceptable terminal outcome, because Sections 9.4, 11.2 and 11.4 say the position loses money at the magnitudes this document is willing to defend.** The three assets that survive every repair in this revision — the trustee-identity map (14.2A), the congestion panel (14.2B), and the leave-one-out cross-issuer identification design — are all inputs to the product and none of them requires a position to have value. In particular, the **latency** forecast, which cannot be monetised as a position because trading it is trading a float differential, is a legitimate and possibly the most valuable field in the product.

The position specification in Sections 5–11 is retained in full and becomes live only if Test 1C returns a within-estate `|S|` distribution whose 90th percentile clears the derived entry gate.

---

## 15. How to falsify the hypothesis BEFORE any backtest

Every test below uses **cross-sectional, institutional or structural evidence**. None requires a return series. Each has a pass/fail threshold **set in advance**. The tests are ordered so that the cheapest killers run first, and — a change from the previous draft — **no test whose data is not historically reconstructable appears in the stopping rule.**

---

### TEST 0 — The go/no-go gate on plan treatment. *(Run first. No capital before this.)*

**Method.** Hand-code, across a docket sample of **150–250** large Chapter 11 cases with public indentures (stratified by year, district and case size, from the LoPucki BRD frame), how each plan resolves indenture trustee fees **for each series separately**:

- (a) estate-paid administrative expense
- (b) §503(b)(5) substantial contribution
- (c) §506(b) add-on to an oversecured claim
- (d) **charging lien preserved and exercised against holder distributions**
- (e) **capped with lien preserved above the cap** (the Nortel form)

Only (d) and (e) generate a toll on that series. **Also record, for each estate, whether treatment differs across series** — this is the Branch F gate in Section 11.2 and it has never been measured.

**Why it is ex ante, not hindsight:** plan treatment is disclosed in the disclosure statement and plan supplement, i.e. **before the effective date**, and often before confirmation.

**Pass:** (d)+(e) ≥ **25%** of cases, **weighted by claim value**.
**Fail:** below 25% → **CLL-F is dead as a cross-sectional trade** and CLL-Q is restricted to the shrinking both-legs-(d)/(e) subset.
**Stated prior:** practitioner sources describe negotiating estate payment as *standard practice*. **The prior on failing this gate is high. A failure here is the expected outcome, not a surprise.**

---

### TEST 1A — PRIMARY. Congestion predicts the fee quantum. *(Publish-or-kill.)*

**Hypothesis.** The trustee and trustee's-counsel fees charged against a series under the charging lien rise in the trustee's concurrent mega-mandate load, measured as **trailing-12-month leave-one-out new-mandate arrivals at T-0** — the same measure and the same timing convention used in deployment (Section 4.7).

**Specification.** Section 4.3, Stage 1, with estate fixed effects wherever two or more series of the same estate are observed, and **with the placebo horse race**: claims-agent congestion, debtor-counsel congestion and financial-advisor congestion entered **simultaneously**, each constructed identically and leave-one-out.

**Sample.** Fee applications and Rule 2016 statements for large Chapter 11 cases with public indentures. Estimated historically reconstructable **n ≈ 200–400** case-series observations across **≥ 8 distinct trustees** and **≥ 10 calendar years** (Section 14.2D). Minimum viable **n = 150**.

**Inference.** Wild cluster bootstrap-t at the trustee level (9,999 reps) **and** randomisation inference permuting congestion across trustees within year (9,999 draws). **Effective cluster count reported with the coefficient. Minimum detectable effect reported before the coefficient.**

**Pass:** `β̂_Q > 0` with randomisation-inference **p < 0.05**; the within-trustee (year-FE) estimate retains **≥ 60%** of the pooled magnitude; **and** `β̂_Q` retains **≥ 50%** of its single-instrument magnitude in the joint specification with the three placebo congestion measures.
**Fail:** any of the above unmet → **the thesis is fiction.** What remains is LoPucki-Doherty applied at series level, which is not original enough to justify the programme as a position. **Kill the position there; the data product may continue on the descriptive panel.**

**What this test does and does not establish.** *(Corrected — the previous draft claimed too much.)* It establishes that fee quantum is predicted by the defaulting behaviour of unrelated issuers sharing an administrative intermediary. It does **not**, on its own, establish that the intermediary is the *trustee*: a shared claims-agent, debtor-counsel or FA bottleneck predicts the same coefficient from a node that is not mapped at CUSIP level and is not tradable via the trustee-identity map. **The previous draft's claim that "no competing explanation can pass this test" was false and is deleted.** The horse race, not the cross-issuer keying alone, is what discriminates.

---

### TEST 1B — Congestion predicts latency. *(Descriptive. Not a gate. Data product only.)*

**Hypothesis.** Days from plan effective date to first holder distribution rise in trailing-12-month leave-one-out mandate arrivals at the trustee, with the same placebo horse race.

**Sample.** Estimated historically reconstructable **n ≈ 50–90** (Section 14.2C), below any threshold at which the inference in Section 4.8 has power. **This test cannot gate deployment and does not appear in the stopping rule.** It is run on whatever historical data exists, reported as reduced-form and descriptive, and re-run annually as prospective collection accumulates.

**Why it is not a gate:** because the latency object is not traded (CLL-D withdrawn), nothing in the position depends on it. It is an input to the data product only. Placing a stopping-rule terminal node on a variable that Section 14.2C says is not reliably reconstructable — as the previous draft did — makes the stopping rule unexecutable and defers the publish-or-kill gate by however many years prospective collection takes.

---

### TEST 1C — The magnitude test. *(Mandatory, and run BEFORE any price work.)*

**Hypothesis to be measured, not assumed:** the **within-estate deviation** in predicted toll, `|S|`, is large enough to clear the derived entry gate of Section 5.3.

**Method.** From the constructed panel, and before touching any price data: report the full empirical distribution of within-estate `Δτ` between pari passu series under distinct indentures, decomposed into (i) baseline fee deviation (CLL-F) and (ii) congestion-driven quantum deviation (CLL-Q). Report each component's contribution to `|S|` separately. Also report the distribution of within-estate `ΔL` and the implied float term, **for the data product only**, so that the reader can see how much of the previously claimed wedge lived in the withdrawn component.

**Pass:** the 90th percentile of `|S|` **from CLL-Q alone** exceeds the derived entry gate (Section 5.3).
**Fail:** it does not → **the thesis component is untradable at the stated cost structure.** Kill Criterion 6 fires; the position is not deployed; the programme continues as the data product.
**Stated prior:** Section 9.4 puts CLL-Q at 0.2–1.0 points against a gate of 5.7–10.3 points. **The prior on failing this test is very high, and it is the single most likely terminal outcome of the programme.** It is placed third, immediately after the two cheapest gates, precisely because it is likely to end the position arm before any price work is paid for.

---

### TEST 2A — The off-switch, fee component. *(Valid control.)*

**Hypothesis.** The **traded** toll is exactly zero for series whose trustee fees are paid by the estate — whether through a plan-appointed disbursing agent, a §503(b)(5) award, a §506(b) add-on, or plan boilerplate releasing the charging lien.

**Why this is valid:** under Section 4.2, `(1 − m)` multiplies both traded terms, so mutualisation zeroes the traded estimand by construction. It mutualises the toll while leaving **every** fundamental, seniority, collateral, liquidity and holder-composition variable unchanged.

**Pass:** estimated charged fee against holder distributions in the mutualised subsample is statistically indistinguishable from zero, and its point estimate is **< 25%** of the non-mutualised subsample.
**Fail:** fees persist at ≥ 50% of magnitude in the mutualised subsample → the classification of plan treatment is wrong, or fees are being charged outside the identified channels, and the causal attribution is wrong.

---

### TEST 2B — The off-switch, latency component. *(Descriptive only. Explicitly not identified.)*

**Hypothesis as previously stated:** latency is unaffected by the appointment of an estate-paid disbursing agent, because the estate paying the agent's *fees* does nothing to the *queue* — cash still arrives on some date, and the queue has merely moved to a different intermediary.

**Why this cannot be a control test.** The disbursing-agent indicator is **not exogenous for latency**: plans that appoint a disbursing agent are plausibly better-organised, faster and more professionally administered cases, so the subsample differs in latency for reasons unrelated to the charging lien. The previous draft asserted that "the wedge is exactly zero" for disbursing-agent series and made the failure of that assertion a TERMINATE condition. Under its own Section 4.2 equation the assertion was false for the latency term, and the control was confounded besides.

**What is run instead:** the disbursing-agent latency comparison, propensity-matched on case size, district, prepack status, class count and elapsed duration to T-0, reported with the matching diagnostics and **no pass/fail threshold**. **No instrument for queue length that is orthogonal to plan quality has been found** (Section 12A, item 15). This test is descriptive input to the data product and appears nowhere in the stopping rule.

---

### TEST 3 — Within-estate scaling of the fee component.

**Hypothesis.** `F/SeriesSize` scaling and additivity in the number of distinct indenture trustees, **tested within estate only** — because the across-estate version is LoPucki-Doherty's published model and cannot be claimed as new content.

**Pass:** within-estate elasticity of per-claim fee burden to series size is **negative and within [−1.3, −0.7]**, significant at 5%; and the coefficient on number of distinct indentures is **positive** and significant at 5%.
**Fail:** elasticity indistinguishable from zero, or outside [−1.5, −0.5] → the fee is not a fixed per-indenture cost and the cost model is wrong.

---

### TEST 4 — Coalition control. The hold-up-rent discriminator.

**Hypothesis.** The wedge survives **within RSA co-signatory pairs** — series that are pari passu, share collateral package, guarantor set and forecast §506(b) status, **and** are co-signatories to the same restructuring support or cooperation agreement (or represented by the same ad hoc group), but sit under **different indentures with different trustees**.

**Why:** this is the only construction in which the administrative chain varies while **hold-up rent does not**. Every variable that would otherwise select the short leg — small, orphaned, dispersed, unorganised, no ad hoc group — is the textbook definition of the excluded creditor in a coordination game, an effect of 5–40 points against a sub-3-point toll.

**Pass:** the within-coalition wedge is **≥ 60%** of the unmatched wedge and significant at 5%.
**Fail:** the within-coalition wedge is **< 30%** of the unmatched wedge, or insignificant → **the original construction was liability-management-victim shorting in a lab coat and must be abandoned.**

---

### TEST 5 — Price test before any position. *(Mandatory. No capital before this.)*

**Hypothesis to be tested, not assumed:** relative price within an estate does not already embed the relative toll.

**Method.** Estimate the **residualised, within-estate** Stage 3 of Section 4.3:

```
(P_{i,s} − P̄_i)  =  a' + b'·τ̃^⊥_{i,s} + φ·ΔLiquidity + ψ·ΔSeriesSize + η_i + v
```

with estate fixed effects `η_i` and with `τ̃^⊥` orthogonalised against `R̂_i` and `R̂_i·r_t·L̂` before entry, and with liquidity controls (odd-lot flag, TRACE print frequency, quoted depth) so the odd-lot discount does not masquerade as toll pricing.

**Why the specification changed.** The previous version regressed the *level* of price on the *level* of `τ̂` with recovery omitted, while `τ̂` was mechanically proportional to `R̂`. Under the null that price fully embeds the toll, that regression returns `Cov(P,τ) = 100·Cov(R,τ) − Var(τ)`; at `sd(R) ≈ 0.3` the first term swamps the second and drives `b̂'` positive — into or above the stated pass band **regardless of the truth**. The test could not reject its own null, and it had **no branch at all** for `b' > 0.1`, which was the modal outcome under that bias. Estate fixed effects absorb `R_i` (the legs are pari passu with identical collateral and guarantors, so they share `R`), and orthogonalisation removes any residual loading. Bands below are re-derived for the residualised specification, in which `b'` is a partial-embedding fraction rather than a recovery-contaminated slope.

**Pass (tradable):** `b' ∈ (−0.4, 0.1]` → less than 40% of the deviation is embedded; the tradable wedge is `(1+b')·τ̃`.
**Ambiguous:** `b' ∈ (−0.7, −0.4]` → partial embedding; proceed at half size only, and note that Section 7.1's `E_j` gate tightens automatically as `(1 + b̂')` falls, which at `b' = −0.5` roughly doubles the required `|S|`.
**Fail (real but untradable):** `b' ≤ −0.7` → **the mechanism is REAL AND UNTRADABLE.** Ship the data product.
**Fail (misspecified):** **`b' > 0.1`** → relative price is *higher* for higher-toll series, which the residualised within-estate specification cannot produce through the recovery channel. Candidate causes: hold-up rent or odd-lot liquidity correlated with both, or measurement error in `τ̃` correlated with price. **Re-specify once, adding coalition status and a finer liquidity control. If `b' > 0.1` survives, the toll model is wrong: do not trade, and do not ship the product until the sign is explained.** *(The previous draft had no branch here at all.)*

---

### TEST 6 — Discrimination against every rival explanation.

Each rival makes a *different* prediction. The test is joint: the data must match CLL's prediction and violate the rivals'.

| Rival explanation | Its prediction | CLL's prediction | Discriminating observable |
|---|---|---|---|
| Liquidity / odd-lot | A **price** gap that closes at emergence, **no cash gap** | A **cash** gap | Charged fee quantum from fee applications (Test 1A), which is docketed and reconstructable |
| Seniority / covenant differences | Gap **constant in absolute size** | Gap **proportional to 1/SeriesSize** | Scaling exponent (Test 3) |
| Holder clientele | Variation with **index membership** | Variation with **charging-lien treatment** | Index-eligibility flag vs plan structure (Test 2A) |
| Professional-fee cost (LoPucki-Doherty) | **Estate-level** variation from case characteristics | **Series-level** variation from **shared-trustee congestion** | Estate fixed effect (Test 3) **and** `β̂_Q` (Test 1A) |
| Hold-up rent / creditor-on-creditor | Gap driven by **coordination**, vanishes when coordination is held fixed | Gap **survives** coalition matching | Within-RSA subsample (Test 4) |
| **Shared non-trustee bottleneck** (claims agent / debtor counsel / FA) | **Same cross-issuer congestion coefficient**, different node | Trustee congestion retains ≥ 50% of its magnitude when the other three are entered simultaneously | **Placebo horse race in Test 1A** |

**Change from the previous draft.** The final row previously read "**All of them** | **None predicts Test 1**", which was false: the shared-bottleneck rival predicts Test 1's coefficient identically, and default clustering plus time-varying trustee market share reproduce much of it. **That row is deleted and replaced by the horse race above, which is the only thing that actually discriminates.**

**Pass:** CLL's column holds and at least four rivals' predictions are rejected at 5%, **including the shared-bottleneck row.**
**Fail:** any rival's prediction fits the data as well as CLL's on its own discriminating observable → attribution unresolved; do not deploy.

---

### TEST 7 — Within-case-type congestion gradient. *(Rebuilt.)*

**Why the previous version was deleted.** It predicted a monotone prepack → prearranged → free-fall gradient with the free-fall estimate ≥ 2× the prepack estimate. **The conceded prior art predicts exactly the same gradient:** LoPucki-Doherty's central result is that professional fees rise with duration, contestedness and complexity, and free-fall cases are longer, more contested and more complex by definition. So does every generic bankruptcy-cost story. The test passed under CLL and under the rival simultaneously and contributed no evidence to the attribution it claimed to establish. A test whose predicted sign is shared with acknowledged prior art cannot appear in a falsification battery.

**Replacement hypothesis.** Hold case type **fixed** and vary only the trustee-side variable: **within free-fall cases only**, and separately within prearranged cases only, the congestion coefficient `β̂_Q` remains positive and retains **≥ 60%** of its pooled magnitude. Case type is additionally entered as a control in the pooled specification, so that the congestion effect must be **incremental to** the workout-intensity gradient rather than a restatement of it.

**Pass:** `β̂_Q` positive and ≥ 60% of pooled magnitude within free-fall cases alone, and positive within prearranged cases alone, with case-type controls included in the pooled specification.
**Fail:** the congestion coefficient is present only across case types and vanishes within them → the effect is workout intensity, which is prior art, and nothing original remains.

**Acknowledged cost:** conditioning on case type shrinks the sample and reduces power. This is accepted, because the previous test had no discriminating power at any sample size.

---

### TEST 8 — Institutional evidence on the marginal price-setter. *(Addresses the weakest link. Extended.)*

The mechanism rests on a claim about **the contents and granularity of other people's models**. That claim must be attacked directly, not only inferred from Test 5.

**Method.** (i) Subscribe to Reorg/Octus and 9fin and inspect whether their plan-waterfall models contain a **series-level trustee fee line** and a **distribution-timing field**. (ii) Review sell-side distressed research on 20 recent large cases for any mention of charging liens or trustee identity. (iii) Check whether any index vendor, terminal or reference-data provider has added a trustee-identity field. (iv) **New and decisive for Section 4.6:** check whether any recovery vendor (Moody's, S&P LossStats, rating-agency recovery ratings, or the paywalled services) produces recovery or net-of-toll estimates at **series level within a pari passu class**, as opposed to at class level.

**Pass:** none of the four checks returns a positive.
**Fail (i)–(iii):** a live version likely exists; assume the wedge is competed and reduce expected magnitude to zero pending direct evidence.
**Fail (iv):** **Section 4.6, Step 2 collapses.** If recovery estimates exist at series level, the within-class deviation is priced along with the level and there is no wedge at all — neither in the level (conceded to URD calibration) nor in the deviation. This is the cleanest single kill in the document and it costs one subscription to check.

---

### Ordering and stopping rule

```
Test 0   →  fail → drop CLL-F; continue on CLL-Q only, in the both-legs-(d)/(e) subset
Test 8   →  fail (any branch) → TERMINATE (already arbitraged, or no wedge exists at all)
Test 1C  →  fail → DO NOT DEPLOY A POSITION; the wedge is smaller than the cost of trading it.
                   Continue as the data product (Section 14.5). *Most likely outcome.*
Test 1A  →  fail → TERMINATE THE POSITION PROGRAMME (thesis is fiction; panel may still be built)
Test 2A  →  fail → TERMINATE (causal attribution wrong)
Test 4   →  fail → TERMINATE (it was hold-up rent)
Test 3, 6, 7  →  fail → do not deploy; attribution unresolved
Test 5   →  fail (either branch) → DO NOT TRADE; ship the data product instead
Test 1B, 2B  →  descriptive only; never gate anything
```

Only if Tests 1A, 1C, 2A, 4, 6, 7 and 8 pass and Test 5 lands in the tradable or ambiguous range does any capital move.

**Stated priors on the outcome, in order of likelihood.** (1) **Test 1C fails** — the within-estate toll deviation is smaller than the round-trip and borrow cost, the position never trades, and the programme is a data product. This is the modal outcome on the arithmetic in Section 9.4 and Section 11.4. (2) **Test 0 fails** and CLL-F is dead, leaving CLL-Q in a shrinking subset. (3) **Test 1A fails**, or fails the placebo horse race, and nothing original remains. (4) Everything passes and the position trades at the capacity in Section 11.2, which is under one estate per year. **Only outcome (4) involves a position, and it is the least likely of the four.**

---

*Document status: pre-registration. No backtest has been run and none should be run before Tests 0, 8, 1C, 1A, 2A, 4 and 5 have returned. A mechanism that cannot be killed without a backtest is not a scientific hypothesis. On the parameters this revision is willing to defend, the arithmetic says the position loses money and the research output is a forecasting product; that conclusion is stated in Section 1 and again in Sections 11.4 and 14.5 rather than buried, because it is what the numbers say.*
