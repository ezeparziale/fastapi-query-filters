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
- 🌳 **Multi-level Relationships**: Filter through nested models at any depth
- 📂 **JSON & Dictionary Support**: Query nested keys within JSON fields with automatic type casting
- 🛡️ **Strict Mode**: Optional strict validation for unknown query parameters
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
        sort_columns = ["id", "title", "created_at", "author__name"]  # Optional whitelist
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

### JSON Filtering 📂

Query nested keys within JSON fields by defining their structure using Pydantic models. The library automatically handles type casting and cross-database compatibility.

```python
class MissionMetadata(BaseModel):
    commander: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    danger_level: int = Field(json_schema_extra={"filters": ["gt", "gte", "between"]})

class MissionOut(BaseModel):
    planet: str = Field(json_schema_extra={"filters": ["eq"]})
    # Nested JSON field support via sub-model
    mission_data: MissionMetadata = Field(alias="data")

# Filter by nested JSON key
GET /missions?data__commander__eq=Jack

# Filter by nested JSON key with range (auto-cast to int)
GET /missions?data__danger_level__gt=5
```

> [!TIP]
> See a complete working example in [examples/json_app/](https://github.com/ezeparziale/fastapi-query-filters/tree/main/examples/json_app).

## Supported Operators

The library supports the following filter operators for different field types:

| Operator | Description | Example | Types |
|----------|-------------|---------|-------|
| `eq` | Equal | `id__eq=1` | all |
| `ne` | Not equal | `status__ne=inactive` | all |
| `gt` | Greater than | `age__gt=18` | int, float, datetime, date, time |
| `lt` | Less than | `age__lt=65` | int, float, datetime, date, time |
| `gte` | Greater than or equal | `created_at__gte=2024-01-01` | int, float, datetime, date, time |
| `lte` | Less than or equal | `price__lte=100` | int, float, datetime, date, time |
| `in` | In list | `id__in=1,2,3` | all |
| `not_in` | Not in list | `status__not_in=deleted,archived` | all |
| `between` | Range (inclusive) | `age__between=18,65` | all |
| `like` | SQL LIKE pattern | `name__like=%john%` | str |
| `ilike` | SQL ILIKE (case-insensitive) | `email__ilike=%gmail%` | str |
| `icontains` | Case-insensitive contains | `title__icontains=python` | str |
| `contains` | Case-sensitive contains | `title__contains=Python` | str |
| `startswith` | Starts with | `name__startswith=John` | str |
| `istartswith` | Case-insensitive starts with | `name__istartswith=john` | str |
| `endswith` | Ends with | `name__endswith=Doe` | str |
| `iendswith` | Case-insensitive ends with | `name__iendswith=doe` | str |
| `isnull` | Check if value is NULL or NOT NULL | `status__isnull=true` | all |
| `not_isnull` | Inverse of isnull (semantically cleaner) | `status__not_isnull=true` | all |

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

        # Maximum depth for recursive relationship filtering (default: 1)
        max_depth = 1

        # Whether to forbid all unknown query parameters (default: False)
        strict = False

        # Optional: explicit whitelist of fields allowed for sorting (default: None = all fields)
        sort_columns = ["id", "title", "created_at", "author__name"]

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
- **max_depth**: Set the recursion limit for relationship filtering. Increase this to allow filtering by fields in nested models (e.g., `author__team__name__eq`).
- **strict**: Enable total strict mode to reject any query parameter not defined in the filter model (returns 422 error). In strict mode, this also applies to `sort_by` — any field not in `sort_columns` returns 422.
- **sort_columns**: Explicit list of field names allowed as sort targets. When set, only listed fields can be used with `sort_by`. If `None`, all leaf fields from the schema are valid sort targets. In `strict` mode, passing an unlisted field returns a 422 error; otherwise it is silently ignored.
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

### Multi-level Relationships 🌳

Use `max_depth` to control how deep the relationships can go (default is 1):

```python
class PostOut(BaseModel):
    author: UserOut # UserOut has a 'team' relationship

    class FilterConfig:
        max_depth = 2 # Allow Post -> User -> Team

# Filter posts by author's team name
GET /posts?author__team__name__eq=Medical
```

### Strict Validation Mode 🛡️

By default, unknown query parameters are ignored. Enable `strict` mode to reject malformed requests or unauthorized parameters:

```python
class FilterConfig:
    strict = True
    prefix = "f_"

# These will return 422 Unprocessable Entity:
GET /posts?invalid_param=1
GET /posts?f_typo__eq=value
GET /posts?page=1 # Even unrelated params are blocked in total strict mode
```

Strict mode also validates the `sort_by` parameter when `sort_columns` is defined. Any sort field not in the whitelist returns 422:

```python
class FilterConfig:
    strict = True
    sort_columns = ["id", "created_at"]

# 422 — not in sort_columns
GET /posts?sort_by=title
GET /posts?sort_by=author__team__name
```

### Dynamic Sorting

Sort by multiple fields with ascending/descending order:

```bash
# Sort by created_at (descending), then by title (ascending)
GET /posts?sort_by=-created_at,title

# Sort by multiple fields
GET /posts?sort_by=-updated_at,id,name
```

By default, all schema leaf fields (including nested ones) are valid sort targets. Use `sort_columns` to restrict which fields can be sorted:

```python
class PostOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    author: UserOut  # UserOut has 'name', 'team', etc.

    class FilterConfig:
        sort_field = "sort_by"
        sort_columns = ["id", "created_at", "author__name"]  # Only these are sortable
```

```bash
# Allowed
GET /posts?sort_by=id
GET /posts?sort_by=-created_at,author__name

# Silently ignored (strict=False, the default)
GET /posts?sort_by=title

# Returns 422 if strict=True
GET /posts?sort_by=title
GET /posts?sort_by=author__team__name
```

When `strict = True`, any `sort_by` value not present in `sort_columns` returns a **422 Unprocessable Entity**:

```python
class FilterConfig:
    strict = True
    sort_columns = ["id", "created_at"]
```

```bash
# 422 — 'title' is not in sort_columns
GET /posts?sort_by=title

# 422 — '-title' strips the '-' direction prefix, then validates 'title'
GET /posts?sort_by=-title

# 422 — 'id' is valid but 'title' is not, whole request is rejected
GET /posts?sort_by=id,title
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
