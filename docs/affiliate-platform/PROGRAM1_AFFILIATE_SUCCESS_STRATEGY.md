# Program 1 — Affiliate Success Strategy

Status: GOVERNING BUSINESS STRATEGY BASELINE
Date: 2026-09-04
Scope: Program 1 — Affiliate Opportunity Intelligence
Governing method: DOCUMENT-DRIVEN / STRATEGY-FIRST / EVIDENCE-FIRST

## 1. Purpose

Program 1 exists to improve the probability that affiliate effort is spent on the right products, at the right time, for the right audience and content opportunity.

Program 1 is not primarily a scraper, crawler, browser extension or product catalog. Those are implementation mechanisms.

The governing business question is:

> Which product opportunities should we pursue next to maximize expected affiliate success per unit of effort, and why?

The platform must therefore optimize for decision quality, not collection volume.

## 2. Program 1 Mission

Program 1 shall discover, observe, qualify and prioritize **affiliate opportunities**, not merely popular products.

A product becomes interesting when market evidence indicates that it may be commercially attractive for affiliate promotion under a specific context.

Program 1 must progressively help answer:
- what buyers appear to want now;
- which demand signals are rising, stable or falling;
- which products are commercially attractive for affiliate promotion;
- which products offer useful content angles;
- which opportunities fit target audiences/accounts;
- which opportunities are timely for current events, campaigns or seasons;
- which opportunities deserve scarce content/marketing effort first;
- which opportunities should be tested, scaled, watched, deprioritized or stopped;
- why the system reached each recommendation.

## 3. Strategy Leads Engineering

Program 1 follows this authority chain:

```text
Affiliate / Marketing Strategy
        -> Business Questions / Hypotheses
        -> Required Decision Signals
        -> Data / Evidence Requirements
        -> Collection / Observation Requirements
        -> Domain Features / Rules
        -> Engineering Implementation
        -> Experiment / Outcome
        -> Learning
```

Engineering must not collect a field merely because it is technically available.

Every proposed signal must answer:

> What affiliate decision does this signal improve?

If the decision value is unknown, the signal remains optional/research evidence until justified.

## 4. Affiliate Success Model

Program 1 evaluates opportunity through multiple dimensions. No single dimension is sufficient.

Candidate dimensions include:

### 4.1 Market Demand
- observed sales/sold signals;
- search/query relevance;
- ranking/placement context where observed;
- review/rating volume as social-proof evidence;
- category/shop demand context;
- historical demand changes.

### 4.2 Momentum / Timing
- sales momentum;
- price movement;
- promotion changes;
- ranking/visibility movement;
- seasonal or campaign timing;
- newly emerging versus already saturated demand.

### 4.3 Buyer Intent
Program 1 should distinguish broad interest from purchase-oriented intent where evidence allows.

Examples of higher-intent context may include:
- product + use case;
- product + price/value constraint;
- product + compatibility/model;
- product + problem to solve.

Intent interpretation must be versioned and evidence-based.

### 4.4 Affiliate Economics
Where Program 2 or another approved source provides evidence:
- commission/rate/value;
- promotion/offer quality;
- offer freshness;
- expected economics relative to effort.

Program 1 may consume approved economic features through versioned cross-program contracts but must not duplicate Program 2 offer authority.

### 4.5 Contentability
Program 1 must consider whether a product provides useful content opportunities.

Candidate contentability signals:
- demonstrability;
- clear problem/solution;
- before/after potential;
- comparison potential;
- visible benefit;
- novelty/surprise;
- value/price hook;
- useful-hack angle;
- gifting/seasonal angle;
- suitability for short-form content.

Contentability is a business feature, not a browser-worker responsibility.

### 4.6 Competition / Saturation
Where measurable:
- number/density of comparable products;
- apparent offer sameness;
- content saturation proxies;
- price competition;
- differentiated positioning opportunities.

