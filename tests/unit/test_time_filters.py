from datetime import time

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.dependencies import FilterValues


class ScheduleOut(BaseModel):
    start_time: time = Field(
        json_schema_extra={
            "filters": [
                "eq",
                "ne",
                "gt",
                "lt",
                "gte",
                "lte",
                "in",
                "not_in",
                "isnull",
                "not_isnull",
                "between",
            ]
        }
    )

    model_config = ConfigDict(from_attributes=True)


FilterModel = create_filter_model(ScheduleOut)


# ---------------------------------------------------------------------------
# Generation tests
# ---------------------------------------------------------------------------


def test_time_eq_filter_generated() -> None:
    """time field with eq operator should generate the filter field."""
    assert "start_time__eq" in FilterModel.model_fields


def test_time_ne_filter_generated() -> None:
    """time field with ne operator should generate the filter field."""
    assert "start_time__ne" in FilterModel.model_fields


def test_time_gt_filter_generated() -> None:
    """time field with gt operator should generate the filter field."""
    assert "start_time__gt" in FilterModel.model_fields


def test_time_lt_filter_generated() -> None:
    """time field with lt operator should generate the filter field."""
    assert "start_time__lt" in FilterModel.model_fields


def test_time_gte_filter_generated() -> None:
    """time field with gte operator should generate the filter field."""
    assert "start_time__gte" in FilterModel.model_fields


def test_time_lte_filter_generated() -> None:
    """time field with lte operator should generate the filter field."""
    assert "start_time__lte" in FilterModel.model_fields


def test_time_in_filter_generated() -> None:
    """time field with in operator should generate the filter field."""
    assert "start_time__in" in FilterModel.model_fields


def test_time_not_in_filter_generated() -> None:
    """time field with not_in operator should generate the filter field."""
    assert "start_time__not_in" in FilterModel.model_fields


def test_time_isnull_filter_generated() -> None:
    """time field with isnull operator should generate the filter field."""
    assert "start_time__isnull" in FilterModel.model_fields


def test_time_not_isnull_filter_generated() -> None:
    """time field with not_isnull operator should generate the filter field."""
    assert "start_time__not_isnull" in FilterModel.model_fields


def test_time_between_filter_generated() -> None:
    """time field with between operator should generate the filter field."""
    assert "start_time__between" in FilterModel.model_fields


# ---------------------------------------------------------------------------
# Operators NOT available for time (must not be generated)
# ---------------------------------------------------------------------------


def test_time_like_operator_not_generated() -> None:
    """like operator should NOT be generated for time fields."""
    assert "start_time__like" not in FilterModel.model_fields


def test_time_ilike_operator_not_generated() -> None:
    """ilike operator should NOT be generated for time fields."""
    assert "start_time__ilike" not in FilterModel.model_fields


def test_time_icontains_operator_not_generated() -> None:
    """icontains operator should NOT be generated for time fields."""
    assert "start_time__icontains" not in FilterModel.model_fields


# ---------------------------------------------------------------------------
# eq — coercion and validation
# ---------------------------------------------------------------------------


def test_time_eq_accepts_time_object() -> None:
    """eq should accept a plain time object."""
    t = time(10, 30, 0)
    instance = FilterModel(**{"start_time__eq": t})
    assert instance.start_time__eq == t


def test_time_eq_accepts_iso_string_hh_mm_ss() -> None:
    """eq should accept and parse an HH:MM:SS time string."""
    instance = FilterModel(**{"start_time__eq": "10:30:00"})
    assert instance.start_time__eq == time(10, 30, 0)


def test_time_eq_accepts_iso_string_hh_mm() -> None:
    """eq should accept and parse an HH:MM time string."""
    instance = FilterModel(**{"start_time__eq": "10:30"})
    assert instance.start_time__eq == time(10, 30, 0)


def test_time_eq_accepts_midnight() -> None:
    """eq should accept midnight (00:00:00)."""
    instance = FilterModel(**{"start_time__eq": time(0, 0, 0)})
    assert instance.start_time__eq == time(0, 0, 0)


