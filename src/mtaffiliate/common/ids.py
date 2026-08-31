from __future__ import annotations

from typing import NewType
from uuid import uuid4

ProductId = NewType("ProductId", str)
ObservationId = NewType("ObservationId", str)
BatchId = NewType("BatchId", str)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"