### 4.7 Seller / Fulfilment Confidence
Where observable and permitted:
- seller/shop quality signals;
- rating/review confidence;
- availability/stock evidence;
- shipping/fulfilment evidence;
- stability of listing/product availability.

### 4.8 Audience / Account Fit
A product does not have one universal opportunity score for every audience.

Future ranking may evaluate:

```text
Product x Audience/Account x Content Angle x Time Context
```

Program 1 should preserve the provenance necessary to support this without making the browser worker aware of marketing policy.

### 4.9 Risk
Candidate risks:
- weak or ambiguous identity;
- stale/insufficient evidence;
- unstable seller/listing;
- extreme competition;
- weak contentability;
- uncertain offer economics;
- schema/parser uncertainty;
- platform access/collection instability.

Unknown must remain unknown; uncertainty must not be converted into optimistic scores.

## 5. Opportunity Thesis

A qualified candidate should eventually be explainable as an **Opportunity Thesis**, for example:

```text
Why now:
Target buyer:
Observed evidence:
Commercial strengths:
Content angles:
Risks / uncertainties:
Recommended action:
Evidence freshness:
Policy/model version:
```

Recommended actions may evolve but should conceptually support:

`TEST_NOW | WATCH | SCALE | HOLD | DEPRIORITIZE | STOP | NEEDS_EVIDENCE`

These are business decisions owned by Back Office policy/engines, not workers.

## 6. Program 1 Funnel

Program 1 should reduce noise progressively:

```text
Market Observations
        -> Product Identities
        -> Interesting Candidates
        -> Qualified Opportunities
        -> Ranked Opportunities
        -> Action Candidates
        -> Program 2 Handoff
```

Success is not maximizing the first number.

The system should become better at concentrating effort on the final stages.

## 7. Data and Intelligence Separation

Program 1 preserves separation between:

```text
Observed Fact
    -> Normalized Fact
    -> Derived Feature
    -> Business Decision
```

Example:

```text
Observed: "฿989"
Normalized: 989 THB
Derived: price_change_7d = -12%
Decision feature: price_attractiveness = HIGH
Opportunity decision: TEST_NOW
```

Browser workers may report observed facts and collection context. They must not own derived business scores.

## 8. Historical Observation Is Required

A snapshot is often insufficient for intelligence.

Program 1 should preserve append-oriented time-stamped observations so that engines can derive:
- trend;
- momentum;
- freshness;
- volatility;
- persistence;
- change-point evidence.

The system must not overwrite historical observations merely to maintain a current projection.

## 9. Evidence-First Policy

Shopee-specific fields, selectors, identities and thresholds remain evidence-gated.

A signal lifecycle should conceptually support:

`EXPERIMENTAL -> LAB_VALIDATED -> EVIDENCE_VALIDATED -> PRODUCTION_CANDIDATE -> PRODUCTION_APPROVED -> DEPRECATED`

Promotion requires appropriate repeated evidence and regression fixtures.

Anti-bot/access-control conditions must fail closed. Program 1 must not rely on bypassing authentication, platform controls, CAPTCHA, anti-bot mechanisms or rate limits.

## 10. Scoring Policy

Program 1 must not invent a production 0-100 opportunity formula before outcome evidence exists.

Early phases should favor:
- feature collection;
- deterministic qualification rules;
- explainable filtering;
- component scores where justified;
- human review;
- controlled experiments.

Exact weights/formula remain a validation gate.

Once outcome data exists, future model evolution may use measured relationships between candidate features and:
- clicks;
- conversion;
- orders;
- commission;
- cancellations/refunds where available;
- net affiliate value;
- content effort/cost.

All decisions must retain model/ruleset version and feature/evidence references.

## 11. North-Star Outcomes

Program 1 should not use raw products-scraped-per-day as its primary success metric.

Preferred strategic measures include:

### Candidate Hit Rate
Percentage of qualified/recommended candidates that later produce defined successful outcomes.

### Revenue Yield per Qualified Candidate
Attributed affiliate revenue or net commission divided by qualified candidates pursued.

