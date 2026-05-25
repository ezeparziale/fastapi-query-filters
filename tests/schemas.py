from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, IPvAnyAddress


class TeamOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq"]})
    name: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq", "in"]})
    name: str = Field(
        json_schema_extra={
            "filters": [
                "eq",
                "icontains",
                "contains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
            ]
        }
    )
    email: EmailStr = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    age: int = Field(json_schema_extra={"filters": ["eq", "gte", "lte"]})
    profile_bio: str | None = Field(
        None, json_schema_extra={"filters": ["eq", "icontains", "isnull"]}
    )
    rank: str = Field(json_schema_extra={"filters": ["eq", "in", "not_in"]})
    is_alien: bool = Field(json_schema_extra={"filters": ["eq", "isnull"]})
    clearance_level: int = Field(json_schema_extra={"filters": ["eq", "gte", "lte"]})
    health_status: float = Field(json_schema_extra={"filters": ["eq", "gte", "lte"]})
    date_of_birth: date | None = Field(
        None, json_schema_extra={"filters": ["gte", "lte"]}
    )
    last_login_ip: IPvAnyAddress | None = Field(
        None, json_schema_extra={"filters": ["eq"]}
    )
    uuid_badge: UUID = Field(json_schema_extra={"filters": ["eq"]})
    team: TeamOut

    model_config = ConfigDict(from_attributes=True)


class PostFilterExtra(BaseModel):
    # Virtual field to filter by author's age range even if not directly in PostOut top-level
    author__age: int | None = Field(
        default=None,
        json_schema_extra={
            "filters": ["gt", "lt", "gte", "lte", "in", "not_in", "between"]
        },
    )


class PostOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq", "gte", "lte", "in", "not_in"]})
    title: str = Field(
        alias="post_title",
        json_schema_extra={
            "filters": [
                "eq",
                "icontains",
                "contains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "between",
            ],
            "filter_alias": "post_title",
        },
    )
    description: str | None = Field(None, json_schema_extra={})
    is_active: bool = Field(
        json_schema_extra={"filters": ["eq", "ne", "gte", "isnull", "not_isnull"]}
    )
    gate_address: str | None = Field(
        None,
        pattern=r"^[A-Z0-9]{3}-[A-Z0-9]{3,4}$",
        json_schema_extra={
            "filters": ["eq", "icontains", "isnull", "not_isnull", "between"]
        },
    )
    casualties: int | None = Field(
        None,
        json_schema_extra={"filters": ["eq", "gte", "isnull", "not_isnull", "between"]},
    )
    success_rate: float | None = Field(
        None, json_schema_extra={"filters": ["gte", "lte", "between"]}
    )
    mission_report_url: HttpUrl | None = Field(
        None, json_schema_extra={"filters": ["eq", "isnull", "not_isnull"]}
    )
    mission_date: date | None = Field(
        None,
        json_schema_extra={
            "filters": ["eq", "gte", "lte", "in", "isnull", "not_isnull", "between"]
        },
    )
    mission_start: datetime | None = Field(
        None,
        json_schema_extra={
            "filters": ["gte", "lte", "isnull", "not_isnull", "between"]
        },
    )
    incident_time: time | None = Field(
        None,
        json_schema_extra={"filters": ["eq", "gte", "lte", "isnull", "not_isnull"]},
    )
    created_at: datetime = Field(json_schema_extra={"filters": ["gte", "lte"]})
    updated_at: datetime
    deleted_at: datetime | None = None
    user_id: int = Field(
        json_schema_extra={"filters": ["eq"], "filter_alias": "userId"},
    )
    author: UserOut

    model_config = ConfigDict(from_attributes=True, validate_by_name=True)

    class FilterConfig:
        search_field = "q"
        sort_field = "sort_by"
        enable_sort = True
        enable_search = True
        max_depth = 2
        strict = True
        extra_filters = PostFilterExtra
        search_columns = ["title", "description"]
        sort_columns = [
            "id",
            "post_title",
            "created_at",
            "f_author__team__name",
            "f_mission_date",
        ]
        prefix = "f_"


class MissionMetadata(BaseModel):
    commander: str = Field(
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
            ]
        }
    )
    danger_level: int = Field(
        json_schema_extra={
            "filters": [
                "eq",
                "ne",
                "gt",
                "lt",
                "gte",
                "lte",
                "in",
                "not_in",
                "between",
                "isnull",
            ]
        }
    )
    naquadah_concentration: float = Field(
        json_schema_extra={
            "filters": ["eq", "ne", "gt", "lt", "gte", "lte", "between", "isnull"]
        }
    )
    is_classified: bool = Field(json_schema_extra={"filters": ["eq", "ne", "isnull"]})
    scheduled_date: date = Field(
        json_schema_extra={
            "filters": [
                "eq",
                "ne",
                "gt",
                "lt",
                "gte",
                "lte",
                "in",
                "not_in",
                "between",
                "isnull",
            ]
        }
    )
    arrival_time: time = Field(
        json_schema_extra={
            "filters": [
                "eq",
                "ne",
                "gt",
                "lt",
                "gte",
                "lte",
                "in",
                "not_in",
                "between",
                "isnull",
            ]
        }
    )
    last_report: datetime = Field(
        json_schema_extra={
            "filters": [
                "eq",
                "ne",
                "gt",
                "lt",
                "gte",
                "lte",
                "in",
                "not_in",
                "between",
                "isnull",
            ]
        }
    )

    model_config = ConfigDict(from_attributes=True)


class ExtraInfo(BaseModel):
    mission_metadata: dict[str, Any] = Field(
        default_factory=dict,
        alias="metadata",
        json_schema_extra={
            "filters": [
                "has_key",
                "has_any_keys",
                "has_all_keys",
            ],
            "filter_alias": "metadata",
        },
    )


class MissionOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq"]})
    planet_name: str = Field(
        alias="planet",
        json_schema_extra={"filters": ["eq", "icontains"], "filter_alias": "planet"},
    )
    mission_metadata: MissionMetadata = Field(
        alias="data", json_schema_extra={"filters": ["has_key"]}
    )

    class FilterConfig:
        prefix = "m_"
        max_depth = 1
        search_columns = ["planet_name", "mission_metadata__commander"]
        extra_filters = ExtraInfo

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
