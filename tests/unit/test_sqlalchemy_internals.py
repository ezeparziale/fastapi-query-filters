from datetime import date, datetime, time
from typing import Any, cast
from unittest.mock import patch

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects import sqlite

from fastapi_query_filters import FilterValues
from fastapi_query_filters.core import FilterConfig, create_filter_model
from fastapi_query_filters.orm.sqlalchemy import SQLAlchemyFilterAdapter
from tests.models import Mission, User


def test_resolve_column_prefix_strip() -> None:
    """Verify that _resolve_column correctly strips the global prefix."""
    adapter = SQLAlchemyFilterAdapter()
    stmt = select(User)
    new_stmt, col = adapter._resolve_column(
        stmt, User, "p_name", set(), global_prefix="p_"
    )
    assert col is not None
    assert "name" in str(col)


def test_json_alias_resolution_via_search() -> None:
    """Verify that internal JSON aliases are resolved during global search."""

    class MetadataWithAlias(BaseModel):
        real_key: str = Field(
            alias="alias_key",
            json_schema_extra={
                "filters": ["eq"],
                "field_alias": "alias_key",
                "original_field": "real_key",
            },
        )

    class SchemaWithJSON(BaseModel):
        mission_metadata: MetadataWithAlias

        class FilterConfig:
            max_depth = 1
            search_columns = ["mission_metadata__alias_key"]

    FilterModel = create_filter_model(SchemaWithJSON)
    filters = FilterValues(FilterModel(q="test"))

    adapter = SQLAlchemyFilterAdapter()
    stmt = select(Mission)
    stmt = adapter.apply_filters(stmt, Mission, filters)

    sql = str(
        stmt.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
    )
    assert "real_key" in sql


def test_map_python_to_sa_type() -> None:
    """Verify mapping of all supported Python types to SQLAlchemy types."""
    adapter = SQLAlchemyFilterAdapter()
    assert adapter._map_python_to_sa_type(int) is not None
    assert adapter._map_python_to_sa_type(float) is not None
    assert adapter._map_python_to_sa_type(bool) is not None
    assert adapter._map_python_to_sa_type(str) is not None
    assert adapter._map_python_to_sa_type(date) is not None
    assert adapter._map_python_to_sa_type(datetime) is not None
    assert adapter._map_python_to_sa_type(time) is not None
    assert adapter._map_python_to_sa_type(complex) is None


def test_search_json_element_mock() -> None:
    """Verify handling of JSON elements in global search using mocks."""
    adapter = SQLAlchemyFilterAdapter()

    class MockCol:
        def as_string(self) -> "MockCol":
            return self

        def ilike(self, q: str) -> bool:
            return True

    class MockConfig(FilterConfig):
        enable_search = True
        search_field = "q"
        search_columns = ["mock_col"]
        prefix = ""

    with patch.object(
        adapter, "_resolve_column", return_value=(select(User), MockCol())
    ):
        stmt = adapter._apply_global_features(
            select(User), User, {"q": "test"}, cast(type[FilterConfig], MockConfig)
        )
    assert stmt is not None


def test_json_temporal_list_conversion() -> None:
    """Verify temporal conversion for lists (IN/BETWEEN) in JSON fields."""

    class SchemaJSONDate(BaseModel):
        mission_metadata: dict[str, Any] = Field(
            json_schema_extra={"filters": ["in", "between"]}
        )

    class ExtraFilters(BaseModel):
        mission_metadata__date: date = Field(
            json_schema_extra={"filters": ["in", "between"]}
        )

    class SchemaWithExtra(SchemaJSONDate):
        class FilterConfig:
            extra_filters = ExtraFilters

    FilterModel = create_filter_model(SchemaWithExtra)
    # BETWEEN triggers a list of 2 dates
    filters = FilterValues(
        FilterModel(
            mission_metadata__date__between=[date(1997, 1, 1), date(1998, 1, 1)]
        )
    )

    adapter = SQLAlchemyFilterAdapter()
    stmt = select(Mission)
    stmt = adapter.apply_filters(stmt, Mission, filters)

    sql = str(
        stmt.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
    )
    assert "1997-01-01" in sql
    assert "1998-01-01" in sql


def test_non_json_column_invalid_nested_path() -> None:
    """Verify that non-JSON columns return None for nested paths."""
    adapter = SQLAlchemyFilterAdapter()
    stmt = select(User)
    # id is an Integer, so id__something is invalid
    new_stmt, col = adapter._resolve_column(stmt, User, "id__something", set())
    assert col is None
