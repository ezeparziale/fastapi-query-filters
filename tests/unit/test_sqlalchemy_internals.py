from datetime import date, datetime, time
from typing import Any, cast
from unittest.mock import patch

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects import mysql, postgresql, sqlite

from fastapi_query_filters import FilterValues
from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.orm.sqlalchemy import (
    SQLAlchemyFilterAdapter,
    apply_filters,
)
from tests.models import Mission, Post, User
from tests.schemas import PostOut


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

    class MockConfig:
        enable_search = True
        search_field = "q"
        search_columns = ["mock_col"]
        prefix = ""

    with patch.object(
        adapter, "_resolve_column", return_value=(select(User), MockCol())
    ):
        stmt = adapter._apply_global_features(
            select(User), User, {"q": "test"}, cast(Any, MockConfig)
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


def test_nested_json_path_with_prefix() -> None:
    """Verify prefix stripping for nested JSON paths in _apply_dynamic_filters.

    When a filter field uses a nested JSON path and a global prefix is configured,
    the adapter must strip the prefix from the path before determining if it is
    a nested JSON access (containing '__'). This ensures 'is_nested' is correctly
    set to True, enabling proper JSON casting and extraction.
    """

    class ManualFilterModel(BaseModel):
        p_mission_metadata__date__gte: date | None = Field(default=None)

        class FilterConfig:
            prefix = "p_"

    # Manually attach the config as the factory would
    ManualFilterModel._source_filter_config = ManualFilterModel.FilterConfig  # type: ignore

    filters = FilterValues(
        ManualFilterModel(**{"p_mission_metadata__date__gte": date(1997, 1, 1)})
    )

    adapter = SQLAlchemyFilterAdapter()
    stmt = select(Mission)
    # field_path = "p_mission_metadata__date", resolve_prefix = "p_"
    # path_no_prefix strips to "mission_metadata__date" -> is_nested = True
    stmt = adapter.apply_filters(stmt, Mission, filters)
    sql = str(
        stmt.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
    )
    assert "1997-01-01" in sql
    # Verify it was treated as nested JSON
    assert "mission_metadata" in sql
    assert "date" in sql


def test_has_key_compiles_per_dialect() -> None:
    """Verify HAS_KEY uses dialect-specific SQL for JSON key existence."""
    from fastapi_query_filters.operators import FilterOperator

    adapter = SQLAlchemyFilterAdapter()
    expr = adapter._get_operator_expression(
        Mission.mission_metadata, FilterOperator.HAS_KEY, "commander"
    )

    sqlite_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
    )
    mysql_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})
    )
    pg_dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    postgres_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=pg_dialect, compile_kwargs={"literal_binds": True})
    )

    assert "json_each(" in sqlite_sql
    assert "JSON_CONTAINS_PATH(" in mysql_sql
    assert " ? " in postgres_sql
    assert "::jsonb" in postgres_sql


def test_has_any_keys_compiles_per_dialect() -> None:
    """Verify HAS_ANY_KEYS uses dialect-specific SQL for JSON keys existence."""
    from fastapi_query_filters.operators import FilterOperator

    adapter = SQLAlchemyFilterAdapter()
    expr = adapter._get_operator_expression(
        Mission.mission_metadata,
        FilterOperator.HAS_ANY_KEYS,
        ["commander", "danger_level"],
    )

    sqlite_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
    )
    mysql_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})
    )
    pg_dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    postgres_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=pg_dialect, compile_kwargs={"literal_binds": True})
    )

    assert "json_each(" in sqlite_sql
    assert "JSON_CONTAINS_PATH(" in mysql_sql
    assert " ?| ARRAY[" in postgres_sql
    assert "::jsonb" in postgres_sql


def test_has_all_keys_compiles_per_dialect() -> None:
    """Verify HAS_ALL_KEYS uses dialect-specific SQL for JSON keys existence."""
    from fastapi_query_filters.operators import FilterOperator

    adapter = SQLAlchemyFilterAdapter()
    expr = adapter._get_operator_expression(
        Mission.mission_metadata,
        FilterOperator.HAS_ALL_KEYS,
        ["commander", "danger_level"],
    )

    sqlite_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
    )
    mysql_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})
    )
    pg_dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    postgres_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=pg_dialect, compile_kwargs={"literal_binds": True})
    )

    assert "COUNT(DISTINCT json_each.key)" in sqlite_sql
    assert "JSON_CONTAINS_PATH(" in mysql_sql
    assert " ?& ARRAY[" in postgres_sql
    assert "::jsonb" in postgres_sql


def test_is_empty_compiles_per_dialect() -> None:
    """Verify IS_EMPTY uses dialect-specific SQL for JSON object checks."""
    from fastapi_query_filters.operators import FilterOperator

    adapter = SQLAlchemyFilterAdapter()
    expr = adapter._get_operator_expression(
        Mission.mission_metadata, FilterOperator.IS_EMPTY, True
    )

    sqlite_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
    )
    mysql_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})
    )
    pg_dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    postgres_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=pg_dialect, compile_kwargs={"literal_binds": True})
    )

    assert "json_type(" in sqlite_sql
    assert "JSON_TYPE(" in mysql_sql
    assert "JSON_LENGTH(" in mysql_sql
    assert "::jsonb = '{}'::jsonb" in postgres_sql


