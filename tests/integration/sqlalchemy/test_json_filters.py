from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterValues
from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.orm.sqlalchemy import apply_filters
from tests.models import Mission
from tests.schemas import MissionOut


def test_json_filter_str_operators(seeded_db: Session) -> None:
    """Test string operators inside JSON metadata."""
    FilterModel = create_filter_model(MissionOut)

    # eq
    filters = FilterValues(FilterModel(m_data__commander__eq="Jack O'Neill"))
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].planet_name == "P3X-984"

    # icontains
    filters = FilterValues(FilterModel(m_data__commander__icontains="carter"))
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].mission_metadata is not None
    assert "Carter" in results[0].mission_metadata["commander"]

    # in
    filters = FilterValues(
        FilterModel(m_data__commander__in=["Jack O'Neill", "Teal'c"])
    )
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 2


def test_json_filter_int_operators(seeded_db: Session) -> None:
    """Test integer operators inside JSON metadata (requires casting)."""
    FilterModel = create_filter_model(MissionOut)

    # gt
    filters = FilterValues(FilterModel(m_data__danger_level__gt=5))
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    # P3X-984 (8) and P2X-555 (10)
    assert len(results) == 2
    for r in results:
        assert r.mission_metadata is not None
        assert r.mission_metadata["danger_level"] > 5

    # between
    filters = FilterValues(FilterModel(m_data__danger_level__between=[3, 5]))
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].mission_metadata is not None
    assert results[0].mission_metadata["danger_level"] == 4


def test_json_filter_float_operators(seeded_db: Session) -> None:
    """Test float operators inside JSON metadata."""
    FilterModel = create_filter_model(MissionOut)

    # gte
    filters = FilterValues(FilterModel(m_data__naquadah_concentration__gte=0.8))
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    # Jack (0.85), Teal'c (0.95)
    assert len(results) == 2


def test_json_filter_date_operators(seeded_db: Session) -> None:
    """Test date operators inside JSON metadata (requires casting)."""
    FilterModel = create_filter_model(MissionOut)

    # gte
    filters = FilterValues(FilterModel(m_data__scheduled_date__gte=date(1998, 1, 1)))
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    # Carter (1998-03-22), Teal'c (1999-01-01)
    assert len(results) == 2


def test_json_filter_null_operators(seeded_db: Session) -> None:
    """Test isnull operator on JSON fields."""
    FilterModel = create_filter_model(MissionOut)

    # isnull=True on a field that doesn't exist in some JSONs
    filters = FilterValues(FilterModel(m_data__danger_level__isnull=True))
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    # Empty Planet (metadata is None), Partial Data Planet (only has commander)
    assert len(results) == 2
    names = [r.planet_name for r in results]
    assert "Empty Planet" in names
    assert "Partial Data Planet" in names


def test_json_global_search(seeded_db: Session) -> None:
    """Test that search_columns works across JSON fields."""
    FilterModel = create_filter_model(MissionOut)

    # Search for "Teal'c" (in metadata__commander)
    filters = FilterValues(FilterModel(q="Teal'c"))
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].planet_name == "P2X-555"

    # Search for "P3X" (in planet_name alias)
    filters = FilterValues(FilterModel(q="P3X"))
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].planet_name == "P3X-984"


def test_json_sorting(seeded_db: Session) -> None:
    """Test sorting by a JSON field."""
    FilterModel = create_filter_model(MissionOut)

    # Sort by danger_level ascending
    filters = FilterValues(FilterModel(sort_by="m_data__danger_level"))
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()

    # Filter out those with None metadata for easier check
    valid_results = [
        r
        for r in results
        if r.mission_metadata and "danger_level" in r.mission_metadata
    ]
    assert len(valid_results) == 3
    assert valid_results[0].mission_metadata is not None
    assert valid_results[1].mission_metadata is not None
    assert valid_results[2].mission_metadata is not None
    assert valid_results[0].mission_metadata["danger_level"] == 4  # Carter
    assert valid_results[1].mission_metadata["danger_level"] == 8  # Jack
    assert valid_results[2].mission_metadata["danger_level"] == 10  # Teal'c


def test_json_is_empty_and_is_blank_operators(seeded_db: Session) -> None:
    """Test is_empty and is_blank operators on JSON fields."""
    from pydantic import BaseModel, Field

    # Add a mission with empty dict metadata {}
    empty_mission = Mission(planet_name="Empty Dict Planet", mission_metadata={})
    seeded_db.add(empty_mission)
    seeded_db.commit()

    class LocalMissionOut(BaseModel):
        mission_metadata: dict[str, Any] = Field(
            json_schema_extra={
                "filters": ["is_empty", "is_blank", "isnull", "not_isnull"]
            }
        )

        class FilterConfig:
            prefix = "m_"

    FilterModel = create_filter_model(LocalMissionOut)

    # Test is_empty=True:
    # Should match only "Empty Dict Planet" (because {} is empty, but None is NULL and not empty)
    filters = FilterValues(FilterModel(m_mission_metadata__is_empty=True))

    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].planet_name == "Empty Dict Planet"

    # Test is_empty=False:
    # Should match all except "Empty Dict Planet" and "Empty Planet" (None is NULL, standard != excludes NULLs)
    # Those are the 4 non-empty missions: P3X-984, P4X-639, P2X-555, Partial Data Planet
    filters = FilterValues(FilterModel(m_mission_metadata__is_empty=False))
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()

    assert len(results) == 4

    planets = [r.planet_name for r in results]
    assert "Empty Dict Planet" not in planets
    assert "Empty Planet" not in planets

    # Test is_blank=True:
    # Should match "Empty Dict Planet" ({}) AND "Empty Planet" (None)
    filters = FilterValues(FilterModel(m_mission_metadata__is_blank=True))
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 2
    planets = [r.planet_name for r in results]
    assert "Empty Dict Planet" in planets
    assert "Empty Planet" in planets

    # Test is_blank=False:
    # Should match only missions that are NOT empty and NOT NULL (the 4 active ones)
    filters = FilterValues(FilterModel(m_mission_metadata__is_blank=False))
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 4
    planets = [r.planet_name for r in results]
    assert "Empty Dict Planet" not in planets
    assert "Empty Planet" not in planets
