import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.dependencies import FilterValues


class UserOut(BaseModel):
    is_active: bool = Field(
        json_schema_extra={"filters": ["eq", "ne", "isnull", "not_isnull"]}
    )

    model_config = ConfigDict(from_attributes=True)


FilterModel = create_filter_model(UserOut)


# ---------------------------------------------------------------------------
# Generation tests
# ---------------------------------------------------------------------------


def test_bool_eq_filter_generated() -> None:
    """bool field with eq operator should generate the filter field."""
    assert "is_active__eq" in FilterModel.model_fields


def test_bool_ne_filter_generated() -> None:
    """bool field with ne operator should generate the filter field."""
    assert "is_active__ne" in FilterModel.model_fields


def test_bool_isnull_filter_generated() -> None:
    """bool field with isnull operator should generate the filter field."""
    assert "is_active__isnull" in FilterModel.model_fields


def test_bool_not_isnull_filter_generated() -> None:
    """bool field with not_isnull operator should generate the filter field."""
    assert "is_active__not_isnull" in FilterModel.model_fields


# ---------------------------------------------------------------------------
# Operators NOT available for bool (must not be generated)
# ---------------------------------------------------------------------------


def test_bool_gt_operator_not_generated() -> None:
    """gt operator should NOT be generated for bool fields."""
    assert "is_active__gt" not in FilterModel.model_fields


def test_bool_lt_operator_not_generated() -> None:
    """lt operator should NOT be generated for bool fields."""
    assert "is_active__lt" not in FilterModel.model_fields


def test_bool_gte_operator_not_generated() -> None:
    """gte operator should NOT be generated for bool fields."""
    assert "is_active__gte" not in FilterModel.model_fields


def test_bool_lte_operator_not_generated() -> None:
    """lte operator should NOT be generated for bool fields."""
    assert "is_active__lte" not in FilterModel.model_fields


def test_bool_like_operator_not_generated() -> None:
    """like operator should NOT be generated for bool fields."""
    assert "is_active__like" not in FilterModel.model_fields


def test_bool_ilike_operator_not_generated() -> None:
    """ilike operator should NOT be generated for bool fields."""
    assert "is_active__ilike" not in FilterModel.model_fields


def test_bool_icontains_operator_not_generated() -> None:
    """icontains operator should NOT be generated for bool fields."""
    assert "is_active__icontains" not in FilterModel.model_fields


def test_bool_in_operator_not_generated() -> None:
    """in operator should NOT be generated for bool fields."""
    assert "is_active__in" not in FilterModel.model_fields


def test_bool_not_in_operator_not_generated() -> None:
    """not_in operator should NOT be generated for bool fields."""
    assert "is_active__not_in" not in FilterModel.model_fields


# ---------------------------------------------------------------------------
# eq — coercion and validation
# ---------------------------------------------------------------------------


def test_bool_eq_accepts_true() -> None:
    """eq should accept boolean True."""
    instance = FilterModel(**{"is_active__eq": True})
    assert instance.is_active__eq is True


def test_bool_eq_accepts_false() -> None:
    """eq should accept boolean False."""
    instance = FilterModel(**{"is_active__eq": False})
    assert instance.is_active__eq is False


def test_bool_eq_accepts_int_1() -> None:
    """eq should coerce integer 1 to True."""
    instance = FilterModel(**{"is_active__eq": 1})
    assert instance.is_active__eq is True


def test_bool_eq_accepts_int_0() -> None:
    """eq should coerce integer 0 to False."""
    instance = FilterModel(**{"is_active__eq": 0})
    assert instance.is_active__eq is False


def test_bool_eq_accepts_string_true() -> None:
    """eq should coerce string 'true' to True."""
    instance = FilterModel(**{"is_active__eq": "true"})
    assert instance.is_active__eq is True


def test_bool_eq_accepts_string_false() -> None:
    """eq should coerce string 'false' to False."""
    instance = FilterModel(**{"is_active__eq": "false"})
    assert instance.is_active__eq is False


def test_bool_eq_accepts_string_1() -> None:
    """eq should coerce string '1' to True."""
    instance = FilterModel(**{"is_active__eq": "1"})
    assert instance.is_active__eq is True


def test_bool_eq_accepts_string_0() -> None:
    """eq should coerce string '0' to False."""
    instance = FilterModel(**{"is_active__eq": "0"})
    assert instance.is_active__eq is False


def test_bool_eq_accepts_string_yes() -> None:
    """eq should coerce string 'yes' to True."""
    instance = FilterModel(**{"is_active__eq": "yes"})
    assert instance.is_active__eq is True


