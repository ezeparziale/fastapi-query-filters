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
    m = FilterModel(created_at__gte=dt_str)
    logging.info(f"Parsed datetime: {m.created_at__gte}")
    assert isinstance(m.created_at__gte, datetime)
    assert m.created_at__gte == datetime(2024, 1, 1, 12, 0, 0)


def test_parse_boolean_isnull() -> None:
    """Test parsing of boolean values, specifically for isnull operator."""
    FilterModel = create_filter_model(PostOut)

    # True variants
    assert FilterModel(author__name__isnull="true").author__name__isnull is True
    assert FilterModel(author__name__isnull="1").author__name__isnull is True
    assert FilterModel(author__name__isnull=1).author__name__isnull is True
    assert FilterModel(author__name__isnull=True).author__name__isnull is True

    # False variants
    assert FilterModel(author__name__isnull="false").author__name__isnull is False
    assert FilterModel(author__name__isnull="0").author__name__isnull is False
    assert FilterModel(author__name__isnull=0).author__name__isnull is False
    assert FilterModel(author__name__isnull=False).author__name__isnull is False


def test_parse_list_integers() -> None:
    """Test that comma-separated strings are correctly converted to lists of the appropriate type."""
    FilterModel = create_filter_model(PostOut)

    # Multiple integers
    m = FilterModel(id__in="1,2,3")
    logging.info(f"Parsed list of ints: {m.id__in}")
    assert m.id__in == [1, 2, 3]

    # Single integer
    m2 = FilterModel(id__in="10")
    assert m2.id__in == [10]


def test_parse_list_with_whitespace() -> None:
    """Test that whitespace around commas is handled correctly."""
    FilterModel = create_filter_model(PostOut)

    m = FilterModel(id__in=" 1 , 2 ,  3 ")
    assert m.id__in == [1, 2, 3]


def test_split_comma_values_single_string_list() -> None:
    """Test a single-item string list for list filters."""
    FilterModel = create_filter_model(PostOut)

    m = FilterModel(id__in=["1, 2, 3"])
    assert m.id__in == [1, 2, 3]


def test_split_comma_values_unknown_field_is_ignored() -> None:
    """Test that unknown filter keys are ignored by the validator."""
    FilterModel = create_filter_model(PostOut)

    m = FilterModel(id__in="1,2,3", unknown__in="a,b,c")
    assert m.id__in == [1, 2, 3]
    assert "unknown__in" not in m.model_dump(exclude_none=True)


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

    # created_at__gte expects a datetime, should fail with a random string
    with pytest.raises(ValidationError):
        FilterModel(created_at__gte="not-a-date")

    # id__eq expects an int
    with pytest.raises(ValidationError):
        FilterModel(id__eq="abc")
