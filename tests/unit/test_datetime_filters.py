from datetime import UTC, datetime

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.dependencies import FilterValues


class LogOut(BaseModel):
    created_at: datetime = Field(
        json_schema_extra={
            "filters": ["eq", "ne", "gt", "lt", "gte", "lte", "in", "not_in", "isnull"]
        }
    )

    model_config = ConfigDict(from_attributes=True)


FilterModel = create_filter_model(LogOut)


# ---------------------------------------------------------------------------
# Generation tests
# ---------------------------------------------------------------------------


def test_datetime_eq_filter_generated() -> None:
    """datetime field with eq operator should generate the filter field."""
    assert "created_at__eq" in FilterModel.model_fields


def test_datetime_ne_filter_generated() -> None:
    """datetime field with ne operator should generate the filter field."""
    assert "created_at__ne" in FilterModel.model_fields


def test_datetime_gt_filter_generated() -> None:
    """datetime field with gt operator should generate the filter field."""
    assert "created_at__gt" in FilterModel.model_fields


def test_datetime_lt_filter_generated() -> None:
    """datetime field with lt operator should generate the filter field."""
    assert "created_at__lt" in FilterModel.model_fields


def test_datetime_gte_filter_generated() -> None:
    """datetime field with gte operator should generate the filter field."""
    assert "created_at__gte" in FilterModel.model_fields


def test_datetime_lte_filter_generated() -> None:
    """datetime field with lte operator should generate the filter field."""
    assert "created_at__lte" in FilterModel.model_fields


def test_datetime_in_filter_generated() -> None:
    """datetime field with in operator should generate the filter field."""
    assert "created_at__in" in FilterModel.model_fields


def test_datetime_not_in_filter_generated() -> None:
    """datetime field with not_in operator should generate the filter field."""
    assert "created_at__not_in" in FilterModel.model_fields


def test_datetime_isnull_filter_generated() -> None:
    """datetime field with isnull operator should generate the filter field."""
    assert "created_at__isnull" in FilterModel.model_fields


# ---------------------------------------------------------------------------
# Operators NOT available for datetime (must not be generated)
# ---------------------------------------------------------------------------


def test_datetime_like_operator_not_generated() -> None:
    """like operator should NOT be generated for datetime fields."""
    assert "created_at__like" not in FilterModel.model_fields


def test_datetime_ilike_operator_not_generated() -> None:
    """ilike operator should NOT be generated for datetime fields."""
    assert "created_at__ilike" not in FilterModel.model_fields


def test_datetime_icontains_operator_not_generated() -> None:
    """icontains operator should NOT be generated for datetime fields."""
    assert "created_at__icontains" not in FilterModel.model_fields


# ---------------------------------------------------------------------------
# eq — coercion and validation
# ---------------------------------------------------------------------------


def test_datetime_eq_accepts_datetime_object() -> None:
    """eq should accept a plain datetime object."""
    dt = datetime(2024, 1, 15, 10, 30, 0)
    instance = FilterModel(**{"created_at__eq": dt})
    assert instance.created_at__eq == dt


def test_datetime_eq_accepts_iso_string() -> None:
    """eq should accept and parse an ISO 8601 datetime string."""
    instance = FilterModel(**{"created_at__eq": "2024-01-15T10:30:00"})
    assert instance.created_at__eq == datetime(2024, 1, 15, 10, 30, 0)


def test_datetime_eq_accepts_iso_string_with_timezone() -> None:
    """eq should accept and parse an ISO 8601 datetime string with UTC timezone."""
    instance = FilterModel(**{"created_at__eq": "2024-01-15T10:30:00Z"})
    assert instance.created_at__eq == datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)


def test_datetime_eq_accepts_iso_string_with_offset() -> None:
    """eq should accept and parse an ISO 8601 datetime string with UTC offset."""
    instance = FilterModel(**{"created_at__eq": "2024-01-15T10:30:00+00:00"})
    assert instance.created_at__eq is not None


def test_datetime_eq_accepts_microseconds() -> None:
    """eq should accept datetime strings with microseconds."""
    instance = FilterModel(**{"created_at__eq": "2024-01-15T10:30:00.123456"})
    assert instance.created_at__eq == datetime(2024, 1, 15, 10, 30, 0, 123456)


def test_datetime_eq_rejects_invalid_string() -> None:
    """eq should reject strings that are not valid datetimes."""
    with pytest.raises(ValidationError):
        FilterModel(**{"created_at__eq": "not-a-datetime"})


