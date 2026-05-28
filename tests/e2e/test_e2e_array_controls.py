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
        ("f_tags__arr_contains", "desert", {"Mission to Abydos"}),
        (
            "f_tags__arr_overlap",
            "medical,jaffa",
            {"Encounter in Chulak", "Medical supplies inventory"},
        ),
        ("f_tags__arr_all", "exploration,desert", {"Mission to Abydos"}),
        ("f_tags__arr_any", "medical,unknown", {"Medical supplies inventory"}),
        ("f_tags__arr_len", "0", {"Contact with Asgard (Classified/Deleted)"}),
        ("f_tags__is_empty", "true", {"Contact with Asgard (Classified/Deleted)"}),
        ("f_tags__is_blank", "true", {"Contact with Asgard (Classified/Deleted)"}),
        (
            "f_tags__isnull",
            "false",
            {
                "Mission to Abydos",
                "Encounter in Chulak",
                "Medical supplies inventory",
                "Contact with Asgard (Classified/Deleted)",
            },
        ),
        (
            "f_tags__not_isnull",
            "true",
            {
                "Mission to Abydos",
                "Encounter in Chulak",
                "Medical supplies inventory",
                "Contact with Asgard (Classified/Deleted)",
            },
        ),
    ],
)
def test_e2e_array_field_all_valid_operators(
    client: TestClient,
    field: str,
    value: str,
    expected_titles: set[str],
) -> None:
    """Validate all allowed array operators end-to-end."""
    response = client.get("/posts", params={field: value})

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == expected_titles


def test_e2e_array_field_combined_filters(client: TestClient) -> None:
    """Validate conjunction of array filters on the same field."""
    response = client.get(
        "/posts",
        params={
            "f_tags__arr_overlap": "desert,goauld",
            "f_tags__arr_len": "3",
        },
    )

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {"Mission to Abydos"}


def test_e2e_array_prefix_disabled_accepts_unprefixed_filter(
    client: TestClient,
) -> None:
    """When prefix is disabled, unprefixed array filters are accepted."""
    response = client.get("/posts-no-prefix", params={"tags__arr_contains": "desert"})

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {"Mission to Abydos"}


def test_e2e_array_prefix_disabled_rejects_prefixed_filter(client: TestClient) -> None:
    """When prefix is disabled in strict mode, prefixed keys are rejected."""
    response = client.get("/posts-no-prefix", params={"f_tags__arr_contains": "desert"})

    assert response.status_code == 422


def test_e2e_array_unknown_filter_ignored_when_non_strict(
    client: TestClient,
) -> None:
    """Unknown filter keys are ignored when strict mode is disabled."""
    response = client.get(
        "/posts-no-prefix-nonstrict",
        params={"tags__arr_contains": "desert", "unknown__eq": "foo"},
    )

    assert response.status_code == 200
    got_titles = {_post_title(item) for item in response.json()}
    assert got_titles == {"Mission to Abydos"}


def test_e2e_array_disallowed_operator_returns_422(client: TestClient) -> None:
    """Operators not declared on array fields yield validation errors."""
    response = client.get("/posts", params={"f_tags__contains": "desert"})
    assert response.status_code == 422

    response = client.get("/posts", params={"f_tags__between": "a,b"})
    assert response.status_code == 422
