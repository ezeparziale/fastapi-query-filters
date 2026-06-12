from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterValues
from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.orm.sqlalchemy import apply_filters
from tests.models import StargateArtifact
from tests.schemas import (
    StargateArtifactCustomActiveOut,
    StargateArtifactDecommissionedOut,
    StargateArtifactDestroyedOut,
)


def test_soft_delete_boolean_is_destroyed(seeded_db: Session) -> None:
    """Test automatic soft-delete with boolean column `is_destroyed`.

    Only GDO and Zat'nik'tel should be returned by default because Staff Weapon is_destroyed=True.
    """
    FilterModel = create_filter_model(StargateArtifactDestroyedOut)
    filters = FilterValues(FilterModel())

    stmt = select(StargateArtifact)
    stmt = apply_filters(stmt, StargateArtifact, filters)

    results = seeded_db.execute(stmt).scalars().all()
    # Should exclude "Staff Weapon" (is_destroyed=True)
    assert len(results) == 2
    names = [r.name for r in results]
    assert "GDO" in names
    assert "Zat'nik'tel" in names
    assert "Staff Weapon" not in names


def test_soft_delete_datetime_decommissioned_at(seeded_db: Session) -> None:
    """Test automatic soft-delete with datetime column `decommissioned_at`.

    Only GDO and Staff Weapon should be returned by default because Zat'nik'tel is decommissioned.
    """
    FilterModel = create_filter_model(StargateArtifactDecommissionedOut)
    filters = FilterValues(FilterModel())

    stmt = select(StargateArtifact)
    stmt = apply_filters(stmt, StargateArtifact, filters)

    results = seeded_db.execute(stmt).scalars().all()
    # Should exclude "Zat'nik'tel" (decommissioned_at is set)
    assert len(results) == 2
    names = [r.name for r in results]
    assert "GDO" in names
    assert "Staff Weapon" in names
    assert "Zat'nik'tel" not in names


def test_soft_delete_custom_active_value(seeded_db: Session) -> None:
    """Test soft-delete with a custom active value (e.g. active if `is_destroyed` is True).

    Only Staff Weapon should be returned because only it has `is_destroyed = True`.
    """
    FilterModel = create_filter_model(StargateArtifactCustomActiveOut)
    filters = FilterValues(FilterModel())

    stmt = select(StargateArtifact)
    stmt = apply_filters(stmt, StargateArtifact, filters)

    results = seeded_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].name == "Staff Weapon"
