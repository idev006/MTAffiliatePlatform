from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mtaffiliate.application.program1_jobs import Program1DiscoveryJobService
from mtaffiliate.application.worker_registry import WorkerRegistryService
from mtaffiliate.domain.job.models import JobRecord
from mtaffiliate.domain.program1.models import (
    AffiliateSuccessHypothesis,
    DiscoveryPlan,
    SignalRequirement,
)
from mtaffiliate.engines.shared_job_engine.service import (
    IdempotencyConflictError,
    InvalidJobTransitionError,
    SharedJobEngine,
    StaleLeaseError,
)
from mtaffiliate.ports.repositories.job import JobRepositoryConflictError


class Program1DiscoveryJobRequest(BaseModel):
    job_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    discovery_plan_ref: str = Field(min_length=1)
    hypothesis: AffiliateSuccessHypothesis
    signals: list[SignalRequirement]
    discovery_plan: DiscoveryPlan
    priority: int = 0


class JobLeaseRequest(BaseModel):
    worker_id: str = Field(min_length=1)


class JobLeaseIdentityRequest(BaseModel):
    worker_id: str = Field(min_length=1)
    lease_token: str = Field(min_length=1)


class JobCheckpointRequest(JobLeaseIdentityRequest):
    checkpoint_type: str = Field(min_length=1)
    payload: dict[str, object] = Field(default_factory=dict)


def build_shared_job_router(
    *,
    program1_jobs: Program1DiscoveryJobService,
    jobs: SharedJobEngine,
    registry: WorkerRegistryService,
    lease_seconds: int,
    clock: Callable[[], datetime],
) -> APIRouter:
    if lease_seconds <= 0:
        raise ValueError("lease_seconds must be positive")

    router = APIRouter(prefix="/api/v1")

    def translate_error(exc: Exception) -> HTTPException:
        if isinstance(exc, KeyError):
            return HTTPException(status_code=404, detail=f"unknown job: {exc.args[0]}")
        if isinstance(
            exc,
            (
                InvalidJobTransitionError,
                StaleLeaseError,
                IdempotencyConflictError,
                JobRepositoryConflictError,
            ),
        ):
            return HTTPException(status_code=409, detail=str(exc))
        if isinstance(exc, ValueError):
            return HTTPException(status_code=422, detail=str(exc))
        return HTTPException(status_code=500, detail="unexpected job lifecycle error")

    @router.post("/program1/discovery-jobs", response_model=JobRecord)
    def create_program1_discovery_job(request: Program1DiscoveryJobRequest) -> JobRecord:
        try:
            return program1_jobs.create_discovery_job(
                hypothesis=request.hypothesis,
                signals=request.signals,
                discovery_plan=request.discovery_plan,
                discovery_plan_ref=request.discovery_plan_ref,
                job_id=request.job_id,
                idempotency_key=request.idempotency_key,
                priority=request.priority,
                created_at=clock(),
            )
        except Exception as exc:
            raise translate_error(exc) from exc

    @router.get("/jobs/{job_id}", response_model=JobRecord)
    def get_job(job_id: str) -> JobRecord:
        job = jobs.repository.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"unknown job: {job_id}")
        return job

    def authoritative_worker(worker_id: str, *, at: datetime):
        try:
            return registry.execution_record(worker_id, now=at)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"unknown worker: {worker_id}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/jobs/lease-next", response_model=JobRecord | None)
    def lease_next_job(request: JobLeaseRequest) -> JobRecord | None:
        at = clock()
        worker = authoritative_worker(request.worker_id, at=at)
        try:
            return jobs.lease_next(
                worker_id=worker.worker_id,
                worker_capabilities=set(worker.capabilities),
                at=at,
                lease_for=timedelta(seconds=lease_seconds),
            )
        except Exception as exc:
            raise translate_error(exc) from exc

    @router.post("/jobs/{job_id}/lease", response_model=JobRecord)
    def lease_job(job_id: str, request: JobLeaseRequest) -> JobRecord:
        at = clock()
        worker = authoritative_worker(request.worker_id, at=at)
        try:
            return jobs.lease_job(
                job_id,
                worker_id=worker.worker_id,
                worker_capabilities=set(worker.capabilities),
                at=at,
                lease_for=timedelta(seconds=lease_seconds),
            )
        except Exception as exc:
            raise translate_error(exc) from exc

    @router.post("/jobs/{job_id}/start", response_model=JobRecord)
    def start_job(job_id: str, request: JobLeaseIdentityRequest) -> JobRecord:
        try:
            return jobs.start_job(
                job_id,
                worker_id=request.worker_id,
                lease_token=request.lease_token,
                at=clock(),
            )
        except Exception as exc:
            raise translate_error(exc) from exc

    @router.post("/jobs/{job_id}/renew", response_model=JobRecord)
    def renew_job(job_id: str, request: JobLeaseIdentityRequest) -> JobRecord:
        try:
            return jobs.renew_lease(
                job_id,
                worker_id=request.worker_id,
                lease_token=request.lease_token,
                at=clock(),
                lease_for=timedelta(seconds=lease_seconds),
            )
        except Exception as exc:
            raise translate_error(exc) from exc

    @router.post("/jobs/{job_id}/checkpoint", response_model=JobRecord)
    def checkpoint_job(job_id: str, request: JobCheckpointRequest) -> JobRecord:
        try:
            return jobs.record_checkpoint(
                job_id,
                worker_id=request.worker_id,
                lease_token=request.lease_token,
                checkpoint_type=request.checkpoint_type,
                payload=request.payload,
                at=clock(),
            )
        except Exception as exc:
            raise translate_error(exc) from exc

    @router.post("/jobs/{job_id}/pause", response_model=JobRecord)
    def pause_job(job_id: str) -> JobRecord:
        try:
            return jobs.pause_job(job_id, at=clock())
        except Exception as exc:
            raise translate_error(exc) from exc

    @router.post("/jobs/{job_id}/resume", response_model=JobRecord)
    def resume_job(job_id: str) -> JobRecord:
        try:
            return jobs.resume_job(job_id, at=clock())
        except Exception as exc:
            raise translate_error(exc) from exc

    @router.post("/jobs/{job_id}/verify", response_model=JobRecord)
    def verify_job(job_id: str, request: JobLeaseIdentityRequest) -> JobRecord:
        try:
            return jobs.begin_verification(
                job_id,
                worker_id=request.worker_id,
                lease_token=request.lease_token,
                at=clock(),
            )
        except Exception as exc:
            raise translate_error(exc) from exc

    @router.post("/jobs/{job_id}/complete", response_model=JobRecord)
    def complete_job(job_id: str, request: JobLeaseIdentityRequest) -> JobRecord:
        try:
            return jobs.complete_job(
                job_id,
                worker_id=request.worker_id,
                lease_token=request.lease_token,
                at=clock(),
            )
        except Exception as exc:
            raise translate_error(exc) from exc

    return router