def test_bool_eq_accepts_string_no() -> None:
    """eq should coerce string 'no' to False."""
    instance = FilterModel(**{"is_active__eq": "no"})
    assert instance.is_active__eq is False


def test_bool_eq_rejects_arbitrary_string() -> None:
    """eq should reject arbitrary strings that don't represent a boolean."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__eq": "active"})


def test_bool_eq_rejects_integer_2() -> None:
    """eq should reject integers other than 0 and 1."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__eq": 2})


def test_bool_eq_rejects_negative_integer() -> None:
    """eq should reject negative integers."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__eq": -1})


def test_bool_eq_rejects_float_1() -> None:
    """eq should reject float 1.0 — from HTTP it arrives as string '1.0' which is not a valid bool."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__eq": "1.0"})


def test_bool_eq_rejects_float_1_1() -> None:
    """eq should reject float 1.1 — not cleanly convertible to int."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__eq": 1.1})


def test_bool_eq_rejects_none_as_value() -> None:
    """eq set to None should be treated as not provided, not as False."""
    instance = FilterModel(**{"is_active__eq": None})
    assert instance.is_active__eq is None


# ---------------------------------------------------------------------------
# ne — same coercion rules as eq
# ---------------------------------------------------------------------------


def test_bool_ne_accepts_true() -> None:
    """ne should accept boolean True."""
    instance = FilterModel(**{"is_active__ne": True})
    assert instance.is_active__ne is True


def test_bool_ne_accepts_false() -> None:
    """ne should accept boolean False."""
    instance = FilterModel(**{"is_active__ne": False})
    assert instance.is_active__ne is False


def test_bool_ne_accepts_int_1() -> None:
    """ne should coerce integer 1 to True."""
    instance = FilterModel(**{"is_active__ne": 1})
    assert instance.is_active__ne is True


def test_bool_ne_accepts_int_0() -> None:
    """ne should coerce integer 0 to False."""
    instance = FilterModel(**{"is_active__ne": 0})
    assert instance.is_active__ne is False


def test_bool_ne_accepts_string_true() -> None:
    """ne should coerce string 'true' to True."""
    instance = FilterModel(**{"is_active__ne": "true"})
    assert instance.is_active__ne is True


def test_bool_ne_accepts_string_false() -> None:
    """ne should coerce string 'false' to False."""
    instance = FilterModel(**{"is_active__ne": "false"})
    assert instance.is_active__ne is False


def test_bool_ne_accepts_string_1() -> None:
    """ne should coerce string '1' to True."""
    instance = FilterModel(**{"is_active__ne": "1"})
    assert instance.is_active__ne is True


def test_bool_ne_accepts_string_0() -> None:
    """ne should coerce string '0' to False."""
    instance = FilterModel(**{"is_active__ne": "0"})
    assert instance.is_active__ne is False


def test_bool_ne_accepts_string_yes() -> None:
    """ne should coerce string 'yes' to True."""
    instance = FilterModel(**{"is_active__ne": "yes"})
    assert instance.is_active__ne is True


def test_bool_ne_accepts_string_no() -> None:
    """ne should coerce string 'no' to False."""
    instance = FilterModel(**{"is_active__ne": "no"})
    assert instance.is_active__ne is False


def test_bool_ne_rejects_arbitrary_string() -> None:
    """ne should reject arbitrary strings that don't represent a boolean."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__ne": "active"})


def test_bool_ne_rejects_integer_2() -> None:
    """ne should reject integers other than 0 and 1."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__ne": 2})


def test_bool_ne_rejects_negative_integer() -> None:
    """ne should reject negative integers."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__ne": -1})


def test_bool_ne_rejects_float_1() -> None:
    """ne should reject float 1.0 — from HTTP it arrives as string '1.0' which is not a valid bool."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__ne": "1.0"})


def test_bool_ne_rejects_float_1_1() -> None:
    """ne should reject float 1.1 — not cleanly convertible to int."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__ne": 1.1})


def test_bool_ne_rejects_none_as_value() -> None:
    """ne set to None should be treated as not provided, not as False."""
    instance = FilterModel(**{"is_active__ne": None})
    assert instance.is_active__ne is None


# ---------------------------------------------------------------------------
# isnull
# ---------------------------------------------------------------------------


def test_bool_isnull_accepts_true() -> None:
    """isnull=True should filter for NULL values."""
    instance = FilterModel(**{"is_active__isnull": True})
    assert instance.is_active__isnull is True


def test_bool_isnull_accepts_false() -> None:
    """isnull=False should filter for NOT NULL values."""
    instance = FilterModel(**{"is_active__isnull": False})
    assert instance.is_active__isnull is False