def test_time_eq_accepts_end_of_day() -> None:
    """eq should accept end-of-day time (23:59:59)."""
    instance = FilterModel(**{"start_time__eq": time(23, 59, 59)})
    assert instance.start_time__eq == time(23, 59, 59)


def test_time_eq_accepts_microseconds() -> None:
    """eq should accept time objects with microseconds."""
    t = time(10, 30, 0, 123456)
    instance = FilterModel(**{"start_time__eq": t})
    assert instance.start_time__eq == t


def test_time_eq_rejects_invalid_string() -> None:
    """eq should reject strings that are not valid time values."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_time__eq": "not-a-time"})


def test_time_eq_rejects_out_of_range_hours() -> None:
    """eq should reject time strings with hours > 23."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_time__eq": "25:00:00"})


def test_time_eq_rejects_empty_string() -> None:
    """eq should reject empty strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_time__eq": ""})


def test_time_eq_accepts_none() -> None:
    """eq set to None should be treated as not provided."""
    instance = FilterModel(**{"start_time__eq": None})
    assert instance.start_time__eq is None


# ---------------------------------------------------------------------------
# Comparison operators
# ---------------------------------------------------------------------------


def test_time_gt_accepts_time_object() -> None:
    """gt should accept a time object."""
    instance = FilterModel(**{"start_time__gt": time(8, 0, 0)})
    assert instance.start_time__gt == time(8, 0, 0)


def test_time_gt_accepts_iso_string() -> None:
    """gt should accept and parse an HH:MM:SS time string."""
    instance = FilterModel(**{"start_time__gt": "08:00:00"})
    assert instance.start_time__gt == time(8, 0, 0)


def test_time_lt_accepts_time_object() -> None:
    """lt should accept a time object."""
    instance = FilterModel(**{"start_time__lt": time(18, 0, 0)})
    assert instance.start_time__lt == time(18, 0, 0)


def test_time_gte_accepts_iso_string() -> None:
    """gte should accept and parse an HH:MM:SS time string."""
    instance = FilterModel(**{"start_time__gte": "09:00:00"})
    assert instance.start_time__gte == time(9, 0, 0)


def test_time_lte_accepts_time_object() -> None:
    """lte should accept a time object."""
    instance = FilterModel(**{"start_time__lte": time(17, 30, 0)})
    assert instance.start_time__lte == time(17, 30, 0)


def test_time_ne_accepts_iso_string() -> None:
    """ne should accept and parse an HH:MM:SS time string."""
    instance = FilterModel(**{"start_time__ne": "12:00:00"})
    assert instance.start_time__ne == time(12, 0, 0)


# ---------------------------------------------------------------------------
# in / not_in
# ---------------------------------------------------------------------------


def test_time_in_accepts_list_of_times() -> None:
    """in should accept a list of time objects."""
    times = [time(8, 0, 0), time(12, 0, 0), time(18, 0, 0)]
    instance = FilterModel(**{"start_time__in": times})
    assert instance.start_time__in == times


def test_time_in_accepts_comma_separated_string() -> None:
    """in should parse a comma-separated string of time values into a list."""
    instance = FilterModel(**{"start_time__in": "08:00:00,12:00:00,18:00:00"})
    assert instance.start_time__in == [time(8, 0, 0), time(12, 0, 0), time(18, 0, 0)]


def test_time_in_accepts_single_time_string() -> None:
    """in should accept a single time string and wrap it in a list."""
    instance = FilterModel(**{"start_time__in": "08:00:00"})
    assert instance.start_time__in == [time(8, 0, 0)]


def test_time_in_rejects_list_with_invalid_strings() -> None:
    """in should reject lists containing invalid time strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_time__in": ["08:00:00", "not-a-time"]})


def test_time_not_in_accepts_list_of_times() -> None:
    """not_in should accept a list of time objects."""
    times = [time(8, 0, 0), time(12, 0, 0)]
    instance = FilterModel(**{"start_time__not_in": times})
    assert instance.start_time__not_in == times


