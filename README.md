# :rocket: fastapi-query-filters

Dynamic and declarative query filters for FastAPI, powered by Pydantic v2 and ready for multiple ORMs.

## Features

- 🔍 **Dynamic Filtering**: Generate powerful query filters from Pydantic models automatically
- 🎯 **Declarative API**: Clean, intuitive syntax for defining filters
- 🔌 **Multi-ORM Support**: Built-in support for SQLAlchemy with extensibility for other ORMs
- 📦 **Pydantic v2**: Full integration with Pydantic v2 for robust data validation
- ⚡ **FastAPI Native**: Seamlessly integrates with FastAPI dependencies
- 🔤 **Search & Sort**: Support for text search and custom sorting operators
- 🧪 **Type Safe**: Full type hints and mypy strict mode support

## Installation

```bash
pip install fastapi-query-filters
```

## Requirements

- Python >= 3.11
- FastAPI >= 0.110.0
- Pydantic >= 2.0.0
- SQLAlchemy >= 2.0.0

## Quick Start

### 1. Define Your Schema

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq"]})
    email: EmailStr = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    model_config = ConfigDict(from_attributes=True)

class PostOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq", "gte", "lte", "in"]})
    title: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    created_at: datetime = Field(json_schema_extra={"filters": ["gte", "lte"]})
    is_active: bool = Field(json_schema_extra={"filters": ["eq"]})
    user_id: int = Field(json_schema_extra={"filters": ["eq"]})
    author: UserOut

    model_config = ConfigDict(from_attributes=True)

    class FilterConfig:
        search_field = "q"
        sort_field = "sort_by"
        enable_sort = True
```

### 2. Use in Your Endpoint

```python
from fastapi import Depends, FastAPI
from fastapi_query_filters import FilterDep, FilterValues
from fastapi_query_filters.orm.sqlalchemy import apply_filters

app = FastAPI()

@app.get("/posts")
def list_posts(
    db: Session = Depends(get_db),
    filters: FilterValues = FilterDep(PostOut)
):
    stmt = select(Post)
    stmt = apply_filters(stmt, Post, filters)
    return db.execute(stmt).scalars().all()
```

### 3. Query Your API

```bash
# Filter by field with eq operator
GET /posts?id__eq=1

# Multiple values for in operator
GET /posts?id__in=1&id__in=2&id__in=3

# Use in operator with comma-separated values
GET /posts?id__in=1,2,3

# Filter by field with icontains operator
GET /posts?title__icontains=python

# Multiple filters
GET /posts?published=true&title__icontains=api

# Search across fields
GET /posts?q=fastapi

# Sort results
GET /posts?sort_by=-created_at,title

# Combine filters and search
GET /posts?id__in=1,2,3&is_active__eq=true&q=fastapi&sort_by=-created_at
```

## Documentation

For detailed documentation and examples, see the [examples/](./examples/) directory.

## License

MIT License - see [LICENSE](./LICENSE) file for details.

## Author

Ezequiel Parziale