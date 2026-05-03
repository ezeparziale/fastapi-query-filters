from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterValues
from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.orm.sqlalchemy import apply_filters
from tests.models import User
from tests.schemas import UserOut


def test_apply_filters_basic_eq(seeded_db: Session) -> None:
    """Test filtering by a simple equality operator."""
    FilterModel = create_filter_model(UserOut)
    # Filter by email
    filters = FilterValues(FilterModel(email__eq="oneill@example.com"))

    stmt = select(User)
    stmt = apply_filters(stmt, User, filters)

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].email == "oneill@example.com"


def test_apply_filters_icontains(seeded_db: Session) -> None:
    """Test case-insensitive contains filter."""
    FilterModel = create_filter_model(UserOut)
    # Search for 'carter'
    filters = FilterValues(FilterModel(email__icontains="carter"))

    stmt = select(User)
    stmt = apply_filters(stmt, User, filters)

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].name == "Samantha Carter"


def test_apply_filters_in_operator(seeded_db: Session) -> None:
    """Test the IN operator with multiple values."""
    FilterModel = create_filter_model(UserOut)
    filters = FilterValues(FilterModel(id__in=[1, 2]))

    stmt = select(User)
    stmt = apply_filters(stmt, User, filters)

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 2
    ids = [r.id for r in results]
    assert 1 in ids
    assert 2 in ids


def test_apply_filters_isnull(seeded_db: Session) -> None:
    """Test the isnull operator."""
    FilterModel = create_filter_model(UserOut)

    filters = FilterValues(FilterModel(name__isnull=False))
    stmt = select(User)
    stmt = apply_filters(stmt, User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 3

    filters_null = FilterValues(FilterModel(name__isnull=True))
    stmt_null = apply_filters(select(User), User, filters_null)
    results_null = seeded_db.execute(stmt_null).scalars().all()
    assert len(results_null) == 0


def test_apply_filters_gt_on_extra_field(seeded_db: Session) -> None:
    """Test filtering on an extra field (not in the response schema)."""
    FilterModel = create_filter_model(UserOut)
    # Users older than 40 (O'Neill=50, Teal'c=157)
    filters = FilterValues(FilterModel(age__gt=40))

    stmt = select(User)
    stmt = apply_filters(stmt, User, filters)

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 2
    for r in results:
        assert r.age is not None
        assert r.age > 40


def test_operators_extra(seeded_db: Session) -> None:
    """Verify the correct behavior of additional operators including NE, GTE, LTE, LIKE, ILIKE, and NOT_IN."""

    class ExtraFiltersSchema(BaseModel):
        email: str = Field(json_schema_extra={"filters": ["ne"]})
        age: int = Field(json_schema_extra={"filters": ["gte", "lte"]})
        name: str = Field(json_schema_extra={"filters": ["like", "ilike"]})
        id: int = Field(json_schema_extra={"filters": ["not_in"]})

    FilterModel = create_filter_model(ExtraFiltersSchema)

    # NE
    filters = FilterValues(FilterModel(email__ne="oneill@example.com"))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 2

    # GTE
    filters = FilterValues(FilterModel(age__gte=50))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) >= 2

    # LTE
    filters = FilterValues(FilterModel(age__lte=40))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) >= 1

    # LIKE
    filters = FilterValues(FilterModel(name__like="Jack%"))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1

    # ILIKE
    filters = FilterValues(FilterModel(name__ilike="jack%"))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1

    # NOT IN (list)
    filters = FilterValues(FilterModel(id__not_in=[1, 2]))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].id == 3

    # NOT IN (string single value)
    filters = FilterValues(FilterModel(id__not_in="1"))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 2
    assert 1 not in [r.id for r in results]
