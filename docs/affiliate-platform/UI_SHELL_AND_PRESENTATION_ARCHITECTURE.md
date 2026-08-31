# UI Shell and Presentation Architecture

Status: IMPLEMENTATION HANDOFF POLICY
Date: 2026-08-31

## 1. Purpose

Ensure a future desktop UI can be added, replaced or removed without changing business logic.

Baseline UI candidate remains PySide6/Qt 6, but no business component depends on Qt.

## 2. Core Rule

> **The UI is a presentation shell over application commands, queries and event streams. It is never the system brain.**

The platform must remain operational in headless mode for automation, tests and server deployments.

## 3. Presentation Boundary

```text
PySide6 View / ViewModel
        |
        v
Presentation Service / Client Facade
        |
        +---- Command Bus / Application Use Cases
        +---- Query Service / Read Models
        +---- Telemetry/Event Subscription
        |
        v
Domain/Application Core
```

The UI receives DTO/read-model data rather than ORM entities.

## 4. Recommended UI Pattern

Use a pragmatic MVVM/MVP-style boundary:
- View: widgets/layout/rendering only;
- ViewModel/Presenter: presentation state, validation display, command invocation;
- Application Facade: stable command/query API;
- Domain/Application: business decisions.

Do not use UI widget state as durable job/business state.

## 5. UI Responsibilities

Allowed:
- display Products/Offers/Videos/Jobs/Workers/Devices;
- submit filters/settings/commands;
- render progress/health/Scene state;
- display errors and evidence;
- provide operator approval/override actions;
- subscribe to live telemetry;
- show configuration and audit history.

Not allowed:
- score/rank products directly;
- select preferred offer by hidden UI logic;
- create independent job state machines;
- directly write DB tables;
- decide duplicate publishing rules;
- run arbitrary Android coordinate macros;
- perform automatic retry policy independently from engines;
- treat window/tab state as authoritative state.

## 6. UI-Agnostic Application Facade

The application should expose operations that make sense equally to CLI, API and GUI.

Examples:
- list_product_candidates(query)
- score_campaign(command)
- approve_shortlist(command)
- list_offer_candidates(query)
- select_offer(command)
- register_video(command)
- build_publish_plan(command)
- queue_publish_job(command)
- pause_worker(command)
- request_human_takeover(command)
- get_job_details(query)
- get_device_farm_status(query)

Names are conceptual; final signatures belong to application contracts.

## 7. Read Models

Complex dashboards should consume purpose-built read models rather than traversing domain objects.

Examples:
- ProductCandidateRow;
- OfferCandidateRow;
- PublishingQueueRow;
- WorkerHealthCard;
- DeviceOverviewTile;
- SceneExecutionSnapshot;
- PublishingEvidenceView.

Read models may be denormalized for display and are not domain authority.

## 8. Long-Running Operations

The UI must never block on long browser/device/media work.

Pattern:
1. UI submits command;
2. application returns accepted/job identity;
3. durable engine/worker performs work;
4. UI observes query/event updates;
5. operator may close/reopen UI without losing progress.

## 9. Event Handling

Live UI events are hints for responsiveness.

On reconnect or suspected event loss, the UI refreshes authoritative state through queries.

Never require delivery of every WebSocket event to maintain business correctness.

## 10. UI Testing

UI tests focus on presentation behavior:
- command mapping;
- validation rendering;
- view-model state;
- event subscription/reconnect;
- disabled/enabled controls based on read models;
- human confirmation flow.

Core business rules are not re-tested through the UI.

Where possible, test ViewModels/Presenters without rendering Qt widgets.

## 11. Headless Modes

The same application core must support:
- pytest/component harness;
- CLI/admin scripts;
- FastAPI server;
- local portable runtime;
- PySide6 desktop shell;
- future web/mobile operator UI if needed.

## 12. Initial UI Development Timing

UI implementation should begin only when a vertical slice has stable commands/queries and meaningful operator value.

Recommended sequence:
1. engines + tests;
2. application use cases;
3. API/CLI laboratory interface;
4. prove end-to-end workflow;
5. build UI shell around stable contracts.

A minimal diagnostic UI may be built earlier for laboratory observation, but it must not become an accidental location for business logic.

## 13. Device Farm Screen UI

For multi-device monitoring, UI concepts should separate:
- Overview Mode: low/medium resource previews for many devices;
- Focus Mode: high-quality stream and operator control for selected device.

Screen preview is operational telemetry only. Worker Scene/state data remains independently reported and durable where required.

## 14. Acceptance Criteria

UI architecture is conforming when:
- engines run with no Qt installation in core test environments where packaging permits separation;
- the same application use case is callable from API/CLI/UI;
- UI imports no SQLAlchemy model/repository implementation;
- UI contains no domain scoring/duplicate/job-transition logic;
- UI restart does not lose active durable work;
- presentation tests can use fake application facades/event sources.