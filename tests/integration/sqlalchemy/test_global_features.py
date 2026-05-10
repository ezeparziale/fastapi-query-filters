from typing import ClassVar, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterValues
from fastapi_query_filters.core import FilterConfig, create_filter_model
from fastapi_query_filters.orm.sqlalchemy import SQLAlchemyFilterAdapter, apply_filters
from tests.models import Post, User
from tests.schemas import PostOut, UserOut


def test_global_search(seeded_db: Session) -> None:
    """Test the global search functionality (q)."""
    FilterModel = create_filter_model(PostOut)
    # Search for 'Chulak' in title or content
    filters = FilterValues(FilterModel(q="Chulak"))

    stmt = select(Post)
    stmt = apply_filters(stmt, Post, filters)

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert "Encounter in Chulak" in results[0].title


class _NonStringSearchConfig:
    search_columns: ClassVar[list[str]] = ["age", "non_existent"]
    enable_search: ClassVar[bool] = True


class _NonStringSearchUserOut(UserOut):
    FilterConfig: ClassVar[type] = _NonStringSearchConfig


def test_search_on_non_string_column(seeded_db: Session) -> None:
    """Test that search works even on non-string fields like age."""
    FilterModel = create_filter_model(_NonStringSearchUserOut)
    filters = FilterValues(FilterModel(q="45"))  # Jack is 45
    stmt = select(User)
    stmt = apply_filters(stmt, User, filters)

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].name == "Jack O'Neill"


def test_sorting(seeded_db: Session) -> None:
    """Test dynamic sorting."""
    FilterModel = create_filter_model(PostOut)

    # Sort by post_title ascending:
    # Contact (C), Encounter (E), Medical (M), Mission (M)
    filters_asc = FilterValues(FilterModel(sort_by="post_title"))
    stmt_asc = apply_filters(select(Post), Post, filters_asc)
    results_asc = seeded_db.execute(stmt_asc).scalars().all()
    assert results_asc[0].title == "Contact with Asgard (Classified/Deleted)"

    # Sort by post_title descending
    filters_desc = FilterValues(FilterModel(sort_by="-post_title"))
    stmt_desc = apply_filters(select(Post), Post, filters_desc)
    results_desc = seeded_db.execute(stmt_desc).scalars().all()
    assert results_desc[0].title == "Mission to Abydos"


class _MultiSortFilterConfig:
    sort_columns: ClassVar[list[str]] = ["userId", "post_title", "id"]
    # inherit the rest of PostOut.FilterConfig attributes explicitly
    search_field: ClassVar[str] = "q"
    sort_field: ClassVar[str] = "sort_by"
    enable_sort: ClassVar[bool] = True
    enable_search: ClassVar[bool] = True
    max_depth: ClassVar[int] = 2
    strict: ClassVar[bool] = True
    search_columns: ClassVar[list[str]] = ["title", "description"]
    prefix: ClassVar[str] = "f_"


class _MultiSortPostOut(PostOut):
    FilterConfig: ClassVar[type] = _MultiSortFilterConfig  # type: ignore[assignment]


def test_apply_filters_multi_sort(seeded_db: Session) -> None:
    """Test dynamic sorting by multiple fields."""
    FilterModel = create_filter_model(_MultiSortPostOut)

    # Sort by userId (asc) and post_title (desc)
    # Jack (userId=1) has: "Mission to Abydos" and "Contact with Asgard (Classified/Deleted)"
    # Result for Jack: Mission (M), Contact (C)
    # Sam (userId=2) has: "Encounter in Chulak"
    # Janet (userId=4) has: "Medical supplies inventory"
    # Total result: Mission, Contact, Encounter, Medical
    filters = FilterValues(FilterModel(sort_by="userId,-post_title"))
    stmt = apply_filters(select(Post), Post, filters)
    results = seeded_db.execute(stmt).scalars().all()

    assert len(results) == 4
    assert results[0].title == "Mission to Abydos"
    assert results[1].title == "Contact with Asgard (Classified/Deleted)"
    assert results[2].title == "Encounter in Chulak"
    assert results[3].title == "Medical supplies inventory"


def test_apply_filters_unauthorized_sort(seeded_db: Session) -> None:
    """Verify that sorting by unauthorized fields (not in schema) is ignored."""
    FilterModel = create_filter_model(PostOut)

    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        FilterModel(sort_by="description")


class MockSearchConfig:
    search_columns: ClassVar[list[str]] = ["author"]
    enable_search: ClassVar[bool] = True
    search_field: ClassVar[str] = "q"


def test_search_column_no_type() -> None:
    """Verify that search columns without a 'type' attribute (like relationships) are skipped during global search."""
    adapter = SQLAlchemyFilterAdapter()
    stmt = adapter._apply_global_features(
        select(Post), Post, {"q": "test"}, cast(type[FilterConfig], MockSearchConfig)
    )
    assert "WHERE" not in str(stmt)
