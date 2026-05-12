# Basic Usage

This tutorial walks you through integrating `fastapi-query-filters` into a FastAPI + SQLAlchemy application from scratch. By the end, you'll have a working `/posts` endpoint that supports filtering, search, and sorting via query parameters.

---

## What You'll Build

A `GET /posts` endpoint that responds to requests like:

- `GET /posts?title__icontains=stargate` — filter by title
- `GET /posts?q=mission` — global search across title and description
- `GET /posts?sort_by=-created_at` — sort by newest first
- `GET /posts?is_active__eq=true&sort_by=title` — combine filters and sorting

---

## 1. The SQLAlchemy Model

Define your database model as usual:

```python
from datetime import datetime
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

---

## 2. The Pydantic Schema

This is where you define which filters are available. Use `json_schema_extra` with a `"filters"` key on each field you want to be filterable.

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PostOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq", "in"]})
    title: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    description: str | None = Field(None)  # not filterable
    is_active: bool = Field(json_schema_extra={"filters": ["eq"]})
    created_at: datetime = Field(json_schema_extra={"filters": ["gte", "lte"]})

    model_config = ConfigDict(from_attributes=True)

    class FilterConfig:
        search_field = "q"
        search_columns = ["title", "description"]
        sort_field = "sort_by"
        sort_columns = ["id", "title", "created_at"]
```

What this gives you:

| Query parameter | Behavior |
| :--- | :--- |
| `id__eq=1` | exact match on id |
| `id__in=1,2,3` | id is one of 1, 2, 3 |
| `title__eq=Hello` | exact match on title |
| `title__icontains=hello` | case-insensitive substring match |
| `is_active__eq=true` | boolean filter |
| `created_at__gte=2024-01-01T00:00:00` | datetime range start |
| `created_at__lte=2024-12-31T23:59:59` | datetime range end |
| `q=stargate` | searches title and description |
| `sort_by=-created_at` | sorts by newest first |
| `sort_by=title,-id` | sorts by title asc, then id desc |

---

## 3. The FastAPI Endpoint

Use `FilterDep` as a dependency and `apply_filters` to modify your SQLAlchemy statement:

```python
from typing import Any
from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi_query_filters import FilterDep, FilterValues
from fastapi_query_filters.orm.sqlalchemy import apply_filters

app = FastAPI()


def get_db() -> Session:
    # your session setup here
    ...


@app.get("/posts", response_model=list[PostOut])
def list_posts(
    filters: FilterValues = FilterDep(PostOut),
    db: Session = Depends(get_db),
) -> Any:
    stmt = select(Post)
    stmt = apply_filters(stmt, Post, filters)
    return db.execute(stmt).scalars().all()
```

That's it. `FilterDep(PostOut)` reads the query parameters from the request, validates them against the schema, and returns a `FilterValues` object. `apply_filters` takes that and builds the SQL.

---

## 4. Making Requests

### Simple filter
`GET /posts?title__icontains=stargate`

```sql
SELECT * FROM posts WHERE title ILIKE '%stargate%'
```

### Boolean filter
`GET /posts?is_active__eq=true`

```sql
SELECT * FROM posts WHERE is_active = true
```

### List filter
`GET /posts?id__in=1,2,3`

```sql
SELECT * FROM posts WHERE id IN (1, 2, 3)
```

### Date range
`GET /posts?created_at__gte=2024-01-01T00:00:00&created_at__lte=2024-12-31T23:59:59`

```sql
SELECT * FROM posts
WHERE created_at >= '2024-01-01 00:00:00'
  AND created_at <= '2024-12-31 23:59:59'
```

### Global search
`GET /posts?q=mission`

```sql
SELECT * FROM posts
WHERE title ILIKE '%mission%'
   OR description ILIKE '%mission%'
```

### Sort descending
`GET /posts?sort_by=-created_at`

```sql
SELECT * FROM posts ORDER BY created_at DESC
```

### Combined
`GET /posts?is_active__eq=true&q=stargate&sort_by=-created_at`

```sql
SELECT * FROM posts
WHERE is_active = true
  AND (title ILIKE '%stargate%' OR description ILIKE '%stargate%')
ORDER BY created_at DESC
```

---

## 5. Validation is Automatic

Pydantic validates every filter value before it reaches your database. Invalid values return a **422** automatically — no extra code needed:

| Request | Result |
| :--- | :--- |
| `?id__eq=abc` | ❌ 422 — `abc` is not an integer |
| `?created_at__gte=not-a-date` | ❌ 422 — not a valid datetime |
| `?is_active__eq=maybe` | ❌ 422 — not a valid boolean |

---

## Next Steps

- Add nested relationship filters → [Advanced Usage](advanced-usage.md)
- Customize global behavior → [Configuration](../user-guide/configuration/index.md)
- See all supported operators → [Operators Reference](../user-guide/operators.md)
- See a full runnable example → [`examples/basic_app`](https://github.com/ezeparziale/fastapi-query-filters/tree/main/examples/basic_app)
