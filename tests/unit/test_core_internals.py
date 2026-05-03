from typing import Annotated, Any, cast

import pytest
from pydantic import BaseModel, ConfigDict, Field
from pydantic.fields import FieldInfo

from fastapi_query_filters.core import _fields_from_schema, _get_root_type
from fastapi_query_filters.operators import DEFAULT_OPERATORS, FilterOperator


class CustomStr(str):
    pass


class UnknownType:
    pass


class BrokenBaseMeta(type):
    def __subclasscheck__(cls, subclass: Any) -> bool:
        raise TypeError("Triggered TypeError in issubclass")


class BrokenBase(metaclass=BrokenBaseMeta):
    pass


class BrokenType(BrokenBase):
    pass


def test_get_root_type_unwraps_annotated() -> None:
    """Verify that _get_root_type correctly unwraps Annotated types."""
    t = Annotated[int, "metadata"]
    assert _get_root_type(t) is int


def test_get_root_type_unwraps_union() -> None:
    """Verify that _get_root_type correctly extracts the base type from a Union/Optional."""
    t = int | None
    assert _get_root_type(t) is int


def test_field_without_annotation_is_skipped() -> None:
    """Ensure that fields without a type annotation are skipped during generation."""

    class NoAnnotModel(BaseModel):
        pass

    NoAnnotModel.model_fields["x"] = FieldInfo(annotation=None)

    fields = _fields_from_schema(NoAnnotModel)
    assert "x__eq" not in fields


def test_type_error_in_issubclass_loop_is_handled() -> None:
    """Verify that TypeErrors during issubclass checks are caught and handled gracefully."""

    class BrokenMeta(type):
        def __subclasscheck__(cls, subclass: Any) -> bool:
            raise TypeError("Triggered TypeError in issubclass")

    class BrokenTypeInternal(metaclass=BrokenMeta):
        pass

    class BrokenModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        field: BrokenTypeInternal = Field(json_schema_extra={"filters": ["eq"]})

    fields = _fields_from_schema(BrokenModel)
    assert "field__eq" in fields


def test_fields_from_schema_handles_typeerror_in_issubclass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Specific case covering the except TypeError: continue branch with monkeypatching."""
    monkeypatch.setitem(DEFAULT_OPERATORS, BrokenBase, [FilterOperator.EQ])

    class BrokenModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        field: BrokenType = Field(json_schema_extra={"filters": ["eq"]})

    fields = _fields_from_schema(BrokenModel)
    assert "field__eq" in fields


def test_list_and_dict_fields_are_skipped() -> None:
    """Verify that complex container types like list and dict are skipped for direct filtering."""

    class ListDictModel(BaseModel):
        tags: list[int] = Field(
            default_factory=list, json_schema_extra={"filters": ["eq"]}
        )
        data: dict[str, int] = Field(
            default_factory=dict, json_schema_extra={"filters": ["eq"]}
        )

    fields = _fields_from_schema(ListDictModel)
    assert "tags__eq" not in fields
    assert "data__eq" not in fields


def test_subclass_of_str_uses_string_ops() -> None:
    """Verify that subclasses of supported types correctly inherit the allowed operators."""

    class SubclassStrModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        custom: CustomStr = Field(
            default=cast(CustomStr, "x"), json_schema_extra={"filters": ["icontains"]}
        )

    fields = _fields_from_schema(SubclassStrModel)
    assert "custom__icontains" in fields


def test_unknown_type_only_allows_eq_operator() -> None:
    """Verify that unknown types fall back to only allowing the equality operator."""

    class UnknownTypeModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        unknown: UnknownType = Field(
            default=cast(UnknownType, None), json_schema_extra={"filters": ["eq", "gt"]}
        )

    fields = _fields_from_schema(UnknownTypeModel, operators=None)
    assert "unknown__eq" in fields
    assert "unknown__gt" not in fields
