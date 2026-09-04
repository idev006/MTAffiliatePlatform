from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from mtaffiliate.application.program1 import Program1Service
from mtaffiliate.application.program1_jobs import Program1DiscoveryJobService
from mtaffiliate.application.program1_opportunity import Program1OpportunityService
from mtaffiliate.application.program2 import Program2Service
from mtaffiliate.application.program2_intelligence import Program2OfferDecisionService
from mtaffiliate.application.program2_jobs import Program2OfferDiscoveryJobService
from mtaffiliate.application.program3 import Program3Service
from mtaffiliate.application.worker_registry import WorkerRegistryService
from mtaffiliate.bootstrap.config import load_settings
from mtaffiliate.bootstrap.migrations import upgrade_database_to_head
from mtaffiliate.bootstrap.program1 import build_durable_program1
from mtaffiliate.bootstrap.program1_jobs import build_durable_program1_job_service
from mtaffiliate.bootstrap.program1_opportunity import (
    build_durable_program1_opportunity_service,
)
from mtaffiliate.bootstrap.program2 import build_durable_program2
from mtaffiliate.bootstrap.program2_intelligence import build_durable_program2_intelligence
from mtaffiliate.bootstrap.program2_jobs import build_durable_program2_job_service
from mtaffiliate.bootstrap.program3 import build_durable_program3
from mtaffiliate.bootstrap.shared_job import build_durable_shared_job_engine
from mtaffiliate.bootstrap.worker_registry import build_durable_worker_registry
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine
from mtaffiliate.interfaces.api.app import create_app

VALID_PROGRAMS = frozenset({"program1", "program2", "program3"})


def project_root_from_environment() -> Path:
    configured = os.getenv("MTAFFILIATE_PROJECT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[3]


def create_runtime_app(
    enabled_programs: set[str],
    *,
    default_profile: str,
    project_root: Path | None = None,
) -> FastAPI:
    unknown = enabled_programs - VALID_PROGRAMS
    if unknown:
        raise ValueError(f"unknown runtime programs: {sorted(unknown)}")

    root = (project_root or project_root_from_environment()).resolve()
    profile = os.getenv("MTAFFILIATE_PROFILE", default_profile)
    settings = load_settings(root, profile=profile)
    settings.path_manager(root).ensure_runtime_dirs()

    if settings.database.auto_migrate:
        upgrade_database_to_head(settings.database.url, project_root=root)

    program1: Program1Service | None = None
    program2: Program2Service | None = None
    program3: Program3Service | None = None
    registry: WorkerRegistryService | None = None
    shared_jobs: SharedJobEngine | None = None
    program1_jobs: Program1DiscoveryJobService | None = None
    program1_opportunities: Program1OpportunityService | None = None
    program2_jobs: Program2OfferDiscoveryJobService | None = None
    program2_intelligence: Program2OfferDecisionService | None = None
    if "program1" in enabled_programs:
        program1 = build_durable_program1(settings, project_root=root)
    if "program2" in enabled_programs:
        program2 = build_durable_program2(settings, project_root=root)
        program2_intelligence = build_durable_program2_intelligence(
            settings,
            project_root=root,
        )
    if "program3" in enabled_programs:
        program3 = build_durable_program3(settings, project_root=root)
    registry = build_durable_worker_registry(settings, project_root=root)
    shared_jobs = build_durable_shared_job_engine(settings, project_root=root)
    if "program1" in enabled_programs:
        program1_jobs = build_durable_program1_job_service(
            settings,
            project_root=root,
            jobs=shared_jobs,
        )
        program1_opportunities = build_durable_program1_opportunity_service(
            settings,
            project_root=root,
            jobs=shared_jobs,
        )
    if "program2" in enabled_programs:
        program2_jobs = build_durable_program2_job_service(
            settings,
            project_root=root,
            jobs=shared_jobs,
        )

    return create_app(
        settings,
        program1=program1,
        program2=program2,
        program3=program3,
        registry=registry,
        shared_jobs=shared_jobs,
        program1_jobs=program1_jobs,
        program1_opportunities=program1_opportunities,
        program2_jobs=program2_jobs,
        program2_intelligence=program2_intelligence,
        enabled_programs=enabled_programs,
    )
