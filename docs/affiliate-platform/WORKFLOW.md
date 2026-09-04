# Canonical End-to-End Workflow

Status: IMPLEMENTATION HANDOFF BASELINE
Date: 2026-08-31

## 1. Governing Flow

```text
Affiliate / Marketing Strategy
    -> Business Questions / Hypotheses
    -> Required Decision Signals
    -> Product / Market Discovery
    -> Observe / Normalize / History
    -> Opportunity Features / Intelligence
    -> Qualification / Explainable Ranking
    -> Shortlist / Action Candidate / Approval
    -> Affiliate Offer Discovery
    -> Offer Eligibility / Freshness / Ranking
    -> Offer Selection
    -> Content Planning
    -> Video Registration / Fingerprint
    -> Product <-> Offer <-> Video Matching
    -> Publish Plan
    -> Duplicate / Policy / Readiness Gate
    -> Job Queue / Lease
    -> Device Host / Android Worker
    -> Scene-Aware Execution
    -> Submit Guard
    -> Result Verification / Reconciliation
    -> Publishing Ledger
    -> Analytics / Attribution
    -> Learning Loop
```

The workflow is business-authoritative at the Back Office. Workers execute bounded tasks and report facts.

## 2. Program 1 — Affiliate Opportunity Intelligence

Governing strategy: `PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md`.

### Business Input
- affiliate/marketing objective and target outcome;
- target audience/account context where applicable;
- campaign/season/event context;
- business hypotheses to test;
- decision signals required by those hypotheses;
- campaign/ruleset and evidence-freshness policy.

### Operational Input
- discovery source/mode;
- search/category/shop/current-page scope;
- worker capabilities;
- versioned collection/profile/evidence status.

### Execution
1. Affiliate/Marketing Strategy defines the business question or opportunity hypothesis before collection work is authorized, except foundational infrastructure/evidence-research slices.
2. Back Office translates the hypothesis into required signals, discovery scope, evidence requirements and bounded jobs/shards.
3. Product Discovery Worker leases bounded work and observes facts only; it does not decide commercial attractiveness.
4. Worker persists observations to local outbox before transmission.
5. Back Office durably commits observation batches and ACKs according to idempotent ingestion semantics.
6. Product identity is normalized/deduplicated and historical observations are preserved rather than overwritten.
7. Intelligence processing derives versioned features such as demand, momentum/timing, buyer-intent context, price/value, seller confidence, competition/saturation, contentability and risk where evidence supports them.
8. Qualification/ranking policy creates explainable Opportunity Thesis/shortlist decisions with reasons, uncertainty, freshness and model/ruleset provenance.
9. Human review/approval may be required according to campaign policy, especially while outcome evidence is insufficient for production scoring.
10. Only qualified/actionable candidates proceed to Program 2; raw harvest volume is not a success criterion.

### Output
Qualified Product Opportunity references for Program 2, including decision rationale/provenance sufficient to explain why the candidate deserves affiliate-offer discovery.

## 3. Step 2 — Affiliate Offer Discovery and Selection

### Input
- approved Product identity;
- affiliate account/session context;
- offer ruleset;
- worker capability.

### Execution
1. Back Office creates offer-discovery jobs.
2. Affiliate Worker observes candidate offers in an authorized session.
3. Candidate observations include account/session provenance where values depend on context.
4. Back Office normalizes/records candidate observations.
5. Offer Engine evaluates eligibility, freshness and ranking.
6. Preferred and backup offer selections are stored as versioned decisions.
7. Affiliate link/export artifact may be collected/imported where applicable.

### Output
Product + selected Offer references for Step 3.

## 4. Content Preparation

### Input
- selected Product/Offer;
- source video/content metadata.

### Execution
1. Register video before publish planning.
2. Extract deterministic media metadata through MediaPort.
3. Calculate exact SHA-256.
4. Calculate perceptual identity when configured/validated.
5. Content Identity Engine classifies duplicate state.
6. Record Product 1:N Video relationship/content angle where applicable.

### Output
Validated Video identity that may enter publish planning.

## 5. Publish Planning

