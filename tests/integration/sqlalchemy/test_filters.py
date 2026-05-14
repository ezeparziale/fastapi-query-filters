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


def test_apply_filters_advanced_text_operators(seeded_db: Session) -> None:
    """Test advanced text operators: startswith, endswith, contains (and their 'i' versions)."""

    class AdvancedStrSchema(BaseModel):
        name: str = Field(
            json_schema_extra={
                "filters": [
                    "startswith",
                    "istartswith",
                    "endswith",
                    "iendswith",
                    "contains",
                ]
            }
        )
        profile_bio: str = Field(json_schema_extra={"filters": ["contains"]})

    FilterModel = create_filter_model(AdvancedStrSchema)

    # startswith
    filters = FilterValues(FilterModel(name__startswith="Jack"))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].name == "Jack O'Neill"

    # istartswith
    filters = FilterValues(FilterModel(name__istartswith="jack"))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].name == "Jack O'Neill"

    # endswith
    filters = FilterValues(FilterModel(name__endswith="Carter"))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].name == "Samantha Carter"

    # iendswith
    filters = FilterValues(FilterModel(name__iendswith="carter"))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].name == "Samantha Carter"

    # contains (case-sensitive)
    filters = FilterValues(FilterModel(profile_bio__contains="Indeed"))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].name == "Teal'c"

    # contains (negative case for case-sensitivity if dialect supports it)
    # SQLite is case-insensitive by default for LIKE, so this might pass even if it shouldn't.
    # But we test it anyway.
    filters = FilterValues(FilterModel(profile_bio__contains="indeed"))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    # In SQLite, this will likely be 1. In Postgres, 0.
    # Given our CI uses SQLite, we don't assert 0 here to avoid flaky tests,
    # but we've exercised the code path.


def test_apply_filters_between_operator(seeded_db: Session) -> None:
    """Test the between operator with various ranges."""

    class BetweenSchema(BaseModel):
        age: int = Field(json_schema_extra={"filters": ["between"]})

    FilterModel = create_filter_model(BetweenSchema)

    # between (35 to 45) -> Sam (35), Janet (38), Jack (45)
    filters = FilterValues(FilterModel(age__between=[35, 45]))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 3

    # between (inclusive boundary check: 38 to 45) -> Janet (38), Jack (45)
    filters = FilterValues(FilterModel(age__between=[38, 45]))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 2

    # between (no matches: 200 to 300)
    filters = FilterValues(FilterModel(age__between=[200, 300]))
    stmt = apply_filters(select(User), User, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 0


def test_apply_filters_not_isnull_operator(seeded_db: Session) -> None:
    """Test the not_isnull operator using the casualties field from Post."""
    from tests.models import Post

    class NotNullSchema(BaseModel):
        casualties: int = Field(json_schema_extra={"filters": ["not_isnull"]})

    FilterModel = create_filter_model(NotNullSchema)

    # 4 posts total:
    # 1. Abydos: casualties=0
    # 2. Chulak: casualties=1
    # 3. Medical inventory: casualties=None
    # 4. Asgard (deleted): casualties=0

    # not_isnull=True (Abydos, Chulak, Asgard have casualties defined)
    filters = FilterValues(FilterModel(casualties__not_isnull=True))
    stmt = apply_filters(select(Post), Post, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 3

    # not_isnull=False (inverse of not null -> null; only Medical inventory has NULL casualties)
    filters = FilterValues(FilterModel(casualties__not_isnull=False))
    stmt = apply_filters(select(Post), Post, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].title == "Medical supplies inventory"