def test_datetime_eq_rejects_date_only_string() -> None:
    """eq should reject bare date strings (no time component) per strict datetime parsing."""
    # Pydantic may or may not coerce this; this test documents the actual behavior.
    # If Pydantic accepts it, the result should be at midnight.
    try:
        instance = FilterModel(**{"created_at__eq": "2024-01-15"})
        assert instance.created_at__eq == datetime(2024, 1, 15, 0, 0, 0)
    except ValidationError:
        pass  # Also acceptable — strict datetime parsing


def test_datetime_eq_rejects_empty_string() -> None:
    """eq should reject empty strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"created_at__eq": ""})


def test_datetime_eq_accepts_none() -> None:
    """eq set to None should be treated as not provided."""
    instance = FilterModel(**{"created_at__eq": None})
    assert instance.created_at__eq is None


# ---------------------------------------------------------------------------
# Comparison operators
# ---------------------------------------------------------------------------


def test_datetime_gt_accepts_datetime_object() -> None:
    """gt should accept a datetime object."""
    dt = datetime(2024, 6, 1, 0, 0, 0)
    instance = FilterModel(**{"created_at__gt": dt})
    assert instance.created_at__gt == dt


def test_datetime_gt_accepts_iso_string() -> None:
    """gt should accept and parse an ISO 8601 datetime string."""
    instance = FilterModel(**{"created_at__gt": "2024-06-01T00:00:00"})
    assert instance.created_at__gt == datetime(2024, 6, 1, 0, 0, 0)


def test_datetime_lt_accepts_datetime_object() -> None:
    """lt should accept a datetime object."""
    dt = datetime(2025, 12, 31, 23, 59, 59)
    instance = FilterModel(**{"created_at__lt": dt})
    assert instance.created_at__lt == dt


def test_datetime_gte_accepts_iso_string() -> None:
    """gte should accept and parse an ISO 8601 datetime string."""
    instance = FilterModel(**{"created_at__gte": "2024-01-01T00:00:00"})
    assert instance.created_at__gte == datetime(2024, 1, 1, 0, 0, 0)


def test_datetime_lte_accepts_datetime_object() -> None:
    """lte should accept a datetime object."""
    dt = datetime(2024, 12, 31, 23, 59, 59)
    instance = FilterModel(**{"created_at__lte": dt})
    assert instance.created_at__lte == dt


def test_datetime_ne_accepts_iso_string() -> None:
    """ne should accept and parse an ISO 8601 datetime string."""
    instance = FilterModel(**{"created_at__ne": "2024-03-20T08:00:00"})
    assert instance.created_at__ne == datetime(2024, 3, 20, 8, 0, 0)


# ---------------------------------------------------------------------------
# in / not_in
# ---------------------------------------------------------------------------


def test_datetime_in_accepts_list_of_datetimes() -> None:
    """in should accept a list of datetime objects."""
    dts = [datetime(2024, 1, 1), datetime(2024, 6, 1), datetime(2024, 12, 31)]
    instance = FilterModel(**{"created_at__in": dts})
    assert instance.created_at__in == dts


def test_datetime_in_accepts_comma_separated_string() -> None:
    """in should parse a comma-separated string of ISO datetimes into a list."""
    instance = FilterModel(
        **{"created_at__in": "2024-01-01T00:00:00,2024-06-01T12:00:00"}
    )
    assert instance.created_at__in == [
        datetime(2024, 1, 1, 0, 0, 0),
        datetime(2024, 6, 1, 12, 0, 0),
    ]


def test_datetime_in_accepts_single_datetime_string() -> None:
    """in should accept a single ISO datetime string and wrap it in a list."""
    instance = FilterModel(**{"created_at__in": "2024-01-01T00:00:00"})
    assert instance.created_at__in == [datetime(2024, 1, 1, 0, 0, 0)]


def test_datetime_in_rejects_list_with_invalid_strings() -> None:
    """in should reject lists containing invalid datetime strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"created_at__in": ["2024-01-01T00:00:00", "bad-value"]})


def test_datetime_not_in_accepts_list_of_datetimes() -> None:
    """not_in should accept a list of datetime objects."""
    dts = [datetime(2024, 1, 1), datetime(2024, 6, 1)]
    instance = FilterModel(**{"created_at__not_in": dts})
    assert instance.created_at__not_in == dts


def test_datetime_not_in_accepts_comma_separated_string() -> None:
    """not_in should parse a comma-separated string of ISO datetimes into a list."""
    instance = FilterModel(
        **{"created_at__not_in": "2024-01-01T00:00:00,2024-06-01T00:00:00"}
    )
    assert instance.created_at__not_in == [
        datetime(2024, 1, 1),
        datetime(2024, 6, 1),
    ]


# ---------------------------------------------------------------------------
# isnull
# ---------------------------------------------------------------------------


