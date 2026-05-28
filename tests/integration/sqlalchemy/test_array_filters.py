from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterValues
from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.orm.sqlalchemy import apply_filters
from tests.models import Post
from tests.schemas import PostOut


def test_array_contains_filter(seeded_db: Session) -> None:
    """arr_contains should match posts whose tags include the requested value."""
    FilterModel = create_filter_model(PostOut)
    filters = FilterValues(FilterModel(f_tags__arr_contains="desert"))

    stmt = apply_filters(select(Post), Post, filters)
    results = seeded_db.execute(stmt).scalars().all()

    assert len(results) == 1
    assert results[0].title == "Mission to Abydos"


def test_array_overlap_filter(seeded_db: Session) -> None:
    """arr_overlap should match posts sharing at least one tag."""
    FilterModel = create_filter_model(PostOut)
    filters = FilterValues(
        FilterModel(f_tags__arr_overlap=["medical", "jaffa", "unknown"])
    )

    stmt = apply_filters(select(Post), Post, filters)
    results = seeded_db.execute(stmt).scalars().all()

    titles = {post.title for post in results}
    assert titles == {"Encounter in Chulak", "Medical supplies inventory"}


def test_array_all_filter(seeded_db: Session) -> None:
    """arr_all should require every requested tag to be present."""
    FilterModel = create_filter_model(PostOut)
    filters = FilterValues(FilterModel(f_tags__arr_all=["exploration", "desert"]))

    stmt = apply_filters(select(Post), Post, filters)
    results = seeded_db.execute(stmt).scalars().all()

    assert len(results) == 1
    assert results[0].title == "Mission to Abydos"


def test_array_length_and_empty_filter(seeded_db: Session) -> None:
    """arr_len and is_empty should work on the seeded empty tag list."""
    FilterModel = create_filter_model(PostOut)

    filters_len = FilterValues(FilterModel(f_tags__arr_len=0))
    stmt_len = apply_filters(select(Post), Post, filters_len)
    results_len = seeded_db.execute(stmt_len).scalars().all()
    assert len(results_len) == 1
    assert results_len[0].title == "Contact with Asgard (Classified/Deleted)"

    filters_empty = FilterValues(FilterModel(f_tags__is_empty=True))
    stmt_empty = apply_filters(select(Post), Post, filters_empty)
    results_empty = seeded_db.execute(stmt_empty).scalars().all()
    assert len(results_empty) == 1
    assert results_empty[0].title == "Contact with Asgard (Classified/Deleted)"
