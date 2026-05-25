from datetime import date, datetime, time
from enum import StrEnum
from typing import Any


class FilterOperator(StrEnum):
    """Enumeration of supported filter operators for query generation."""

    EQ = "eq"
    NE = "ne"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    LIKE = "like"
    ILIKE = "ilike"
    ICONTAINS = "icontains"
    CONTAINS = "contains"
    STARTSWITH = "startswith"
    ISTARTSWITH = "istartswith"
    ENDSWITH = "endswith"
    IENDSWITH = "iendswith"
    IN = "in"
    NOT_IN = "not_in"
    ISNULL = "isnull"
    NOT_ISNULL = "not_isnull"
    BETWEEN = "between"
    IS_EMPTY = "is_empty"
    IS_BLANK = "is_blank"
    HAS_KEY = "has_key"
    HAS_ANY_KEYS = "has_any_keys"
    HAS_ALL_KEYS = "has_all_keys"


# Mapping of Python types to their default allowed filter operators.
# This ensures sensible defaults are used if no specific filters are defined in the schema.
DEFAULT_OPERATORS: dict[Any, list[FilterOperator]] = {
    int: [
        FilterOperator.EQ,
        FilterOperator.NE,
        FilterOperator.GT,
        FilterOperator.LT,
        FilterOperator.GTE,
        FilterOperator.LTE,
        FilterOperator.IN,
        FilterOperator.NOT_IN,
        FilterOperator.ISNULL,
        FilterOperator.NOT_ISNULL,
        FilterOperator.BETWEEN,
    ],
    float: [
        FilterOperator.EQ,
        FilterOperator.NE,
        FilterOperator.GT,
        FilterOperator.LT,
        FilterOperator.GTE,
        FilterOperator.LTE,
        FilterOperator.ISNULL,
        FilterOperator.NOT_ISNULL,
        FilterOperator.BETWEEN,
    ],
    str: [
        FilterOperator.EQ,
        FilterOperator.NE,
        FilterOperator.LIKE,
        FilterOperator.ILIKE,
        FilterOperator.ICONTAINS,
        FilterOperator.CONTAINS,
        FilterOperator.STARTSWITH,
        FilterOperator.ISTARTSWITH,
        FilterOperator.ENDSWITH,
        FilterOperator.IENDSWITH,
        FilterOperator.IN,
        FilterOperator.NOT_IN,
        FilterOperator.ISNULL,
        FilterOperator.NOT_ISNULL,
        FilterOperator.BETWEEN,
    ],
    bool: [
        FilterOperator.EQ,
        FilterOperator.NE,
        FilterOperator.ISNULL,
        FilterOperator.NOT_ISNULL,
    ],
    date: [
        FilterOperator.EQ,
        FilterOperator.NE,
        FilterOperator.GT,
        FilterOperator.LT,
        FilterOperator.GTE,
        FilterOperator.LTE,
        FilterOperator.IN,
        FilterOperator.NOT_IN,
        FilterOperator.ISNULL,
        FilterOperator.NOT_ISNULL,
        FilterOperator.BETWEEN,
    ],
    datetime: [
        FilterOperator.EQ,
        FilterOperator.NE,
        FilterOperator.GT,
        FilterOperator.LT,
        FilterOperator.GTE,
        FilterOperator.LTE,
        FilterOperator.IN,
        FilterOperator.NOT_IN,
        FilterOperator.ISNULL,
        FilterOperator.NOT_ISNULL,
        FilterOperator.BETWEEN,
    ],
    time: [
        FilterOperator.EQ,
        FilterOperator.NE,
        FilterOperator.GT,
        FilterOperator.LT,
        FilterOperator.GTE,
        FilterOperator.LTE,
        FilterOperator.IN,
        FilterOperator.NOT_IN,
        FilterOperator.ISNULL,
        FilterOperator.NOT_ISNULL,
        FilterOperator.BETWEEN,
    ],
    dict: [
        FilterOperator.IS_EMPTY,
        FilterOperator.IS_BLANK,
        FilterOperator.ISNULL,
        FilterOperator.NOT_ISNULL,
        FilterOperator.HAS_KEY,
        FilterOperator.HAS_ANY_KEYS,
        FilterOperator.HAS_ALL_KEYS,
    ],
}
