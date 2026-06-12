from collections.abc import Generator
from typing import Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterDep, FilterValues
from fastapi_query_filters.orm.sqlalchemy import apply_filters
from tests.models import StargateArtifact
from tests.schemas import (
    StargateArtifactDecommissionedOut,
    StargateArtifactDestroyedOut,
)

app = FastAPI()


def get_db() -> Session | None:
    return None


@app.get("/artifacts/destroyed", response_model=list[dict[str, Any]])
def list_artifacts_destroyed(
    filters: FilterValues = FilterDep(StargateArtifactDestroyedOut),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    stmt = select(StargateArtifact)
    stmt = apply_filters(stmt, StargateArtifact, filters)
    results = db.execute(stmt).scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "origin_planet": r.origin_planet,
            "is_destroyed": r.is_destroyed,
        }
        for r in results
    ]


@app.get("/artifacts/decommissioned", response_model=list[dict[str, Any]])
def list_artifacts_decommissioned(
    filters: FilterValues = FilterDep(StargateArtifactDecommissionedOut),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    stmt = select(StargateArtifact)
    stmt = apply_filters(stmt, StargateArtifact, filters)
    results = db.execute(stmt).scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "origin_planet": r.origin_planet,
            "decommissioned_at": r.decommissioned_at.isoformat()
            if r.decommissioned_at
            else None,
        }
        for r in results
    ]


@pytest.fixture
def client(seeded_db: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_e2e_soft_delete_boolean(client: TestClient) -> None:
    """Test soft-delete with boolean flag via E2E GET request.

    Should automatically exclude the destroyed staff weapon by default.
    """
    response = client.get("/artifacts/destroyed")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [item["name"] for item in data]
    assert "GDO" in names
    assert "Zat'nik'tel" in names
    assert "Staff Weapon" not in names


def test_e2e_soft_delete_datetime(client: TestClient) -> None:
    """Test soft-delete with decommissioned timestamp via E2E GET request.

    Should automatically exclude decommissioned Zat'nik'tel by default.
    """
    response = client.get("/artifacts/decommissioned")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [item["name"] for item in data]
    assert "GDO" in names
    assert "Staff Weapon" in names
    assert "Zat'nik'tel" not in names
