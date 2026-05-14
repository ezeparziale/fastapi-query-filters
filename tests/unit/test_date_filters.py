from datetime import date

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.dependencies import FilterValues


class EventOut(BaseModel):
    start_date: date = Field(
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


FilterModel = create_filter_model(EventOut)


# ---------------------------------------------------------------------------
# Generation tests
# ---------------------------------------------------------------------------


def test_date_eq_filter_generated() -> None:
    """date field with eq operator should generate the filter field."""
    assert "start_date__eq" in FilterModel.model_fields


def test_date_ne_filter_generated() -> None:
    """date field with ne operator should generate the filter field."""
    assert "start_date__ne" in FilterModel.model_fields


def test_date_gt_filter_generated() -> None:
    """date field with gt operator should generate the filter field."""
    assert "start_date__gt" in FilterModel.model_fields


def test_date_lt_filter_generated() -> None:
    """date field with lt operator should generate the filter field."""
    assert "start_date__lt" in FilterModel.model_fields


def test_date_gte_filter_generated() -> None:
    """date field with gte operator should generate the filter field."""
    assert "start_date__gte" in FilterModel.model_fields


def test_date_lte_filter_generated() -> None:
    """date field with lte operator should generate the filter field."""
    assert "start_date__lte" in FilterModel.model_fields


def test_date_in_filter_generated() -> None:
    """date field with in operator should generate the filter field."""
    assert "start_date__in" in FilterModel.model_fields


def test_date_not_in_filter_generated() -> None:
    """date field with not_in operator should generate the filter field."""
    assert "start_date__not_in" in FilterModel.model_fields


def test_date_isnull_filter_generated() -> None:
    """date field with isnull operator should generate the filter field."""
    assert "start_date__isnull" in FilterModel.model_fields


def test_date_not_isnull_filter_generated() -> None:
    """date field with not_isnull operator should generate the filter field."""
    assert "start_date__not_isnull" in FilterModel.model_fields


def test_date_between_filter_generated() -> None:
    """date field with between operator should generate the filter field."""
    assert "start_date__between" in FilterModel.model_fields


# ---------------------------------------------------------------------------
# Operators NOT available for date (must not be generated)
# ---------------------------------------------------------------------------


def test_date_like_operator_not_generated() -> None:
    """like operator should NOT be generated for date fields."""
    assert "start_date__like" not in FilterModel.model_fields


def test_date_ilike_operator_not_generated() -> None:
    """ilike operator should NOT be generated for date fields."""
    assert "start_date__ilike" not in FilterModel.model_fields


def test_date_icontains_operator_not_generated() -> None:
    """icontains operator should NOT be generated for date fields."""
    assert "start_date__icontains" not in FilterModel.model_fields


# ---------------------------------------------------------------------------
# eq — coercion and validation
# ---------------------------------------------------------------------------


def test_date_eq_accepts_date_object() -> None:
    """eq should accept a plain date object."""
    instance = FilterModel(**{"start_date__eq": date(2024, 1, 15)})
    assert instance.start_date__eq == date(2024, 1, 15)


def test_date_eq_accepts_iso_string() -> None:
    """eq should accept and parse an ISO 8601 date string."""
    instance = FilterModel(**{"start_date__eq": "2024-01-15"})
    assert instance.start_date__eq == date(2024, 1, 15)


def test_date_eq_accepts_min_date() -> None:
    """eq should accept the minimum date value."""
    instance = FilterModel(**{"start_date__eq": date.min})
    assert instance.start_date__eq == date.min


def test_date_eq_accepts_max_date() -> None:
    """eq should accept the maximum date value."""
    instance = FilterModel(**{"start_date__eq": date.max})
    assert instance.start_date__eq == date.max


def test_date_eq_rejects_invalid_string() -> None:
    """eq should reject strings that are not valid dates."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_date__eq": "not-a-date"})


def test_date_eq_rejects_partial_string() -> None:
    """eq should reject partial date strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_date__eq": "2024-01"})


def test_date_eq_rejects_empty_string() -> None:
    """eq should reject empty strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_date__eq": ""})


def test_date_eq_accepts_none() -> None:
    """eq set to None should be treated as not provided."""
    instance = FilterModel(**{"start_date__eq": None})
    assert instance.start_date__eq is None


# ---------------------------------------------------------------------------
# Comparison operators
# ---------------------------------------------------------------------------


def test_date_gt_accepts_date_object() -> None:
    """gt should accept a date object."""
    instance = FilterModel(**{"start_date__gt": date(2024, 6, 1)})
    assert instance.start_date__gt == date(2024, 6, 1)


def test_date_gt_accepts_iso_string() -> None:
    """gt should accept and parse an ISO 8601 date string."""
    instance = FilterModel(**{"start_date__gt": "2024-06-01"})
    assert instance.start_date__gt == date(2024, 6, 1)


def test_date_lt_accepts_date_object() -> None:
    """lt should accept a date object."""
    instance = FilterModel(**{"start_date__lt": date(2025, 12, 31)})
    assert instance.start_date__lt == date(2025, 12, 31)


def test_date_gte_accepts_iso_string() -> None:
    """gte should accept and parse an ISO 8601 date string."""
    instance = FilterModel(**{"start_date__gte": "2024-01-01"})
    assert instance.start_date__gte == date(2024, 1, 1)


def test_date_lte_accepts_date_object() -> None:
    """lte should accept a date object."""
    instance = FilterModel(**{"start_date__lte": date(2024, 12, 31)})
    assert instance.start_date__lte == date(2024, 12, 31)


def test_date_ne_accepts_iso_string() -> None:
    """ne should accept and parse an ISO 8601 date string."""
    instance = FilterModel(**{"start_date__ne": "2024-03-20"})
    assert instance.start_date__ne == date(2024, 3, 20)


# ---------------------------------------------------------------------------
# in / not_in
# ---------------------------------------------------------------------------


def test_date_in_accepts_list_of_dates() -> None:
    """in should accept a list of date objects."""
    dates = [date(2024, 1, 1), date(2024, 6, 1), date(2024, 12, 31)]
    instance = FilterModel(**{"start_date__in": dates})
    assert instance.start_date__in == dates


def test_date_in_accepts_comma_separated_string() -> None:
    """in should parse a comma-separated string of ISO dates into a list."""
    instance = FilterModel(**{"start_date__in": "2024-01-01,2024-06-01,2024-12-31"})
    assert instance.start_date__in == [
        date(2024, 1, 1),
        date(2024, 6, 1),
        date(2024, 12, 31),
    ]


def test_date_in_accepts_single_date_string() -> None:
    """in should accept a single ISO date string and wrap it in a list."""
    instance = FilterModel(**{"start_date__in": "2024-01-01"})
    assert instance.start_date__in == [date(2024, 1, 1)]


def test_date_in_rejects_list_with_invalid_strings() -> None:
    """in should reject lists containing invalid date strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_date__in": ["2024-01-01", "not-a-date"]})


def test_date_not_in_accepts_list_of_dates() -> None:
    """not_in should accept a list of date objects."""
    dates = [date(2024, 1, 1), date(2024, 6, 1)]
    instance = FilterModel(**{"start_date__not_in": dates})
    assert instance.start_date__not_in == dates


def test_date_not_in_accepts_comma_separated_string() -> None:
    """not_in should parse a comma-separated string of ISO dates into a list."""
    instance = FilterModel(**{"start_date__not_in": "2024-01-01,2024-06-01"})
    assert instance.start_date__not_in == [date(2024, 1, 1), date(2024, 6, 1)]


# ---------------------------------------------------------------------------
# isnull
# ---------------------------------------------------------------------------


def test_date_isnull_accepts_true() -> None:
    """isnull=True should filter for NULL values."""
    instance = FilterModel(**{"start_date__isnull": True})
    assert instance.start_date__isnull is True


def test_date_isnull_accepts_false() -> None:
    """isnull=False should filter for NOT NULL values."""
    instance = FilterModel(**{"start_date__isnull": False})
    assert instance.start_date__isnull is False


def test_date_isnull_accepts_string_true() -> None:
    """isnull should coerce string 'true' to True."""
    instance = FilterModel(**{"start_date__isnull": "true"})
    assert instance.start_date__isnull is True


def test_date_isnull_accepts_string_false() -> None:
    """isnull should coerce string 'false' to False."""
    instance = FilterModel(**{"start_date__isnull": "false"})
    assert instance.start_date__isnull is False


def test_date_isnull_accepts_string_1() -> None:
    """isnull should coerce string '1' to True."""
    instance = FilterModel(**{"start_date__isnull": "1"})
    assert instance.start_date__isnull is True


def test_date_isnull_accepts_string_0() -> None:
    """isnull should coerce string '0' to False."""
    instance = FilterModel(**{"start_date__isnull": "0"})
    assert instance.start_date__isnull is False


def test_date_isnull_accepts_int_1() -> None:
    """isnull should coerce integer 1 to True."""
    instance = FilterModel(**{"start_date__isnull": 1})
    assert instance.start_date__isnull is True


def test_date_isnull_accepts_int_0() -> None:
    """isnull should coerce integer 0 to False."""
    instance = FilterModel(**{"start_date__isnull": 0})
    assert instance.start_date__isnull is False


def test_date_isnull_rejects_arbitrary_string() -> None:
    """isnull should reject arbitrary strings that don't represent a boolean."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_date__isnull": "active"})


def test_date_isnull_rejects_integer_2() -> None:
    """isnull should reject integers other than 0 and 1."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_date__isnull": 2})


