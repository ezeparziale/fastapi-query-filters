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
    ("field", "value", "expected_titles"),
    [
        (
            "f_post_title__eq",
            "Mission to Abydos",
            {"Mission to Abydos"},
        ),
        (
            "f_post_title__icontains",
            "mIssIoN",
            {"Mission to Abydos"},
        ),
        (
            "f_post_title__icontains",
            "(Classified/Deleted)",
            {"Contact with Asgard (Classified/Deleted)"},
        ),
        (
            "f_author__rank__in",
            "Colonel,Major",
            {
                "Mission to Abydos",
                "Contact with Asgard (Classified/Deleted)",
                "Encounter in Chulak",
            },
        ),
        (
            "f_author__rank__not_in",
            "Colonel,Major",
            {"Medical supplies inventory"},
        ),
        (
            "f_post_title__startswith",
            "Mission",
            {"Mission to Abydos"},
        ),
        (
            "f_post_title__istartswith",
            "mission",
            {"Mission to Abydos"},
        ),
        (
            "f_post_title__endswith",
            "Abydos",
            {"Mission to Abydos"},
        ),
        (
            "f_post_title__iendswith",
            "abydos",
            {"Mission to Abydos"},
        ),
        (
            "f_post_title__contains",
            "Abydos",
            {"Mission to Abydos"},
        ),
    ],
)
def test_e2e_str_field_all_valid_operators(
    client: TestClient,
    field: str,
    value: str,
    expected_titles: set[str],
) -> None:
    """Validate all allowed string operators end-to-end."""
    response = client.get("/posts", params={field: value})

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == expected_titles


def test_e2e_str_field_combined_filters_on_same_field(client: TestClient) -> None:
    """Validate conjunction of two string filters on the same field."""
    # post_title that contains "mission" AND contains "abydos"
    response = client.get(
        "/posts",
        params={
            "f_post_title__icontains": "mission",
            "f_post_title__eq": "Mission to Abydos",
        },
    )

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {"Mission to Abydos"}


def test_e2e_str_field_combined_with_nested_str_field(client: TestClient) -> None:
    """Validate combining top-level str filters with nested str filters."""
    response = client.get(
        "/posts",
        params={
            "f_post_title__icontains": "inventory",
            "f_author__rank__eq": "Doctor",
        },
    )

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {"Medical supplies inventory"}


def test_e2e_prefix_disabled_accepts_unprefixed_str_filter(client: TestClient) -> None:
    """When prefix is disabled, unprefixed str filters are accepted."""
    response = client.get(
        "/posts-no-prefix", params={"post_title__eq": "Encounter in Chulak"}
    )

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {"Encounter in Chulak"}


def test_e2e_prefix_disabled_rejects_prefixed_str_filter(client: TestClient) -> None:
    """When prefix is disabled in strict mode, prefixed keys are rejected."""
    response = client.get(
        "/posts-no-prefix", params={"f_post_title__eq": "Encounter in Chulak"}
    )

    assert response.status_code == 422


def test_e2e_unknown_filter_ignored_when_non_strict(client: TestClient) -> None:
    """Unknown filter keys are ignored when strict mode is disabled."""
    response = client.get(
        "/posts-no-prefix-nonstrict",
        params={"post_title__eq": "Encounter in Chulak", "unknown__eq": "foo"},
    )

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {"Encounter in Chulak"}


def test_e2e_strict_unknown_key_with_valid_filter_returns_422(
    client: TestClient,
) -> None:
    """With strict=True, an extra query param invalidates the request entirely."""
    response = client.get(
        "/posts",
        params={
            "f_post_title__eq": "Encounter in Chulak",
            "f_totally_fake__eq": "1",
        },
    )

    assert response.status_code == 422


def test_e2e_str_disallowed_operator_returns_422(client: TestClient) -> None:
    """Operators not declared on string fields yield validation errors."""
    # title allows eq, icontains but NOT in or gt
    response = client.get("/posts", params={"f_post_title__in": "A,B"})
    assert response.status_code == 422

    # id allows eq, in, etc but NOT icontains
    response = client.get("/posts", params={"f_id__icontains": "1"})
    assert response.status_code == 422


def test_e2e_str_in_repeated_query_params(client: TestClient) -> None:
    """Repeated string __in keys are aggregated like a logical list."""
    response = client.get(
        "/posts-no-prefix",
        params=[("author__rank__in", "Colonel"), ("author__rank__in", "Doctor")],
    )

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {
        "Mission to Abydos",
        "Contact with Asgard (Classified/Deleted)",
        "Medical supplies inventory",
    }


def test_e2e_str_not_in_repeated_query_params(client: TestClient) -> None:
    """Repeated string __not_in keys combine into one exclusion list."""
    response = client.get(
        "/posts-no-prefix",
        params=[("author__rank__not_in", "Colonel"), ("author__rank__not_in", "Major")],
    )

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {"Medical supplies inventory"}


