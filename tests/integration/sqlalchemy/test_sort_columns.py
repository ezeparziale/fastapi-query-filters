import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterValues
from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.orm.sqlalchemy import apply_filters
from tests.models import Post
from tests.schemas import PostOut


def test_explicit_sort_columns(seeded_db: Session) -> None:
    class RestrictedPostOut(PostOut):
        class FilterConfig(PostOut.FilterConfig):
            # Only allow sorting by 'id'
            sort_columns = ["id"]

    FilterModel = create_filter_model(RestrictedPostOut)

    # Try sorting by 'title' (should be ignored)
    filters = FilterValues(FilterModel(sort_by="title"))
    stmt = apply_filters(select(Post), Post, filters)
    sql = str(stmt.compile(bind=seeded_db.get_bind()))
    assert "ORDER BY" not in sql

    # Try sorting by 'id' (should work)
    filters = FilterValues(FilterModel(sort_by="id"))
    stmt = apply_filters(select(Post), Post, filters)
    sql = str(stmt.compile(bind=seeded_db.get_bind()))
    assert "ORDER BY posts.id ASC" in sql


def test_default_sort_columns(seeded_db: Session) -> None:
    # Default behavior: all schema fields are sortable
    FilterModel = create_filter_model(PostOut)

    # title should be sortable
    filters = FilterValues(FilterModel(sort_by="title"))
    stmt = apply_filters(select(Post), Post, filters)
    sql = str(stmt.compile(bind=seeded_db.get_bind()))
    assert "ORDER BY posts.title ASC" in sql


def test_strict_sort_rejects_unknown_field(seeded_db: Session) -> None:
    """With strict=True, sorting by a field not in sort_columns raises ValueError."""

    class StrictPostOut(PostOut):
        class FilterConfig(PostOut.FilterConfig):
            strict = True
            sort_columns = ["id", "created_at"]

    FilterModel = create_filter_model(StrictPostOut)

    with pytest.raises(ValueError, match="Sort field 'title' is not allowed"):
        FilterModel(sort_by="title")


def test_strict_sort_rejects_nested_field_not_in_sort_columns(
    seeded_db: Session,
) -> None:
    """With strict=True, sorting by a nested field not in sort_columns raises ValueError."""

    class StrictPostOut(PostOut):
        class FilterConfig(PostOut.FilterConfig):
            strict = True
            sort_columns = ["id", "author__name"]

    FilterModel = create_filter_model(StrictPostOut)

    with pytest.raises(
        ValueError, match="Sort field 'author__team__name' is not allowed"
    ):
        FilterModel(sort_by="author__team__name")


def test_strict_sort_accepts_valid_field(seeded_db: Session) -> None:
    """With strict=True, sorting by a field in sort_columns works normally."""

    class StrictPostOut(PostOut):
        class FilterConfig(PostOut.FilterConfig):
            strict = True
            sort_columns = ["id", "created_at"]

    FilterModel = create_filter_model(StrictPostOut)

    # Should not raise
    filters = FilterValues(FilterModel(sort_by="created_at"))
    stmt = apply_filters(select(Post), Post, filters)
    sql = str(stmt.compile(bind=seeded_db.get_bind()))
    assert "ORDER BY posts.created_at ASC" in sql


def test_strict_sort_accepts_descending_prefix(seeded_db: Session) -> None:
    """With strict=True, the '-' prefix for descending order is handled correctly."""

    class StrictPostOut(PostOut):
        class FilterConfig(PostOut.FilterConfig):
            strict = True
            sort_columns = ["id", "created_at"]

    FilterModel = create_filter_model(StrictPostOut)

    # '-created_at' should strip the '-' and validate 'created_at' → valid
    filters = FilterValues(FilterModel(sort_by="-created_at"))
    stmt = apply_filters(select(Post), Post, filters)
    sql = str(stmt.compile(bind=seeded_db.get_bind()))
    assert "ORDER BY posts.created_at DESC" in sql


def test_strict_sort_rejects_descending_unknown_field(seeded_db: Session) -> None:
    """With strict=True, '-field' with an unknown field still raises ValueError."""

    class StrictPostOut(PostOut):
        class FilterConfig(PostOut.FilterConfig):
            strict = True
            sort_columns = ["id", "created_at"]

    FilterModel = create_filter_model(StrictPostOut)

    with pytest.raises(ValueError, match="Sort field 'title' is not allowed"):
        FilterModel(sort_by="-title")


def test_strict_sort_rejects_mixed_valid_invalid(seeded_db: Session) -> None:
    """With strict=True, a comma-separated sort with one invalid field raises ValueError."""

    class StrictPostOut(PostOut):
        class FilterConfig(PostOut.FilterConfig):
            strict = True
            sort_columns = ["id", "created_at"]

    FilterModel = create_filter_model(StrictPostOut)

    # 'id' is valid but 'title' is not — should still raise
    with pytest.raises(ValueError, match="Sort field 'title' is not allowed"):
        FilterModel(sort_by="id,title")


def test_non_strict_sort_ignores_unknown_field(seeded_db: Session) -> None:
    """Without strict=True, sorting by a field not in sort_columns is silently ignored."""

    class NonStrictPostOut(PostOut):
        class FilterConfig(PostOut.FilterConfig):
            strict = False
            sort_columns = ["id"]

    FilterModel = create_filter_model(NonStrictPostOut)

    # 'title' is not in sort_columns but strict=False → no error, no ORDER BY
    filters = FilterValues(FilterModel(sort_by="title"))
    stmt = apply_filters(select(Post), Post, filters)
    sql = str(stmt.compile(bind=seeded_db.get_bind()))
    assert "ORDER BY" not in sql
