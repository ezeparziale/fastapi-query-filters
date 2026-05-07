import logging

from pydantic import BaseModel, Field

from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.operators import FilterOperator
from tests.schemas import PostOut, UserOut

logging.basicConfig(level=logging.INFO)


def test_create_filter_model_basic() -> None:
    """Test generating a filter model and verify the exact set of fields."""
    FilterModel = create_filter_model(UserOut)
    actual_fields = set(FilterModel.model_fields.keys())

    expected_fields = {
        # Standard fields from UserOut
        "id__eq",
        "id__in",
        "email__eq",
        "email__icontains",
        "name__eq",
        "name__icontains",
        "name__isnull",
        "is_active__eq",
        # Extra filters from UserFilterExtra
        "age__gt",
        "age__lt",
        "age__gte",
        "age__lte",
        # Global control fields
        "q",
        "sort_by",
    }

    logging.info(f"Fields found: {actual_fields}")
    assert actual_fields == expected_fields


def test_create_filter_model_nested() -> None:
    """Test generating filters for nested relationships and verify the exact set."""
    FilterModel = create_filter_model(PostOut)
    actual_fields = set(FilterModel.model_fields.keys())

    expected_fields = {
        # Post fields
        "id__eq",
        "id__gt",
        "id__lt",
        "id__in",
        "title__eq",
        "title__icontains",
        "user_id__eq",
        "created_at__gte",
        "created_at__lte",
        # Nested User (author) fields
        "author__id__eq",
        "author__id__in",
        "author__email__eq",
        "author__email__icontains",
        "author__name__eq",
        "author__name__icontains",
        "author__name__isnull",
        "author__is_active__eq",
        # Nested User Extra Filters (age)
        "author__age__gt",
        "author__age__lt",
        "author__age__gte",
        "author__age__lte",
        # Global control fields
        "q",
        "sort_by",
    }

    logging.info(f"Nested fields found: {actual_fields}")
    assert actual_fields == expected_fields


def test_create_filter_model_config_overrides() -> None:
    """Test that explicit parameters override FilterConfig and verify the exact set."""
    FilterModel = create_filter_model(
        PostOut, prefix="f_", search_field="search", sort_field="order"
    )
    actual_fields = set(FilterModel.model_fields.keys())

    expected_fields = {
        # Prefixed Post fields
        "f_id__eq",
        "f_id__gt",
        "f_id__lt",
        "f_id__in",
        "f_title__eq",
        "f_title__icontains",
        "f_user_id__eq",
        "f_created_at__gte",
        "f_created_at__lte",
        # Prefixed Nested User fields
        "f_author__id__eq",
        "f_author__id__in",
        "f_author__email__eq",
        "f_author__email__icontains",
        "f_author__name__eq",
        "f_author__name__icontains",
        "f_author__name__isnull",
        "f_author__is_active__eq",
        "f_author__age__gt",
        "f_author__age__lt",
        "f_author__age__gte",
        "f_author__age__lte",
        # Overridden Global control fields
        "search",
        "order",
    }

    logging.info(f"Prefixed fields found: {actual_fields}")
    assert actual_fields == expected_fields


def test_annotated_field_generates_filter() -> None:
    from typing import Annotated

    class AnnotatedModel(BaseModel):
        field: Annotated[int, "meta"] = Field(json_schema_extra={"filters": ["eq"]})

    FilterModel = create_filter_model(AnnotatedModel)

    assert "field__eq" in FilterModel.model_fields


def test_http_url_field_generates_filter() -> None:
    from pydantic import HttpUrl

    class UrlModel(BaseModel):
        url: HttpUrl = Field(json_schema_extra={"filters": ["eq"]})

    FilterModel = create_filter_model(UrlModel)

    assert "url__eq" in FilterModel.model_fields


def test_bad_json_schema_extra_is_ignored() -> None:
    class BadJsonExtraModel(BaseModel):
        x: int = Field(1, json_schema_extra="bad")  # type: ignore[call-overload]

    FilterModel = create_filter_model(BadJsonExtraModel)

    assert "x__eq" not in FilterModel.model_fields


def test_filter_alias_generates_alias_name() -> None:
    class AliasModel(BaseModel):
        value: int = Field(
            1,
            json_schema_extra={"filter_alias": "alias", "filters": ["eq"]},
        )

    FilterModel = create_filter_model(AliasModel)

    assert "alias__eq" in FilterModel.model_fields


def test_operator_override_creates_requested_filter() -> None:
    class OverrideModel(BaseModel):
        value: int = Field(1)

    FilterModel = create_filter_model(
        OverrideModel,
        operators={"value": [FilterOperator.IN]},
    )

    assert "value__in" in FilterModel.model_fields


def test_field_without_filters_is_ignored() -> None:
    class NoFilterModel(BaseModel):
        value: int = Field(1)

    FilterModel = create_filter_model(NoFilterModel)

    assert "value__eq" not in FilterModel.model_fields
