import pytest
from pydantic import ValidationError

from mtaffiliate.bootstrap.config import Settings


def test_program2_program3_defaults_are_typed_and_safe() -> None:
    settings = Settings()
    assert settings.program2.backup_offer_count == 2
    assert settings.program2.scoring.commission_weight == 1.0
    assert settings.program3.duplicate_policy_version == "duplicate-v1"


def test_program2_rejects_invalid_scoring_and_backup_count() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate(
            {
                "program2": {
                    "backup_offer_count": -1,
                }
            }
        )
    with pytest.raises(ValidationError):
        Settings.model_validate(
            {
                "program2": {
                    "scoring": {
                        "commission_weight": 0,
                        "rating_weight": 0,
                        "review_weight": 0,
                        "demand_weight": 0,
                    }
                }
            }
        )


def test_program3_rejects_blank_policy_version() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"program3": {"duplicate_policy_version": ""}})
