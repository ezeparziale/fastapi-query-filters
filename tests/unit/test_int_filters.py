import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.dependencies import FilterValues


class UserOut(BaseModel):
    age: int = Field(
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


FilterModel = create_filter_model(UserOut)


# ---------------------------------------------------------------------------
# Generation tests
# ---------------------------------------------------------------------------


def test_int_eq_filter_generated() -> None:
    """int field with eq operator should generate the filter field."""
    assert "age__eq" in FilterModel.model_fields


def test_int_ne_filter_generated() -> None:
    """int field with ne operator should generate the filter field."""
    assert "age__ne" in FilterModel.model_fields


def test_int_gt_filter_generated() -> None:
    """int field with gt operator should generate the filter field."""
    assert "age__gt" in FilterModel.model_fields


def test_int_lt_filter_generated() -> None:
    """int field with lt operator should generate the filter field."""
    assert "age__lt" in FilterModel.model_fields


def test_int_gte_filter_generated() -> None:
    """int field with gte operator should generate the filter field."""
    assert "age__gte" in FilterModel.model_fields


def test_int_lte_filter_generated() -> None:
    """int field with lte operator should generate the filter field."""
    assert "age__lte" in FilterModel.model_fields


def test_int_in_filter_generated() -> None:
    """int field with in operator should generate the filter field."""
    assert "age__in" in FilterModel.model_fields


def test_int_not_in_filter_generated() -> None:
    """int field with not_in operator should generate the filter field."""
    assert "age__not_in" in FilterModel.model_fields


def test_int_isnull_filter_generated() -> None:
    """int field with isnull operator should generate the filter field."""
    assert "age__isnull" in FilterModel.model_fields


def test_int_not_isnull_filter_generated() -> None:
    """int field with not_isnull operator should generate the filter field."""
    assert "age__not_isnull" in FilterModel.model_fields


def test_int_between_filter_generated() -> None:
    """int field with between operator should generate the filter field."""
    assert "age__between" in FilterModel.model_fields


# ---------------------------------------------------------------------------
# Operators NOT available for int (must not be generated)
# ---------------------------------------------------------------------------


def test_int_like_operator_not_generated() -> None:
    """like operator should NOT be generated for int fields."""
    assert "age__like" not in FilterModel.model_fields


def test_int_ilike_operator_not_generated() -> None:
    """ilike operator should NOT be generated for int fields."""
    assert "age__ilike" not in FilterModel.model_fields


def test_int_icontains_operator_not_generated() -> None:
    """icontains operator should NOT be generated for int fields."""
    assert "age__icontains" not in FilterModel.model_fields


# ---------------------------------------------------------------------------
# eq — coercion and validation
# ---------------------------------------------------------------------------


def test_int_eq_accepts_integer() -> None:
    """eq should accept a plain integer value."""
    instance = FilterModel(**{"age__eq": 25})
    assert instance.age__eq == 25


def test_int_eq_accepts_zero() -> None:
    """eq should accept 0 as a valid value (not treated as falsy/None)."""
    instance = FilterModel(**{"age__eq": 0})
    assert instance.age__eq == 0
    assert "age__eq" in instance.model_fields_set


def test_int_eq_accepts_negative() -> None:
    """eq should accept negative integers."""
    instance = FilterModel(**{"age__eq": -10})
    assert instance.age__eq == -10


def test_int_eq_accepts_numeric_string() -> None:
    """eq should coerce numeric strings to int."""
    instance = FilterModel(**{"age__eq": "25"})
    assert instance.age__eq == 25


def test_int_eq_accepts_negative_numeric_string() -> None:
    """eq should coerce negative numeric strings to int."""
    instance = FilterModel(**{"age__eq": "-10"})
    assert instance.age__eq == -10


def test_int_eq_rejects_non_numeric_string() -> None:
    """eq should reject non-numeric strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__eq": "not_an_int"})


def test_int_eq_rejects_float_string() -> None:
    """eq should reject float strings — no implicit truncation."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__eq": "18.5"})


def test_int_eq_rejects_empty_string() -> None:
    """eq should reject empty strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__eq": ""})


def test_int_eq_accepts_float_with_zero_decimal() -> None:
    """eq should coerce float 1.0 to int 1 (Pydantic lax mode allows this)."""
    instance = FilterModel(**{"age__eq": 1.0})
    assert instance.age__eq == 1


def test_int_eq_rejects_float_with_decimal() -> None:
    """eq should reject floats with non-zero decimal part."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__eq": 18.5})


