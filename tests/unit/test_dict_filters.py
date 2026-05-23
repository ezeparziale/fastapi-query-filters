from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fastapi_query_filters.core import create_filter_model


class DictUserOut(BaseModel):
    metadata: dict[str, Any] = Field(
        json_schema_extra={"filters": ["is_empty", "is_blank", "isnull", "not_isnull"]}
    )

    model_config = ConfigDict(from_attributes=True)


FilterModel = create_filter_model(DictUserOut)


def test_dict_is_empty_filter_generated() -> None:
    """dict field with is_empty operator should generate the filter field."""
    assert "metadata__is_empty" in FilterModel.model_fields


def test_dict_is_blank_filter_generated() -> None:
    """dict field with is_blank operator should generate the filter field."""
    assert "metadata__is_blank" in FilterModel.model_fields


def test_dict_isnull_filter_generated() -> None:
    """dict field with isnull operator should generate the filter field."""
    assert "metadata__isnull" in FilterModel.model_fields


def test_dict_not_isnull_filter_generated() -> None:
    """dict field with not_isnull operator should generate the filter field."""
    assert "metadata__not_isnull" in FilterModel.model_fields


def test_dict_eq_filter_not_allowed() -> None:
    """dict field requesting eq/ne filters should ignore or disallow them."""

    class LegacyDictOut(BaseModel):
        metadata: dict[str, Any] = Field(json_schema_extra={"filters": ["eq", "ne"]})

    LegacyFilterModel = create_filter_model(LegacyDictOut)
    assert "metadata__eq" not in LegacyFilterModel.model_fields
    assert "metadata__ne" not in LegacyFilterModel.model_fields


def test_dict_is_empty_valid_inputs() -> None:
    """dict is_empty filter should accept valid boolean inputs."""
    # bool
    filters = FilterModel(metadata__is_empty=True)
    assert filters.metadata__is_empty is True

    filters = FilterModel(metadata__is_empty=False)
    assert filters.metadata__is_empty is False

    # None
    filters = FilterModel(metadata__is_empty=None)
    assert filters.metadata__is_empty is None


def test_dict_is_blank_valid_inputs() -> None:
    """dict is_blank filter should accept valid boolean inputs."""
    filters = FilterModel(metadata__is_blank=True)
    assert filters.metadata__is_blank is True


def test_dict_is_empty_invalid_inputs() -> None:
    """dict is_empty filter should reject non-boolean inputs."""
    with pytest.raises(ValidationError):
        FilterModel(metadata__is_empty="not-a-bool")
