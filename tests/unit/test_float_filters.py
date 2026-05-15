import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.dependencies import FilterValues


class UserOut(BaseModel):
    score: float = Field(
        json_schema_extra={
            "filters": [
                "eq",
                "ne",
                "gt",
                "lt",
                "gte",
                "lte",
                "isnull",
                "not_isnull",
                "between",
            ]
        }
    )

    model_config = ConfigDict(from_attributes=True)


FilterModel = create_filter_model(UserOut)


# ---------------------------------------------------------------------------
# Generation tests
# ---------------------------------------------------------------------------


def test_float_eq_filter_generated() -> None:
    """float field with eq operator should generate the filter field."""
    assert "score__eq" in FilterModel.model_fields


def test_float_ne_filter_generated() -> None:
    """float field with ne operator should generate the filter field."""
    assert "score__ne" in FilterModel.model_fields


def test_float_gt_filter_generated() -> None:
    """float field with gt operator should generate the filter field."""
    assert "score__gt" in FilterModel.model_fields


def test_float_lt_filter_generated() -> None:
    """float field with lt operator should generate the filter field."""
    assert "score__lt" in FilterModel.model_fields


def test_float_gte_filter_generated() -> None:
    """float field with gte operator should generate the filter field."""
    assert "score__gte" in FilterModel.model_fields


def test_float_lte_filter_generated() -> None:
    """float field with lte operator should generate the filter field."""
    assert "score__lte" in FilterModel.model_fields


def test_float_isnull_filter_generated() -> None:
    """float field with isnull operator should generate the filter field."""
    assert "score__isnull" in FilterModel.model_fields


def test_float_not_isnull_filter_generated() -> None:
    """float field with not_isnull operator should generate the filter field."""
    assert "score__not_isnull" in FilterModel.model_fields


def test_float_between_filter_generated() -> None:
    """float field with between operator should generate the filter field."""
    assert "score__between" in FilterModel.model_fields


# ---------------------------------------------------------------------------
# Operators NOT available for float by default (must not be generated)
# ---------------------------------------------------------------------------


def test_float_in_operator_not_generated_by_default() -> None:
    """in operator should NOT be generated for float fields by default."""
    assert "score__in" not in FilterModel.model_fields


def test_float_like_operator_not_generated() -> None:
    """like operator should NOT be generated for float fields."""
    assert "score__like" not in FilterModel.model_fields


# ---------------------------------------------------------------------------
# eq — coercion and validation
# ---------------------------------------------------------------------------


def test_float_eq_accepts_float() -> None:
    """eq should accept a plain float value."""
    instance = FilterModel(**{"score__eq": 3.14})
    assert instance.score__eq == 3.14


def test_float_eq_accepts_integer() -> None:
    """eq should accept an integer and coerce it to float."""
    instance = FilterModel(**{"score__eq": 10})
    assert instance.score__eq == 10.0


def test_float_eq_accepts_numeric_string() -> None:
    """eq should coerce numeric strings to float."""
    instance = FilterModel(**{"score__eq": "99.5"})
    assert instance.score__eq == 99.5


def test_float_eq_accepts_integer_string() -> None:
    """eq should coerce integer strings to float."""
    instance = FilterModel(**{"score__eq": "100"})
    assert instance.score__eq == 100.0


def test_float_eq_rejects_non_numeric_string() -> None:
    """eq should reject non-numeric strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"score__eq": "not_a_number"})


def test_float_eq_rejects_empty_string() -> None:
    """eq should reject empty strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"score__eq": ""})


# ---------------------------------------------------------------------------
# Comparison operators
# ---------------------------------------------------------------------------


def test_float_gt_accepts_float() -> None:
    """gt should accept a float value."""
    instance = FilterModel(**{"score__gt": 10.5})
    assert instance.score__gt == 10.5


def test_float_lt_accepts_integer_string() -> None:
    """lt should coerce integer string to float."""
    instance = FilterModel(**{"score__lt": "20"})
    assert instance.score__lt == 20.0


# ---------------------------------------------------------------------------
# isnull
# ---------------------------------------------------------------------------


def test_float_isnull_accepts_true() -> None:
    """isnull=True should filter for NULL values."""
    instance = FilterModel(**{"score__isnull": True})
    assert instance.score__isnull is True


def test_float_isnull_accepts_false() -> None:
    """isnull=False should filter for NOT NULL values."""
    instance = FilterModel(**{"score__isnull": False})
    assert instance.score__isnull is False


def test_float_isnull_accepts_string_true() -> None:
    """isnull should coerce string 'true' to True."""
    instance = FilterModel(**{"score__isnull": "true"})
    assert instance.score__isnull is True


def test_float_isnull_accepts_string_false() -> None:
    """isnull should coerce string 'false' to False."""
    instance = FilterModel(**{"score__isnull": "false"})
    assert instance.score__isnull is False


def test_float_isnull_accepts_string_1() -> None:
    """isnull should coerce string '1' to True."""
    instance = FilterModel(**{"score__isnull": "1"})
    assert instance.score__isnull is True


