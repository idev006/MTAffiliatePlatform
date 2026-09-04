from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from mtaffiliate.domain.job.models import JobRecord, JobState

NOW = datetime(2026, 9, 4, tzinfo=UTC)


def base_job(**updates):
    payload = {
        "job_id": "job-1",
        "job_type": "DISCOVER_PRODUCTS",
        "domain": "program1",
        "payload_ref": "discovery-plan:plan-1",
        "idempotency_key": "idem-1",
        "created_at": NOW,
        "updated_at": NOW,
    }
    payload.update(updates)
    return payload


@pytest.mark.parametrize(
    "updates",
    [
        {"assigned_worker_id": "worker-1"},
        {"lease_token": "lease-1"},
        {"lease_until": NOW + timedelta(minutes=1)},
    ],
)
def test_partial_lease_shape_is_invalid(updates) -> None:
    with pytest.raises(ValidationError, match="populated together"):
        JobRecord(**base_job(**updates))


@pytest.mark.parametrize(
    "state",
    [JobState.LEASED, JobState.IN_PROGRESS, JobState.VERIFYING],
)
def test_active_execution_states_require_lease(state: JobState) -> None:
    with pytest.raises(ValidationError, match="requires an active lease"):
        JobRecord(**base_job(state=state))
