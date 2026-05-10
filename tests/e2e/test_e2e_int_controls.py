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


def _first_post_id(db: Session) -> int:
    first_id = db.execute(select(Post.id).order_by(Post.id)).scalars().first()
    assert first_id is not None
    return first_id


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
    ("field", "value_builder", "expected_builder"),
    [
        (
            "f_id__eq",
            lambda ids: str(ids[0]),
            lambda ids: {ids[0]},
        ),
        (
            "f_id__gte",
            lambda ids: str(ids[1]),
            lambda ids: {i for i in ids if i >= ids[1]},
        ),
        (
            "f_id__lte",
            lambda ids: str(ids[1]),
            lambda ids: {i for i in ids if i <= ids[1]},
        ),
        (
            "f_id__in",
            lambda ids: f"{ids[0]},{ids[-1]}",
            lambda ids: {ids[0], ids[-1]},
        ),
        (
            "f_id__not_in",
            lambda ids: f"{ids[0]},{ids[-1]}",
            lambda ids: set(ids) - {ids[0], ids[-1]},
        ),
    ],
)
def test_e2e_int_field_all_valid_operators(
    seeded_db: Session,
    client: TestClient,
    field: str,
    value_builder: Any,
    expected_builder: Any,
) -> None:
    """Validate all allowed integer operators for PostOut.id end-to-end."""
    ids = [row[0] for row in seeded_db.execute(select(Post.id).order_by(Post.id)).all()]
    response = client.get("/posts", params={field: value_builder(ids)})

    assert response.status_code == 200
    got_ids = {item["id"] for item in response.json()}
    assert got_ids == expected_builder(ids)


