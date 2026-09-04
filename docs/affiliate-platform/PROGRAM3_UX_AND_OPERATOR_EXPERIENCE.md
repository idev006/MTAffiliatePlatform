# Program 3 — UX and Operator Experience

Status: DESIGN BASELINE
Date: 2026-09-04

## Goal

A novice operator should understand:
- what content is being published;
- to which account/device;
- which product/offer/link is attached;
- current Scene/process;
- whether submit has occurred;
- whether outcome is confirmed, unknown or needs intervention;
- the safest next action.

## Default view

- Job state
- Target account/device
- Content/video identity
- Offer/product summary
- Current Scene/process
- Duplicate/freshness guard state
- Submit boundary state
- Final outcome

## Important warnings

Use clear actionable wording:
- Device authorization required
- Current screen not recognized — no action taken
- Offer evidence stale — refresh required
- Duplicate publication blocked
- Post may already have been submitted — automatic retry disabled
- Outcome unknown — operator review required

## UI authority

UI may request commands and display state/evidence.
UI may not:
- override duplicate guard silently;
- fabricate Scene confirmation;
- mark canonical publish success;
- issue retry after ambiguous submit without Back Office authorization;
- write ledger tables directly.
