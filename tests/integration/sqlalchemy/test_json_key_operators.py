from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterValues
from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.orm.sqlalchemy import apply_filters
from tests.models import Mission
from tests.schemas import MissionOut

# Coverage matrix
# Operators: has_key, has_any_keys, has_all_keys
# Scenarios: key exists, key missing, JSON null value, partial JSON, empty JSON object, NULL column, duplicate keys
# Engines: sqlite/mysql/postgresql (via TEST_DATABASE_URL)


def _mission_names(seeded_db: Session, filters: FilterValues) -> set[str]:
    stmt = apply_filters(select(Mission), Mission, filters)
    results = seeded_db.execute(stmt).scalars().all()
    return {r.planet_name for r in results}


def test_has_key_exists_and_missing(seeded_db: Session) -> None:
    FilterModel = create_filter_model(MissionOut)

    names = _mission_names(
        seeded_db, FilterValues(FilterModel(m_metadata__has_key="commander"))
    )
    assert names == {"P3X-984", "P4X-639", "P2X-555", "Partial Data Planet"}

    names = _mission_names(
        seeded_db, FilterValues(FilterModel(m_metadata__has_key="nope"))
    )
    assert names == set()


def test_has_key_counts_json_null_value_as_existing(seeded_db: Session) -> None:
    FilterModel = create_filter_model(MissionOut)
    with_null = Mission(
        planet_name="Null Value Planet",
        mission_metadata={"commander": None, "danger_level": 3},
    )
    seeded_db.add(with_null)
    seeded_db.commit()

    names = _mission_names(
        seeded_db, FilterValues(FilterModel(m_metadata__has_key="commander"))
    )
    assert "Null Value Planet" in names


def test_has_any_keys_variants(seeded_db: Session) -> None:
    FilterModel = create_filter_model(MissionOut)

    names = _mission_names(
        seeded_db,
        FilterValues(
            FilterModel(m_metadata__has_any_keys=["danger_level", "does_not_exist"])
        ),
    )
    assert names == {"P3X-984", "P4X-639", "P2X-555"}

    names = _mission_names(
        seeded_db,
        FilterValues(FilterModel(m_metadata__has_any_keys=["commander", "nope"])),
    )
    assert names == {"P3X-984", "P4X-639", "P2X-555", "Partial Data Planet"}

    names = _mission_names(
        seeded_db, FilterValues(FilterModel(m_metadata__has_any_keys=["zzz", "yyy"]))
    )
    assert names == set()


def test_has_all_keys_variants(seeded_db: Session) -> None:
    FilterModel = create_filter_model(MissionOut)

    names = _mission_names(
        seeded_db,
        FilterValues(
            FilterModel(m_metadata__has_all_keys=["commander", "danger_level"])
        ),
    )
    assert names == {"P3X-984", "P4X-639", "P2X-555"}

    names = _mission_names(
        seeded_db,
        FilterValues(
            FilterModel(m_metadata__has_all_keys=["commander", "does_not_exist"])
        ),
    )
    assert names == set()

    names = _mission_names(
        seeded_db, FilterValues(FilterModel(m_metadata__has_all_keys=["commander"]))
    )
    assert names == {"P3X-984", "P4X-639", "P2X-555", "Partial Data Planet"}


def test_has_any_and_all_with_empty_or_duplicate_inputs(seeded_db: Session) -> None:
    FilterModel = create_filter_model(MissionOut)

    names = _mission_names(
        seeded_db, FilterValues(FilterModel(m_metadata__has_any_keys=[]))
    )
    assert names == set()

    names = _mission_names(
        seeded_db, FilterValues(FilterModel(m_metadata__has_all_keys=[]))
    )
    # Empty "all" is vacuously true for all rows.
    assert names == {
        "P3X-984",
        "P4X-639",
        "P2X-555",
        "Empty Planet",
        "Partial Data Planet",
    }

    names = _mission_names(
        seeded_db,
        FilterValues(FilterModel(m_metadata__has_all_keys=["commander", "commander"])),
    )
    assert names == {"P3X-984", "P4X-639", "P2X-555", "Partial Data Planet"}
