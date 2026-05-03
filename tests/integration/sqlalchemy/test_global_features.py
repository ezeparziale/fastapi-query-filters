from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterValues
from fastapi_query_filters.core import (
    FilterConfig as FilterConfigBase,
)
from fastapi_query_filters.core import (
    create_filter_model,
)
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
    assert "Children of the Gods" in results[0].title


def test_search_on_non_string_column(seeded_db: Session) -> None:
    """Test that search works even on non-string fields like age."""

    class CustomUserOut(UserOut):
        class FilterConfig(FilterConfigBase):
            search_columns = ["age", "non_existent"]
            enable_search = True

    FilterModel = create_filter_model(CustomUserOut)
    filters = FilterValues(FilterModel(q="50"))  # Jack is 50
    stmt = select(User)
    stmt = apply_filters(stmt, User, filters)

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].name == "Jack O'Neill"


def test_sorting(seeded_db: Session) -> None:
    """Test dynamic sorting."""
    FilterModel = create_filter_model(PostOut)

    # Sort by title ascending: Children (C), The Fifth (T), Window (W)
    filters_asc = FilterValues(FilterModel(sort_by="title"))
    stmt_asc = apply_filters(select(Post), Post, filters_asc)
    results_asc = seeded_db.execute(stmt_asc).scalars().all()
    assert results_asc[0].title == "Children of the Gods"

    # Sort by title descending
    filters_desc = FilterValues(FilterModel(sort_by="-title"))
    stmt_desc = apply_filters(select(Post), Post, filters_desc)
    results_desc = seeded_db.execute(stmt_desc).scalars().all()
    assert results_desc[0].title == "Window of Opportunity"


def test_apply_filters_multi_sort(seeded_db: Session) -> None:
    """Test dynamic sorting by multiple fields."""
    FilterModel = create_filter_model(PostOut)

    # Sort by user_id (asc) and title (desc)
    # Jack (user_id=1) has: "Children of the Gods" and "Window of Opportunity"
    # Sam (user_id=2) has: "The Fifth Race"
    # Result should be: Window (Jack), Children (Jack), The Fifth Race (Sam)
    filters = FilterValues(FilterModel(sort_by="user_id,-title"))
    stmt = apply_filters(select(Post), Post, filters)
    results = seeded_db.execute(stmt).scalars().all()

    assert len(results) == 3
    assert results[0].title == "Window of Opportunity"
    assert results[1].title == "Children of the Gods"
    assert results[2].title == "The Fifth Race"


def test_search_column_no_type() -> None:
    """Verify that search columns without a 'type' attribute (like relationships) are skipped during global search."""

    class MockConfig(FilterConfigBase):
        search_columns = ["posts"]
        enable_search = True
        search_field = "q"

    adapter = SQLAlchemyFilterAdapter()
    stmt = adapter._apply_global_features(select(User), User, {"q": "test"}, MockConfig)
    assert "WHERE" not in str(stmt)