def test_int_eq_rejects_none_as_value() -> None:
    """eq set to None should be treated as not provided."""
    instance = FilterModel(**{"age__eq": None})
    assert instance.age__eq is None


# ---------------------------------------------------------------------------
# ne — same coercion rules as eq
# ---------------------------------------------------------------------------


def test_int_ne_accepts_integer() -> None:
    """ne should accept a plain integer value."""
    instance = FilterModel(**{"age__ne": 40})
    assert instance.age__ne == 40


def test_int_ne_accepts_zero() -> None:
    """ne should accept 0 as a valid value."""
    instance = FilterModel(**{"age__ne": 0})
    assert instance.age__ne == 0


def test_int_ne_accepts_negative() -> None:
    """ne should accept negative integers."""
    instance = FilterModel(**{"age__ne": -1})
    assert instance.age__ne == -1


def test_int_ne_accepts_numeric_string() -> None:
    """ne should coerce numeric strings to int."""
    instance = FilterModel(**{"age__ne": "40"})
    assert instance.age__ne == 40


def test_int_ne_rejects_non_numeric_string() -> None:
    """ne should reject non-numeric strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__ne": "forty"})


def test_int_ne_rejects_float_string() -> None:
    """ne should reject float strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__ne": "40.5"})


def test_int_ne_rejects_none_as_value() -> None:
    """ne set to None should be treated as not provided."""
    instance = FilterModel(**{"age__ne": None})
    assert instance.age__ne is None


# ---------------------------------------------------------------------------
# gt / lt / gte / lte — comparison operators
# ---------------------------------------------------------------------------


def test_int_gt_accepts_integer() -> None:
    """gt should accept a plain integer value."""
    instance = FilterModel(**{"age__gt": 18})
    assert instance.age__gt == 18


def test_int_lt_accepts_integer() -> None:
    """lt should accept a plain integer value."""
    instance = FilterModel(**{"age__lt": 65})
    assert instance.age__lt == 65


def test_int_gte_accepts_integer() -> None:
    """gte should accept a plain integer value."""
    instance = FilterModel(**{"age__gte": 18})
    assert instance.age__gte == 18


def test_int_lte_accepts_integer() -> None:
    """lte should accept a plain integer value."""
    instance = FilterModel(**{"age__lte": 65})
    assert instance.age__lte == 65


def test_int_gt_accepts_zero() -> None:
    """gt should accept 0 as a valid boundary value."""
    instance = FilterModel(**{"age__gt": 0})
    assert instance.age__gt == 0


def test_int_lt_accepts_negative() -> None:
    """lt should accept negative integers."""
    instance = FilterModel(**{"age__lt": -5})
    assert instance.age__lt == -5


def test_int_gte_accepts_numeric_string() -> None:
    """gte should coerce numeric strings to int."""
    instance = FilterModel(**{"age__gte": "18"})
    assert instance.age__gte == 18


def test_int_lte_rejects_float_string() -> None:
    """lte should reject float strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__lte": "65.5"})


def test_int_gt_rejects_non_numeric_string() -> None:
    """gt should reject non-numeric strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__gt": "old"})


# ---------------------------------------------------------------------------
# in / not_in — list membership
# ---------------------------------------------------------------------------


def test_int_in_accepts_list_of_integers() -> None:
    """in should accept a list of integers."""
    instance = FilterModel(**{"age__in": [18, 21, 25]})
    assert instance.age__in == [18, 21, 25]


def test_int_not_in_accepts_list_of_integers() -> None:
    """not_in should accept a list of integers."""
    instance = FilterModel(**{"age__not_in": [30, 40]})
    assert instance.age__not_in == [30, 40]


def test_int_in_accepts_single_element_list() -> None:
    """in should accept a single-element list."""
    instance = FilterModel(**{"age__in": [18]})
    assert instance.age__in == [18]


def test_int_in_accepts_empty_list() -> None:
    """in should accept an empty list (results in no matches, valid query)."""
    instance = FilterModel(**{"age__in": []})
    assert instance.age__in == []


def test_int_in_accepts_list_of_numeric_strings() -> None:
    """in should coerce a list of numeric strings to integers."""
    instance = FilterModel(**{"age__in": ["18", "21"]})
    assert instance.age__in == [18, 21]


def test_int_in_accepts_comma_separated_string() -> None:
    """in should parse a comma-separated string into a list via split_comma_values."""
    instance = FilterModel(**{"age__in": "10,20,30"})
    assert instance.age__in == [10, 20, 30]