def test_bool_isnull_accepts_string_true() -> None:
    """isnull should coerce string 'true' to True."""
    instance = FilterModel(**{"is_active__isnull": "true"})
    assert instance.is_active__isnull is True


def test_bool_isnull_accepts_string_false() -> None:
    """isnull should coerce string 'false' to False."""
    instance = FilterModel(**{"is_active__isnull": "false"})
    assert instance.is_active__isnull is False


def test_bool_isnull_accepts_int_1() -> None:
    """isnull should coerce integer 1 to True."""
    instance = FilterModel(**{"is_active__isnull": 1})
    assert instance.is_active__isnull is True


def test_bool_isnull_accepts_int_0() -> None:
    """isnull should coerce integer 0 to False."""
    instance = FilterModel(**{"is_active__isnull": 0})
    assert instance.is_active__isnull is False


def test_bool_isnull_accepts_string_yes() -> None:
    """isnull should coerce string 'yes' to True."""
    instance = FilterModel(**{"is_active__isnull": "yes"})
    assert instance.is_active__isnull is True


def test_bool_isnull_accepts_string_no() -> None:
    """isnull should coerce string 'no' to False."""
    instance = FilterModel(**{"is_active__isnull": "no"})
    assert instance.is_active__isnull is False


def test_bool_isnull_accepts_string_1() -> None:
    """isnull should coerce string '1' to True."""
    instance = FilterModel(**{"is_active__isnull": "1"})
    assert instance.is_active__isnull is True


def test_bool_isnull_accepts_string_0() -> None:
    """isnull should coerce string '0' to False."""
    instance = FilterModel(**{"is_active__isnull": "0"})
    assert instance.is_active__isnull is False


def test_bool_isnull_rejects_float_1() -> None:
    """isnull should reject float 1.0 — from HTTP it arrives as string '1.0' which is not a valid bool."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__isnull": "1.0"})


def test_bool_isnull_rejects_float_1_1() -> None:
    """isnull should reject float 1.1 — not cleanly convertible to int."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__isnull": 1.1})


def test_bool_isnull_rejects_integer_2() -> None:
    """isnull should reject integers other than 0 and 1."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__isnull": 2})


def test_bool_isnull_rejects_negative_integer() -> None:
    """isnull should reject negative integers."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__isnull": -1})


def test_bool_isnull_rejects_arbitrary_string() -> None:
    """isnull should reject arbitrary strings that don't represent a boolean."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__isnull": "active"})


def test_bool_isnull_rejects_none_as_value() -> None:
    """isnull set to None should be treated as not provided."""
    instance = FilterModel(**{"is_active__isnull": None})
    assert instance.is_active__isnull is None


# ---------------------------------------------------------------------------
# not_isnull
# ---------------------------------------------------------------------------


def test_bool_not_isnull_accepts_true() -> None:
    """not_isnull=True should filter for NOT NULL values."""
    instance = FilterModel(**{"is_active__not_isnull": True})
    assert instance.is_active__not_isnull is True


def test_bool_not_isnull_accepts_false() -> None:
    """not_isnull=False should filter for NULL values."""
    instance = FilterModel(**{"is_active__not_isnull": False})
    assert instance.is_active__not_isnull is False


def test_bool_not_isnull_accepts_string_true() -> None:
    """not_isnull should coerce string 'true' to True."""
    instance = FilterModel(**{"is_active__not_isnull": "true"})
    assert instance.is_active__not_isnull is True


def test_bool_not_isnull_accepts_string_false() -> None:
    """not_isnull should coerce string 'false' to False."""
    instance = FilterModel(**{"is_active__not_isnull": "false"})
    assert instance.is_active__not_isnull is False


def test_bool_not_isnull_accepts_int_1() -> None:
    """not_isnull should coerce integer 1 to True."""
    instance = FilterModel(**{"is_active__not_isnull": 1})
    assert instance.is_active__not_isnull is True


def test_bool_not_isnull_accepts_int_0() -> None:
    """not_isnull should coerce integer 0 to False."""
    instance = FilterModel(**{"is_active__not_isnull": 0})
    assert instance.is_active__not_isnull is False


def test_bool_not_isnull_accepts_string_yes() -> None:
    """not_isnull should coerce string 'yes' to True."""
    instance = FilterModel(**{"is_active__not_isnull": "yes"})
    assert instance.is_active__not_isnull is True


def test_bool_not_isnull_accepts_string_no() -> None:
    """not_isnull should coerce string 'no' to False."""
    instance = FilterModel(**{"is_active__not_isnull": "no"})
    assert instance.is_active__not_isnull is False


def test_bool_not_isnull_accepts_string_1() -> None:
    """not_isnull should coerce string '1' to True."""
    instance = FilterModel(**{"is_active__not_isnull": "1"})
    assert instance.is_active__not_isnull is True


def test_bool_not_isnull_accepts_string_0() -> None:
    """not_isnull should coerce string '0' to False."""
    instance = FilterModel(**{"is_active__not_isnull": "0"})
    assert instance.is_active__not_isnull is False


def test_bool_not_isnull_rejects_float_1() -> None:
    """not_isnull should reject float 1.0 — from HTTP it arrives as string '1.0' which is not a valid bool."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__not_isnull": "1.0"})


