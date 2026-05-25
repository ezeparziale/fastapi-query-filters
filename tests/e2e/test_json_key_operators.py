from collections.abc import Generator
from typing import Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterDep, FilterValues
from fastapi_query_filters.orm.sqlalchemy import apply_filters
from tests.models import Mission
from tests.schemas import MissionOut

app = FastAPI()

# Coverage matrix
# Operators: has_key, has_any_keys, has_all_keys
# Scenarios: exists/missing, partial JSON, NULL column, list parsing (repeated params)
# Engines: sqlite/mysql/postgresql (via TEST_DATABASE_URL)


def get_db() -> Session | None:
    return None


@app.get("/missions-keys", response_model=list[dict[str, Any]])
def list_missions(
    filters: FilterValues = FilterDep(MissionOut), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    stmt = apply_filters(select(Mission), Mission, filters)
    results = db.execute(stmt).scalars().all()
    return [
        {"id": m.id, "planet": m.planet_name, "data": m.mission_metadata}
        for m in results
    ]


@pytest.fixture
def client(seeded_db: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_e2e_has_key_exists(client: TestClient) -> None:
    response = client.get("/missions-keys?m_metadata__has_key=commander")
    assert response.status_code == 200
    planets = {d["planet"] for d in response.json()}
    assert planets == {"P3X-984", "P4X-639", "P2X-555", "Partial Data Planet"}


def test_e2e_has_key_missing(client: TestClient) -> None:
    response = client.get("/missions-keys?m_metadata__has_key=nope")
    assert response.status_code == 200
    assert response.json() == []


def test_e2e_has_any_keys_repeated_params(client: TestClient) -> None:
    response = client.get(
        "/missions-keys?m_metadata__has_any_keys=danger_level&m_metadata__has_any_keys=nope"
    )
    assert response.status_code == 200
    planets = {d["planet"] for d in response.json()}
    assert planets == {"P3X-984", "P4X-639", "P2X-555"}


def test_e2e_has_all_keys_repeated_params(client: TestClient) -> None:
    response = client.get(
        "/missions-keys?m_metadata__has_all_keys=commander&m_metadata__has_all_keys=danger_level"
    )
    assert response.status_code == 200
    planets = {d["planet"] for d in response.json()}
    assert planets == {"P3X-984", "P4X-639", "P2X-555"}


def test_e2e_has_all_keys_missing_one(client: TestClient) -> None:
    response = client.get(
        "/missions-keys?m_metadata__has_all_keys=commander&m_metadata__has_all_keys=missing"
    )
    assert response.status_code == 200
    assert response.json() == []
