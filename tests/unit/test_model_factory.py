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
        "name__eq",
        "name__icontains",
        "email__eq",
        "email__icontains",
        "age__eq",
        "age__gte",
        "age__lte",
        "profile_bio__eq",
        "profile_bio__icontains",
        "profile_bio__isnull",
        "rank__eq",
        "rank__in",
        "rank__not_in",
        "is_alien__eq",
        "is_alien__isnull",
        "clearance_level__eq",
        "clearance_level__gte",
        "clearance_level__lte",
        "health_status__eq",
        "health_status__gte",
        "health_status__lte",
        "date_of_birth__gte",
        "date_of_birth__lte",
        "last_login_ip__eq",
        "uuid_badge__eq",
        # Nested Team fields
        "team__id__eq",
        "team__name__eq",
        "team__name__icontains",
        # Global control fields
        "q",
        "sort_by",
    }

    logging.info(f"Fields found: {actual_fields}")
    assert actual_fields == expected_fields


def test_create_filter_model_nested() -> None:
    """Test generating filters for nested relationships and verify the exact set."""
    # PostOut has prefix="f_" in its FilterConfig
    FilterModel = create_filter_model(PostOut)
    actual_fields = set(FilterModel.model_fields.keys())

    expected_fields = {
        # Post fields (prefixed)
        "f_id__eq",
        "f_id__gte",
        "f_id__lte",
        "f_id__in",
        "f_id__not_in",
        "f_post_title__eq",  # title alias
        "f_post_title__icontains",
        "f_is_active__eq",
        "f_is_active__ne",
        "f_is_active__isnull",
        "f_gate_address__eq",
        "f_gate_address__icontains",
        "f_gate_address__isnull",
        "f_casualties__eq",
        "f_casualties__gte",
        "f_casualties__isnull",
        "f_success_rate__gte",
        "f_success_rate__lte",
        "f_mission_report_url__eq",
        "f_mission_report_url__isnull",
        "f_mission_date__eq",
        "f_mission_date__gte",
        "f_mission_date__lte",
        "f_mission_date__in",
        "f_mission_date__isnull",
        "f_mission_start__gte",
        "f_mission_start__lte",
        "f_mission_start__isnull",
        "f_incident_time__eq",
        "f_incident_time__gte",
        "f_incident_time__lte",
        "f_incident_time__isnull",
        "f_created_at__gte",
        "f_created_at__lte",
        "f_userId__eq",  # user_id alias
        # Nested User (author) fields (prefixed)
        "f_author__id__eq",
        "f_author__id__in",
        "f_author__name__eq",
        "f_author__name__icontains",
        "f_author__email__eq",
        "f_author__email__icontains",
        "f_author__age__eq",
        "f_author__age__gte",
        "f_author__age__lte",
        "f_author__age__gt",
        "f_author__age__lt",
        "f_author__profile_bio__eq",
        "f_author__profile_bio__icontains",
        "f_author__profile_bio__isnull",
        "f_author__rank__eq",
        "f_author__rank__in",
        "f_author__rank__not_in",
        "f_author__is_alien__eq",
        "f_author__is_alien__isnull",
        "f_author__clearance_level__eq",
        "f_author__clearance_level__gte",
        "f_author__clearance_level__lte",
        "f_author__health_status__eq",
        "f_author__health_status__gte",
        "f_author__health_status__lte",
        "f_author__date_of_birth__gte",
        "f_author__date_of_birth__lte",
        "f_author__last_login_ip__eq",
        "f_author__uuid_badge__eq",
        # Double-nested Team (author.team)
        "f_author__team__id__eq",
        "f_author__team__name__eq",
        "f_author__team__name__icontains",
        # Extra filters from PostFilterExtra (prefixed)
        "f_author__age__in",
        "f_author__age__not_in",
        # Global control fields (NOT prefixed usually, but can be if configured)
        "q",
        "sort_by",
    }

    logging.info(f"Nested fields found: {actual_fields}")
    assert actual_fields == expected_fields


def test_create_filter_model_config_overrides() -> None:
    """Test that explicit parameters override FilterConfig and verify the exact set."""
    # We use prefix="f_" which matches PostOut's default, but let's change it to "p_"
    FilterModel = create_filter_model(
        PostOut, prefix="p_", search_field="search", sort_field="order"
    )
    actual_fields = set(FilterModel.model_fields.keys())

    # We won't list every single field here to keep it manageable, but check key ones
    assert "p_id__eq" in actual_fields
    assert "p_post_title__eq" in actual_fields
    assert "p_author__email__eq" in actual_fields
    assert "p_author__team__name__eq" in actual_fields
    assert "search" in actual_fields
    assert "order" in actual_fields
    # Ensure old prefix/fields are NOT there
    assert "f_id__eq" not in actual_fields
    assert "q" not in actual_fields
    assert "sort_by" not in actual_fields


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


def test_nested_schema_extra_filters_are_included() -> None:
    class WrapperModel(BaseModel):
        post: PostOut

    FilterModel = create_filter_model(WrapperModel, depth=3)

    assert "post__author__age__gt" in FilterModel.model_fields
