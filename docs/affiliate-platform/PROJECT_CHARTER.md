# Project Charter

## Project Name
MTAffiliatePlatform — Affiliate Intelligence & Publishing Platform

## Mission
Build a document-driven operating system for affiliate work that improves three decisions and one execution problem:

1. Which products should be marketed?
2. Which affiliate offers/links should be selected for each product?
3. Which videos should be paired with which product/offer/account?
4. How can publishing be executed reliably across multiple devices/accounts while preventing duplicate video use?

## Core Business Outcome
The system must progressively improve expected affiliate revenue per unit of content effort, not merely increase posting speed.

## In Scope

### Domain A — Product Intelligence
- Product discovery from approved/available data sources.
- Product identity using platform identifiers.
- Normalization, deduplication, snapshots, scoring, filtering, ranking, shortlist generation.
- Opportunity scoring using demand, price, sales signals, seller quality, competition, commission potential, content potential, and own historical performance where available.

### Domain B — Affiliate Offer Automation
- Accept approved Product IDs from Domain A.
- Assist/automate permitted workflows on affiliate pages through worker adapters.
- Collect candidate offers for a product.
- Support configurable target counts such as 10–20 offers.
- Import platform-generated affiliate exports/links.
- Rank and maintain multiple offers per product.

### Domain C — Content Publishing
- One product may own many videos.
- Register every video before publishing.
- Generate video identity/fingerprint.
- Prevent duplicate publishing according to platform policy configured by the project.
- Match Product ↔ Offer ↔ Video ↔ Account ↔ Device.
- Queue, dispatch, execute, recover, and audit publishing jobs.

### Shared Core
- Central database.
- Rules engine.
- Worker registry and heartbeat.
- Job queue/state machine.
- Audit trail.
- Monitoring.
- Analytics and feedback loop.

## Architectural Principles

1. **Document first.** Approved documents are the SSOT.
2. **Decision logic is centralized.** Workers execute; the Python control plane decides.
3. **Workers are replaceable.** Browser, API, Android, and future adapters must not own business truth.
4. **Data source adapters are replaceable.** Product intelligence must not depend on one acquisition technique.
5. **Idempotency is mandatory.** Restarting a job must not create unintended duplicates.
6. **Auditability is mandatory.** Important actions and state transitions must be traceable.
7. **Human override exists at every risky stage.**
8. **Platform compliance is a design constraint.** Do not depend on bypassing authentication, access controls, anti-bot mechanisms, or rate limiting.
9. **Measure outcomes.** Publishing is not complete until results can be attributed back to product, offer, video, account, and time.
10. **Feedback improves discovery.** Own performance data must eventually influence product selection.
11. **API as Core.** Versioned business-level contracts govern component communication.
12. **Component-based and pluggable.** Core business policy must not depend on one tool/vendor/selector/database engine.
13. **Portable-first, scale-ready.** Default distribution is simple; scaling must not require domain redesign.

## Repository SSOT

Authoritative repository: `idev006/MTAffiliatePlatform`.

The former `idev006/MTShopeeMobile` repository is an existing Android publishing implementation/reference and is not the SSOT for the overall platform.

## Non-Goals for Initial Phases
- Building every crawler ourselves before evaluating existing tools.
- Maximizing raw request/click speed.
- Scraping the entire marketplace solely for dataset size.
- Full autonomous posting before reliability, duplicate prevention, auditability, and policy constraints are understood.
- Embedding business rules permanently inside browser extensions or Android workers.

## Success Measures
Initial system quality will be measured by:
- Product shortlist precision.
- Percentage of shortlisted products that can be converted into usable affiliate offers.
- Offer freshness and availability.
- Duplicate-prevention accuracy.
- Publishing job success/recovery rate.
- Traceability of every published video.
- Commission per 1,000 views / per content unit when data becomes available.

## Governance Rule
Any developer or agent implementing this project must read the SSOT documents before modifying architecture, data contracts, workflow rules, or publishing behavior.
