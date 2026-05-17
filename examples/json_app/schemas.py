from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field


class MissionMetadata(BaseModel):
    commander: str = Field(
        json_schema_extra={
            "filters": [
                "eq",
                "icontains",
                "startswith",
                "in",
                "isnull",
            ]
        }
    )
    danger_level: int = Field(
        json_schema_extra={
            "filters": [
                "eq",
                "gt",
                "lt",
                "between",
            ]
        }
    )
    naquadah_concentration: float = Field(
        json_schema_extra={"filters": ["gte", "lte", "between"]}
    )
    is_classified: bool = Field(json_schema_extra={"filters": ["eq"]})
    scheduled_date: date = Field(
        json_schema_extra={"filters": ["gte", "lte", "between"]}
    )
    arrival_time: time | None = Field(None, json_schema_extra={"filters": ["gt", "lt"]})
    last_report: datetime | None = Field(
        None, json_schema_extra={"filters": ["gte", "lte", "between"]}
    )


class MissionOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq"]})
    planet_name: str = Field(
        alias="planet",
        json_schema_extra={"filters": ["eq", "icontains"], "filter_alias": "planet"},
    )
    mission_metadata: MissionMetadata = Field(alias="data")

    class FilterConfig:
        prefix = "m_"
        max_depth = 1
        search_columns = ["planet_name", "mission_metadata__commander"]
        sort_columns = [
            "id",
            "m_planet",
            "m_data__danger_level",
            "m_data__scheduled_date",
        ]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
