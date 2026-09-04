from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mtaffiliate.adapters.persistence.inmemory.affiliate_offer import (
    InMemoryAffiliateOfferRepository,
)
from mtaffiliate.adapters.persistence.inmemory.job import InMemoryJobRepository
from mtaffiliate.adapters.persistence.inmemory.product import InMemoryProductRepository
from mtaffiliate.adapters.persistence.inmemory.program1_opportunity import (
    InMemoryProgram1OpportunityRepository,
)
from mtaffiliate.adapters.persistence.inmemory.program1_strategy import (
    InMemoryProgram1StrategyRepository,
)
from mtaffiliate.adapters.persistence.inmemory.program2_artifact import (
    InMemoryProgram2ArtifactRepository,
)
from mtaffiliate.adapters.persistence.inmemory.program2_decision import (
    InMemoryProgram2DecisionRepository,
)
from mtaffiliate.adapters.persistence.inmemory.program2_work import InMemoryProgram2WorkRepository
from mtaffiliate.adapters.persistence.inmemory.program3_execution import (
    InMemoryProgram3ExecutionRepository,
)
from mtaffiliate.adapters.persistence.inmemory.publishing import (
    InMemoryPublishingLedgerRepository,
)
from mtaffiliate.adapters.persistence.inmemory.worker_registry import (
    InMemoryWorkerRegistryRepository,
)
from mtaffiliate.application.program1 import IngestionBatchConflictError, Program1Service
from mtaffiliate.application.program1_jobs import Program1DiscoveryJobService
from mtaffiliate.application.program1_opportunity import Program1OpportunityService
from mtaffiliate.application.program1_strategy import Program1StrategyPlanner
from mtaffiliate.application.program2 import Program2Service
from mtaffiliate.application.program2_artifacts import Program2ArtifactService
from mtaffiliate.application.program2_intelligence import Program2OfferDecisionService
from mtaffiliate.application.program2_jobs import Program2OfferDiscoveryJobService
from mtaffiliate.application.program3 import Program3Service
from mtaffiliate.application.program3_authority import Program3AuthoritativeService
from mtaffiliate.application.worker_registry import (
    DEFAULT_STALE_HEARTBEAT_MULTIPLIER,
    WorkerRegistryService,
    utc_now,
)
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateLinkArtifact,
    AffiliateOfferObservation,
    OfferScore,
    OfferSelection,
    OfferSelectionDecision,
    Program3OfferHandoff,
)
from mtaffiliate.domain.product.models import ProductObservation, ShortlistEntry
from mtaffiliate.domain.program1.opportunity import (
    OpportunityDecisionRecord,
    QualifiedOpportunityHandoff,
)
from mtaffiliate.domain.publishing.models import (
    DuplicateDecision,
    PreSubmitDecision,
    Program3PlanPackage,
    PublishingLedgerEntry,
    PublishPlan,
    ReconciliationDecision,
    SubmissionRecord,
)
from mtaffiliate.domain.worker_registry.models import (
    WorkerHealthState,
    WorkerRecord,
    WorkerRegistration,
    WorkerSummary,
)
from mtaffiliate.engines.affiliate_offer_engine.service import (
    AffiliateOfferEngine,
    EvidenceFirstOfferIntelligence,
    OfferScoringPolicy,
)
from mtaffiliate.engines.opportunity_intelligence_engine.service import (
    OpportunityIntelligenceEngine,
)
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine
from mtaffiliate.interfaces.api.shared_jobs import build_shared_job_router
from mtaffiliate.ports.repositories.product import ObservationConflictError
from mtaffiliate.ports.repositories.worker_registry import (
    UnknownWorkerError,
    WorkerRegistrationConflictError,
)


class ObservationBatch(BaseModel):
    batch_id: str = Field(min_length=1)
    observations: list[ProductObservation]
    job_id: str | None = Field(default=None, min_length=1)
    worker_id: str | None = Field(default=None, min_length=1)
    lease_token: str | None = Field(default=None, min_length=1)