def test_time_not_in_accepts_comma_separated_string() -> None:
    """not_in should parse a comma-separated string of time values into a list."""
    instance = FilterModel(**{"start_time__not_in": "08:00:00,12:00:00"})
    assert instance.start_time__not_in == [time(8, 0, 0), time(12, 0, 0)]


# ---------------------------------------------------------------------------
# isnull
# ---------------------------------------------------------------------------


def test_time_isnull_accepts_true() -> None:
    """isnull=True should filter for NULL values."""
    instance = FilterModel(**{"start_time__isnull": True})
    assert instance.start_time__isnull is True


def test_time_isnull_accepts_false() -> None:
    """isnull=False should filter for NOT NULL values."""
    instance = FilterModel(**{"start_time__isnull": False})
    assert instance.start_time__isnull is False


def test_time_isnull_accepts_string_true() -> None:
    """isnull should coerce string 'true' to True."""
    instance = FilterModel(**{"start_time__isnull": "true"})
    assert instance.start_time__isnull is True


def test_time_isnull_accepts_string_false() -> None:
    """isnull should coerce string 'false' to False."""
    instance = FilterModel(**{"start_time__isnull": "false"})
    assert instance.start_time__isnull is False


def test_time_isnull_accepts_string_1() -> None:
    """isnull should coerce string '1' to True."""
    instance = FilterModel(**{"start_time__isnull": "1"})
    assert instance.start_time__isnull is True


def test_time_isnull_accepts_string_0() -> None:
    """isnull should coerce string '0' to False."""
    instance = FilterModel(**{"start_time__isnull": "0"})
    assert instance.start_time__isnull is False


def test_time_isnull_accepts_int_1() -> None:
    """isnull should coerce integer 1 to True."""
    instance = FilterModel(**{"start_time__isnull": 1})
    assert instance.start_time__isnull is True


def test_time_isnull_accepts_int_0() -> None:
    """isnull should coerce integer 0 to False."""
    instance = FilterModel(**{"start_time__isnull": 0})
    assert instance.start_time__isnull is False


def test_time_isnull_rejects_arbitrary_string() -> None:
    """isnull should reject arbitrary strings that don't represent a boolean."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_time__isnull": "active"})


def test_time_isnull_rejects_integer_2() -> None:
    """isnull should reject integers other than 0 and 1."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_time__isnull": 2})


def test_time_isnull_accepts_none() -> None:
    """isnull set to None should be treated as not provided."""
    instance = FilterModel(**{"start_time__isnull": None})
    assert instance.start_time__isnull is None


# ---------------------------------------------------------------------------
# not_isnull
# ---------------------------------------------------------------------------


def test_time_not_isnull_accepts_true() -> None:
    """not_isnull=True should filter for NOT NULL values."""
    instance = FilterModel(**{"start_time__not_isnull": True})
    assert instance.start_time__not_isnull is True


def test_time_not_isnull_accepts_false() -> None:
    """not_isnull=False should filter for NULL values."""
    instance = FilterModel(**{"start_time__not_isnull": False})
    assert instance.start_time__not_isnull is False


def test_time_not_isnull_accepts_string_true() -> None:
    """not_isnull should coerce string 'true' to True."""
    instance = FilterModel(**{"start_time__not_isnull": "true"})
    assert instance.start_time__not_isnull is True


def test_time_not_isnull_accepts_string_false() -> None:
    """not_isnull should coerce string 'false' to False."""
    instance = FilterModel(**{"start_time__not_isnull": "false"})
    assert instance.start_time__not_isnull is False


def test_time_not_isnull_accepts_string_1() -> None:
    """not_isnull should coerce string '1' to True."""
    instance = FilterModel(**{"start_time__not_isnull": "1"})
    assert instance.start_time__not_isnull is True


def test_time_not_isnull_accepts_string_0() -> None:
    """not_isnull should coerce string '0' to False."""
    instance = FilterModel(**{"start_time__not_isnull": "0"})
    assert instance.start_time__not_isnull is False


