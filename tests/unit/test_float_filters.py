import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fastapi_query_filters.core import create_filter_model


class HealthOut(BaseModel):
    health_status: float = Field(
        json_schema_extra={"filters": ["eq", "ne", "gt", "lt", "gte", "lte", "isnull"]}
    )

    model_config = ConfigDict(from_attributes=True)


FilterModel = create_filter_model(HealthOut)


def test_float_gte_filter_generated() -> None:
    """float field with gte operator should generate the filter field."""
    assert "health_status__gte" in FilterModel.model_fields


def test_float_lte_filter_generated() -> None:
    """float field with lte operator should generate the filter field."""
    assert "health_status__lte" in FilterModel.model_fields


def test_float_eq_filter_generated() -> None:
    """float field with eq operator should generate the filter field."""
    assert "health_status__eq" in FilterModel.model_fields


def test_float_ne_filter_generated() -> None:
    """float field with ne operator should generate the filter field."""
    assert "health_status__ne" in FilterModel.model_fields


def test_float_gt_filter_generated() -> None:
    """float field with gt operator should generate the filter field."""
    assert "health_status__gt" in FilterModel.model_fields


def test_float_lt_filter_generated() -> None:
    """float field with lt operator should generate the filter field."""
    assert "health_status__lt" in FilterModel.model_fields


def test_float_isnull_filter_generated() -> None:
    """float field with isnull operator should generate the filter field."""
    assert "health_status__isnull" in FilterModel.model_fields


def test_float_filter_accepts_integer_value() -> None:
    """float filter should accept integer values and coerce them to float."""
    instance = FilterModel(**{"health_status__gte": 10})
    assert instance.model_fields_set
    assert instance.health_status__gte == 10.0


def test_float_filter_accepts_float_value() -> None:
    """float filter should accept float values."""
    instance = FilterModel(**{"health_status__gte": 3.14})
    assert instance.health_status__gte == 3.14


def test_float_filter_accepts_string_numeric_value() -> None:
    """float filter should coerce numeric strings to float (FastAPI query param behavior)."""
    instance = FilterModel(**{"health_status__lte": "99.5"})
    assert instance.health_status__lte == 99.5


def test_float_filter_rejects_non_numeric_string() -> None:
    """float filter should reject non-numeric strings with a validation error."""
    with pytest.raises(ValidationError):
        FilterModel(**{"health_status__gte": "not_a_number"})


def test_float_filter_defaults_to_none() -> None:
    """float filter fields should default to None when not provided."""
    instance = FilterModel()
    assert instance.health_status__gte is None
    assert instance.health_status__lte is None