def test_int_not_in_accepts_comma_separated_string() -> None:
    """not_in should parse a comma-separated string into a list."""
    instance = FilterModel(**{"age__not_in": "30,40"})
    assert instance.age__not_in == [30, 40]


def test_int_in_comma_separated_strips_spaces() -> None:
    """Comma-separated parsing should strip spaces around each element."""
    instance = FilterModel(**{"age__in": "10 , 20 , 30"})
    assert instance.age__in == [10, 20, 30]


def test_int_in_accepts_list_with_zero() -> None:
    """in should accept a list that includes 0."""
    instance = FilterModel(**{"age__in": [0, 1, 2]})
    assert instance.age__in == [0, 1, 2]


def test_int_in_accepts_list_with_negatives() -> None:
    """in should accept a list of negative integers."""
    instance = FilterModel(**{"age__in": [-3, -2, -1]})
    assert instance.age__in == [-3, -2, -1]


def test_int_in_accepts_list_with_duplicates() -> None:
    """in should accept lists with duplicate values without deduplication."""
    instance = FilterModel(**{"age__in": [18, 18, 21]})
    assert instance.age__in == [18, 18, 21]


def test_int_in_rejects_list_with_non_numeric_strings() -> None:
    """in should reject lists containing non-integer elements."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__in": [10, "abc", 30]})


def test_int_in_rejects_list_with_float_strings() -> None:
    """in should reject lists containing float strings."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__in": ["18.5", "21"]})


# ---------------------------------------------------------------------------
# isnull
# ---------------------------------------------------------------------------


def test_int_isnull_accepts_true() -> None:
    """isnull=True should filter for NULL values."""
    instance = FilterModel(**{"age__isnull": True})
    assert instance.age__isnull is True


def test_int_isnull_accepts_false() -> None:
    """isnull=False should filter for NOT NULL values."""
    instance = FilterModel(**{"age__isnull": False})
    assert instance.age__isnull is False


def test_int_isnull_accepts_string_true() -> None:
    """isnull should coerce string 'true' to True."""
    instance = FilterModel(**{"age__isnull": "true"})
    assert instance.age__isnull is True


def test_int_isnull_accepts_string_false() -> None:
    """isnull should coerce string 'false' to False."""
    instance = FilterModel(**{"age__isnull": "false"})
    assert instance.age__isnull is False


def test_int_isnull_accepts_string_1() -> None:
    """isnull should coerce string '1' to True."""
    instance = FilterModel(**{"age__isnull": "1"})
    assert instance.age__isnull is True


def test_int_isnull_accepts_string_0() -> None:
    """isnull should coerce string '0' to False."""
    instance = FilterModel(**{"age__isnull": "0"})
    assert instance.age__isnull is False


def test_int_isnull_accepts_int_1() -> None:
    """isnull should coerce integer 1 to True."""
    instance = FilterModel(**{"age__isnull": 1})
    assert instance.age__isnull is True


def test_int_isnull_accepts_int_0() -> None:
    """isnull should coerce integer 0 to False."""
    instance = FilterModel(**{"age__isnull": 0})
    assert instance.age__isnull is False


def test_int_isnull_accepts_string_yes() -> None:
    """isnull should coerce string 'yes' to True."""
    instance = FilterModel(**{"age__isnull": "yes"})
    assert instance.age__isnull is True


def test_int_isnull_accepts_string_no() -> None:
    """isnull should coerce string 'no' to False."""
    instance = FilterModel(**{"age__isnull": "no"})
    assert instance.age__isnull is False


def test_int_isnull_rejects_float_1() -> None:
    """isnull should reject float 1.0 — from HTTP it arrives as string '1.0' which is not a valid bool."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__isnull": "1.0"})


def test_int_isnull_rejects_float_1_1() -> None:
    """isnull should reject float 1.1 — not cleanly convertible to int."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__isnull": 1.1})


def test_int_isnull_rejects_integer_2() -> None:
    """isnull should reject integers other than 0 and 1."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__isnull": 2})


def test_int_isnull_rejects_negative_integer() -> None:
    """isnull should reject negative integers."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__isnull": -1})