def test_time_not_isnull_accepts_int_1() -> None:
    """not_isnull should coerce integer 1 to True."""
    instance = FilterModel(**{"start_time__not_isnull": 1})
    assert instance.start_time__not_isnull is True


def test_time_not_isnull_accepts_int_0() -> None:
    """not_isnull should coerce integer 0 to False."""
    instance = FilterModel(**{"start_time__not_isnull": 0})
    assert instance.start_time__not_isnull is False


def test_time_not_isnull_rejects_arbitrary_string() -> None:
    """not_isnull should reject arbitrary strings that don't represent a boolean."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_time__not_isnull": "active"})


def test_time_not_isnull_rejects_integer_2() -> None:
    """not_isnull should reject integers other than 0 and 1."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_time__not_isnull": 2})


def test_time_not_isnull_accepts_none() -> None:
    """not_isnull set to None should be treated as not provided."""
    instance = FilterModel(**{"start_time__not_isnull": None})
    assert instance.start_time__not_isnull is None


# ---------------------------------------------------------------------------
# between
# ---------------------------------------------------------------------------


def test_time_between_accepts_time_objects() -> None:
    """between should accept a list of two time objects."""
    times = [time(8, 0, 0), time(18, 0, 0)]
    instance = FilterModel(**{"start_time__between": times})
    assert instance.start_time__between == times


def test_time_between_accepts_iso_strings() -> None:
    """between should parse a comma-separated string with two time values."""
    instance = FilterModel(**{"start_time__between": "08:00:00,18:00:00"})
    assert instance.start_time__between == [time(8, 0, 0), time(18, 0, 0)]


def test_time_between_rejects_invalid_count() -> None:
    """between should reject lists that don't have exactly two elements."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_time__between": ["08:00:00"]})


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


def test_time_filter_defaults_to_none() -> None:
    """All time filter fields should default to None when not provided."""
    instance = FilterModel()
    assert instance.start_time__eq is None
    assert instance.start_time__gt is None
    assert instance.start_time__in is None
    assert instance.start_time__isnull is None


# ---------------------------------------------------------------------------
# Optional time field
# ---------------------------------------------------------------------------


def test_time_optional_field_generates_filters() -> None:
    """Optional time fields should generate filters correctly."""

    class OptionalScheduleOut(BaseModel):
        end_time: time | None = Field(
            None,
            json_schema_extra={"filters": ["eq", "isnull"]},
        )

    OptionalFilterModel = create_filter_model(OptionalScheduleOut)
    assert "end_time__eq" in OptionalFilterModel.model_fields
    assert "end_time__isnull" in OptionalFilterModel.model_fields

    instance = OptionalFilterModel(end_time__eq=time(17, 0, 0))
    assert instance.end_time__eq == time(17, 0, 0)


# ---------------------------------------------------------------------------
# Multiple filters at once
# ---------------------------------------------------------------------------


def test_time_multiple_filters_at_once() -> None:
    """Filter model should allow combining multiple time filters simultaneously."""
    data = {
        "start_time__gte": time(9, 0, 0),
        "start_time__lte": time(18, 0, 0),
        "start_time__ne": time(13, 0, 0),
    }
    instance = FilterModel(**data)
    assert instance.start_time__gte == time(9, 0, 0)
    assert instance.start_time__lte == time(18, 0, 0)
    assert instance.start_time__ne == time(13, 0, 0)


# ---------------------------------------------------------------------------
# FilterValues integration
# ---------------------------------------------------------------------------


def test_time_filter_values_dict_excludes_none() -> None:
    """FilterValues.dict() should only include fields that were explicitly set."""
    instance = FilterModel(**{"start_time__gte": time(9, 0, 0)})
    fv = FilterValues(instance)
    result = fv.dict()

    assert "start_time__gte" in result
    assert result["start_time__gte"] == time(9, 0, 0)
    assert "start_time__eq" not in result
    assert "start_time__in" not in result
