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


# Dummy DB dependency for the test app
def get_db() -> Session | None:
    # This will be overridden by the test
    return None


@app.get("/missions", response_model=list[dict[str, Any]])
def list_missions(
    filters: FilterValues = FilterDep(MissionOut), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    stmt = select(Mission)
    stmt = apply_filters(stmt, Mission, filters)
    results = db.execute(stmt).scalars().all()

    # Manual serialization to match MissionOut structure
    return [
        {
            "id": m.id,
            "planet": m.planet_name,
            "data": m.mission_metadata,
        }
        for m in results
    ]


@pytest.fixture
def client(seeded_db: Session) -> Generator[TestClient, None, None]:
    # Override get_db to use our seeded test database
    app.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_missions_no_filters(client: TestClient) -> None:
    response = client.get("/missions")
    assert response.status_code == 200
    # 3 full missions + 1 empty + 1 partial
    assert len(response.json()) == 5


def test_get_missions_filter_commander(client: TestClient) -> None:
    # Test m_data__commander__eq
    response = client.get("/missions?m_data__commander__eq=Jack O'Neill")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["planet"] == "P3X-984"


def test_get_missions_filter_danger_level(client: TestClient) -> None:
    # Test m_data__danger_level__gt
    response = client.get("/missions?m_data__danger_level__gt=6")
    assert response.status_code == 200
    data = response.json()
    # P3X-984 (8), P2X-555 (10)
    assert len(data) == 2
    planets = [d["planet"] for d in data]
    assert "P3X-984" in planets
    assert "P2X-555" in planets


def test_get_missions_global_search(client: TestClient) -> None:
    # Search for "Carter"
    response = client.get("/missions?q=Carter")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["planet"] == "P4X-639"


def test_get_missions_sorting(client: TestClient) -> None:
    # Sort by danger_level ascending. None values are sorted first by default in SQLite.
    response = client.get("/missions?sort_by=m_data__danger_level")
    assert response.status_code == 200
    data = response.json()

    # Filter out None values to check relative order of the rest
    values = [
        d["data"]["danger_level"]
        for d in data
        if d["data"] and "danger_level" in d["data"]
    ]
    # 4, 8, 10
    assert values == [4, 8, 10]


def test_get_missions_date_range(client: TestClient) -> None:
    # Test gte and lte on dates
    response = client.get(
        "/missions?m_data__scheduled_date__gte=1998-01-01&m_data__scheduled_date__lte=2000-01-01"
    )
    assert response.status_code == 200
    data = response.json()
    # P4X-639 (1998-03-22) and P2X-555 (1999-01-01)
    assert len(data) == 2
    planets = [d["planet"] for d in data]
    assert "P4X-639" in planets
    assert "P2X-555" in planets


def test_get_missions_alias_check(client: TestClient) -> None:
    # Ensure 'planet' (alias) works instead of 'planet_name'
    response = client.get("/missions?m_planet__eq=P3X-984")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["planet"] == "P3X-984"