def test_int_isnull_rejects_arbitrary_string() -> None:
    """isnull should reject arbitrary strings that don't represent a boolean."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__isnull": "active"})


def test_int_isnull_rejects_none_as_value() -> None:
    """isnull set to None should be treated as not provided."""
    instance = FilterModel(**{"age__isnull": None})
    assert instance.age__isnull is None


# ---------------------------------------------------------------------------
# not_isnull
# ---------------------------------------------------------------------------


def test_int_not_isnull_accepts_true() -> None:
    """not_isnull=True should filter for NOT NULL values."""
    instance = FilterModel(**{"age__not_isnull": True})
    assert instance.age__not_isnull is True


def test_int_not_isnull_accepts_false() -> None:
    """not_isnull=False should filter for NULL values."""
    instance = FilterModel(**{"age__not_isnull": False})
    assert instance.age__not_isnull is False


def test_int_not_isnull_accepts_string_true() -> None:
    """not_isnull should coerce string 'true' to True."""
    instance = FilterModel(**{"age__not_isnull": "true"})
    assert instance.age__not_isnull is True


def test_int_not_isnull_accepts_string_false() -> None:
    """not_isnull should coerce string 'false' to False."""
    instance = FilterModel(**{"age__not_isnull": "false"})
    assert instance.age__not_isnull is False


def test_int_not_isnull_accepts_string_1() -> None:
    """not_isnull should coerce string '1' to True."""
    instance = FilterModel(**{"age__not_isnull": "1"})
    assert instance.age__not_isnull is True


def test_int_not_isnull_accepts_string_0() -> None:
    """not_isnull should coerce string '0' to False."""
    instance = FilterModel(**{"age__not_isnull": "0"})
    assert instance.age__not_isnull is False


def test_int_not_isnull_accepts_int_1() -> None:
    """not_isnull should coerce integer 1 to True."""
    instance = FilterModel(**{"age__not_isnull": 1})
    assert instance.age__not_isnull is True


def test_int_not_isnull_accepts_int_0() -> None:
    """not_isnull should coerce integer 0 to False."""
    instance = FilterModel(**{"age__not_isnull": 0})
    assert instance.age__not_isnull is False


def test_int_not_isnull_accepts_string_yes() -> None:
    """not_isnull should coerce string 'yes' to True."""
    instance = FilterModel(**{"age__not_isnull": "yes"})
    assert instance.age__not_isnull is True


def test_int_not_isnull_accepts_string_no() -> None:
    """not_isnull should coerce string 'no' to False."""
    instance = FilterModel(**{"age__not_isnull": "no"})
    assert instance.age__not_isnull is False


def test_int_not_isnull_rejects_float_1() -> None:
    """not_isnull should reject float 1.0 — from HTTP it arrives as string '1.0' which is not a valid bool."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__not_isnull": "1.0"})


def test_int_not_isnull_rejects_float_1_1() -> None:
    """not_isnull should reject float 1.1 — not cleanly convertible to int."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__not_isnull": 1.1})


def test_int_not_isnull_rejects_integer_2() -> None:
    """not_isnull should reject integers other than 0 and 1."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__not_isnull": 2})


def test_int_not_isnull_rejects_negative_integer() -> None:
    """not_isnull should reject negative integers."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__not_isnull": -1})


def test_int_not_isnull_rejects_arbitrary_string() -> None:
    """not_isnull should reject arbitrary strings that don't represent a boolean."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__not_isnull": "active"})


def test_int_not_isnull_rejects_none_as_value() -> None:
    """not_isnull set to None should be treated as not provided."""
    instance = FilterModel(**{"age__not_isnull": None})
    assert instance.age__not_isnull is None


# ---------------------------------------------------------------------------
# between — range filtering (requires exactly 2 values)
# ---------------------------------------------------------------------------


def test_int_between_accepts_list_of_two_integers() -> None:
    """between should accept a list of exactly two integers."""
    instance = FilterModel(**{"age__between": [18, 65]})
    assert instance.age__between == [18, 65]


def test_int_between_accepts_comma_separated_string() -> None:
    """between should parse a comma-separated string with two values."""
    instance = FilterModel(**{"age__between": "18,65"})
    assert instance.age__between == [18, 65]


def test_int_between_accepts_comma_separated_string_in_list() -> None:
    """between should parse a list containing one comma-separated string (FastAPI style)."""
    instance = FilterModel(**{"age__between": ["18,65"]})
    assert instance.age__between == [18, 65]


def test_int_between_accepts_same_values() -> None:
    """between should accept two identical values (range of 1)."""
    instance = FilterModel(**{"age__between": [30, 30]})
    assert instance.age__between == [30, 30]


