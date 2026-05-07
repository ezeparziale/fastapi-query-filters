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
    IN = "in"
    NOT_IN = "not_in"
    ISNULL = "isnull"


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
    ],
    float: [
        FilterOperator.EQ,
        FilterOperator.NE,
        FilterOperator.GT,
        FilterOperator.LT,
        FilterOperator.GTE,
        FilterOperator.LTE,
        FilterOperator.ISNULL,
    ],
    str: [
        FilterOperator.EQ,
        FilterOperator.NE,
        FilterOperator.LIKE,
        FilterOperator.ILIKE,
        FilterOperator.ICONTAINS,
        FilterOperator.IN,
        FilterOperator.NOT_IN,
        FilterOperator.ISNULL,
    ],
    bool: [FilterOperator.EQ, FilterOperator.NE, FilterOperator.ISNULL],
}
