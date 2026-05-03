from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterValues
from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.orm.sqlalchemy import SQLAlchemyFilterAdapter, apply_filters
from tests.models import Post, User
from tests.schemas import PostOut, UserOut


def test_automatic_join_one_level(seeded_db: Session) -> None:
    """Test that filtering by a nested field automatically joins the related table."""
    FilterModel = create_filter_model(PostOut)
    # Filter posts by author email
    filters = FilterValues(FilterModel(author__email__eq="oneill@example.com"))

    stmt = select(Post)
    stmt = apply_filters(stmt, Post, filters)

    # Check the SQL string to verify join exists
    sql = str(stmt.compile(seeded_db.bind))
    assert "JOIN users" in sql

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 2  # Jack has 2 posts
    for r in results:
        assert r.author.email == "oneill@example.com"


def test_automatic_join_with_extra_filter(seeded_db: Session) -> None:
    """Test that nested joins work even for fields defined in extra_filters."""
    FilterModel = create_filter_model(PostOut)
    # Filter posts by author age (age is in UserFilterExtra)
    # Carter is 35, O'Neill is 50.
    filters = FilterValues(FilterModel(author__age__lt=40))

    stmt = select(Post)
    stmt = apply_filters(stmt, Post, filters)

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1  # Only Sam's post
    assert results[0].author.name == "Samantha Carter"


def test_multiple_joins_avoid_duplicates(seeded_db: Session) -> None:
    """Test that multiple filters on the same relation only result in one JOIN."""
    FilterModel = create_filter_model(PostOut)
    filters = FilterValues(
        FilterModel(author__email__icontains="example.com", author__is_active__eq=True)
    )

    stmt = select(Post)
    stmt = apply_filters(stmt, Post, filters)

    # Verify SQL only has ONE join for users
    sql = str(stmt.compile(seeded_db.bind))
    assert sql.count("JOIN users") == 1

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 3  # Jack (2) and Sam (1) are active


def test_apply_filters_nested_invalid_relationship() -> None:
    """Verify that filtering on non-existent nested relationships does not crash and is skipped."""
    FilterModel = create_filter_model(UserOut)
    filter_inst = FilterModel()
    data = {"nonexistent__name__eq": "test"}

    adapter = SQLAlchemyFilterAdapter()
    stmt = adapter._apply_dynamic_filters(
        select(User), User, filter_inst, data, FilterModel._source_filter_config
    )
    assert "WHERE" not in str(stmt)


def test_apply_filters_nested_not_a_property() -> None:
    """Ensure that nested path resolution stops if an attribute is not a SQLAlchemy property or relationship."""

    class ModelWithPlainAttr(User):
        plain_attr = "not a SA property"

    FilterModel = create_filter_model(UserOut)
    filter_inst = FilterModel()
    data = {"plain_attr__name__eq": "test"}

    adapter = SQLAlchemyFilterAdapter()
    stmt = adapter._apply_dynamic_filters(
        select(ModelWithPlainAttr),
        ModelWithPlainAttr,
        filter_inst,
        data,
        FilterModel._source_filter_config,
    )
    assert "WHERE" not in str(stmt)