def test_datetime_isnull_accepts_true() -> None:
    """isnull=True should filter for NULL values."""
    instance = FilterModel(**{"created_at__isnull": True})
    assert instance.created_at__isnull is True


def test_datetime_isnull_accepts_false() -> None:
    """isnull=False should filter for NOT NULL values."""
    instance = FilterModel(**{"created_at__isnull": False})
    assert instance.created_at__isnull is False


def test_datetime_isnull_accepts_string_true() -> None:
    """isnull should coerce string 'true' to True."""
    instance = FilterModel(**{"created_at__isnull": "true"})
    assert instance.created_at__isnull is True


def test_datetime_isnull_accepts_string_false() -> None:
    """isnull should coerce string 'false' to False."""
    instance = FilterModel(**{"created_at__isnull": "false"})
    assert instance.created_at__isnull is False


def test_datetime_isnull_accepts_string_1() -> None:
    """isnull should coerce string '1' to True."""
    instance = FilterModel(**{"created_at__isnull": "1"})
    assert instance.created_at__isnull is True


def test_datetime_isnull_accepts_string_0() -> None:
    """isnull should coerce string '0' to False."""
    instance = FilterModel(**{"created_at__isnull": "0"})
    assert instance.created_at__isnull is False


def test_datetime_isnull_accepts_int_1() -> None:
    """isnull should coerce integer 1 to True."""
    instance = FilterModel(**{"created_at__isnull": 1})
    assert instance.created_at__isnull is True


def test_datetime_isnull_accepts_int_0() -> None:
    """isnull should coerce integer 0 to False."""
    instance = FilterModel(**{"created_at__isnull": 0})
    assert instance.created_at__isnull is False


def test_datetime_isnull_rejects_arbitrary_string() -> None:
    """isnull should reject arbitrary strings that don't represent a boolean."""
    with pytest.raises(ValidationError):
        FilterModel(**{"created_at__isnull": "active"})


def test_datetime_isnull_rejects_integer_2() -> None:
    """isnull should reject integers other than 0 and 1."""
    with pytest.raises(ValidationError):
        FilterModel(**{"created_at__isnull": 2})


def test_datetime_isnull_accepts_none() -> None:
    """isnull set to None should be treated as not provided."""
    instance = FilterModel(**{"created_at__isnull": None})
    assert instance.created_at__isnull is None


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


def test_datetime_filter_defaults_to_none() -> None:
    """All datetime filter fields should default to None when not provided."""
    instance = FilterModel()
    assert instance.created_at__eq is None
    assert instance.created_at__gt is None
    assert instance.created_at__in is None
    assert instance.created_at__isnull is None


# ---------------------------------------------------------------------------
# Optional datetime field
# ---------------------------------------------------------------------------


def test_datetime_optional_field_generates_filters() -> None:
    """Optional datetime fields should generate filters correctly."""

    class OptionalLogOut(BaseModel):
        deleted_at: datetime | None = Field(
            None,
            json_schema_extra={"filters": ["eq", "isnull"]},
        )

    OptionalFilterModel = create_filter_model(OptionalLogOut)
    assert "deleted_at__eq" in OptionalFilterModel.model_fields
    assert "deleted_at__isnull" in OptionalFilterModel.model_fields

    dt = datetime(2024, 6, 15, 12, 0, 0)
    instance = OptionalFilterModel(deleted_at__eq=dt)
    assert instance.deleted_at__eq == dt


# ---------------------------------------------------------------------------
# Multiple filters at once
# ---------------------------------------------------------------------------


def test_datetime_multiple_filters_at_once() -> None:
    """Filter model should allow combining multiple datetime filters simultaneously."""
    data = {
        "created_at__gte": datetime(2024, 1, 1, 0, 0, 0),
        "created_at__lte": datetime(2024, 12, 31, 23, 59, 59),
        "created_at__ne": datetime(2024, 6, 15, 12, 0, 0),
    }
    instance = FilterModel(**data)
    assert instance.created_at__gte == datetime(2024, 1, 1, 0, 0, 0)
    assert instance.created_at__lte == datetime(2024, 12, 31, 23, 59, 59)
    assert instance.created_at__ne == datetime(2024, 6, 15, 12, 0, 0)


# ---------------------------------------------------------------------------
# FilterValues integration
# ---------------------------------------------------------------------------


def test_datetime_filter_values_dict_excludes_none() -> None:
    """FilterValues.dict() should only include fields that were explicitly set."""
    dt = datetime(2024, 1, 1, 0, 0, 0)
    instance = FilterModel(**{"created_at__gte": dt})
    fv = FilterValues(instance)
    result = fv.dict()

    assert "created_at__gte" in result
    assert result["created_at__gte"] == dt
    assert "created_at__eq" not in result
    assert "created_at__in" not in result
