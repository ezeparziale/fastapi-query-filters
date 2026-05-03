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


# Dummy DB dependency for the test app
def get_db() -> Session | None:
    # This will be overridden by the test
    return None


@app.get("/posts", response_model=list[dict[str, Any]])
def list_posts(
    filters: FilterValues = FilterDep(PostOut), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    stmt = select(Post)
    stmt = apply_filters(stmt, Post, filters)
    results = db.execute(stmt).scalars().all()

    # Simple manual serialization for testing
    return [
        {"id": p.id, "title": p.title, "author_email": p.author.email} for p in results
    ]


@pytest.fixture
def client(seeded_db: Session) -> Generator[TestClient, None, None]:
    # Override get_db to use our seeded test database
    app.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_fastapi_e2e_basic_filter(client: TestClient) -> None:
    """Test basic filtering via HTTP query parameters."""
    response = client.get("/posts?author__email__eq=oneill@example.com")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for item in data:
        assert item["author_email"] == "oneill@example.com"


def test_fastapi_e2e_global_search(client: TestClient) -> None:
    """Test global search functionality (q) via HTTP."""
    response = client.get("/posts?q=Chulak")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "Children of the Gods" in data[0]["title"]


def test_fastapi_e2e_multi_filter_and_sort(client: TestClient) -> None:
    """Test combining multiple filters and sorting via HTTP."""
    # Jack has 2 posts. Sort by title descending.
    response = client.get("/posts?author__email__eq=oneill@example.com&sort_by=-title")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Window of Opportunity"
    assert data[1]["title"] == "Children of the Gods"


def test_fastapi_e2e_invalid_param(client: TestClient) -> None:
    """Test that invalid query parameters (e.g. wrong type) return 422."""
    # id__eq expects int
    response = client.get("/posts?id__eq=not-an-int")
    assert response.status_code == 422

    # created_at__gte expects datetime
    response = client.get("/posts?created_at__gte=bad-date")
    assert response.status_code == 422