class OfferObservationBatch(BaseModel):
    batch_id: str = Field(default="legacy-unbound-batch-v1", min_length=1)
    observations: list[AffiliateOfferObservation]
    job_id: str | None = Field(default=None, min_length=1)
    worker_id: str | None = Field(default=None, min_length=1)
    lease_token: str | None = Field(default=None, min_length=1)


class OfferSelectionRequest(BaseModel):
    affiliate_account_id: str = Field(min_length=1)
    backup_count: int | None = Field(default=None, ge=0, le=20)


class OfferDecisionRequest(BaseModel):
    affiliate_account_id: str = Field(min_length=1)
    source_job_id: str = Field(min_length=1)
    evaluated_at: datetime


class Program3HandoffRequest(BaseModel):
    as_of: datetime


class PublishStatusRequest(BaseModel):
    plan: PublishPlan
    status: str = Field(min_length=1)


class Program3PlanRequest(BaseModel):
    handoff: Program3OfferHandoff
    plan_ref: str = Field(min_length=1)
    publish_job_id: str = Field(min_length=1)
    target_account_id: str = Field(min_length=1)
    video_id: str = Field(min_length=1)
    video_sha256: str = Field(min_length=64, max_length=64)
    created_at: datetime
    caption: str = ""
    tags: list[str] = Field(default_factory=list)


class Program3JobRequest(BaseModel):
    idempotency_key: str = Field(min_length=1)
    created_at: datetime
    priority: int = 0


class Program3PreSubmitRequest(BaseModel):
    worker_id: str = Field(min_length=1)
    lease_token: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    target_account_id: str = Field(min_length=1)
    scene_ready: bool
    evaluated_at: datetime
    evidence_refs: tuple[str, ...] = ()


class Program3SubmittedRequest(BaseModel):
    decision_id: str = Field(min_length=1)
    lease_token: str = Field(min_length=1)
    submitted_at: datetime
    idempotency_key: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()


class Program3ReconcileRequest(BaseModel):
    evaluated_at: datetime
    success_confirmed: bool = False
    failure_safe_to_retry_confirmed: bool = False
    human_required: bool = False
    evidence_refs: tuple[str, ...] = ()


class Program3ConfirmRequest(BaseModel):
    reconciliation: ReconciliationDecision
    confirmed_at: datetime


class WorkerHeartbeatRequest(BaseModel):
    schema_version: str = Field(default="worker-heartbeat-v1", min_length=1)
    health_state: WorkerHealthState


class OpportunityEvaluationRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    evaluated_at: datetime


def build_inmemory_program1(settings: Settings) -> Program1Service:
    scoring = settings.program1.scoring
    engine = ProductIntelligenceEngine(
        ScoringPolicy(
            demand_weight=scoring.demand_weight,
            rating_weight=scoring.rating_weight,
            review_weight=scoring.review_weight,
            price_fit_weight=scoring.price_fit_weight,
        )
    )
    return Program1Service(
        InMemoryProductRepository(),
        engine,
        shortlist_limit=settings.program1.shortlist_limit,
        minimum_score=settings.program1.minimum_score,
    )


def build_inmemory_program2(settings: Settings) -> Program2Service:
    scoring = settings.program2.scoring
    return Program2Service(
        InMemoryAffiliateOfferRepository(),
        AffiliateOfferEngine(
            OfferScoringPolicy(
                commission_weight=scoring.commission_weight,
                rating_weight=scoring.rating_weight,
                review_weight=scoring.review_weight,
                demand_weight=scoring.demand_weight,
            )
        ),
    )


def build_inmemory_program3() -> Program3Service:
    return Program3Service(
        InMemoryPublishingLedgerRepository(),
        PublishingGuardEngine(),
    )


def build_inmemory_worker_registry(settings: Settings) -> WorkerRegistryService:
    return WorkerRegistryService(
        InMemoryWorkerRegistryRepository(),
        stale_after=timedelta(
            seconds=settings.worker.heartbeat_seconds * DEFAULT_STALE_HEARTBEAT_MULTIPLIER
        ),
    )