def test_date_isnull_accepts_none() -> None:
    """isnull set to None should be treated as not provided."""
    instance = FilterModel(**{"start_date__isnull": None})
    assert instance.start_date__isnull is None


# ---------------------------------------------------------------------------
# not_isnull
# ---------------------------------------------------------------------------


def test_date_not_isnull_accepts_true() -> None:
    """not_isnull=True should filter for NOT NULL values."""
    instance = FilterModel(**{"start_date__not_isnull": True})
    assert instance.start_date__not_isnull is True


def test_date_not_isnull_accepts_false() -> None:
    """not_isnull=False should filter for NULL values."""
    instance = FilterModel(**{"start_date__not_isnull": False})
    assert instance.start_date__not_isnull is False


def test_date_not_isnull_accepts_string_true() -> None:
    """not_isnull should coerce string 'true' to True."""
    instance = FilterModel(**{"start_date__not_isnull": "true"})
    assert instance.start_date__not_isnull is True


def test_date_not_isnull_accepts_string_false() -> None:
    """not_isnull should coerce string 'false' to False."""
    instance = FilterModel(**{"start_date__not_isnull": "false"})
    assert instance.start_date__not_isnull is False


def test_date_not_isnull_accepts_string_1() -> None:
    """not_isnull should coerce string '1' to True."""
    instance = FilterModel(**{"start_date__not_isnull": "1"})
    assert instance.start_date__not_isnull is True


