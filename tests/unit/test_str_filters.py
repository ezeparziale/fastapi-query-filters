from pydantic import BaseModel, ConfigDict, Field

from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.dependencies import FilterValues


class UserOut(BaseModel):
    name: str = Field(
        json_schema_extra={
            "filters": [
                "eq",
                "ne",
                "like",
                "ilike",
                "icontains",
                "contains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
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


def test_str_eq_filter_generated() -> None:
    """str field with eq operator should generate the filter field."""
    assert "name__eq" in FilterModel.model_fields


def test_str_ne_filter_generated() -> None:
    """str field with ne operator should generate the filter field."""
    assert "name__ne" in FilterModel.model_fields


def test_str_like_filter_generated() -> None:
    """str field with like operator should generate the filter field."""
    assert "name__like" in FilterModel.model_fields


def test_str_ilike_filter_generated() -> None:
    """str field with ilike operator should generate the filter field."""
    assert "name__ilike" in FilterModel.model_fields


def test_str_icontains_filter_generated() -> None:
    """str field with icontains operator should generate the filter field."""
    assert "name__icontains" in FilterModel.model_fields


def test_str_contains_filter_generated() -> None:
    """str field with contains operator should generate the filter field."""
    assert "name__contains" in FilterModel.model_fields


def test_str_startswith_filter_generated() -> None:
    """str field with startswith operator should generate the filter field."""
    assert "name__startswith" in FilterModel.model_fields


def test_str_istartswith_filter_generated() -> None:
    """str field with istartswith operator should generate the filter field."""
    assert "name__istartswith" in FilterModel.model_fields


def test_str_endswith_filter_generated() -> None:
    """str field with endswith operator should generate the filter field."""
    assert "name__endswith" in FilterModel.model_fields


def test_str_iendswith_filter_generated() -> None:
    """str field with iendswith operator should generate the filter field."""
    assert "name__iendswith" in FilterModel.model_fields


def test_str_in_filter_generated() -> None:
    """str field with in operator should generate the filter field."""
    assert "name__in" in FilterModel.model_fields


def test_str_not_in_filter_generated() -> None:
    """str field with not_in operator should generate the filter field."""
    assert "name__not_in" in FilterModel.model_fields


def test_str_isnull_filter_generated() -> None:
    """str field with isnull operator should generate the filter field."""
    assert "name__isnull" in FilterModel.model_fields


def test_str_not_isnull_filter_generated() -> None:
    """str field with not_isnull operator should generate the filter field."""
    assert "name__not_isnull" in FilterModel.model_fields


def test_str_between_filter_generated() -> None:
    """str field with between operator should generate the filter field."""
    assert "name__between" in FilterModel.model_fields


# ---------------------------------------------------------------------------
# eq / ne — basic equality
# ---------------------------------------------------------------------------


def test_str_eq_accepts_plain_string() -> None:
    """eq should accept a plain string value."""
    instance = FilterModel(**{"name__eq": "Alice"})
    assert instance.name__eq == "Alice"


def test_str_ne_accepts_plain_string() -> None:
    """ne should accept a plain string value."""
    instance = FilterModel(**{"name__ne": "Bob"})
    assert instance.name__ne == "Bob"


def test_str_eq_accepts_empty_string() -> None:
    """eq should accept an empty string (valid API use-case: filter by blank field)."""
    instance = FilterModel(**{"name__eq": ""})
    assert instance.name__eq == ""


def test_str_eq_accepts_whitespace_only_string() -> None:
    """eq should accept a whitespace-only string without stripping it."""
    instance = FilterModel(**{"name__eq": "   "})
    assert instance.name__eq == "   "


def test_str_eq_accepts_unicode() -> None:
    """eq should accept unicode characters (accents, CJK, emoji, etc.)."""
    instance = FilterModel(**{"name__eq": "Ñoño 日本語 🎉"})
    assert instance.name__eq == "Ñoño 日本語 🎉"


def test_str_eq_accepts_numeric_string() -> None:
    """eq should accept a string that looks like a number (e.g. zip codes)."""
    instance = FilterModel(**{"name__eq": "12345"})
    assert instance.name__eq == "12345"


def test_str_eq_accepts_string_with_special_chars() -> None:
    """eq should accept strings with special characters like quotes and slashes."""
    instance = FilterModel(**{"name__eq": 'O\'Brien & Co. / "Test"'})
    assert instance.name__eq == 'O\'Brien & Co. / "Test"'


def test_str_eq_accepts_very_long_string() -> None:
    """eq should accept very long strings (no length restriction at filter level)."""
    long_str = "a" * 10_000
    instance = FilterModel(**{"name__eq": long_str})
    assert instance.name__eq == long_str


def test_str_filter_defaults_to_none() -> None:
    """All str filter fields should default to None when not provided."""
    instance = FilterModel()
    assert instance.name__eq is None
    assert instance.name__ilike is None
    assert instance.name__in is None
    assert instance.name__isnull is None


# ---------------------------------------------------------------------------
# like / ilike / icontains — pattern matching
# ---------------------------------------------------------------------------


def test_str_like_accepts_wildcard_pattern() -> None:
    """like should accept SQL wildcard patterns."""
    instance = FilterModel(**{"name__like": "Ali%"})
    assert instance.name__like == "Ali%"


def test_str_like_accepts_underscore_wildcard() -> None:
    """like should accept SQL single-char wildcard (_)."""
    instance = FilterModel(**{"name__like": "A_ice"})
    assert instance.name__like == "A_ice"


def test_str_like_accepts_plain_string_no_wildcard() -> None:
    """like should accept plain strings without wildcards (exact match behavior)."""
    instance = FilterModel(**{"name__like": "Alice"})
    assert instance.name__like == "Alice"


def test_str_ilike_accepts_mixed_case_pattern() -> None:
    """ilike should accept patterns regardless of case."""
    instance = FilterModel(**{"name__ilike": "%ALICE%"})
    assert instance.name__ilike == "%ALICE%"


def test_str_ilike_accepts_empty_string() -> None:
    """ilike should accept an empty string pattern (matches everything)."""
    instance = FilterModel(**{"name__ilike": ""})
    assert instance.name__ilike == ""


def test_str_icontains_accepts_plain_string() -> None:
    """icontains should accept a plain substring (adapter wraps it in %)."""
    instance = FilterModel(**{"name__icontains": "ali"})
    assert instance.name__icontains == "ali"


def test_str_icontains_accepts_whitespace() -> None:
    """icontains should accept strings with internal whitespace."""
    instance = FilterModel(**{"name__icontains": "van der"})
    assert instance.name__icontains == "van der"


def test_str_icontains_accepts_unicode_substring() -> None:
    """icontains should handle unicode substrings correctly."""
    instance = FilterModel(**{"name__icontains": "日本"})
    assert instance.name__icontains == "日本"


def test_str_contains_accepts_plain_string() -> None:
    """contains should accept a plain string."""
    instance = FilterModel(**{"name__contains": "Ali"})
    assert instance.name__contains == "Ali"


def test_str_startswith_accepts_plain_string() -> None:
    """startswith should accept a plain string."""
    instance = FilterModel(**{"name__startswith": "John"})
    assert instance.name__startswith == "John"


def test_str_istartswith_accepts_plain_string() -> None:
    """istartswith should accept a plain string."""
    instance = FilterModel(**{"name__istartswith": "john"})
    assert instance.name__istartswith == "john"


def test_str_endswith_accepts_plain_string() -> None:
    """endswith should accept a plain string."""
    instance = FilterModel(**{"name__endswith": "Doe"})
    assert instance.name__endswith == "Doe"


def test_str_iendswith_accepts_plain_string() -> None:
    """iendswith should accept a plain string."""
    instance = FilterModel(**{"name__iendswith": "doe"})
    assert instance.name__iendswith == "doe"


# ---------------------------------------------------------------------------
# in / not_in — list membership
# ---------------------------------------------------------------------------


def test_str_in_accepts_list_of_strings() -> None:
    """in should accept a list of strings."""
    instance = FilterModel(**{"name__in": ["Alice", "Bob", "Charlie"]})
    assert instance.name__in == ["Alice", "Bob", "Charlie"]


def test_str_not_in_accepts_list_of_strings() -> None:
    """not_in should accept a list of strings."""
    instance = FilterModel(**{"name__not_in": ["Alice", "Bob"]})
    assert instance.name__not_in == ["Alice", "Bob"]


def test_str_in_accepts_single_element_list() -> None:
    """in should accept a single-element list."""
    instance = FilterModel(**{"name__in": ["Alice"]})
    assert instance.name__in == ["Alice"]


def test_str_in_accepts_empty_list() -> None:
    """in should accept an empty list (results in no matches, valid query)."""
    instance = FilterModel(**{"name__in": []})
    assert instance.name__in == []


def test_str_in_accepts_comma_separated_string() -> None:
    """in should parse a comma-separated string into a list via split_comma_values."""
    instance = FilterModel(**{"name__in": "Alice,Bob,Charlie"})
    assert instance.name__in == ["Alice", "Bob", "Charlie"]


def test_str_not_in_accepts_comma_separated_string() -> None:
    """not_in should parse a comma-separated string into a list."""
    instance = FilterModel(**{"name__not_in": "Alice,Bob"})
    assert instance.name__not_in == ["Alice", "Bob"]


def test_str_in_comma_separated_preserves_spaces() -> None:
    """Comma-separated parsing strips leading/trailing spaces per element."""
    instance = FilterModel(**{"name__in": "Alice , Bob , Charlie"})
    assert instance.name__in == ["Alice", "Bob", "Charlie"]


def test_str_in_accepts_list_with_empty_string_element() -> None:
    """in should accept a list that contains an empty string."""
    instance = FilterModel(**{"name__in": ["Alice", ""]})
    assert instance.name__in == ["Alice", ""]


def test_str_in_accepts_list_with_unicode_elements() -> None:
    """in should accept a list of unicode strings."""
    instance = FilterModel(**{"name__in": ["Ñoño", "日本語", "🎉"]})
    assert instance.name__in == ["Ñoño", "日本語", "🎉"]


def test_str_in_accepts_list_with_duplicate_values() -> None:
    """in should accept lists with duplicate values without deduplication."""
    instance = FilterModel(**{"name__in": ["Alice", "Alice", "Bob"]})
    assert instance.name__in == ["Alice", "Alice", "Bob"]


# ---------------------------------------------------------------------------
# isnull
# ---------------------------------------------------------------------------


def test_str_isnull_accepts_true() -> None:
    """isnull=True should filter for NULL values."""
    instance = FilterModel(**{"name__isnull": True})
    assert instance.name__isnull is True


def test_str_isnull_accepts_false() -> None:
    """isnull=False should filter for NOT NULL values."""
    instance = FilterModel(**{"name__isnull": False})
    assert instance.name__isnull is False


def test_str_isnull_accepts_string_true() -> None:
    """isnull should coerce string 'true' to True."""
    instance = FilterModel(**{"name__isnull": "true"})
    assert instance.name__isnull is True


def test_str_isnull_accepts_string_false() -> None:
    """isnull should coerce string 'false' to False."""
    instance = FilterModel(**{"name__isnull": "false"})
    assert instance.name__isnull is False


def test_str_isnull_accepts_int_1() -> None:
    """isnull should coerce integer 1 to True."""
    instance = FilterModel(**{"name__isnull": 1})
    assert instance.name__isnull is True


def test_str_isnull_accepts_int_0() -> None:
    """isnull should coerce integer 0 to False."""
    instance = FilterModel(**{"name__isnull": 0})
    assert instance.name__isnull is False


def test_str_isnull_accepts_string_yes() -> None:
    """isnull should coerce string 'yes' to True."""
    instance = FilterModel(**{"name__isnull": "yes"})
    assert instance.name__isnull is True


def test_str_isnull_accepts_string_no() -> None:
    """isnull should coerce string 'no' to False."""
    instance = FilterModel(**{"name__isnull": "no"})
    assert instance.name__isnull is False


# ---------------------------------------------------------------------------
# not_isnull
# ---------------------------------------------------------------------------


def test_str_not_isnull_accepts_true() -> None:
    """not_isnull=True should filter for NOT NULL values."""
    instance = FilterModel(**{"name__not_isnull": True})
    assert instance.name__not_isnull is True


def test_str_not_isnull_accepts_false() -> None:
    """not_isnull=False should filter for NULL values."""
    instance = FilterModel(**{"name__not_isnull": False})
    assert instance.name__not_isnull is False


def test_str_not_isnull_accepts_string_true() -> None:
    """not_isnull should coerce string 'true' to True."""
    instance = FilterModel(**{"name__not_isnull": "true"})
    assert instance.name__not_isnull is True


def test_str_not_isnull_accepts_string_false() -> None:
    """not_isnull should coerce string 'false' to False."""
    instance = FilterModel(**{"name__not_isnull": "false"})
    assert instance.name__not_isnull is False


def test_str_not_isnull_accepts_int_1() -> None:
    """not_isnull should coerce integer 1 to True."""
    instance = FilterModel(**{"name__not_isnull": 1})
    assert instance.name__not_isnull is True


def test_str_not_isnull_accepts_int_0() -> None:
    """not_isnull should coerce integer 0 to False."""
    instance = FilterModel(**{"name__not_isnull": 0})
    assert instance.name__not_isnull is False


def test_str_not_isnull_accepts_string_yes() -> None:
    """not_isnull should coerce string 'yes' to True."""
    instance = FilterModel(**{"name__not_isnull": "yes"})
    assert instance.name__not_isnull is True


def test_str_not_isnull_accepts_string_no() -> None:
    """not_isnull should coerce string 'no' to False."""
    instance = FilterModel(**{"name__not_isnull": "no"})
    assert instance.name__not_isnull is False


# ---------------------------------------------------------------------------
# between — lexicographical comparison
# ---------------------------------------------------------------------------


def test_str_between_accepts_strings() -> None:
    """between should accept a list of two strings."""
    instance = FilterModel(**{"name__between": ["A", "M"]})
    assert instance.name__between == ["A", "M"]


def test_str_between_accepts_comma_separated_string() -> None:
    """between should parse a comma-separated string with two strings."""
    instance = FilterModel(**{"name__between": "Alice,Bob"})
    assert instance.name__between == ["Alice", "Bob"]


def test_str_between_rejects_invalid_count() -> None:
    """between should reject lists that don't have exactly two elements."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        FilterModel(**{"name__between": ["Alice"]})


# ---------------------------------------------------------------------------
# Operators NOT available for str (must not be generated)
# ---------------------------------------------------------------------------


def test_str_gt_operator_not_generated() -> None:
    """gt operator should NOT be generated for str fields."""
    assert "name__gt" not in FilterModel.model_fields


def test_str_lt_operator_not_generated() -> None:
    """lt operator should NOT be generated for str fields."""
    assert "name__lt" not in FilterModel.model_fields


def test_str_gte_operator_not_generated() -> None:
    """gte operator should NOT be generated for str fields."""
    assert "name__gte" not in FilterModel.model_fields


def test_str_lte_operator_not_generated() -> None:
    """lte operator should NOT be generated for str fields."""
    assert "name__lte" not in FilterModel.model_fields


# ---------------------------------------------------------------------------
# Optional str field
# ---------------------------------------------------------------------------


def test_str_optional_field_generates_filters() -> None:
    """Optional str fields should generate filters correctly."""

    class ProductOut(BaseModel):
        description: str | None = Field(
            None,
            json_schema_extra={"filters": ["eq", "icontains", "isnull"]},
        )

    OptionalFilterModel = create_filter_model(ProductOut)
    assert "description__eq" in OptionalFilterModel.model_fields
    assert "description__icontains" in OptionalFilterModel.model_fields
    assert "description__isnull" in OptionalFilterModel.model_fields

    instance = OptionalFilterModel(**{"description__icontains": "test"})
    assert instance.description__icontains == "test"


# ---------------------------------------------------------------------------
# Multiple filters at once
# ---------------------------------------------------------------------------


def test_str_multiple_filters_at_once() -> None:
    """Filter model should allow combining multiple str filters simultaneously."""
    data = {
        "name__icontains": "ali",
        "name__ne": "Alice Smith",
        "name__isnull": False,
    }
    instance = FilterModel(**data)
    assert instance.name__icontains == "ali"
    assert instance.name__ne == "Alice Smith"
    assert instance.name__isnull is False


# ---------------------------------------------------------------------------
# FilterValues integration
# ---------------------------------------------------------------------------


def test_filter_values_dict_excludes_none_for_str() -> None:
    """FilterValues.dict() should exclude str filter fields that are None."""
    instance = FilterModel(**{"name__ilike": "%alice%"})
    fv = FilterValues(instance)
    result = fv.dict()

    assert "name__ilike" in result
    assert result["name__ilike"] == "%alice%"
    assert "name__eq" not in result
    assert "name__in" not in result


def test_filter_values_dict_includes_empty_string() -> None:
    """FilterValues.dict() should include fields set to empty string (not None)."""
    instance = FilterModel(**{"name__eq": ""})
    fv = FilterValues(instance)
    result = fv.dict()

    # Empty string is a valid filter value — should NOT be excluded
    assert "name__eq" in result
    assert result["name__eq"] == ""


def test_filter_values_dict_includes_empty_list() -> None:
    """FilterValues.dict() should include fields set to an empty list."""
    instance = FilterModel(**{"name__in": []})
    fv = FilterValues(instance)
    result = fv.dict()

    assert "name__in" in result
    assert result["name__in"] == []


# ---------------------------------------------------------------------------
# Selective operator exposure
# ---------------------------------------------------------------------------


def test_str_field_with_only_eq_operator() -> None:
    """A str field configured with only eq should not expose other operators."""

    class StrictOut(BaseModel):
        status: str = Field(json_schema_extra={"filters": ["eq"]})

    StrictModel = create_filter_model(StrictOut)
    assert "status__eq" in StrictModel.model_fields
    assert "status__ilike" not in StrictModel.model_fields
    assert "status__in" not in StrictModel.model_fields
    assert "status__icontains" not in StrictModel.model_fields


def test_str_field_with_only_search_operators() -> None:
    """A str field configured with only search operators should not expose eq/in."""

    class SearchOut(BaseModel):
        title: str = Field(
            json_schema_extra={"filters": ["like", "ilike", "icontains"]}
        )

    SearchModel = create_filter_model(SearchOut)
    assert "title__like" in SearchModel.model_fields
    assert "title__ilike" in SearchModel.model_fields
    assert "title__icontains" in SearchModel.model_fields
    assert "title__eq" not in SearchModel.model_fields
    assert "title__in" not in SearchModel.model_fields
