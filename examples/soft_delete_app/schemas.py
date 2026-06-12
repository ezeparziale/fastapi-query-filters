from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StargateArtifactOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq"]})
    name: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    origin_planet: str = Field(json_schema_extra={"filters": ["eq"]})
    is_destroyed: bool = Field(json_schema_extra={"filters": ["eq"]})
    decommissioned_at: datetime | None = Field(
        None, json_schema_extra={"filters": ["isnull"]}
    )

    class FilterConfig:
        soft_delete_field = "is_destroyed"  # Auto-filters is_destroyed == False

    model_config = ConfigDict(from_attributes=True)
