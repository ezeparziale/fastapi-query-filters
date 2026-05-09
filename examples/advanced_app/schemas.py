from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, IPvAnyAddress


class TeamOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq"]})
    name: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq"]})
    name: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
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
        json_schema_extra={"filters": ["gte", "lte", "in", "not_in"]},
    )


class PostOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq", "gte", "lte", "in", "not_in"]})
    title: str = Field(
        alias="post_title",
        json_schema_extra={
            "filters": ["eq", "icontains"],
            "filter_alias": "post_title",
        },
    )
    description: str | None = Field(None, json_schema_extra={})
    is_active: bool = Field(json_schema_extra={"filters": ["eq", "gte"]})
    gate_address: str | None = Field(
        None,
        pattern=r"^[A-Z0-9]{3}-[A-Z0-9]{3,4}$",
        json_schema_extra={"filters": ["eq", "icontains", "isnull"]},
    )
    casualties: int | None = Field(
        None, json_schema_extra={"filters": ["eq", "gte", "isnull"]}
    )
    success_rate: float | None = Field(
        None, json_schema_extra={"filters": ["gte", "lte"]}
    )
    mission_report_url: HttpUrl | None = Field(
        None, json_schema_extra={"filters": ["eq", "isnull"]}
    )
    mission_date: date | None = Field(
        None, json_schema_extra={"filters": ["eq", "gte", "lte", "in", "isnull"]}
    )
    mission_start: datetime | None = Field(
        None, json_schema_extra={"filters": ["gte", "lte", "isnull"]}
    )
    incident_time: time | None = Field(
        None, json_schema_extra={"filters": ["eq", "gte", "lte", "isnull"]}
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