def test_bool_not_isnull_rejects_float_1_1() -> None:
    """not_isnull should reject float 1.1 — not cleanly convertible to int."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__not_isnull": 1.1})


def test_bool_not_isnull_rejects_integer_2() -> None:
    """not_isnull should reject integers other than 0 and 1."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__not_isnull": 2})


def test_bool_not_isnull_rejects_negative_integer() -> None:
    """not_isnull should reject negative integers."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__not_isnull": -1})


def test_bool_not_isnull_rejects_arbitrary_string() -> None:
    """not_isnull should reject arbitrary strings that don't represent a boolean."""
    with pytest.raises(ValidationError):
        FilterModel(**{"is_active__not_isnull": "active"})


def test_bool_not_isnull_rejects_none_as_value() -> None:
    """not_isnull set to None should be treated as not provided."""
    instance = FilterModel(**{"is_active__not_isnull": None})
    assert instance.is_active__not_isnull is None


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


def test_bool_filter_defaults_to_none() -> None:
    """All bool filter fields should default to None when not provided."""
    instance = FilterModel()
    assert instance.is_active__eq is None
    assert instance.is_active__ne is None
    assert instance.is_active__isnull is None


# ---------------------------------------------------------------------------
# bool vs int — no cross-contamination
# ---------------------------------------------------------------------------


def test_bool_field_does_not_inherit_int_operators() -> None:
    """bool fields must not inherit int operators like gt/lt even via subclass."""

    class StatsOut(BaseModel):
        is_verified: bool = Field(
            json_schema_extra={"filters": ["eq", "ne", "gt", "lt", "isnull"]}
        )

    StrictModel = create_filter_model(StatsOut)

    # eq and ne are valid for bool
    assert "is_verified__eq" in StrictModel.model_fields
    assert "is_verified__ne" in StrictModel.model_fields

    # gt and lt are requested but NOT allowed for bool — must be silently dropped
    assert "is_verified__gt" not in StrictModel.model_fields
    assert "is_verified__lt" not in StrictModel.model_fields


# ---------------------------------------------------------------------------
# Optional bool field
# ---------------------------------------------------------------------------


def test_bool_optional_field_generates_filters() -> None:
    """Optional bool fields should generate filters correctly."""

    class ItemOut(BaseModel):
        is_published: bool | None = Field(
            None,
            json_schema_extra={"filters": ["eq", "isnull"]},
        )

    OptionalFilterModel = create_filter_model(ItemOut)
    assert "is_published__eq" in OptionalFilterModel.model_fields
    assert "is_published__isnull" in OptionalFilterModel.model_fields

    instance = OptionalFilterModel(**{"is_published__eq": True})
    assert instance.is_published__eq is True


# ---------------------------------------------------------------------------
# Multiple filters at once
# ---------------------------------------------------------------------------


def test_bool_multiple_filters_at_once() -> None:
    """Filter model should allow combining eq, ne and isnull simultaneously."""
    data = {
        "is_active__eq": True,
        "is_active__isnull": False,
    }
    instance = FilterModel(**data)
    assert instance.is_active__eq is True
    assert instance.is_active__isnull is False


# ---------------------------------------------------------------------------
# FilterValues integration
# ---------------------------------------------------------------------------


def test_filter_values_dict_excludes_none_for_bool() -> None:
    """FilterValues.dict() should exclude bool filter fields that are None."""
    instance = FilterModel(**{"is_active__eq": True})
    fv = FilterValues(instance)
    result = fv.dict()

    assert "is_active__eq" in result
    assert result["is_active__eq"] is True
    assert "is_active__ne" not in result
    assert "is_active__isnull" not in result


def test_filter_values_dict_includes_false() -> None:
    """FilterValues.dict() should include fields explicitly set to False (not None)."""
    instance = FilterModel(**{"is_active__eq": False})
    fv = FilterValues(instance)
    result = fv.dict()

    # False is a valid filter value — must NOT be excluded like None would be
    assert "is_active__eq" in result
    assert result["is_active__eq"] is False
