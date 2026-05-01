from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq"]})
    email: EmailStr = Field(json_schema_extra={"filters": ["eq", "icontains"]})

    model_config = ConfigDict(from_attributes=True)


class PostFilterExtra(BaseModel):
    # Virtual field to filter by author's age range even if not directly in PostOut top-level
    author__age: int | None = Field(
        default=None, json_schema_extra={"filters": ["gte", "lte", "in"]}
    )


class PostOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq", "gte", "lte", "in"]})

    # Title with alias and search enabled
    title: str = Field(
        alias="post_title",
        json_schema_extra={
            "filters": ["eq", "icontains"],
            "filter_alias": "post_title",
        },
    )

    description: str | None = Field(None, json_schema_extra={})

    # Boolean with a forbidden 'gte' filter (to test the new strict validation)
    is_active: bool = Field(json_schema_extra={"filters": ["eq", "gte"]})

    created_at: datetime = Field(json_schema_extra={"filters": ["gte", "lte"]})
    updated_at: datetime
    deleted_at: datetime | None = None
    user_id: int = Field(
        json_schema_extra={"filters": ["eq"], "filter_alias": "userId"},
    )
    author: UserOut

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    class FilterConfig:
        search_field = "q"
        sort_field = "sort_by"
        enable_sort = True
        enable_search = True
        extra_filters = PostFilterExtra
        search_columns = ["title", "description"]
        prefix = "f_"