def test_date_not_isnull_accepts_string_0() -> None:
    """not_isnull should coerce string '0' to False."""
    instance = FilterModel(**{"start_date__not_isnull": "0"})
    assert instance.start_date__not_isnull is False


def test_date_not_isnull_accepts_int_1() -> None:
    """not_isnull should coerce integer 1 to True."""
    instance = FilterModel(**{"start_date__not_isnull": 1})
    assert instance.start_date__not_isnull is True


def test_date_not_isnull_accepts_int_0() -> None:
    """not_isnull should coerce integer 0 to False."""
    instance = FilterModel(**{"start_date__not_isnull": 0})
    assert instance.start_date__not_isnull is False


def test_date_not_isnull_rejects_arbitrary_string() -> None:
    """not_isnull should reject arbitrary strings that don't represent a boolean."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_date__not_isnull": "active"})


def test_date_not_isnull_rejects_integer_2() -> None:
    """not_isnull should reject integers other than 0 and 1."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_date__not_isnull": 2})


def test_date_not_isnull_accepts_none() -> None:
    """not_isnull set to None should be treated as not provided."""
    instance = FilterModel(**{"start_date__not_isnull": None})
    assert instance.start_date__not_isnull is None


# ---------------------------------------------------------------------------
# between
# ---------------------------------------------------------------------------


def test_date_between_accepts_date_objects() -> None:
    """between should accept a list of two date objects."""
    dates = [date(2024, 1, 1), date(2024, 12, 31)]
    instance = FilterModel(**{"start_date__between": dates})
    assert instance.start_date__between == dates


def test_date_between_accepts_iso_strings() -> None:
    """between should parse a comma-separated string with two ISO dates."""
    instance = FilterModel(**{"start_date__between": "2024-01-01,2024-12-31"})
    assert instance.start_date__between == [date(2024, 1, 1), date(2024, 12, 31)]


def test_date_between_rejects_invalid_count() -> None:
    """between should reject lists that don't have exactly two elements."""
    with pytest.raises(ValidationError):
        FilterModel(**{"start_date__between": ["2024-01-01"]})


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


def test_date_filter_defaults_to_none() -> None:
    """All date filter fields should default to None when not provided."""
    instance = FilterModel()
    assert instance.start_date__eq is None
    assert instance.start_date__gt is None
    assert instance.start_date__in is None
    assert instance.start_date__isnull is None


# ---------------------------------------------------------------------------
# Optional date field
# ---------------------------------------------------------------------------


def test_date_optional_field_generates_filters() -> None:
    """Optional date fields should generate filters correctly."""

    class OptionalEventOut(BaseModel):
        end_date: date | None = Field(
            None,
            json_schema_extra={"filters": ["eq", "isnull"]},
        )

    OptionalFilterModel = create_filter_model(OptionalEventOut)
    assert "end_date__eq" in OptionalFilterModel.model_fields
    assert "end_date__isnull" in OptionalFilterModel.model_fields

    instance = OptionalFilterModel(end_date__eq=date(2024, 12, 31))
    assert instance.end_date__eq == date(2024, 12, 31)


# ---------------------------------------------------------------------------
# Multiple filters at once
# ---------------------------------------------------------------------------


def test_date_multiple_filters_at_once() -> None:
    """Filter model should allow combining multiple date filters simultaneously."""
    data = {
        "start_date__gte": date(2024, 1, 1),
        "start_date__lte": date(2024, 12, 31),
        "start_date__ne": date(2024, 6, 15),
    }
    instance = FilterModel(**data)
    assert instance.start_date__gte == date(2024, 1, 1)
    assert instance.start_date__lte == date(2024, 12, 31)
    assert instance.start_date__ne == date(2024, 6, 15)


# ---------------------------------------------------------------------------
# FilterValues integration
# ---------------------------------------------------------------------------


def test_date_filter_values_dict_excludes_none() -> None:
    """FilterValues.dict() should only include fields that were explicitly set."""
    instance = FilterModel(**{"start_date__gte": date(2024, 1, 1)})
    fv = FilterValues(instance)
    result = fv.dict()

    assert "start_date__gte" in result
    assert result["start_date__gte"] == date(2024, 1, 1)
    assert "start_date__eq" not in result
    assert "start_date__in" not in result