def test_e2e_int_field_combined_filters_on_same_field(
    seeded_db: Session, client: TestClient
) -> None:
    """Validate conjunction of two integer filters on the same field."""
    ids = [row[0] for row in seeded_db.execute(select(Post.id).order_by(Post.id)).all()]
    target = ids[1]
    response = client.get(
        "/posts",
        params={
            "f_id__eq": str(target),
            "f_id__gte": str(target),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == target


def test_e2e_int_field_combined_with_nested_int_field(
    seeded_db: Session, client: TestClient
) -> None:
    """Validate combining top-level int filters with nested int filters."""
    ids = [row[0] for row in seeded_db.execute(select(Post.id).order_by(Post.id)).all()]
    response = client.get(
        "/posts",
        params={
            "f_id__in": ",".join(str(i) for i in ids),
            "f_author__age__gte": "40",
        },
    )

    assert response.status_code == 200
    got_ids = {item["id"] for item in response.json()}
    # In seeded data, only Jack's posts have author age >= 40.
    assert got_ids == {ids[0], ids[-1]}


def test_e2e_prefix_disabled_accepts_unprefixed_int_filter(
    seeded_db: Session, client: TestClient
) -> None:
    """When prefix is disabled, unprefixed integer filters are accepted."""
    first_id = _first_post_id(seeded_db)
    response = client.get("/posts-no-prefix", params={"id__eq": str(first_id)})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == first_id


def test_e2e_prefix_disabled_rejects_prefixed_int_filter(
    seeded_db: Session, client: TestClient
) -> None:
    """When prefix is disabled in strict mode, prefixed keys are rejected."""
    first_id = _first_post_id(seeded_db)
    response = client.get("/posts-no-prefix", params={"f_id__eq": str(first_id)})

    assert response.status_code == 422


def test_e2e_unknown_filter_ignored_when_non_strict(
    seeded_db: Session, client: TestClient
) -> None:
    """Unknown filter keys are ignored when strict mode is disabled."""
    first_id = _first_post_id(seeded_db)
    response = client.get(
        "/posts-no-prefix-nonstrict",
        params={"id__eq": str(first_id), "unknown__eq": "foo"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == first_id


def test_e2e_int_id_range_gte_and_lte(seeded_db: Session, client: TestClient) -> None:
    """Constrain rows to an inclusive id range using gte and lte together."""
    ids = [row[0] for row in seeded_db.execute(select(Post.id).order_by(Post.id)).all()]
    lo, hi = ids[1], ids[2]
    response = client.get("/posts", params={"f_id__gte": str(lo), "f_id__lte": str(hi)})

    assert response.status_code == 200
    got_ids = {item["id"] for item in response.json()}
    assert got_ids == {i for i in ids if lo <= i <= hi}


def test_e2e_int_author_age_gte_lte_range(client: TestClient) -> None:
    """Nested author.age supports inclusive range with gte and lte."""
    response = client.get(
        "/posts",
        params={
            "f_author__age__gte": "35",
            "f_author__age__lte": "40",
        },
    )

    assert response.status_code == 200
    titles = {_post_title(item) for item in response.json()}
    assert titles == {"Encounter in Chulak", "Medical supplies inventory"}


def test_e2e_int_author_age_gt_lt_range(client: TestClient) -> None:
    """Author age accepts gt and lt via PostFilterExtra (virtual f_author__age)."""
    # Seed: Samantha Carter age 35 (post Encounter in Chulak), Janet Fraiser 38 (medical).
    # Strictly between 34 and 41 matches both; Teal'c has no posts, Jack/Janet edge cases excluded.
    response = client.get(
        "/posts",
        params={
            "f_author__age__gt": "34",
            "f_author__age__lt": "41",
        },
    )

    assert response.status_code == 200
    titles = {_post_title(item) for item in response.json()}
    assert titles == {"Encounter in Chulak", "Medical supplies inventory"}


def test_e2e_int_disallowed_operator_on_id_returns_422(client: TestClient) -> None:
    """Operators not declared on id (no gt / lt on PostOut.id) yield validation errors."""
    response = client.get("/posts", params={"f_id__gt": "1"})
    assert response.status_code == 422

    response = client.get("/posts", params={"f_id__lt": "999"})
    assert response.status_code == 422


def test_e2e_strict_unknown_key_with_valid_filter_returns_422(
    seeded_db: Session, client: TestClient
) -> None:
    """With strict=True, an extra query param invalidates the request entirely."""
    first_id = _first_post_id(seeded_db)
    response = client.get(
        "/posts",
        params={
            "f_id__eq": str(first_id),
            "f_totally_fake__eq": "1",
        },
    )

    assert response.status_code == 422


def test_e2e_int_not_in_excludes_known_ids(
    seeded_db: Session, client: TestClient
) -> None:
    """not_in rejects a comma-separated exclusion list mapped to seeded ids."""
    ids = [row[0] for row in seeded_db.execute(select(Post.id).order_by(Post.id)).all()]
    a, b = ids[0], ids[-1]
    response = client.get("/posts-no-prefix", params={"id__not_in": f"{a},{b}"})

    assert response.status_code == 200
    got_ids = {item["id"] for item in response.json()}
    assert got_ids == set(ids) - {a, b}


@pytest.mark.parametrize(
    ("raw_value", "expected_status"),
    [
        ("1.1,2", 422),
        ("a,2", 422),
        ("", 422),
    ],
)
def test_e2e_int_not_in_invalid_values(
    client: TestClient, raw_value: str, expected_status: int
) -> None:
    """Invalid tokens for integer not_in return 422."""
    response = client.get("/posts-no-prefix", params={"id__not_in": raw_value})

    assert response.status_code == expected_status


def test_e2e_int_in_repeated_query_params(client: TestClient) -> None:
    """Repeated id__in keys are aggregated like a logical list."""
    response = client.get(
        "/posts-no-prefix",
        params=[("id__in", "1"), ("id__in", "2"), ("id__in", "3")],
    )

    assert response.status_code == 200
    got_ids = {item["id"] for item in response.json()}
    assert got_ids == {1, 2, 3}


def test_e2e_int_not_in_repeated_query_params(
    seeded_db: Session, client: TestClient
) -> None:
    """Repeated id__not_in keys combine into one exclusion list."""
    ids = [row[0] for row in seeded_db.execute(select(Post.id).order_by(Post.id)).all()]
    a, b = ids[0], ids[1]
    response = client.get(
        "/posts-no-prefix",
        params=[("id__not_in", str(a)), ("id__not_in", str(b))],
    )

    assert response.status_code == 200
    got_ids = {item["id"] for item in response.json()}
    assert got_ids == set(ids) - {a, b}


@pytest.mark.parametrize(
    ("raw_value", "expected_status", "expected_count"),
    [
        ("-1", 200, 0),
        ("0", 200, 0),
        ("1", 200, 1),
        ("+1", 200, 1),
        (" 1 ", 200, 1),
        ("001", 200, 1),
        ("1.0", 200, 1),
        ("1.1", 422, None),
        ("a", 422, None),
        ("0,1", 422, None),
        ('"1"', 422, None),
    ],
)
def test_e2e_int_eq_random_value_variants(
    client: TestClient,
    raw_value: str,
    expected_status: int,
    expected_count: int | None,
) -> None:
    """Validate random/edge integer representations for the eq operator."""
    response = client.get("/posts-no-prefix", params={"id__eq": raw_value})

    assert response.status_code == expected_status
    if expected_count is not None:
        assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("raw_value", "expected_status", "expected_ids"),
    [
        ("1,2,3", 200, {1, 2, 3}),
        (" 1 , 2 , 3 ", 200, {1, 2, 3}),
        ("-1,0,1", 200, {1}),
        ("1.0,2", 200, {1, 2}),
        ("1.1,2", 422, None),
        ("a,2", 422, None),
        ('"1,2,3"', 422, None),
        ("1,,,,", 422, None),
        ("", 422, None),
    ],
)
def test_e2e_int_in_random_value_variants(
    client: TestClient,
    raw_value: str,
    expected_status: int,
    expected_ids: set[int] | None,
) -> None:
    """Validate random/edge integer representations for the in operator."""
    response = client.get("/posts-no-prefix", params={"id__in": raw_value})

    assert response.status_code == expected_status
    if expected_ids is not None:
        got_ids = {item["id"] for item in response.json()}
        assert got_ids == expected_ids


@pytest.mark.parametrize(
    ("value", "expected_count"),
    [("true", 1), ("TRUE", 1), ("TrUe", 1), ("false", 3), ("FALSE", 3)],
)
def test_e2e_int_isnull_standard_variants(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate standard true/false for isnull on integer fields."""
    response = client.get("/posts", params={"f_casualties__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(("value", "expected_count"), [("1", 1), ("0", 3)])
def test_e2e_int_isnull_numeric_truthiness(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate numeric 1/0 for isnull on integer fields."""
    response = client.get("/posts", params={"f_casualties__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("value", "expected_count"),
    [("yes", 1), ("YeS", 1), ("on", 1), ("no", 3), ("No", 3), ("off", 3)],
)
def test_e2e_int_isnull_extended_truthiness(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate extended yes/no/on/off for isnull on integer fields."""
    response = client.get("/posts", params={"f_casualties__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("value", "expected_count"), [("y", 1), ("t", 1), ("n", 3), ("f", 3)]
)
def test_e2e_int_isnull_shorthands(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate shorthands y/n/t/f for isnull on integer fields."""
    # casualties is null for 'Medical supplies inventory' (1 result)
    response = client.get("/posts", params={"f_casualties__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


def test_e2e_int_isnull_invalid_value(client: TestClient) -> None:
    """Invalid boolean values for isnull yield 422."""
    response = client.get("/posts", params={"f_casualties__isnull": "not-a-bool"})
    assert response.status_code == 422


def test_e2e_int_author_age_not_in_nested(client: TestClient) -> None:
    """author__age__not_in excludes posts from authors with the given ages (nested, e2e DB check)."""
    response = client.get("/posts", params={"f_author__age__not_in": "45"})
    assert response.status_code == 200
    titles = {_post_title(item) for item in response.json()}
    # Jack (age 45) has 2 posts — both excluded; Sam and Janet remain
    assert titles == {"Encounter in Chulak", "Medical supplies inventory"}
