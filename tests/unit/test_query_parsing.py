import logging
from datetime import datetime

import pytest

from fastapi_query_filters.core import FilterBase, create_filter_model
from tests.schemas import PostOut

logging.basicConfig(level=logging.INFO)


def test_parse_datetime() -> None:
    """Test parsing of datetime strings in query parameters."""
    FilterModel = create_filter_model(PostOut)

    # ISO format
    dt_str = "2024-01-01T12:00:00"
    m = FilterModel(f_created_at__gte=dt_str)
    logging.info(f"Parsed datetime: {m.f_created_at__gte}")
    assert isinstance(m.f_created_at__gte, datetime)
    assert m.f_created_at__gte == datetime(2024, 1, 1, 12, 0, 0)


def test_parse_boolean_isnull() -> None:
    """Test parsing of boolean values, specifically for isnull operator."""
    FilterModel = create_filter_model(PostOut)

    # True variants
    assert (
        FilterModel(f_author__profile_bio__isnull="true").f_author__profile_bio__isnull
        is True
    )
    assert (
        FilterModel(f_author__profile_bio__isnull="1").f_author__profile_bio__isnull
        is True
    )
    assert (
        FilterModel(f_author__profile_bio__isnull=1).f_author__profile_bio__isnull
        is True
    )
    assert (
        FilterModel(f_author__profile_bio__isnull=True).f_author__profile_bio__isnull
        is True
    )

    # False variants
    assert (
        FilterModel(f_author__profile_bio__isnull="false").f_author__profile_bio__isnull
        is False
    )
    assert (
        FilterModel(f_author__profile_bio__isnull="0").f_author__profile_bio__isnull
        is False
    )
    assert (
        FilterModel(f_author__profile_bio__isnull=0).f_author__profile_bio__isnull
        is False
    )
    assert (
        FilterModel(f_author__profile_bio__isnull=False).f_author__profile_bio__isnull
        is False
    )


def test_parse_list_integers() -> None:
    """Test that comma-separated strings are correctly converted to lists of the appropriate type."""
    FilterModel = create_filter_model(PostOut)

    # Multiple integers
    m = FilterModel(f_id__in="1,2,3")
    logging.info(f"Parsed list of ints: {m.f_id__in}")
    assert m.f_id__in == [1, 2, 3]

    # Single integer
    m2 = FilterModel(f_id__in="10")
    assert m2.f_id__in == [10]


def test_parse_list_with_whitespace() -> None:
    """Test that whitespace around commas is handled correctly."""
    FilterModel = create_filter_model(PostOut)

    m = FilterModel(f_id__in=" 1 , 2 ,  3 ")
    assert m.f_id__in == [1, 2, 3]


def test_split_comma_values_single_string_list() -> None:
    """Test a single-item string list for list filters."""
    FilterModel = create_filter_model(PostOut)

    m = FilterModel(f_id__in=["1, 2, 3"])
    assert m.f_id__in == [1, 2, 3]


def test_split_comma_values_unknown_field_is_ignored() -> None:
    """Unknown keys are ignored when strict mode is disabled."""

    class NonStrictPostOut(PostOut):
        class FilterConfig(PostOut.FilterConfig):
            strict = False

    FilterModel = create_filter_model(NonStrictPostOut)

    # Unknown field should be ignored (FilterBase has extra="ignore")
    model = FilterModel(f_id__in="1,2", unknown_field="value")
    assert model.f_id__in == [1, 2]
    assert "unknown_field" not in model.model_dump()


def test_split_comma_values_non_dict_input() -> None:
    """Test that non-dict data is returned unchanged by the validator."""
    # Accessing __func__ because pydantic wraps the validator
    assert (
        FilterBase.split_comma_values.__func__(FilterBase, "just a string")
        == "just a string"
    )


def test_validation_error_invalid_type() -> None:
    """Test that Pydantic validation still works for invalid types."""
    FilterModel = create_filter_model(PostOut)

    from pydantic import ValidationError

    # f_created_at__gte expects a datetime, should fail with a random string
    with pytest.raises(ValidationError):
        FilterModel(f_created_at__gte="not-a-date")

    # f_id__eq expects an int
    with pytest.raises(ValidationError):
        FilterModel(f_id__eq="abc")


def test_strict_mode_error() -> None:
    """Test that strict mode (extra='forbid') raises error for unknown fields."""
    FilterModel = create_filter_model(PostOut)
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        FilterModel(unknown_field="value")
