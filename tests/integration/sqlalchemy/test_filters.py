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
    filters = FilterValues(FilterModel(email__eq="j.oneill@sgc.mil"))

    stmt = select(User)
    stmt = apply_filters(stmt, User, filters)

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].email == "j.oneill@sgc.mil"


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
    # Get first two users from DB to be safe with IDs
    all_users = seeded_db.execute(select(User).order_by(User.id)).scalars().all()
    target_ids = [all_users[0].id, all_users[1].id]

    filters = FilterValues(FilterModel(id__in=target_ids))

    stmt = select(User)
    stmt = apply_filters(stmt, User, filters)

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 2
    ids = [r.id for r in results]
    for tid in target_ids:
        assert tid in ids


def test_apply_filters_isnull(seeded_db: Session) -> None:
    """Test the isnull operator."""
    FilterModel = create_filter_model(UserOut)

    # name is never null in our seed
    filters = FilterValues(FilterModel(name__isnull=False))
    stmt = select(User)
    stmt = apply_filters(stmt, User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 4

    # profile_bio is never null in our seed either now
    filters_null = FilterValues(FilterModel(profile_bio__isnull=True))
    stmt_null = apply_filters(select(User), User, filters_null)
    results_null = seeded_db.execute(stmt_null).scalars().all()
    assert len(results_null) == 0


def test_apply_filters_gt_on_extra_field(seeded_db: Session) -> None:
    """Test filtering on an extra field (not in the response schema)."""
    FilterModel = create_filter_model(UserOut)
    # Users older than 40 (O'Neill=45, Teal'c=105)
    filters = FilterValues(FilterModel(age__gte=40))

    stmt = select(User)
    stmt = apply_filters(stmt, User, filters)

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 2
    for r in results:
        assert r.age is not None
        assert r.age >= 40


def test_operators_extra(seeded_db: Session) -> None:
    """Verify the correct behavior of additional operators including NE, GTE, LTE, LIKE, ILIKE, and NOT_IN."""

    class ExtraFiltersSchema(BaseModel):
        email: str = Field(json_schema_extra={"filters": ["ne"]})
        age: int = Field(json_schema_extra={"filters": ["gt", "gte", "lte"]})
        name: str = Field(json_schema_extra={"filters": ["like", "ilike"]})
        id: int = Field(json_schema_extra={"filters": ["not_in"]})

    FilterModel = create_filter_model(ExtraFiltersSchema)

    # NE
    filters = FilterValues(FilterModel(email__ne="j.oneill@sgc.mil"))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 3

    # GTE
    filters = FilterValues(FilterModel(age__gte=45))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 2  # Jack (45), Teal'c (105)

    # GT
    filters = FilterValues(FilterModel(age__gt=45))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1  # Teal'c (105)

    # LTE
    filters = FilterValues(FilterModel(age__lte=38))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 2  # Sam (35), Janet (38)

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
    all_users = seeded_db.execute(select(User).order_by(User.id)).scalars().all()
    exclude_ids = [all_users[0].id, all_users[1].id]

    filters = FilterValues(FilterModel(id__not_in=exclude_ids))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 2
    for r in results:
        assert r.id not in exclude_ids
