# Program 1 ACK Accounting Contract

Date: 2026-09-09
Card: P1-C-ACK — durable observation accounting and receipt presentation
Status: IMPLEMENTED — local non-browser gates pass; CI and visible Brave acceptance tracked in verification report
Governing: ADR-042; Application Contracts §7; Program 1 architecture §13; UML D5/D6; P1-C card.

## Objective and ownership

Back Office must acknowledge every observation that is durably accounted for, including exact duplicates. Worker/UI must not equate accepted observation count with new product count. This is a reliability foundation slice, not a marketing-policy change.

## Additive response version

Successful `POST /api/v1/program1/observations` retains `batch_id`, `received_count`, `accepted_count` and adds:

```json
{
  "ack_schema_version": "program1-observation-ack-v2",
  "batch_id": "example",
  "received_count": 3,
  "accepted_count": 1,
  "duplicate_count": 2,
  "accounted_count": 3
}
```

- accepted_count: observations inserted by the original logical batch commit.
- duplicate_count: received entries already represented by an identical observation at that commit, including repeated identical entries within the batch.
- accounted_count: accepted_count + duplicate_count = received_count.
- All counts are nonnegative integers. Same batch/payload replay reproduces the original receipt, including accepted_count; it does not mean new inserts occurred during retransmission.
- Different payload under the same batch or observation identity remains HTTP 409. Validation failure remains non-ACK. No partial success/rejected count is introduced.
- These counts derive from the existing atomic receipt; no migration is necessary. `source_job_id` must round-trip through the batch ingestor just as through the ordinary product repository.
- Old stored observations whose source_job_id was previously omitted are not silently repaired. Conflicting replay remains fail closed; historical provenance recovery requires independent evidence.

## Worker compatibility and checkpoint rules

- v2 requires matching batch identity, exact received/accounted totals, integer/range validation and accepted + duplicate = accounted. Unknown versions or malformed totals retain the message for reconciliation.
- Unversioned legacy ACK remains supported only under the old strict accepted = received rule; the worker never infers duplicate acceptance from an incomplete legacy response.
- A successful drain returns receipts keyed by message ID. A page checkpoint uses its own receipt, never totals belonging to other drained messages.
- Persist the latest validated receipt with the outbox removal in one storage update. Serialize enqueue/remove/quarantine mutations within the background owner to prevent lost updates. Storage failure leaves the message retryable; no UI success is reported before completion.
- Latest receipt is bounded display evidence; canonical history remains in Back Office. It is associated with the backend URL used for delivery and is not shown as current evidence for another configured backend.

## Operator presentation

Use existing daisyUI. Show the last acknowledged batch, newly recorded observations, exact duplicate observations and durably accounted observations. Explain that these are original-batch counts, not new-product counts or inserts on every retry. New product identities are not established by this receipt and must not be invented from observation totals.

Panel close/reopen restores the persisted receipt. A refresh command reads runtime state only. Existing delay slider, pagination and Shopee profiles remain unchanged.

## Acceptance / Definition of Ready

- Owner: Program1Service / atomic batch ingestor; extension transport projects the receipt only.
- Inputs/output: existing observation payload and additive response above.
- Tests: actual SQLite rows/receipts after mixed, duplicate-only, same-batch replay, restart and changed-payload conflict; source_job_id round-trip; malformed/legacy ACK; backlog/current checkpoint isolation; outbox concurrency/storage failure; UI receipt restoration.
- Infrastructure waits never occur inside DB transactions. Local storage has one background mutation owner.
- No new Shopee facts, scoring rules, database columns or Program 2/3 behavior.
- CRITICAL/HIGH unresolved design issues: zero for this contract. Existing historical provenance loss is explicitly not guessed/repaired.
- Verification: narrow tests -> shared pipeline -> CI -> separate visible Brave acceptance when available. Chromium/mock evidence cannot claim live Brave/Shopee acceptance.