@pytest.mark.parametrize(
    ("raw_value", "expected_status", "expected_count"),
    [
        ("", 200, 4),  # ranks are not "", so all 4 posts are returned
    ],
)
def test_e2e_str_not_in_invalid_values(
    client: TestClient, raw_value: str, expected_status: int, expected_count: int
) -> None:
    """Empty strings are valid for string not_in."""
    response = client.get(
        "/posts-no-prefix", params={"author__rank__not_in": raw_value}
    )

    assert response.status_code == expected_status
    if expected_status == 200:
        assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("raw_value", "expected_status", "expected_count"),
    [
        ("Mission to Abydos", 200, 1),
        (" Mission to Abydos ", 200, 0),  # Spaces are NOT stripped by default for eq
        ("mission to abydos", 200, 0),  # eq is case sensitive
        ("", 200, 0),
    ],
)
def test_e2e_str_eq_random_value_variants(
    client: TestClient,
    raw_value: str,
    expected_status: int,
    expected_count: int | None,
) -> None:
    """Validate random/edge string representations for the eq operator."""
    response = client.get("/posts-no-prefix", params={"post_title__eq": raw_value})

    assert response.status_code == expected_status
    if expected_count is not None:
        assert len(response.json()) == expected_count


def test_e2e_str_icontains_random_value_variants(client: TestClient) -> None:
    """Validate icontains with mixed case and whitespace."""
    # "mIssIoN" matches "Mission to Abydos" (case-insensitive)
    response = client.get("/posts", params={"f_post_title__icontains": "mIssIoN"})
    assert response.status_code == 200
    assert len(response.json()) == 1

    # " mIssIoN " with spaces should NOT match unless the title has those spaces
    response = client.get("/posts", params={"f_post_title__icontains": " mIssIoN "})
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.parametrize(
    ("raw_value", "expected_status", "expected_titles"),
    [
        (
            "Colonel,Doctor",
            200,
            {
                "Mission to Abydos",
                "Contact with Asgard (Classified/Deleted)",
                "Medical supplies inventory",
            },
        ),
        (
            " Colonel , Doctor ",
            200,
            {
                "Mission to Abydos",
                "Contact with Asgard (Classified/Deleted)",
                "Medical supplies inventory",
            },
        ),
        ("Unknown", 200, set()),
        ("", 200, set()),
        (
            "Colonel,,Doctor",
            200,
            {
                "Mission to Abydos",
                "Contact with Asgard (Classified/Deleted)",
                "Medical supplies inventory",
            },
        ),  # Empty string in list is ok, though might not match anything
    ],
)
def test_e2e_str_in_random_value_variants(
    client: TestClient,
    raw_value: str,
    expected_status: int,
    expected_titles: set[str] | None,
) -> None:
    """Validate random/edge string representations for the in operator (strips whitespace)."""
    response = client.get("/posts-no-prefix", params={"author__rank__in": raw_value})

    assert response.status_code == expected_status
    if expected_titles is not None:
        got_titles = {_post_title(item) for item in response.json()}
        assert got_titles == expected_titles


@pytest.mark.parametrize(
    ("value", "expected_count"),
    [("true", 1), ("TRUE", 1), ("TrUe", 1), ("false", 3), ("FALSE", 3)],
)
def test_e2e_str_isnull_standard_variants(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate standard true/false for isnull on string fields."""
    response = client.get("/posts", params={"f_gate_address__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(("value", "expected_count"), [("1", 1), ("0", 3)])
def test_e2e_str_isnull_numeric_truthiness(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate numeric 1/0 for isnull on string fields."""
    response = client.get("/posts", params={"f_gate_address__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("value", "expected_count"),
    [("yes", 1), ("YeS", 1), ("on", 1), ("no", 3), ("No", 3), ("off", 3)],
)
def test_e2e_str_isnull_extended_truthiness(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate extended yes/no/on/off for isnull on string fields."""
    response = client.get("/posts", params={"f_gate_address__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    ("value", "expected_count"), [("y", 1), ("t", 1), ("n", 3), ("f", 3)]
)
def test_e2e_str_isnull_shorthands(
    client: TestClient, value: str, expected_count: int
) -> None:
    """Validate shorthands y/n/t/f for isnull on string fields."""
    response = client.get("/posts", params={"f_gate_address__isnull": value})
    assert response.status_code == 200
    assert len(response.json()) == expected_count


def test_e2e_str_isnull_invalid_value(client: TestClient) -> None:
    """Invalid boolean values for isnull yield 422."""
    response = client.get("/posts", params={"f_gate_address__isnull": "not-a-bool"})
    assert response.status_code == 422


def test_e2e_str_icontains_multi_word(client: TestClient) -> None:
    """Validate icontains with multiple words and internal spaces."""
    response = client.get("/posts", params={"f_post_title__icontains": "to Abydos"})
    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {"Mission to Abydos"}


def test_e2e_str_eq_empty_string(client: TestClient) -> None:
    """An empty string filter for eq should match only actually empty columns (0 results in seed)."""
    response = client.get("/posts-no-prefix", params={"post_title__eq": ""})
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_e2e_str_sql_escaping_apostrophe(client: TestClient) -> None:
    """Validate that single quotes (apostrophes) are escaped correctly and don't break the query."""
    # Jack O'Neill's bio contains "O'Neill"
    response = client.get(
        "/posts", params={"f_author__profile_bio__icontains": "O'Neill"}
    )
    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {
        "Mission to Abydos",
        "Contact with Asgard (Classified/Deleted)",
    }


def test_e2e_str_regex_validation_ignored(client: TestClient) -> None:
    """gate_address has a regex pattern, but filters don't enforce it strictly (currently)."""
    # Valid is like P8X-412
    response = client.get("/posts", params={"f_gate_address__eq": "INVALID-GATE"})
    assert response.status_code == 200
    assert len(response.json()) == 0

    response = client.get("/posts", params={"f_gate_address__eq": "P8X-412"})
    assert response.status_code == 200
    assert len(response.json()) == 1
