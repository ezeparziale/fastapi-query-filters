# :rocket: fastapi-query-filters

[![CI](https://github.com/ezeparziale/fastapi-query-filters/actions/workflows/ci.yml/badge.svg)](https://github.com/ezeparziale/fastapi-query-filters/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/fastapi-query-filters.svg)](https://pypi.org/project/fastapi-query-filters/)
[![Python versions](https://img.shields.io/pypi/pyversions/fastapi-query-filters.svg)](https://pypi.org/project/fastapi-query-filters/)
[![License](https://img.shields.io/github/license/ezeparziale/fastapi-query-filters.svg)](https://github.com/ezeparziale/fastapi-query-filters/blob/main/LICENSE)

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
# Standard installation
pip install fastapi-query-filters

# Installation with SQLAlchemy support
pip install "fastapi-query-filters[sqlalchemy]"
```

*Note: If you are installing directly from GitHub:*

```bash
pip install "fastapi-query-filters[sqlalchemy] @ git+https://github.com/ezeparziale/fastapi-query-filters.git"
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
    profile_bio: str | None = Field(
        None,
        json_schema_extra={"filters": ["eq", "icontains", "isnull"]},
    )

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
        enable_search = True
        prefix = ""
        search_columns = ["title", "description"]
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

# Filter by author profile bio NULL / NOT NULL values
GET /posts?author__profile_bio__isnull=true
GET /posts?author__profile_bio__isnull=false

# Multiple filters
GET /posts?published__eq=true&title__icontains=api

# Search across fields
GET /posts?q=fastapi

# Sort results
GET /posts?sort_by=-created_at,title

# Combine filters and search
GET /posts?id__in=1,2,3&is_active__eq=true&q=fastapi&sort_by=-created_at
```

## Supported Operators

The library supports the following filter operators for different field types:

| Operator | Description | Example | Types |
|----------|-------------|---------|-------|
| `eq` | Equal | `id__eq=1` | all |
| `ne` | Not equal | `status__ne=inactive` | all |
| `gt` | Greater than | `age__gt=18` | int, datetime |
| `lt` | Less than | `age__lt=65` | int, datetime |
| `gte` | Greater than or equal | `created_at__gte=2024-01-01` | int, datetime |
| `lte` | Less than or equal | `price__lte=100` | int, datetime |
| `in` | In list | `id__in=1,2,3` | all |
| `not_in` | Not in list | `status__not_in=deleted,archived` | all |
| `like` | SQL LIKE pattern | `name__like=%john%` | str |
| `ilike` | SQL ILIKE (case-insensitive) | `email__ilike=%gmail%` | str |
| `icontains` | Case-insensitive contains | `title__icontains=python` | str |
| `isnull` | Check if value is NULL or NOT NULL (supports true/false or 1/0) | `status__isnull=true` | all |

## FilterConfig Configuration

Customize filter behavior using the `FilterConfig` nested class in your schema:

```python
class PostOut(BaseModel):
    # ... fields ...

    class FilterConfig:
        # Query parameter name for global search (default: "q")
        search_field = "q"
        
        # Query parameter name for sorting (default: "sort_by")
        sort_field = "sort_by"
        
        # Global prefix for all filter parameters (default: "")
        prefix = ""
        
        # Enable/disable global search functionality (default: True)
        enable_search = True
        
        # Enable/disable sorting functionality (default: True)
        enable_sort = True
        
        # Columns to search when using global search query
        search_columns = ["title", "description", "content"]
        
        # Optional: Pydantic model with virtual/extra filter fields
        extra_filters = PostFilterExtra
```

### FilterConfig Parameters Explained

- **search_field**: The query parameter name used for global search across multiple columns
- **sort_field**: The query parameter name used to specify sorting order
- **prefix**: A prefix prepended to all filter parameter names (e.g., `f_id__eq=1`)
- **enable_search**: Toggle global search functionality on/off
- **enable_sort**: Toggle dynamic sorting functionality on/off
- **search_columns**: List of database columns to search when using the search_field parameter
- **extra_filters**: A Pydantic model containing additional filter fields from the database that are not included in the main schema output

## Advanced Features

### Nested Relationship Filtering

Filter by nested relationship fields using double underscore notation:

```python
# Filter posts by author's email
GET /posts?author__email__icontains=example.com

# Filter posts by author's age range
GET /posts?author__age__gte=18&author__age__lte=65
```

### Dynamic Sorting

Sort by multiple fields with ascending/descending order:

```bash
# Sort by created_at (descending), then by title (ascending)
GET /posts?sort_by=-created_at,title

# Sort by multiple fields
GET /posts?sort_by=-updated_at,id,name
```

### Field Aliases

Use `filter_alias` in `json_schema_extra` to map query parameters to different field names:

```python
class PostOut(BaseModel):
    title: str = Field(
        alias="post_title",
        json_schema_extra={
            "filters": ["eq", "icontains"],
            "filter_alias": "post_title",
        },
    )

# Query using the alias
GET /posts?post_title__icontains=python
```

### Multiple Query Parameter Values

Multiple values can be passed in different ways:

```bash
# Multiple eq operators
GET /posts?id__eq=1&id__eq=2&id__eq=3

# Comma-separated values with in operator
GET /posts?id__in=1,2,3

# Combined search and filters
GET /posts?q=fastapi&is_active__eq=true&author__id__in=1,2,3
```

### Global Prefix

Add a global prefix to all filter parameters for namespace isolation:

```python
class FilterConfig:
    prefix = "f_"
    
# Query with prefix
GET /posts?f_id__eq=1&f_title__icontains=api
```

### Extra Filters (Virtual Fields)

Define additional filter fields that exist in the database but are not included in your main response schema:

```python
class PostFilterExtra(BaseModel):
    # Database column available for filtering but not in PostOut response
    author__age: int | None = Field(
        default=None,
        json_schema_extra={"filters": ["gte", "lte", "in"]}
    )
    # Another database field not exposed in the API response
    status: str | None = Field(
        default=None,
        json_schema_extra={"filters": ["eq", "in"]}
    )

class PostOut(BaseModel):
    # ... fields exposed in response ...
    
    class FilterConfig:
        extra_filters = PostFilterExtra
        
# Query using extra filter fields
GET /posts?author__age__gte=18
GET /posts?status__eq=draft
```

## Documentation

For detailed documentation and examples, see the [examples/](./examples/) directory.

## License

MIT License - see [LICENSE](./LICENSE) file for details.

## Author

Ezequiel Parziale