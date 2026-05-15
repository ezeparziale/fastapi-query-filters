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
    """Response JSON may expose title via Field alias depending on serialization."""
    return str(item.get("post_title") or item.get("title"))


class PostOutNoPrefix(PostOut):
    class FilterConfig(PostOut.FilterConfig):
        prefix = ""


class PostOutNoPrefixNonStrict(PostOut):
    class FilterConfig(PostOut.FilterConfig):
        prefix = ""
        strict = False


@app.get("/posts", response_model=list[PostOut])
def list_posts(
    filters: FilterValues = FilterDep(PostOut),
    session: Session = Depends(get_db),
) -> Any:
    stmt = apply_filters(select(Post), Post, filters)
    return session.execute(stmt).scalars().all()


@app.get("/posts-no-prefix", response_model=list[PostOutNoPrefix])
def list_posts_no_prefix(
    filters: FilterValues = FilterDep(PostOutNoPrefix),
    session: Session = Depends(get_db),
) -> Any:
    stmt = apply_filters(select(Post), Post, filters)
    return session.execute(stmt).scalars().all()


@app.get("/posts-no-prefix-nonstrict", response_model=list[PostOutNoPrefixNonStrict])
def list_posts_no_prefix_nonstrict(
    filters: FilterValues = FilterDep(PostOutNoPrefixNonStrict),
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
    ("field", "value", "expected_count"),
    [
        ("f_is_active__eq", "true", 3),  # 3 active posts in seed
        ("f_is_active__eq", "false", 1),  # 1 inactive post (classified)
        ("f_is_active__ne", "true", 1),
        ("f_is_active__ne", "false", 3),
        ("f_is_active__isnull", "false", 4),  # none are null
        ("f_is_active__isnull", "true", 0),
    ],
)
def test_e2e_bool_field_all_valid_operators(
    client: TestClient,
    field: str,
    value: str,
    expected_count: int,
) -> None:
    """Validate all allowed boolean operators end-to-end."""
    response = client.get("/posts", params={field: value})

    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("value", "expected_count"),
    [
        ("true", 3),
        ("TRUE", 3),
        ("TrUe", 3),
        ("false", 1),
        ("FALSE", 1),
        ("FaLsE", 1),
    ],
)
def test_e2e_bool_standard_variants(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate standard true/false string representations (case-insensitive)."""
    response = client.get("/posts", params={"f_is_active__eq": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("value", "expected_count"),
    [
        ("1", 3),
        ("0", 1),
    ],
)
def test_e2e_bool_numeric_truthiness(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate numeric 1/0 representations for boolean fields."""
    response = client.get("/posts", params={"f_is_active__eq": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("value", "expected_count"),
    [
        ("yes", 3),
        ("YeS", 3),
        ("on", 3),
        ("ON", 3),
        ("no", 1),
        ("No", 1),
        ("off", 1),
        ("OfF", 1),
    ],
)
def test_e2e_bool_extended_truthiness(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate extended truthiness (yes/no, on/off) for boolean fields."""
    response = client.get("/posts", params={"f_is_active__eq": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("value", "expected_count"),
    [
        ("y", 3),
        ("t", 3),
        ("n", 1),
        ("f", 1),
    ],
)
def test_e2e_bool_shorthands(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Shorthands (y/n/t/f) are also accepted by Pydantic's default bool parsing."""
    response = client.get("/posts", params={"f_is_active__eq": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    "value",
    [
        "1.0",
        "1.1",
        "-1",
        "not-a-bool",
    ],
)
def test_e2e_bool_invalid_return_422(client: TestClient, value: str) -> None:
    """Ambiguous numbers or random strings are rejected for boolean parsing."""
    response = client.get("/posts", params={"f_is_active__eq": value})
    assert response.status_code == 422


def test_e2e_bool_redundant_filters(client: TestClient) -> None:
    """Multiple identical boolean filters should be handled gracefully (last value wins)."""
    response = client.get(
        "/posts",
        params=[("f_is_active__eq", "true"), ("f_is_active__eq", "true")],
    )
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_e2e_bool_contradictory_filters_use_last_value(client: TestClient) -> None:
    """Contradictory repeated single-value parameters take the last value in FastAPI."""
    response = client.get(
        "/posts",
        params=[("f_is_active__eq", "true"), ("f_is_active__eq", "false")],
    )
    assert response.status_code == 200
    assert len(response.json()) == 1  # Matches false


def test_e2e_bool_disallowed_operator_even_if_in_schema(client: TestClient) -> None:
    """Even if 'gte' is added to json_schema_extra, the core filters it out for booleans."""
    response = client.get("/posts", params={"f_is_active__gte": "true"})
    assert response.status_code == 422


def test_e2e_bool_nested_field(client: TestClient) -> None:
    """Validate filtering by a nested boolean field (author.is_alien)."""
    response = client.get("/posts", params={"f_author__is_alien__eq": "false"})
    assert response.status_code == 200
    assert len(response.json()) == 4

    response = client.get("/posts", params={"f_author__is_alien__eq": "true"})
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_e2e_bool_disallowed_operator_returns_422(client: TestClient) -> None:
    """Boolean fields do not support range or string operators."""
    response = client.get("/posts", params={"f_is_active__gt": "true"})
    assert response.status_code == 422

    response = client.get("/posts", params={"f_is_active__icontains": "t"})
    assert response.status_code == 422


def test_e2e_bool_combined_with_other_filters(client: TestClient) -> None:
    """Validate combining boolean filters with string/int filters."""
    response = client.get(
        "/posts",
        params={
            "f_is_active__eq": "true",
            "f_post_title__icontains": "Abydos",
        },
    )
    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {"Mission to Abydos"}


def test_e2e_bool_prefix_and_strict_variants(client: TestClient) -> None:
    """Validate prefix and strict mode behavior for boolean fields."""
    response = client.get("/posts-no-prefix", params={"is_active__eq": "true"})
    assert response.status_code == 200

    response = client.get("/posts-no-prefix", params={"f_is_active__eq": "true"})
    assert response.status_code == 422

    response = client.get(
        "/posts-no-prefix-nonstrict", params={"is_active__eq": "true", "foo": "bar"}
    )
    assert response.status_code == 200


@pytest.mark.parametrize(
    ("value", "expected_count"),
    [
        ("true", 4),  # all 4 are NOT NULL
        ("false", 0),  # all are NOT NULL, so none are NULL
        ("1", 4),
        ("0", 0),
        ("yes", 4),
        ("no", 0),
    ],
)
def test_e2e_bool_not_isnull_exhaustive(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate not_isnull operator for boolean fields with various truthy/falsy values."""
    response = client.get("/posts", params={"f_is_active__not_isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize("value", ["active", "1.1", "-1"])
def test_e2e_bool_not_isnull_invalid_returns_422(
    client: TestClient, value: str
) -> None:
    """Invalid values for not_isnull should return 422."""
    response = client.get("/posts", params={"f_is_active__not_isnull": value})
    assert response.status_code == 422