def create_app(
    settings: Settings | None = None,
    *,
    program1: Program1Service | None = None,
    program2: Program2Service | None = None,
    program3: Program3Service | None = None,
    registry: WorkerRegistryService | None = None,
    shared_jobs: SharedJobEngine | None = None,
    program1_jobs: Program1DiscoveryJobService | None = None,
    program1_opportunities: Program1OpportunityService | None = None,
    program2_jobs: Program2OfferDiscoveryJobService | None = None,
    program2_intelligence: Program2OfferDecisionService | None = None,
    program2_artifacts: Program2ArtifactService | None = None,
    program3_authority: Program3AuthoritativeService | None = None,
    enabled_programs: set[str] | None = None,
) -> FastAPI:
    enabled = enabled_programs or {"program1", "program2", "program3"}
    unknown = enabled - {"program1", "program2", "program3"}
    if unknown:
        raise ValueError(f"unknown enabled programs: {sorted(unknown)}")
    cfg = settings or Settings()
    service1 = program1 or build_inmemory_program1(cfg) if "program1" in enabled else None
    service2 = program2 or build_inmemory_program2(cfg) if "program2" in enabled else None
    service3 = program3 or build_inmemory_program3() if "program3" in enabled else None
    registry_service = registry or build_inmemory_worker_registry(cfg)
    shared_job_engine = shared_jobs or SharedJobEngine(InMemoryJobRepository())
    program1_job_service = program1_jobs or Program1DiscoveryJobService(
        Program1StrategyPlanner(),
        InMemoryProgram1StrategyRepository(),
        shared_job_engine,
    )
    program1_opportunity_service = program1_opportunities
    if program1_opportunity_service is None and "program1" in enabled:
        assert service1 is not None
        program1_opportunity_service = Program1OpportunityService(
            products=service1.repository,
            jobs=shared_job_engine.repository,
            strategies=program1_job_service.strategy_repository,
            decisions=InMemoryProgram1OpportunityRepository(),
            intelligence=OpportunityIntelligenceEngine(),
        )
    program2_job_service = program2_jobs
    if program2_job_service is None and "program2" in enabled:
        program2_job_service = Program2OfferDiscoveryJobService(
            InMemoryProgram2WorkRepository(),
            shared_job_engine,
        )
    program2_decision_service = program2_intelligence
    if program2_decision_service is None and "program2" in enabled:
        assert service2 is not None
        program2_decision_service = Program2OfferDecisionService(
            offers=service2.repository,
            decisions=InMemoryProgram2DecisionRepository(),
            intelligence=EvidenceFirstOfferIntelligence(),
        )
    program2_artifact_service = program2_artifacts
    if program2_artifact_service is None and "program2" in enabled:
        assert program2_decision_service is not None
        program2_artifact_service = Program2ArtifactService(
            decisions=program2_decision_service.decisions,
            artifacts=InMemoryProgram2ArtifactRepository(),
        )
    program3_authority_service = program3_authority
    if program3_authority_service is None and "program3" in enabled:
        program3_decisions = (
            program2_decision_service.decisions
            if program2_decision_service is not None
            else InMemoryProgram2DecisionRepository()
        )
        program3_artifacts = (
            program2_artifact_service.artifacts
            if program2_artifact_service is not None
            else InMemoryProgram2ArtifactRepository()
        )
        program3_ledger = service3.ledger if service3 is not None else InMemoryPublishingLedgerRepository()
        program3_authority_service = Program3AuthoritativeService(
            decisions=program3_decisions,
            artifacts=program3_artifacts,
            execution=InMemoryProgram3ExecutionRepository(),
            ledger=program3_ledger,
            jobs=shared_job_engine,
            guard=PublishingGuardEngine(),
        )
    app = FastAPI(title="MTAffiliatePlatform", version="0.2.0")

    @app.get("/")
    def root() -> dict[str, str | list[str]]:
        return {
            "service": "MTAffiliatePlatform API",
            "status": "ok",
            "enabled_programs": sorted(enabled),
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/workers/register", response_model=WorkerRecord)
    def register_worker(registration: WorkerRegistration) -> WorkerRecord:
        try:
            return registry_service.register(registration, seen_at=utc_now())
        except WorkerRegistrationConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post(
        "/api/v1/workers/{worker_id}/heartbeat",
        response_model=WorkerRecord,
    )
    def heartbeat(worker_id: str, request: WorkerHeartbeatRequest) -> WorkerRecord:
        try:
            return registry_service.record_heartbeat(
                worker_id,
                health_state=request.health_state,
                seen_at=utc_now(),
            )
        except UnknownWorkerError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/v1/workers", response_model=list[WorkerSummary])
    def list_workers() -> list[WorkerSummary]:
        return registry_service.summaries(now=utc_now())

    @app.get("/api/v1/workers/{worker_id}", response_model=WorkerSummary)
    def get_worker(worker_id: str) -> WorkerSummary:
        summary = registry_service.summary(worker_id, now=utc_now())
        if summary is None:
            raise HTTPException(status_code=404, detail=f"unknown worker: {worker_id}")
        return summary

    if enabled.intersection({"program1", "program2", "program3"}):
        app.include_router(
            build_shared_job_router(
                program1_jobs=program1_job_service if "program1" in enabled else None,
                program2_jobs=program2_job_service if "program2" in enabled else None,
                jobs=shared_job_engine,
                registry=registry_service,
                lease_seconds=cfg.worker.lease_seconds,
                clock=utc_now,
            )
        )

    if "program1" in enabled:

        @app.post("/api/v1/program1/observations")
        def ingest(batch: ObservationBatch) -> dict[str, int | str]:
            assert service1 is not None
            bound_observations = [
                observation
                for observation in batch.observations
                if observation.source_job_id is not None
            ]
            if bound_observations:
                if not (batch.job_id and batch.worker_id and batch.lease_token):
                    raise HTTPException(
                        status_code=422,
                        detail="job-bound observations require job_id, worker_id and lease_token",
                    )
                if any(
                    observation.source_job_id != batch.job_id
                    or observation.source_worker_id != batch.worker_id
                    for observation in bound_observations
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="observation provenance does not match execution envelope",
                    )
                try:
                    shared_job_engine.validate_active_execution(
                        batch.job_id,
                        worker_id=batch.worker_id,
                        lease_token=batch.lease_token,
                        at=utc_now(),
                    )
                except (KeyError, ValueError, RuntimeError) as exc:
                    raise HTTPException(status_code=409, detail=str(exc)) from exc
            try:
                result = service1.ingest_batch(batch.batch_id, batch.observations)
            except (IngestionBatchConflictError, ObservationConflictError) as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            return {
                "batch_id": batch.batch_id,
                "received_count": result.received_count,
                "accepted_count": result.accepted_count,
            }

        @app.get("/api/v1/program1/shortlist", response_model=list[ShortlistEntry])
        def shortlist() -> list[ShortlistEntry]:
            assert service1 is not None
            return service1.build_shortlist()

        @app.post(
            "/api/v1/program1/opportunities/evaluate",
            response_model=list[OpportunityDecisionRecord],
        )
        def evaluate_opportunities(
            request: OpportunityEvaluationRequest,
        ) -> list[OpportunityDecisionRecord]:
            assert program1_opportunity_service is not None
            try:
                return program1_opportunity_service.evaluate_campaign(
                    request.campaign_id,
                    evaluated_at=request.evaluated_at,
                )
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

        @app.get(
            "/api/v1/program1/campaigns/{campaign_id}/opportunities",
            response_model=list[OpportunityDecisionRecord],
        )
        def list_opportunities(campaign_id: str) -> list[OpportunityDecisionRecord]:
            assert program1_opportunity_service is not None
            return program1_opportunity_service.decisions.list_for_campaign(campaign_id)

        @app.get(
            "/api/v1/program1/campaigns/{campaign_id}/qualified-handoffs",
            response_model=list[QualifiedOpportunityHandoff],
        )
        def qualified_handoffs(campaign_id: str) -> list[QualifiedOpportunityHandoff]:
            assert program1_opportunity_service is not None
            return program1_opportunity_service.qualified_handoffs(campaign_id)

    if "program2" in enabled:

        @app.post("/api/v1/program2/observations")
        def ingest_offers(batch: OfferObservationBatch) -> dict[str, int | str]:
            assert service2 is not None
            bound = [
                observation
                for observation in batch.observations
                if observation.source_job_id is not None
            ]
            if bound:
                if not (batch.job_id and batch.worker_id and batch.lease_token):
                    raise HTTPException(
                        status_code=422,
                        detail="job-bound offer observations require job_id, worker_id and lease_token",
                    )
                try:
                    shared_job_engine.validate_active_execution(
                        batch.job_id,
                        worker_id=batch.worker_id,
                        lease_token=batch.lease_token,
                        at=utc_now(),
                    )
                    if program2_job_service is None:
                        raise ValueError("Program 2 job service is unavailable")
                    package = program2_job_service.get_work_package(batch.job_id)
                except (KeyError, ValueError, RuntimeError) as exc:
                    raise HTTPException(status_code=409, detail=str(exc)) from exc

                if any(
                    observation.source_job_id != batch.job_id
                    or observation.source_worker_id != batch.worker_id
                    for observation in bound
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="offer observation provenance does not match execution envelope",
                    )
                if any(
                    observation.product_id != package.product_id
                    or observation.affiliate_account_id != package.affiliate_account_id
                    for observation in bound
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="offer observation product/account does not match work package",
                    )
                if any(not observation.session_context_id for observation in bound):
                    raise HTTPException(
                        status_code=422,
                        detail="job-bound offer observations require session_context_id",
                    )

            try:
                accepted = service2.ingest_observations(batch.observations)
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            response: dict[str, int | str] = {
                "received_count": len(batch.observations),
                "accepted_count": accepted,
            }
            if "batch_id" in batch.model_fields_set:
                response["batch_id"] = batch.batch_id
            return response

        @app.get(
            "/api/v1/program2/products/{product_id}/offers",
            response_model=list[OfferScore],
        )
        def rank_offers(
            product_id: str,
            affiliate_account_id: str | None = None,
        ) -> list[OfferScore]:
            assert service2 is not None
            return service2.rank_offers(
                product_id,
                affiliate_account_id=affiliate_account_id,
            )

        @app.post(
            "/api/v1/program2/products/{product_id}/selection",
            response_model=OfferSelection,
        )
        def select_offers(product_id: str, request: OfferSelectionRequest) -> OfferSelection:
            assert service2 is not None
            try:
                return service2.select_offers(
                    product_id,
                    affiliate_account_id=request.affiliate_account_id,
                    backup_count=(
                        cfg.program2.backup_offer_count
                        if request.backup_count is None
                        else request.backup_count
                    ),
                )
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

        @app.post(
            "/api/v1/program2/products/{product_id}/selection-decisions",
            response_model=OfferSelectionDecision,
        )
        def decide_offers(
            product_id: str,
            request: OfferDecisionRequest,
        ) -> OfferSelectionDecision:
            assert program2_decision_service is not None
            try:
                return program2_decision_service.evaluate_and_select(
                    product_id=product_id,
                    affiliate_account_id=request.affiliate_account_id,
                    source_job_id=request.source_job_id,
                    evaluated_at=request.evaluated_at,
                )
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

        @app.get(
            "/api/v1/program2/products/{product_id}/accounts/{affiliate_account_id}/selection-decision",
            response_model=OfferSelectionDecision,
        )
        def latest_offer_decision(
            product_id: str,
            affiliate_account_id: str,
        ) -> OfferSelectionDecision:
            assert program2_decision_service is not None
            decision = program2_decision_service.decisions.latest_for_product_account(
                product_id,
                affiliate_account_id,
            )
            if decision is None:
                raise HTTPException(status_code=404, detail="selection decision not found")
            return decision

        @app.post(
            "/api/v1/program2/link-artifacts",
            response_model=AffiliateLinkArtifact,
        )
        def register_link_artifact(
            artifact: AffiliateLinkArtifact,
        ) -> AffiliateLinkArtifact:
            assert program2_artifact_service is not None
            try:
                return program2_artifact_service.register_artifact(artifact)
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

        @app.post(
            "/api/v1/program2/selection-decisions/{decision_id}/program3-handoff",
            response_model=Program3OfferHandoff,
        )
        def build_program3_handoff(
            decision_id: str,
            request: Program3HandoffRequest,
        ) -> Program3OfferHandoff:
            assert program2_artifact_service is not None
            try:
                return program2_artifact_service.build_program3_handoff(
                    decision_id,
                    as_of=request.as_of,
                )
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

    if "program3" in enabled:

        @app.post("/api/v1/program3/publish/evaluate", response_model=DuplicateDecision)
        def evaluate_publish(plan: PublishPlan) -> DuplicateDecision:
            assert service3 is not None
            return service3.evaluate_plan(plan)

        @app.post("/api/v1/program3/publish/status", response_model=PublishingLedgerEntry)
        def record_publish_status(request: PublishStatusRequest) -> PublishingLedgerEntry:
            assert service3 is not None
            try:
                return service3.record_status(request.plan, request.status)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

        @app.post("/api/v1/program3/plans", response_model=Program3PlanPackage)
        def build_program3_plan(request: Program3PlanRequest) -> Program3PlanPackage:
            assert program3_authority_service is not None
            try:
                return program3_authority_service.build_publish_plan(
                    handoff=request.handoff,
                    plan_ref=request.plan_ref,
                    publish_job_id=request.publish_job_id,
                    target_account_id=request.target_account_id,
                    video_id=request.video_id,
                    video_sha256=request.video_sha256,
                    created_at=request.created_at,
                    caption=request.caption,
                    tags=request.tags,
                )
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

        @app.post("/api/v1/program3/plans/{plan_ref}/job")
        def create_program3_job(plan_ref: str, request: Program3JobRequest):
            assert program3_authority_service is not None
            try:
                return program3_authority_service.create_publish_job(
                    plan_ref=plan_ref,
                    idempotency_key=request.idempotency_key,
                    created_at=request.created_at,
                    priority=request.priority,
                )
            except (ValueError, RuntimeError) as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

        @app.post(
            "/api/v1/program3/jobs/{publish_job_id}/pre-submit",
            response_model=PreSubmitDecision,
        )
        def program3_pre_submit(
            publish_job_id: str,
            request: Program3PreSubmitRequest,
        ) -> PreSubmitDecision:
            assert program3_authority_service is not None
            try:
                return program3_authority_service.pre_submit(
                    publish_job_id=publish_job_id,
                    worker_id=request.worker_id,
                    lease_token=request.lease_token,
                    device_id=request.device_id,
                    target_account_id=request.target_account_id,
                    scene_ready=request.scene_ready,
                    evaluated_at=request.evaluated_at,
                    evidence_refs=request.evidence_refs,
                )
            except (KeyError, ValueError, RuntimeError) as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

        @app.post("/api/v1/program3/submissions", response_model=SubmissionRecord)
        def program3_post_submitted(request: Program3SubmittedRequest) -> SubmissionRecord:
            assert program3_authority_service is not None
            try:
                return program3_authority_service.record_post_submitted(
                    decision_id=request.decision_id,
                    lease_token=request.lease_token,
                    submitted_at=request.submitted_at,
                    idempotency_key=request.idempotency_key,
                    evidence_refs=request.evidence_refs,
                )
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

        @app.post(
            "/api/v1/program3/submissions/{submission_id}/reconcile",
            response_model=ReconciliationDecision,
        )
        def program3_reconcile(
            submission_id: str,
            request: Program3ReconcileRequest,
        ) -> ReconciliationDecision:
            assert program3_authority_service is not None
            try:
                return program3_authority_service.reconcile(
                    submission_id=submission_id,
                    evaluated_at=request.evaluated_at,
                    success_confirmed=request.success_confirmed,
                    failure_safe_to_retry_confirmed=request.failure_safe_to_retry_confirmed,
                    human_required=request.human_required,
                    evidence_refs=request.evidence_refs,
                )
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

        @app.post(
            "/api/v1/program3/publish/confirm",
            response_model=PublishingLedgerEntry,
        )
        def program3_confirm(request: Program3ConfirmRequest) -> PublishingLedgerEntry:
            assert program3_authority_service is not None
            try:
                return program3_authority_service.confirm_success(
                    reconciliation=request.reconciliation,
                    confirmed_at=request.confirmed_at,
                )
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

    return app
