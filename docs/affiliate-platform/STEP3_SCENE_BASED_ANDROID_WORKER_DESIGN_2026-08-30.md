# Step 3 — Scene-Based Android Worker Design

Date: 2026-08-30
Status: ACCEPTED DESIGN BASELINE / DEVELOPMENT HANDOFF

## Goal
Control Shopee Android publishing from the Python Back Office through distributed Android Workers, with reliable state recognition, recovery, duplicate prevention and resource governance.

## Execution Model
`Worker -> Job -> Workflow -> Scene -> Process -> Action -> Element -> Selector`

Worker Golden Rule:
`Observe -> Recognize -> Validate -> Act -> Verify -> Checkpoint`

Before a business action, Worker must know:
1. current Scene
2. permitted/current Process
3. expected next Scene/state

Unknown/ambiguous state blocks blind execution.

## Runtime Topology
```text
Back Office Orchestrator
        ↓
Device Host Manager
        ↓
Worker Supervisor
        ↓
Worker Runtime (one active device)
        ↓
Android Control Adapters
        ↓
Shopee Android App
```

Global orchestration belongs to Back Office. Device lifecycle/resource orchestration belongs to Device Host Manager. Scene/process orchestration belongs to Worker.

## Scene Model
Each meaningful Shopee screen/state is a Scene with:
- scene_id/name/version
- entry conditions
- required/strong/optional indicators
- negative indicators
- structural relationships
- allowed processes/actions
- expected transitions
- failure/success signals
- timeout/recovery policy
- safe-anchor classification

## Scene Signature
Use multiple independent indicators where possible:
- package/activity
- resource-id
- accessibility/content-description
- text/context
- class/state/properties
- relative hierarchy
- required element combinations
- negative indicators
- optional visual fingerprint fallback

Recognition result can be CONFIRMED, PROBABLE, AMBIGUOUS or UNKNOWN. Exact scoring thresholds require real-app validation.

## Logical Element Resolution
Preferred order:
1. resource-id/platform identifier
2. accessibility/content-description
3. stable text + context
4. class/state/properties
5. relative hierarchy
6. controlled XPath-like selector
7. visual/image fallback
8. absolute coordinate as last resort

Workflow references logical elements, not raw coordinates.

## Recovery
Bounded levels:
0. re-observe after UI stability
1. local safe transition
2. Safe Anchor recovery
3. controlled app restart when safe
4. human takeover / NEEDS_HUMAN

After final POST/SUBMIT, unknown outcome is `POST_OUTCOME_UNKNOWN`; never blind repost.

## Shopee Video Happy Path v1
`VIDEO_SOURCE -> VIDEO_PREPARE/EDITOR (when present) -> PRODUCT_BASKET -> POST_DETAILS -> READY_TO_PUBLISH -> PUBLISHING -> PUBLISH_SUCCESS`

Baseline human flow:
1. browse/select video
2. upload/import
3. optional preview/editor
4. choose/adjust affiliate products in basket
5. validate selected target products/offers
6. caption/tags/metadata
7. final QA/duplicate/freshness gate
8. post
9. verify outcome
10. update publishing ledger

Current observed product-basket maximum of 6 is a configurable platform rule and must be revalidated against target app/account before production freeze.

## Device Control Adapters
Replaceable families:
- DeviceTransportAdapter — ADB candidate
- UIAutomationAdapter — uiautomator2 / Appium UiAutomator2 family candidates
- ScreenStreamAdapter — scrcpy / STF-style candidates
- InputControlAdapter

Screen stream is operator observability/control, not business SSOT.

## Resource / Conflict Management
Device Host Manager owns:
- device registry/discovery
- one active Worker per device
- worker process lifecycle
- ADB lifecycle coordination
- CPU/RAM/USB/stream/disk/outbox budgets
- admission control
- controlled degradation

Do not overload the host merely to maximize active worker count.

## DB / Event Ownership
Workers report facts/events/results through API. They do not directly mutate canonical business tables.

Typical events:
- JOB_STARTED
- SCENE_CHANGED
- JOB_CHECKPOINT
- VIDEO_SELECTED
- BASKET_ATTACHED
- POST_SUBMITTED
- POST_CONFIRMED
- POST_FAILED
- NEEDS_HUMAN

## Video / Duplicate Policy
- exact file hash + perceptual fingerprint
- filename never defines video identity
- global Publishing Ledger is authoritative
- baseline Shopee policy: once a video identity is confirmed published to Shopee, another Shopee publish is blocked unless governing policy is intentionally revised

## Implementation Gates
- real target Shopee Scene inventory/signatures
- selector-profile validation by app/locale/account context
- Safe Anchor and transition/recovery validation
- post-submit reconciliation validation
- screen-stream/device-host benchmark for 10/20/50/100-device scenarios
- video fingerprint algorithm/threshold validation
- Step2→Step3 job/handoff contract freeze
