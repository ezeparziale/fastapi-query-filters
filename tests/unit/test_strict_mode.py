import pytest
from pydantic import BaseModel, Field, ValidationError

from fastapi_query_filters.core import create_filter_model


class SimpleSchema(BaseModel):
    name: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    age: int = Field(json_schema_extra={"filters": ["gte", "lte"]})


def test_strict_mode_disabled_by_default() -> None:
    """Verify that unknown parameters are ignored by default (strict=False)."""
    FilterModel = create_filter_model(SimpleSchema)

    # Should not raise error
    filters = FilterModel(
        name__eq="John", unknown_param="value", rogue_filter__eq="test"
    )
    assert filters.name__eq == "John"
    # Pydantic with extra='ignore' (default) won't have these in model_dump if they aren't fields
    data = filters.model_dump(exclude_none=True)
    assert "unknown_param" not in data
    assert "rogue_filter__eq" not in data


def test_total_strict_mode_enabled() -> None:
    """Verify that ANY unknown parameter raises an error when strict=True."""

    class StrictSchema(SimpleSchema):
        class FilterConfig:
            strict = True
            search_field = "q"
            sort_field = "sort"

    FilterModel = create_filter_model(StrictSchema)

    # Legitimate filters should pass
    filters = FilterModel(name__eq="John", q="search", sort="name")
    assert filters.name__eq == "John"

    # Unrelated parameter should fail
    with pytest.raises(ValidationError) as excinfo:
        FilterModel(name__eq="John", extra="forbidden")
    assert "Extra inputs are not permitted: extra" in str(excinfo.value)

    # Unknown filter should fail
    with pytest.raises(ValidationError) as excinfo:
        FilterModel(rogue__eq="value")
    assert "Extra inputs are not permitted: rogue__eq" in str(excinfo.value)


def test_strict_mode_with_prefix() -> None:
    """Verify that strict mode forbids unknown parameters even when a prefix is used."""

    class PrefixStrictSchema(SimpleSchema):
        class FilterConfig:
            prefix = "f_"
            strict = True

    FilterModel = create_filter_model(PrefixStrictSchema)

    # Legitimate prefixed filters should pass
    filters = FilterModel(f_name__eq="John")
    assert filters.f_name__eq == "John"

    # Prefixed unknown filter should fail
    with pytest.raises(ValidationError) as excinfo:
        FilterModel(f_unknown__eq="value")
    assert "Extra inputs are not permitted: f_unknown__eq" in str(excinfo.value)

    # Non-prefixed unknown parameter should also fail (Total Strict)
    with pytest.raises(ValidationError) as excinfo:
        FilterModel(page=1)
    assert "Extra inputs are not permitted: page" in str(excinfo.value)


def test_strict_mode_with_extra_filters() -> None:
    """Verify that fields in extra_filters are allowed in strict mode."""

    class ExtraFilters(BaseModel):
        virtual_field: str = Field(json_schema_extra={"filters": ["eq"]})

    class SchemaWithExtra(SimpleSchema):
        class FilterConfig:
            strict = True
            extra_filters = ExtraFilters

    FilterModel = create_filter_model(SchemaWithExtra)

    # Both standard and extra filters should pass
    assert FilterModel(name__eq="John", virtual_field__eq="test")

    # Truly unknown should still fail
    with pytest.raises(ValidationError):
        FilterModel(something_else=1)


def test_strict_mode_non_dict_data() -> None:
    """Verify that strict validator handles non-dict data gracefully (e.g. from model_validate)."""

    class StrictSchema(SimpleSchema):
        class FilterConfig:
            strict = True

    FilterModel = create_filter_model(StrictSchema)

    # Passing a non-dict should be handled by the validator (it just returns it,
    # then Pydantic will likely raise its own validation error because it expects fields)
    with pytest.raises(ValidationError):
        FilterModel.model_validate("not a dict")