def test_is_blank_compiles_per_dialect() -> None:
    """Verify IS_BLANK uses dialect-specific SQL for JSON blank checks."""
    from fastapi_query_filters.operators import FilterOperator

    adapter = SQLAlchemyFilterAdapter()
    expr = adapter._get_operator_expression(
        Mission.mission_metadata, FilterOperator.IS_BLANK, True
    )

    sqlite_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
    )
    mysql_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})
    )
    pg_dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    postgres_sql = str(
        select(Mission)
        .where(expr)
        .compile(dialect=pg_dialect, compile_kwargs={"literal_binds": True})
    )

    assert "json_type(" in sqlite_sql
    assert "JSON_TYPE(" in mysql_sql
    assert "::jsonb = '{}'::jsonb" in postgres_sql
    assert "::jsonb = 'null'::jsonb" in postgres_sql


def test_string_eq_mysql_compiles_as_binary_comparison() -> None:
    """Verify EQ on string columns compiles to _bin collation in MySQL."""
    from fastapi_query_filters.operators import FilterOperator

    adapter = SQLAlchemyFilterAdapter()
    expr = adapter._get_operator_expression(User.name, FilterOperator.EQ, "Jack")

    mysql_sql = str(
        select(User)
        .where(expr)
        .compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})
    )
    sqlite_sql = str(
        select(User)
        .where(expr)
        .compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
    )

    assert "COLLATE utf8mb4_bin" in mysql_sql
    assert " = " in sqlite_sql


def test_array_contains_compiles_per_dialect() -> None:
    """Verify ARR_CONTAINS compiles for PostgreSQL and MySQL."""
    from fastapi_query_filters.operators import FilterOperator

    adapter = SQLAlchemyFilterAdapter()
    expr = adapter._get_operator_expression(
        Post.tags, FilterOperator.ARR_CONTAINS, "desert", target_type=list[str]
    )

    pg_dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    postgres_sql = str(select(Post).where(expr).compile(dialect=pg_dialect))
    mysql_sql = str(select(Post).where(expr).compile(dialect=mysql.dialect()))

    assert " @> " in postgres_sql
    assert "JSON_CONTAINS(" in mysql_sql


def test_array_contains_compiles_for_sqlite() -> None:
    """Verify ARR_CONTAINS compiles for SQLite."""
    from fastapi_query_filters.operators import FilterOperator

    adapter = SQLAlchemyFilterAdapter()
    expr = adapter._get_operator_expression(
        Post.tags, FilterOperator.ARR_CONTAINS, "desert", target_type=list[str]
    )

    sqlite_sql = str(select(Post).where(expr).compile(dialect=sqlite.dialect()))

    assert "json_each(posts.tags)" in sqlite_sql


def test_array_length_compiles_per_dialect() -> None:
    """Verify ARR_LENGTH compiles for PostgreSQL and MySQL."""
    from fastapi_query_filters.operators import FilterOperator

    adapter = SQLAlchemyFilterAdapter()
    expr = adapter._get_operator_expression(
        Post.tags, FilterOperator.ARR_LENGTH, 3, target_type=list[str]
    )

    pg_dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    postgres_sql = str(select(Post).where(expr).compile(dialect=pg_dialect))
    mysql_sql = str(select(Post).where(expr).compile(dialect=mysql.dialect()))

    assert "cardinality(posts.tags)" in postgres_sql
    assert "JSON_LENGTH(posts.tags)" in mysql_sql


def test_array_length_compiles_for_sqlite() -> None:
    """Verify ARR_LENGTH compiles for SQLite."""
    from fastapi_query_filters.operators import FilterOperator

    adapter = SQLAlchemyFilterAdapter()
    expr = adapter._get_operator_expression(
        Post.tags, FilterOperator.ARR_LENGTH, 3, target_type=list[str]
    )

    sqlite_sql = str(select(Post).where(expr).compile(dialect=sqlite.dialect()))

    assert "json_array_length(posts.tags)" in sqlite_sql


def test_array_overlap_compiles_per_dialect() -> None:
    """Verify ARR_OVERLAP compiles for SQLite, PostgreSQL and MySQL."""
    from fastapi_query_filters.operators import FilterOperator

    adapter = SQLAlchemyFilterAdapter()
    expr = adapter._get_operator_expression(
        Post.tags,
        FilterOperator.ARR_OVERLAP,
        ["desert", "medical"],
        target_type=list[str],
    )

    sqlite_sql = str(select(Post).where(expr).compile(dialect=sqlite.dialect()))
    pg_dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    postgres_sql = str(select(Post).where(expr).compile(dialect=pg_dialect))
    mysql_sql = str(select(Post).where(expr).compile(dialect=mysql.dialect()))

    assert "json_each(posts.tags)" in sqlite_sql
    assert " && " in postgres_sql
    assert "JSON_OVERLAPS(posts.tags" in mysql_sql


def test_module_level_apply_filters_helper_is_used() -> None:
    """Verify the module-level apply_filters helper delegates correctly."""
    FilterModel = create_filter_model(PostOut)
    filters = FilterValues(FilterModel(f_tags__arr_len=0))

    stmt = apply_filters(select(Post), Post, filters)
    sql = str(stmt.compile(dialect=sqlite.dialect()))

    assert "json_array_length(posts.tags) = ?" in sql