def test_int_between_accepts_inverse_order() -> None:
    """between should accept values in any order (ORM handles the range logic)."""
    instance = FilterModel(**{"age__between": [65, 18]})
    assert instance.age__between == [65, 18]


def test_int_between_rejects_single_value_list() -> None:
    """between should reject a list with only one value."""
    with pytest.raises(ValidationError, match="must have exactly two values"):
        FilterModel(**{"age__between": [18]})


def test_int_between_rejects_three_value_list() -> None:
    """between should reject a list with more than two values."""
    with pytest.raises(ValidationError, match="must have exactly two values"):
        FilterModel(**{"age__between": [18, 30, 65]})


def test_int_between_rejects_single_value_string() -> None:
    """between should reject a string without a comma (single value)."""
    with pytest.raises(ValidationError, match="must have exactly two values"):
        FilterModel(**{"age__between": "18"})


def test_int_between_rejects_three_value_string() -> None:
    """between should reject a string with more than one comma."""
    with pytest.raises(ValidationError, match="must have exactly two values"):
        FilterModel(**{"age__between": "18,30,65"})


def test_int_between_rejects_non_numeric_elements() -> None:
    """between elements must be valid integers."""
    with pytest.raises(ValidationError):
        FilterModel(**{"age__between": "18,abc"})


def test_int_between_rejects_single_integer_value() -> None:
    """between should reject a single integer value (triggers the non-list/non-str path)."""
    with pytest.raises(ValidationError, match="must have exactly two values"):
        FilterModel(**{"age__between": 10})


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


def test_int_filter_defaults_to_none() -> None:
    """All int filter fields should default to None when not provided."""
    instance = FilterModel()
    assert instance.age__eq is None
    assert instance.age__gt is None
    assert instance.age__in is None
    assert instance.age__isnull is None


# ---------------------------------------------------------------------------
# Optional int field
# ---------------------------------------------------------------------------


def test_int_optional_field_generates_filters() -> None:
    """Optional int fields should generate filters correctly."""

    class OptionalUserOut(BaseModel):
        score: int | None = Field(
            None,
            json_schema_extra={"filters": ["eq", "isnull"]},
        )

    OptionalFilterModel = create_filter_model(OptionalUserOut)
    assert "score__eq" in OptionalFilterModel.model_fields
    assert "score__isnull" in OptionalFilterModel.model_fields

    instance = OptionalFilterModel(score__eq=100)
    assert instance.score__eq == 100


# ---------------------------------------------------------------------------
# Selective operator exposure
# ---------------------------------------------------------------------------


def test_int_field_with_only_range_operators() -> None:
    """An int field configured with only range operators should not expose eq/in."""

    class RangeOut(BaseModel):
        price: int = Field(json_schema_extra={"filters": ["gte", "lte"]})

    RangeModel = create_filter_model(RangeOut)
    assert "price__gte" in RangeModel.model_fields
    assert "price__lte" in RangeModel.model_fields
    assert "price__eq" not in RangeModel.model_fields
    assert "price__in" not in RangeModel.model_fields


# ---------------------------------------------------------------------------
# Multiple filters at once
# ---------------------------------------------------------------------------


def test_int_multiple_filters_at_once() -> None:
    """Filter model should allow combining multiple int filters simultaneously."""
    data = {"age__gte": 18, "age__lte": 65, "age__ne": 40}
    instance = FilterModel(**data)
    assert instance.age__gte == 18
    assert instance.age__lte == 65
    assert instance.age__ne == 40


# ---------------------------------------------------------------------------
# FilterValues integration
# ---------------------------------------------------------------------------


def test_filter_values_dict_excludes_none() -> None:
    """FilterValues.dict() should only include fields that were explicitly set."""
    instance = FilterModel(**{"age__gte": 18})
    fv = FilterValues(instance)
    result = fv.dict()

    assert "age__gte" in result
    assert result["age__gte"] == 18
    assert "age__eq" not in result
    assert "age__in" not in result


def test_filter_values_dict_includes_zero() -> None:
    """FilterValues.dict() should include fields set to 0 (not falsy-excluded)."""
    instance = FilterModel(**{"age__eq": 0})
    fv = FilterValues(instance)
    result = fv.dict()

    assert "age__eq" in result
    assert result["age__eq"] == 0


def test_filter_values_dict_includes_empty_list() -> None:
    """FilterValues.dict() should include fields set to an empty list."""
    instance = FilterModel(**{"age__in": []})
    fv = FilterValues(instance)
    result = fv.dict()

    assert "age__in" in result
    assert result["age__in"] == []
