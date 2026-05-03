from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, EmailStr

# --- Pydantic Schemas for Testing ---

class UserFilterExtra(BaseModel):
    # Extra field not in UserOut but present in DB
    age: Optional[int] = Field(None, json_schema_extra={"filters": ["gt", "lt", "gte", "lte"]})

class UserOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq", "in"]})
    email: EmailStr = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    name: Optional[str] = Field(None, json_schema_extra={"filters": ["eq", "icontains", "isnull"]})
    is_active: bool = Field(json_schema_extra={"filters": ["eq"]})
    
    model_config = ConfigDict(from_attributes=True)
    
    class FilterConfig:
        extra_filters = UserFilterExtra

class PostOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq", "gt", "lt", "in"]})
    title: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    created_at: datetime = Field(json_schema_extra={"filters": ["gte", "lte"]})
    author: UserOut
    
    model_config = ConfigDict(from_attributes=True)
    
    class FilterConfig:
        search_field = "q"
        sort_field = "sort_by"
        search_columns = ["title", "content"]
        enable_sort = True
        enable_search = True
