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
            "f_mission_start__gte",
            "1997-08-15T00:00:00Z",
            {"Medical supplies inventory", "Contact with Asgard (Classified/Deleted)"},
        ),
        (
            "f_created_at__lte",
            "1997-08-01T23:59:59Z",
            {"Mission to Abydos"},
        ),
        (
            "f_mission_start__gte",
            "1997-07-27T20:00:00",  # No timezone (naïve) - handled by Pydantic
            {
                "Mission to Abydos",
                "Encounter in Chulak",
                "Medical supplies inventory",
                "Contact with Asgard (Classified/Deleted)",
            },
        ),
    ],
)
def test_e2e_datetime_field_all_valid_operators(
    client: TestClient,
    field: str,
    value: str,
    expected_titles: set[str],
) -> None:
    """Validate all allowed datetime operators end-to-end."""
    response = client.get("/posts", params={field: value})

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == expected_titles


def test_e2e_datetime_field_combined_range(client: TestClient) -> None:
    """Validate conjunction of gte and lte to form a datetime range."""
    # Between Aug 1st and Aug 15th
    response = client.get(
        "/posts",
        params={
            "f_mission_start__gte": "1997-08-01T00:00:00Z",
            "f_mission_start__lte": "1997-08-15T23:59:59Z",
        },
    )
    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {"Encounter in Chulak", "Medical supplies inventory"}


@pytest.mark.parametrize(
    ("value", "expected_status"),
    [
        ("1997-07-27", 200),  # Date-only is often accepted as T00:00:00
        ("invalid-datetime", 422),
        ("2023-13-01T00:00:00", 422),  # Invalid month
    ],
)
def test_e2e_datetime_invalid_formats_return_422(
    client: TestClient, value: str, expected_status: int
) -> None:
    """Validate that invalid datetime formats return 422."""
    response = client.get("/posts", params={"f_mission_start__gte": value})
    assert response.status_code == expected_status


@pytest.mark.parametrize(("value", "expected_count"), [("true", 0), ("false", 4)])
def test_e2e_datetime_isnull_standard_variants(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate standard true/false for isnull on datetime fields."""
    response = client.get("/posts", params={"f_mission_start__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(("value", "expected_count"), [("1", 0), ("0", 4)])
def test_e2e_datetime_isnull_numeric_truthiness(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate numeric 1/0 for isnull on datetime fields."""
    response = client.get("/posts", params={"f_mission_start__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(("value", "expected_count"), [("yes", 0), ("no", 4)])
def test_e2e_datetime_isnull_extended_truthiness(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate extended yes/no for isnull on datetime fields."""
    response = client.get("/posts", params={"f_mission_start__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("value", "expected_count"), [("y", 0), ("t", 0), ("n", 4), ("f", 4)]
)
def test_e2e_datetime_isnull_shorthands(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate shorthands y/n/t/f for isnull on datetime fields."""
    response = client.get("/posts", params={"f_mission_start__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


def test_e2e_datetime_disallowed_operator_returns_422(client: TestClient) -> None:
    """Datetime fields do not support string operators like icontains."""
    response = client.get("/posts", params={"f_mission_start__icontains": "1997"})
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("value", "expected_count"),
    [
        ("true", 4),  # all posts have mission_start
        ("false", 0),
        ("1", 4),
        ("0", 0),
        ("yes", 4),
        ("no", 0),
        ("y", 4),
        ("n", 0),
    ],
)
def test_e2e_datetime_not_isnull_exhaustive(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate not_isnull operator for datetime fields with various boolean representations."""
    response = client.get("/posts", params={"f_mission_start__not_isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


def test_e2e_datetime_not_isnull_invalid_returns_422(client: TestClient) -> None:
    """Invalid boolean values for not_isnull yield 422."""
    response = client.get(
        "/posts", params={"f_mission_start__not_isnull": "not-a-bool"}
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("value", "expected_count", "expected_status"),
    [
        (
            "1997-07-01T00:00:00Z,1997-08-16T00:00:00Z",
            3,
            200,
        ),
        (
            "1997-09-01T00:00:00Z,1997-09-30T23:59:59Z",
            1,
            200,
        ),
        (
            "2000-01-01T00:00:00Z,2000-01-02T00:00:00Z",
            0,
            200,
        ),
        (
            "1997-07-01,1997-08-16",  # Date-only strings
            3,
            200,
        ),
        (
            "1997-07-01T20:00:00,1997-08-16T00:00:00",  # Naïve datetimes (no Z)
            3,
            200,
        ),
        (
            "1997-07-27 20:00:00,1997-08-15 09:00:00",  # Space separator
            3,
            200,
        ),
        (
            "1997-07-27T20:00:00+00:00,1997-08-01T10:30:00+00:00",  # Explicit offset
            2,
            200,
        ),
        (
            "1997-07-27T20:00:00.000Z,1997-07-27T20:00:00.999Z",  # Microseconds
            1,
            200,
        ),
        (
            "2023-01-01,1997-01-01",  # Inverted range (lower > upper) -> Should return 0
            0,
            200,
        ),
        # Invalid formats
        ("invalid-datetime,1997-08-01T00:00:00Z", 0, 422),
        ("1997-07-27T20:00:00Z,invalid-datetime", 0, 422),
        ("1997-13-01T00:00:00Z,1997-08-01T00:00:00Z", 0, 422),  # Invalid month
        ("1997-07-27T20:00:00Z", 0, 422),  # Single value
        (
            "1997-07-27T20:00:00Z,1997-08-01T00:00:00Z,1997-08-15T00:00:00Z",
            0,
            422,
        ),  # Three values
    ],
)
def test_e2e_datetime_between_exhaustive(
    client: TestClient,
    value: str,
    expected_count: int,
    expected_status: int,
) -> None:
    """Validate between operator for datetime fields with various valid and invalid ranges."""
    response = client.get("/posts", params={"f_mission_start__between": value})
    assert response.status_code == expected_status
    if expected_status == 200:
        assert len(response.json()) == expected_count