def test_float_isnull_accepts_string_0() -> None:
    """isnull should coerce string '0' to False."""
    instance = FilterModel(**{"score__isnull": "0"})
    assert instance.score__isnull is False


def test_float_isnull_accepts_int_1() -> None:
    """isnull should coerce integer 1 to True."""
    instance = FilterModel(**{"score__isnull": 1})
    assert instance.score__isnull is True


def test_float_isnull_accepts_int_0() -> None:
    """isnull should coerce integer 0 to False."""
    instance = FilterModel(**{"score__isnull": 0})
    assert instance.score__isnull is False


def test_float_isnull_rejects_arbitrary_string() -> None:
    """isnull should reject arbitrary strings that don't represent a boolean."""
    with pytest.raises(ValidationError):
        FilterModel(**{"score__isnull": "active"})


def test_float_isnull_rejects_integer_2() -> None:
    """isnull should reject integers other than 0 and 1."""
    with pytest.raises(ValidationError):
        FilterModel(**{"score__isnull": 2})


def test_float_isnull_accepts_none() -> None:
    """isnull set to None should be treated as not provided."""
    instance = FilterModel(**{"score__isnull": None})
    assert instance.score__isnull is None


# ---------------------------------------------------------------------------
# not_isnull
# ---------------------------------------------------------------------------


def test_float_not_isnull_accepts_true() -> None:
    """not_isnull=True should filter for NOT NULL values."""
    instance = FilterModel(**{"score__not_isnull": True})
    assert instance.score__not_isnull is True


def test_float_not_isnull_accepts_false() -> None:
    """not_isnull=False should filter for NULL values."""
    instance = FilterModel(**{"score__not_isnull": False})
    assert instance.score__not_isnull is False


def test_float_not_isnull_accepts_string_true() -> None:
    """not_isnull should coerce string 'true' to True."""
    instance = FilterModel(**{"score__not_isnull": "true"})
    assert instance.score__not_isnull is True


def test_float_not_isnull_accepts_string_false() -> None:
    """not_isnull should coerce string 'false' to False."""
    instance = FilterModel(**{"score__not_isnull": "false"})
    assert instance.score__not_isnull is False


def test_float_not_isnull_accepts_string_1() -> None:
    """not_isnull should coerce string '1' to True."""
    instance = FilterModel(**{"score__not_isnull": "1"})
    assert instance.score__not_isnull is True


def test_float_not_isnull_accepts_string_0() -> None:
    """not_isnull should coerce string '0' to False."""
    instance = FilterModel(**{"score__not_isnull": "0"})
    assert instance.score__not_isnull is False


def test_float_not_isnull_accepts_int_1() -> None:
    """not_isnull should coerce integer 1 to True."""
    instance = FilterModel(**{"score__not_isnull": 1})
    assert instance.score__not_isnull is True


def test_float_not_isnull_accepts_int_0() -> None:
    """not_isnull should coerce integer 0 to False."""
    instance = FilterModel(**{"score__not_isnull": 0})
    assert instance.score__not_isnull is False


def test_float_not_isnull_rejects_arbitrary_string() -> None:
    """not_isnull should reject arbitrary strings that don't represent a boolean."""
    with pytest.raises(ValidationError):
        FilterModel(**{"score__not_isnull": "active"})


def test_float_not_isnull_rejects_integer_2() -> None:
    """not_isnull should reject integers other than 0 and 1."""
    with pytest.raises(ValidationError):
        FilterModel(**{"score__not_isnull": 2})


def test_float_not_isnull_accepts_none() -> None:
    """not_isnull set to None should be treated as not provided."""
    instance = FilterModel(**{"score__not_isnull": None})
    assert instance.score__not_isnull is None


# ---------------------------------------------------------------------------
# between
# ---------------------------------------------------------------------------


def test_float_between_accepts_floats() -> None:
    """between should accept a list of two floats."""
    instance = FilterModel(**{"score__between": [1.5, 9.9]})
    assert instance.score__between == [1.5, 9.9]


def test_float_between_accepts_comma_separated_string() -> None:
    """between should parse a comma-separated string with two floats."""
    instance = FilterModel(**{"score__between": "0.5,1.5"})
    assert instance.score__between == [0.5, 1.5]


def test_float_between_rejects_invalid_count() -> None:
    """between should reject lists that don't have exactly two elements."""
    with pytest.raises(ValidationError):
        FilterModel(**{"score__between": [1.0, 2.0, 3.0]})


# ---------------------------------------------------------------------------
# FilterValues integration
# ---------------------------------------------------------------------------


def test_float_filter_values_dict_excludes_none() -> None:
    """FilterValues.dict() should only include fields that were set."""
    instance = FilterModel(**{"score__gte": 5.0})
    fv = FilterValues(instance)
    result = fv.dict()

    assert "score__gte" in result
    assert result["score__gte"] == 5.0
    assert "score__eq" not in result
