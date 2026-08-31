# Android Scene Engine Specification

Status: IMPLEMENTATION HANDOFF BASELINE
Owner: Step 3 / Android Worker Runtime
Date: 2026-08-31

## 1. Purpose

Define the Scene-based mobile automation engine so workflow logic is testable without a physical phone and Android implementation details remain replaceable adapters.

## 2. Execution Hierarchy

`Worker -> Job -> Workflow -> Scene -> Process -> Action -> Logical Element -> Selector`

Worker golden loop:

`Observe -> Recognize -> Validate -> Act -> Verify -> Checkpoint`

Before every business action the runtime must know:
1. current Scene;
2. current Process;
3. expected outcome/next Scene.

Unknown/ambiguous state blocks business action.

## 3. Scene Engine vs Android Adapter

Scene Engine owns:
- Scene definitions/signatures;
- recognition scoring/classification;
- workflow/process/action sequencing;
- transition validation;
- recovery policy;
- safe-anchor policy;
- recovery budgets;
- logical checkpoints/events.

Android/UI adapters own:
- capture UI hierarchy/snapshot;
- package/activity facts;
- map logical elements to selectors;
- tap/type/swipe/wait primitives;
- raw selector fallback strategies;
- screenshots/evidence capture;
- device transport.

The Scene Engine must never contain uiautomator2 objects, Appium driver objects, XPath engine objects or screen coordinates.

## 4. Normalized UI Snapshot

UIAutomationPort returns a normalized snapshot containing where observable:
- package/activity;
- stable semantic elements;
- resource/accessibility/text/class/state properties;
- hierarchy/relative relationships;
- dialogs/system overlays;
- current orientation/window metadata;
- adapter/app/version/locale metadata.

Tests can construct the same snapshot type from fixture files.

## 5. Scene Signature

A Scene signature may contain:
- required indicators;
- strong positive indicators;
- optional indicators;
- negative indicators;
- relative structural relationships;
- package/activity constraints where useful;
- minimum confidence policy.

Do not recognize a Scene using only one brittle text string where multiple signals can be used.

## 6. Recognition Output

Return:
- scene_id;
- confidence;
- classification;
- matched positive/required/negative evidence;
- missing required evidence;
- profile/version.

Classification baseline:
- CONFIRMED;
- PROBABLE;
- AMBIGUOUS;
- UNKNOWN.

Exact numeric thresholds are configurable/versioned and require validation; do not freeze illustrative values as constants without evidence.

Business action normally requires CONFIRMED or explicitly permitted confidence class.

## 7. Logical Element Registry

Examples:
- `SHOPEE.VIDEO.CREATE_BUTTON`
- `SHOPEE.VIDEO.CAPTION_INPUT`
- `SHOPEE.VIDEO.PRODUCT_BASKET_BUTTON`
- `SHOPEE.VIDEO.PRODUCT_SEARCH_INPUT`
- `SHOPEE.VIDEO.ATTACH_PRODUCT_BUTTON`
- `SHOPEE.VIDEO.PUBLISH_BUTTON`
- `SHOPEE.VIDEO.PUBLISH_SUCCESS_SIGNAL`

Business workflow references logical IDs only.

## 8. Selector Strategy

Priority baseline:
1. resource/platform identifier;
2. accessibility/content-description;
3. stable text + context;
4. class/state/property combination;
5. relative hierarchy;
6. controlled XPath-like fallback;
7. visual/image matching fallback where justified;
8. absolute coordinates only as last resort.

Selector profiles are versioned by app/version/locale/context and may contain ordered fallbacks.

Long absolute hierarchy XPath and coordinate macros are considered brittle and require explicit justification.

## 9. Baseline Shopee Video Scenes

Conceptual catalog:
- VIDEO_SOURCE;
- VIDEO_PREPARE;
- optional VIDEO_EDITOR/LOADING/PERMISSION scenes;
- PRODUCT_BASKET;
- POST_DETAILS;
- READY_TO_PUBLISH;
- PUBLISHING;
- PUBLISH_SUCCESS;
- NETWORK_ERROR_DIALOG;
- SESSION/LOGIN_REQUIRED;
- UNKNOWN/UNSUPPORTED.

Real catalog is a production validation gate and must be captured from actual supported app versions.

## 10. Processes

Example VIDEO_SOURCE:
- VERIFY_SOURCE_SCENE;
- LOCATE_TARGET_VIDEO;
- SELECT_VIDEO;
- VERIFY_SELECTED_VIDEO;
- START_UPLOAD/NEXT.

Example PRODUCT_BASKET:
- VERIFY_PRODUCT_BASKET_SCENE;
- SEARCH_TARGET_OFFER;
- MATCH_PRODUCT_IDENTITY;
- SELECT_PRODUCT;
- VERIFY_SELECTED_PRODUCT;
- repeat within configured required count/cap;
- VERIFY_BASKET;
- CONFIRM.

