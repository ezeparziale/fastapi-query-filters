from collections.abc import Generator
from typing import Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterDep, FilterValues
from fastapi_query_filters.orm.sqlalchemy import apply_filters
from tests.models import Post
from tests.schemas import PostOut

app = FastAPI()


def get_db() -> Session | None:
    # This dependency is overridden by the test fixture.
    return None


def _post_title(item: dict[str, Any]) -> str:
    return str(item.get("post_title") or item.get("title"))


@app.get("/posts", response_model=list[PostOut])
def list_posts(
    filters: FilterValues = FilterDep(PostOut),
    session: Session = Depends(get_db),
) -> Any:
    stmt = apply_filters(select(Post), Post, filters)
    return session.execute(stmt).scalars().all()


@pytest.fixture
def client(seeded_db: Session) -> Generator[TestClient, None, None]:
    """Build a TestClient overriding DB dependency with the seeded session."""
    app.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("field", "value", "expected_titles"),
    [
        (
            "f_incident_time__eq",
            "10:00:00",
            {"Medical supplies inventory"},
        ),
        (
            "f_incident_time__gte",
            "20:00:00",
            {"Mission to Abydos", "Contact with Asgard (Classified/Deleted)"},
        ),
        (
            "f_incident_time__lte",
            "11:00:00",
            {"Medical supplies inventory"},
        ),
    ],
)
def test_e2e_time_field_all_valid_operators(
    client: TestClient,
    field: str,
    value: str,
    expected_titles: set[str],
) -> None:
    """Validate all allowed time operators end-to-end."""
    response = client.get("/posts", params={field: value})

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == expected_titles


def test_e2e_time_field_combined_range(client: TestClient) -> None:
    """Validate conjunction of gte and lte to form a time range."""
    # From 10:00 to 12:00 inclusive
    response = client.get(
        "/posts",
        params={
            "f_incident_time__gte": "10:00:00",
            "f_incident_time__lte": "12:00:00",
        },
    )
    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {"Encounter in Chulak", "Medical supplies inventory"}


@pytest.mark.parametrize(
    ("value", "expected_status"),
    [
        ("10:00", 200),  # HH:MM is usually accepted by Pydantic
        ("10-00-00", 422),  # Dashes
        ("invalid-time", 422),
        ("25:00:00", 422),  # Invalid hour
    ],
)
def test_e2e_time_invalid_formats_return_422(
    client: TestClient, value: str, expected_status: int
) -> None:
    """Validate that non-ISO or logically invalid times return 422 (or 200 if valid HH:MM)."""
    response = client.get("/posts", params={"f_incident_time__eq": value})
    assert response.status_code == expected_status


@pytest.mark.parametrize(("value", "expected_count"), [("true", 0), ("false", 4)])
def test_e2e_time_isnull_standard_variants(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate standard true/false for isnull on time fields."""
    response = client.get("/posts", params={"f_incident_time__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(("value", "expected_count"), [("1", 0), ("0", 4)])
def test_e2e_time_isnull_numeric_truthiness(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate numeric 1/0 for isnull on time fields."""
    response = client.get("/posts", params={"f_incident_time__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("value", "expected_count"), [("yes", 0), ("no", 4), ("off", 4)]
)
def test_e2e_time_isnull_extended_truthiness(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate extended yes/no/on/off for isnull on time fields."""
    response = client.get("/posts", params={"f_incident_time__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("value", "expected_count"), [("y", 0), ("t", 0), ("n", 4), ("f", 4)]
)
def test_e2e_time_isnull_shorthands(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate shorthands y/n/t/f for isnull on time fields."""
    response = client.get("/posts", params={"f_incident_time__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


def test_e2e_time_disallowed_operator_returns_422(client: TestClient) -> None:
    """Time fields do not support string operators like icontains."""
    response = client.get("/posts", params={"f_incident_time__icontains": "10"})
    assert response.status_code == 422