### Expected Affiliate Value per Unit of Content Effort
Long-term project-level north star from the Project Charter.

### Decision Precision / Waste Reduction
How effectively Program 1 reduces effort spent on low-value opportunities.

Until downstream attribution is available, proxy metrics must be explicitly labeled as proxies.

## 12. Closed Learning Loop

Program 1 must preserve traceability for the future loop:

```text
Observation
 -> Candidate Decision
 -> Offer
 -> Content
 -> Account/Channel
 -> Publication
 -> Click
 -> Order
 -> Commission
 -> Learning
 -> Future Opportunity Policy
```

Outcome data must not directly mutate ranking policy. Learning changes versioned models/rules after analysis/validation.

## 13. Team Responsibilities

### Affiliate / Marketing Strategy
Own:
- success hypotheses;
- target audience/problem;
- business signals;
- opportunity thesis;
- campaign/season context;
- action definitions and experiment questions.

### Data / Decision Science
Own:
- feature definitions;
- measurement design;
- scoring experiments;
- attribution analysis;
- model validation.

### Data / Scraping Engineering
Own:
- evidence-source feasibility;
- observation fidelity;
- normalization inputs;
- time-series collection;
- schema-drift detection.

### Software Engineering
Own:
- domain/application/port architecture;
- deterministic engines;
- versioned contracts;
- persistence;
- reliability.

### Browser Automation
Own:
- bounded collection execution;
- job/lease lifecycle integration;
- pagination/navigation mechanics;
- recovery;
- platform-adapter evidence.

### QA / Test
Own:
- signal correctness;
- regression fixtures;
- contract/resilience tests;
- evidence-to-implementation conformance.

### Process / SSOT
Own:
- document precedence;
- evidence gates;
- Definition of Ready/Done;
- ADR/Kanban/CAPA traceability.

## 14. Program 1 Architecture Implications

The target logical flow is:

```text
Strategy / Campaign Policy
        -> Discovery Planning
        -> Worker Job / Lease
        -> Product Source / Collection Profile
        -> ProductObservation
        -> Durable Ingestion
        -> Normalize / Identity / History
        -> Feature Derivation
        -> Qualification
        -> Opportunity Evaluation
        -> Explainable Ranking
        -> Human/Policy Approval
        -> Qualified Candidate Handoff
```

The Side Panel/UI is an operator shell only.

The browser worker is a bounded execution agent only.

The Back Office owns business policy, durable decisions, scoring/ranking, shortlist and handoff.

## 15. Program 1 -> Program 2 Boundary

Program 1 should hand off **qualified opportunity candidates**, not arbitrary harvested products.

The handoff must preserve enough rationale/provenance for Program 2 to understand:
- which candidate was selected;
- why it was selected;
- evidence freshness;
- policy/model version;
- relevant market/context features;
- unresolved uncertainty relevant to offer discovery.

Program 2 remains authoritative for affiliate offer discovery/evaluation/selection.

## 16. Definition of Strategic Success

Program 1 is strategically successful when it can demonstrate that its decisions increasingly direct affiliate resources toward opportunities that outperform uninformed/random/baseline selection under measured downstream outcomes.

Until that evidence exists, Program 1 remains an explainable evidence-driven decision-support system rather than claiming predictive superiority.

## 17. Non-Goals

Program 1 shall not:
- maximize scraping volume for its own sake;
- treat popularity as equivalent to affiliate opportunity;
- embed marketing policy in browser selectors/UI;
- invent production scoring weights without evidence;
- bypass platform protections;
- collect unsupported data solely because it is technically obtainable;
- make Program 2 offer decisions;
- make Program 3 publishing decisions.

## 18. Governing Consequence

All future Program 1 documents, Kanban cards, data fields, collectors, engines, tests and dashboards must trace back to this strategy.

When an implementation proposal cannot state the affiliate decision/business hypothesis it supports, it is not Ready for implementation unless explicitly classified as foundational infrastructure or controlled evidence research.