Example READY_TO_PUBLISH:
- VERIFY_VIDEO;
- VERIFY_PRODUCTS/OFFERS;
- VERIFY_METADATA;
- REQUEST_BACKOFFICE_PRE_SUBMIT_GUARD;
- only then SUBMIT.

## 11. Action Contract

Actions are atomic logical interactions such as:
- TAP(logical_element);
- TYPE(logical_element, value_ref);
- CLEAR_AND_TYPE(...);
- SWIPE(region/semantic direction);
- WAIT_FOR(condition);
- BACK;
- OPEN_APP;
- RESTART_APP under recovery policy.

Each action defines:
- precondition Scene/state;
- logical target;
- timeout policy reference;
- expected result/transition;
- retry safety classification;
- evidence requirement.

## 12. Transition Validation

Every action that changes workflow state has expected transition(s).

Example:
`VIDEO_PREPARE --OPEN_BASKET--> PRODUCT_BASKET`

Observed alternatives may be known valid scenes such as loading/editor/permission. The engine decides whether to continue, wait, branch or recover.

A tap succeeding technically is not sufficient; the expected business transition must be verified.

## 13. Recovery Graph

Recovery levels:

### Level 0 — Re-observe
- wait for UI stability;
- capture fresh snapshot;
- recognize again.

### Level 1 — Local Recovery
Use a verified action/path from known wrong Scene to desired state.

### Level 2 — Safe Anchor
Navigate to a Scene tagged SAFE_ANCHOR, e.g. known Shopee/video home, then resume from durable checkpoint.

### Level 3 — Controlled App Restart
Save checkpoint/evidence, restart app, recognize safe anchor, navigate/resume only when irreversible boundary permits it.

### Level 4 — Human Takeover
Ambiguous/unknown/schema-changed/recovery-exhausted conditions stop automated business action and request operator help.

## 14. Recovery Budget

Retry/recovery is bounded by policy.

Exact counts/timing are configuration validated by endurance tests.

The engine must prevent infinite loops and repeated destructive action.

## 15. Irreversible Boundary Integration

After `POST_SUBMITTED`:
- recovery must not invoke submit again unless Publishing Engine explicitly concludes `CONFIRMED_FAILURE_SAFE_TO_RETRY`;
- app restart/navigation may be used only for evidence/reconciliation if safe;
- unknown outcome routes to reconciliation/NEEDS_HUMAN.

Scene Engine cannot override Publishing Engine duplicate/irreversible-action policy.

## 16. Worker State

Operational state should include:
- worker_id/device_id/account_id;
- job_id/job_type/job_state;
- current_scene/previous_scene/expected_scene;
- current_process/current_action/current_element;
- scene_confidence/profile version;
- recovery level/count;
- checkpoint;
- health_state;
- last_success/error/evidence refs.

High-frequency snapshots are not automatically durable canonical DB data; store checkpoints/events/evidence according to policy.

## 17. Headless Simulation

Foundation implementation must include `ScriptedUIAutomationAdapter` capable of returning a predetermined sequence of normalized snapshots/action results.

This supports tests such as:
- happy path;
- loading Scene insertion;
- expected transition mismatch;
- known network dialog;
- unknown Scene;
- local recovery success;
- safe-anchor recovery;
- recovery exhaustion;
- app restart before submit;
- crash/unknown state after submit.

## 18. Fixture Strategy

Sanitized golden fixtures may include:
- normalized UI hierarchy snapshots;
- Scene signature definitions;
- selector profile examples;
- expected recognition output;
- expected transition/recovery plan.

Fixtures must not contain account credentials/session secrets/personal sensitive data.

## 19. Physical Device Laboratory

Real-device testing validates:
- selector stability;
- hierarchy availability;
- timing/loading behavior;
- package/activity transitions;
- system permissions/dialogs;
- safe anchor feasibility;
- actual publish-success evidence;
- ADB/uiautomator2/Appium compatibility;
- stream/input performance.

Business workflow rules should already pass simulation tests before this stage.

## 20. Screen Streaming

ScreenStreamAdapter is separate from Scene recognition and business truth.

Overview mode may use lower resource previews across many devices; Focus mode may provide higher quality/operator control for one selected device.

Worker must remain able to report Scene/process state independently of screen-preview availability.

## 21. Testability Acceptance

Scene Engine is conforming only if:
- recognition/transition/recovery tests run with no Android SDK/device;
- exact same logical workflow can use Fake or concrete UIAutomationPort;
- selector changes do not require changing Process business logic;
- an unknown Scene results in no business tap;
- retries are bounded;
- post-submit ambiguity never creates automatic resubmit.

## 22. Open Production Gates

- real Shopee Scene catalog;
- real signature indicators;
- selector profiles by supported app version/locale;
- exact confidence thresholds;
- safe-anchor paths;
- retry/recovery timing budgets;
- product basket capacity behavior;
- post-submit success/reconciliation evidence;
- high-scale device-host streaming/control benchmark.