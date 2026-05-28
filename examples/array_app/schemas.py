from pydantic import BaseModel, ConfigDict, Field


class PlanetOut(BaseModel):
    id: int
    name: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    tags: list[str] = Field(
        json_schema_extra={
            "filters": [
                "arr_contains",
                "arr_overlap",
                "arr_all",
                "arr_any",
                "arr_len",
                "is_empty",
                "is_blank",
            ]
        }
    )
    model_config = ConfigDict(from_attributes=True)


class TeamOut(BaseModel):
    id: int
    name: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    members: list[str] = Field(
        json_schema_extra={
            "filters": [
                "arr_contains",
                "arr_overlap",
                "arr_all",
                "arr_any",
                "arr_len",
            ]
        }
    )
    assigned_planet: PlanetOut | None = None

    class FilterConfig:
        max_depth = 1

    model_config = ConfigDict(from_attributes=True)
