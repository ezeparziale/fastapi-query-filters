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
            "f_mission_date__eq",
            "1997-07-27",
            {"Mission to Abydos"},
        ),
        (
            "f_mission_date__gte",
            "1997-08-15",
            {"Medical supplies inventory", "Contact with Asgard (Classified/Deleted)"},
        ),
        (
            "f_mission_date__lte",
            "1997-08-01",
            {"Mission to Abydos", "Encounter in Chulak"},
        ),
        (
            "f_mission_date__in",
            "1997-07-27,1997-09-26",
            {"Mission to Abydos", "Contact with Asgard (Classified/Deleted)"},
        ),
    ],
)
def test_e2e_date_field_all_valid_operators(
    client: TestClient,
    field: str,
    value: str,
    expected_titles: set[str],
) -> None:
    """Validate all allowed date operators end-to-end."""
    response = client.get("/posts", params={field: value})

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == expected_titles


def test_e2e_date_field_combined_range(client: TestClient) -> None:
    """Validate conjunction of gte and lte to form a date range."""
    # From Aug 1st to Aug 15th inclusive
    response = client.get(
        "/posts",
        params={
            "f_mission_date__gte": "1997-08-01",
            "f_mission_date__lte": "1997-08-15",
        },
    )
    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {"Encounter in Chulak", "Medical supplies inventory"}


@pytest.mark.parametrize(
    ("value", "expected_status"),
    [
        ("97-07-27", 422),  # Non-ISO
        ("1997/07/27", 422),  # Slashes
        ("invalid-date", 422),
        ("2023-02-30", 422),  # Invalid day
    ],
)
def test_e2e_date_invalid_formats_return_422(
    client: TestClient, value: str, expected_status: int
) -> None:
    """Validate that non-ISO or logically invalid dates return 422."""
    response = client.get("/posts", params={"f_mission_date__eq": value})
    assert response.status_code == expected_status


@pytest.mark.parametrize(("value", "expected_count"), [("true", 0), ("false", 4)])
def test_e2e_date_isnull_standard_variants(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate standard true/false for isnull on date fields."""
    # mission_date is NOT NULL for all posts in seed
    response = client.get("/posts", params={"f_mission_date__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(("value", "expected_count"), [("1", 0), ("0", 4)])
def test_e2e_date_isnull_numeric_truthiness(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate numeric 1/0 for isnull on date fields."""
    response = client.get("/posts", params={"f_mission_date__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("value", "expected_count"), [("yes", 0), ("no", 4), ("off", 4)]
)
def test_e2e_date_isnull_extended_truthiness(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate extended yes/no/on/off for isnull on date fields."""
    response = client.get("/posts", params={"f_mission_date__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("value", "expected_count"), [("y", 0), ("t", 0), ("n", 4), ("f", 4)]
)
def test_e2e_date_isnull_shorthands(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate shorthands y/n/t/f for isnull on date fields."""
    response = client.get("/posts", params={"f_mission_date__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


def test_e2e_date_disallowed_operator_returns_422(client: TestClient) -> None:
    """Date fields do not support string operators like icontains."""
    response = client.get("/posts", params={"f_mission_date__icontains": "1997"})
    assert response.status_code == 422
