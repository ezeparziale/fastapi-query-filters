import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.dialects import mysql, postgresql, sqlite

from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.dependencies import FilterValues
from fastapi_query_filters.operators import DEFAULT_OPERATORS, FilterOperator
from fastapi_query_filters.orm.sqlalchemy import SQLAlchemyFilterAdapter
from tests.models import Post
from tests.schemas import PostOut


class PlanetOut(BaseModel):
    tags: list[str] = Field(
        default_factory=list,
        json_schema_extra={
            "filters": [
                "arr_contains",
                "arr_overlap",
                "arr_all",
                "arr_any",
                "arr_len",
                "is_empty",
                "is_blank",
                "isnull",
                "not_isnull",
            ]
        },
    )

    model_config = ConfigDict(from_attributes=True)


FilterModel = create_filter_model(PlanetOut)


def test_list_default_operators_include_array_controls() -> None:
    """list fields should advertise the dedicated array operator set."""
    assert DEFAULT_OPERATORS[list] == [
        FilterOperator.ARR_CONTAINS,
        FilterOperator.ARR_OVERLAP,
        FilterOperator.ARR_ALL,
        FilterOperator.ARR_ANY,
        FilterOperator.ARR_LENGTH,
        FilterOperator.IS_EMPTY,
        FilterOperator.IS_BLANK,
        FilterOperator.ISNULL,
        FilterOperator.NOT_ISNULL,
    ]


@pytest.mark.parametrize(
    "field_name",
    [
        "tags__arr_contains",
        "tags__arr_overlap",
        "tags__arr_all",
        "tags__arr_any",
        "tags__arr_len",
        "tags__is_empty",
        "tags__is_blank",
        "tags__isnull",
        "tags__not_isnull",
    ],
)
def test_array_filter_fields_are_generated(field_name: str) -> None:
    """Explicit array operators should generate filter fields for list schemas."""
    assert field_name in FilterModel.model_fields


def test_array_filter_field_types_match_operator_shape() -> None:
    """Array operators should expose scalar, list, integer, and bool input shapes."""
    assert FilterModel.model_fields["tags__arr_contains"].annotation == str | None
    assert FilterModel.model_fields["tags__arr_overlap"].annotation == list[str] | None
    assert FilterModel.model_fields["tags__arr_all"].annotation == list[str] | None
    assert FilterModel.model_fields["tags__arr_any"].annotation == list[str] | None
    assert FilterModel.model_fields["tags__arr_len"].annotation == int | None
    assert FilterModel.model_fields["tags__is_empty"].annotation == bool | None


def test_array_contains_accepts_single_inner_value() -> None:
    """arr_contains should accept one value typed as the list inner type."""
    instance = FilterModel(tags__arr_contains="desert")
    assert instance.tags__arr_contains == "desert"


def test_array_list_operators_parse_comma_separated_values() -> None:
    """Array list operators should split comma-separated query strings."""
    instance = FilterModel(
        tags__arr_overlap="desert, goauld",
        tags__arr_all="exploration,desert",
        tags__arr_any=["medical, inventory"],
    )

    assert instance.tags__arr_overlap == ["desert", "goauld"]
    assert instance.tags__arr_all == ["exploration", "desert"]
    assert instance.tags__arr_any == ["medical", "inventory"]


def test_array_length_accepts_integer_and_numeric_string() -> None:
    """arr_len should be typed as an integer equality check."""
    assert FilterModel(tags__arr_len=3).tags__arr_len == 3
    assert FilterModel(tags__arr_len="2").tags__arr_len == 2


def test_array_length_rejects_non_integer_value() -> None:
    """arr_len should reject values that cannot be parsed as integers."""
    with pytest.raises(ValidationError):
        FilterModel(tags__arr_len="many")


def test_array_boolean_controls_parse_bool_strings() -> None:
    """is_empty/is_blank/isnull controls should keep standard boolean parsing."""
    instance = FilterModel(
        tags__is_empty="true",
        tags__is_blank="0",
        tags__isnull=True,
        tags__not_isnull="false",
    )

    assert instance.tags__is_empty is True
    assert instance.tags__is_blank is False
    assert instance.tags__isnull is True
    assert instance.tags__not_isnull is False


def test_array_filter_values_exclude_unset_fields() -> None:
    """FilterValues should only expose array filters explicitly provided."""
    values = FilterValues(FilterModel(tags__arr_contains="jaffa"))

    assert values.dict() == {"tags__arr_contains": "jaffa"}


def test_postout_tags_keep_real_path_metadata() -> None:
    """Generated PostOut tag filters should resolve back to the Post.tags column."""
    PostFilterModel = create_filter_model(PostOut)
    field = PostFilterModel.model_fields["f_tags__is_empty"]

    assert field.json_schema_extra == {
        "original_field": "tags",
        "real_path": "tags",
        "container_type": "list",
    }


def test_array_is_empty_uses_array_length_for_sqlalchemy() -> None:
    """is_empty on list fields should compile as an array-length check."""
    PostFilterModel = create_filter_model(PostOut)
    filters = FilterValues(PostFilterModel(f_tags__is_empty=True))

    stmt = SQLAlchemyFilterAdapter().apply_filters(select(Post), Post, filters)
    sql = str(
        stmt.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
    )

    assert "json_array_length(posts.tags) = 0" in sql
    assert "json_type(posts.tags) = 'object'" not in sql


def test_array_overlap_compiles_for_supported_dialects() -> None:
    """arr_overlap/arr_any should have SQL compilers for SQLite, MySQL, and Postgres."""
    PostFilterModel = create_filter_model(PostOut)
    filters = FilterValues(PostFilterModel(f_tags__arr_overlap=["desert", "medical"]))
    stmt = SQLAlchemyFilterAdapter().apply_filters(select(Post), Post, filters)

    sqlite_sql = str(stmt.compile(dialect=sqlite.dialect()))
    mysql_sql = str(stmt.compile(dialect=mysql.dialect()))
    postgres_sql = str(stmt.compile(dialect=postgresql.dialect()))  # type: ignore[no-untyped-call]

    assert "json_each(posts.tags)" in sqlite_sql
    assert "JSON_OVERLAPS(posts.tags" in mysql_sql
    assert "posts.tags &&" in postgres_sql