Publishing Engine builds a plan using:
- video_id;
- platform/account target;
- selected product/offer identities;
- caption/tag references;
- basket/product capacity policy;
- duplicate policy;
- freshness/readiness evidence.

Before queue admission, validate:
- video is known and valid;
- duplicate gate passes;
- product/offer still eligible enough for configured policy;
- required account/device capability exists;
- required metadata is available;
- irreversible-action prerequisites are satisfied.

Invalid plan does not reach a device worker.

## 6. Job Orchestration

Shared Job Engine is lifecycle SSOT.

Baseline lifecycle:
`CREATED -> QUEUED -> LEASED -> IN_PROGRESS -> VERIFYING -> COMPLETED`

Alternative terminal outcomes:
`FAILED | NEEDS_HUMAN | CANCELLED | SKIPPED_DUPLICATE`

Rules:
- one valid active lease per executable job;
- lease has token, owner, expiry, attempt/version;
- worker side effects use idempotency identity;
- stale worker result cannot silently overwrite newer state;
- durable ACK occurs only after commit.

## 7. Step 3 — Android Execution

Worker loop:

`Observe -> Recognize -> Validate -> Act -> Verify -> Checkpoint`

Conceptual happy path:
1. VIDEO_SOURCE — choose/verify target clip.
2. VIDEO_PREPARE — load/preview/advance, including optional valid editor/loading scenes.
3. PRODUCT_BASKET — locate/verify/select required products/offers and confirm.
4. POST_DETAILS — fill caption/tags/metadata.
5. READY_TO_PUBLISH — final deterministic validation gate.
6. PUBLISHING — submit once under irreversible-action guard.
7. PUBLISH_SUCCESS — verify evidence, then record success.

Scene order is recognized dynamically; it is not implemented as blind coordinate macro steps.

## 8. Scene Transition and Recovery

For every action:
- current Scene known;
- current Process known;
- expected next Scene/state known.

If actual != expected:
1. re-observe;
2. local verified recovery;
3. navigate to safe anchor;
4. controlled app restart from checkpoint if safe;
5. NEEDS_HUMAN.

Recovery has bounded budgets. Infinite retry is prohibited.

## 9. Irreversible Publish Boundary

Before `POST_SUBMITTED`:
- normal bounded retry/recovery may be allowed according to action policy.

At/after `POST_SUBMITTED`:
- do not assume failure from timeout/disconnect;
- do not blindly submit again;
- classify `POST_OUTCOME_UNKNOWN` where success cannot be proven;
- run reconciliation/evidence checks;
- if still ambiguous -> NEEDS_HUMAN.

This rule has higher priority than throughput.

## 10. Publishing Ledger

On confirmed success, one short transaction records:
- durable platform publish state;
- authoritative ledger event;
- post/platform identifiers/evidence references;
- job completion transition;
- timestamps/version.

Database/application constraints must prevent a duplicate success that violates configured platform policy.

## 11. Analytics Loop

Publishing/performance facts are attributed to:
- Product;
- Offer;
- Video/content angle;
- platform/account;
- publication time;
- campaign/ruleset version.

Analytics feeds future Product/Offer scoring only through versioned rules; raw analytics adapter data does not directly mutate ranking policy.

## 12. Failure Ownership

- Worker/device/browser failure -> adapter/runtime reports facts.
- Job decision -> Shared Job Engine.
- Product/Offer/Publishing policy -> relevant domain engine.
- DB transaction/repository conflict -> application/persistence boundary.
- UI disconnect -> presentation concern only.
- unknown irreversible outcome -> Publishing Engine reconciliation/NEEDS_HUMAN.

## 13. Restart / Resume Principle

Every long-running workflow is split by durable checkpoints.

Never keep an SQL transaction open while waiting for:
- browser page;
- network response from external platform;
- Android UI;
- video upload;
- human action.

The pattern is:
`short transaction -> external work -> short checkpoint/result transaction`.

## 14. Headless Workflow Requirement

Before production UI is required, the workflow must be demonstrable using fake adapters and application/API/CLI harnesses through:
- Step 1 thin slice;
- Step 2 thin slice;
- Content identity;
- Publish planning;
- Shared Job lifecycle;
- Scene simulation;
- publish result/reconciliation simulation.