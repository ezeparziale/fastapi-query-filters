from typing import Annotated, Any, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel

from .core import create_filter_model

T = TypeVar("T", bound=BaseModel)


class FilterValues:
    """Wrapper class for validated filter values.

    Encapsulates the generated Pydantic model instance and provides
    utilities for extracting data for database queries.
    """

    def __init__(self, model: BaseModel):
        self.model = model

    def dict(self) -> dict[str, Any]:
        """Returns the filter data as a dictionary, excluding None values."""
        return self.model.model_dump(exclude_none=True, by_alias=True)


def FilterDep(base_schema: type[BaseModel]) -> Any:
    """FastAPI dependency factory for automatic query parameter filtering.

    Generates a dynamic Pydantic model based on the provided schema and
    configures it as a FastAPI dependency that extracts and validates
    parameters from the query string.

    Args:
        base_schema: The Pydantic model (usually an output schema)
            to use as the template for filters.

    Returns:
        A FastAPI dependency that returns a FilterValues instance.
    """
    # Generate the filter model from the base schema
    filter_model: Any = create_filter_model(base_schema)

    # Use the Annotated[Model, Query()] pattern to force FastAPI
    # to unpack model fields as individual query parameters.
    def get_values(filters: Annotated[filter_model, Query()]) -> FilterValues:
        return FilterValues(filters)

    return Depends(get_values)
