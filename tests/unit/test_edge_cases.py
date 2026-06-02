from typing import TYPE_CHECKING, Any, cast

import pytest
from pydantic import BaseModel, Field, create_model
from sqlalchemy import select

from fastapi_query_filters.core import FilterBase, create_filter_model
from fastapi_query_filters.dependencies import FilterDep, FilterValues
from fastapi_query_filters.orm.sqlalchemy import SQLAlchemyFilterAdapter
from tests.models import User
from tests.schemas import UserOut

if TYPE_CHECKING:
    from sqlalchemy.sql.selectable import Select


def test_split_comma_values_not_dict() -> None:
    """Verify that split_comma_values returns the input data unchanged if it's not a dictionary."""
    split_func = cast(Any, FilterBase).split_comma_values
    assert split_func("not a dict") == "not a dict"


def test_split_comma_values_single_item_list() -> None:
    """Verify that split_comma_values correctly handles and splits a single-item string list containing commas."""
    GeneratedFilter = create_model(
        "GenFilter",
        tags__in=(list[str] | None, Field(default=None)),
        __base__=FilterBase,
    )
    data = {"tags__in": ["a,b,c"]}
    inst = GeneratedFilter.model_validate(data)
    assert cast(Any, inst).tags__in == ["a", "b", "c"]


def test_split_comma_values_field_not_found() -> None:
    """Verify that split_comma_values skips processing for fields not present in the model's fields."""

    GeneratedFilter = create_model("EmptyFilter", __base__=FilterBase)

    data = {"unknown": "a,b,c"}

    split_func = cast(Any, GeneratedFilter).split_comma_values
    assert split_func(data) == data


def test_validate_strict_filters_not_dict() -> None:
    """Verify that validate_strict_filters returns input as-is if it's not a dictionary."""
    validate_func = cast(Any, FilterBase).validate_strict_filters
    assert validate_func("not a dict") == "not a dict"


def test_validate_strict_filters_error() -> None:
    """Verify that strict mode correctly raises a ValueError for unknown fields."""

    class StrictSchema(BaseModel):
        class FilterConfig:
            strict = True

    FilterModel = create_filter_model(StrictSchema)
    with pytest.raises(ValueError, match="Extra inputs are not permitted"):
        FilterModel.model_validate({"extra": "value"})


def test_filter_dep_execution() -> None:
    """Verify the execution logic of FilterDep, ensuring it correctly processes filters and returns FilterValues."""
    dep = FilterDep(UserOut)
    # The dep is a Depends object, its dependency is the inner get_values
    inner_func = dep.dependency

    # Create a mock filter model instance
    FilterModel = create_filter_model(UserOut)
    mock_filters = FilterModel(id__eq=1)

    result = inner_func(mock_filters)
    assert isinstance(result, FilterValues)
    assert cast(Any, result.model).id__eq == 1


def test_sqlalchemy_adapter_no_sqlalchemy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that _check_sqlalchemy raises an ImportError when HAS_SQLALCHEMY is False."""
    import fastapi_query_filters.orm.sqlalchemy._compat as sa_adapter

    monkeypatch.setattr(sa_adapter, "HAS_SQLALCHEMY", False)

    with pytest.raises(ImportError, match="The 'sqlalchemy' extra is required"):
        sa_adapter._check_sqlalchemy()


def test_resolve_column_with_nested_alias() -> None:
    """Verify that _resolve_column handles nested field aliases correctly during relationship joins."""

    class AddressOut(BaseModel):
        street: str = Field(json_schema_extra={"filters": ["eq"], "field_alias": "st"})

    class PersonOut(BaseModel):
        addr: AddressOut

    FilterModel = create_filter_model(PersonOut, depth=1)

    from sqlalchemy import Column, ForeignKey, Integer, String
    from sqlalchemy.orm import declarative_base, relationship

    Base: Any = declarative_base()

    class Address(Base):  # type: ignore[misc]
        __tablename__ = "addr"
        id = Column(Integer, primary_key=True)
        street = Column(String)

    class Person(Base):  # type: ignore[misc]
        __tablename__ = "person"
        id = Column(Integer, primary_key=True)
        addr_id = Column(Integer, ForeignKey("addr.id"))
        addr = relationship(Address)

    adapter = SQLAlchemyFilterAdapter()
    stmt = select(Person)
    joined_paths: set[str] = set()

    # Try to resolve addr__st
    new_stmt, col = adapter._resolve_column(
        stmt, Person, "addr__st", joined_paths, filter_model_class=FilterModel
    )

    assert col is not None
    assert col.name == "street"


def test_search_on_integer_column() -> None:
    """Verify that global search casts non-string columns to String to enable string-based comparison."""
    from sqlalchemy import Column, Integer, select
    from sqlalchemy.orm import declarative_base

    Base: Any = declarative_base()

    class Item(Base):  # type: ignore[misc]
        __tablename__ = "item"
        id = Column(Integer, primary_key=True)
        code = Column(Integer)

    class MockFilterConfig:
        search_columns = ["code"]

    adapter = SQLAlchemyFilterAdapter()
    stmt = adapter._apply_global_features(
        select(Item), Item, {"q": "123"}, cast(Any, MockFilterConfig)
    )
    sql = str(stmt.compile()).lower()
    assert "cast" in sql
    assert "item.code" in sql


def test_resolve_column_invalid_relationship() -> None:
    """Verify that _resolve_column returns None when encountering an invalid relationship or property."""
    adapter = SQLAlchemyFilterAdapter()
    stmt = cast("Select[Any]", select(User))

    # Non-existent relationship
    stmt2, col = adapter._resolve_column(stmt, User, "nonexistent__name", set())
    assert col is None

    # Attribute is not a property
    class FakeModel:
        not_a_prop = "value"

    stmt3, col = adapter._resolve_column(
        stmt, cast(Any, FakeModel), "not_a_prop__name", set()
    )
    assert col is None
