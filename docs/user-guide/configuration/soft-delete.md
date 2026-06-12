# `soft_delete_field` / `soft_delete_active_value`

- **`soft_delete_field` type:** `str | None`
- **`soft_delete_field` default:** `None`
- **`soft_delete_active_value` type:** `Any`
- **`soft_delete_active_value` default:** `None`

Automatically excludes logically deleted records from all queries without any manual `.where()` clause in your endpoints.

---

## How It Works

When `soft_delete_field` is set, `apply_filters` injects a `WHERE` condition **before** any user-supplied filters are evaluated:

- If the column type is **Boolean** → filters by `col IS False`
- If the column type is **Date / DateTime** (or any other type) → filters by `col IS NULL`

This works transparently with **SQLite**, **PostgreSQL**, and **MySQL/MariaDB** because it uses standard SQLAlchemy expressions that compile correctly on every dialect.

---

## Minimal Setup

### Boolean flag (`is_deleted`, `is_destroyed`)

```python
from pydantic import BaseModel, ConfigDict, Field


class ArtifactOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq"]})
    name: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    is_destroyed: bool = Field(json_schema_extra={"filters": ["eq"]})

    class FilterConfig:
        soft_delete_field = "is_destroyed"
        # soft_delete_active_value is auto-detected as False for boolean columns

    model_config = ConfigDict(from_attributes=True)
```

```bash
GET /artifacts   # WHERE is_destroyed IS false
```

### Timestamp (`deleted_at`, `decommissioned_at`)

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PostOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq"]})
    title: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    deleted_at: datetime | None = Field(None, json_schema_extra={"filters": ["isnull"]})

    class FilterConfig:
        soft_delete_field = "deleted_at"
        # soft_delete_active_value is auto-detected as NULL for datetime columns

    model_config = ConfigDict(from_attributes=True)
```

```bash
GET /posts   # WHERE deleted_at IS NULL
```

---

## Custom Active Value

If your convention doesn't match the auto-detection rules, provide an explicit active value:

```python
class FilterConfig:
    soft_delete_field = "status"
    soft_delete_active_value = "active"  # WHERE status = 'active'
```

| `soft_delete_active_value` | Condition injected |
| :--- | :--- |
| `None` + Boolean column | `col IS false` |
| `None` + Date/DateTime column | `col IS NULL` |
| `False` | `col = false` (equivalent to auto-detect for booleans) |
| `"active"` | `col = 'active'` |
| `1` | `col = 1` |

---

## Database Compatibility

No custom compiler is needed. The expressions used (`col.is_(False)` and `col.is_(None)`) compile natively on all supported databases:

| Expression | PostgreSQL | MySQL / MariaDB | SQLite |
| :--- | :--- | :--- | :--- |
| `col.is_(False)` | `col IS false` | `col IS false` | `col IS 0` |
| `col.is_(None)` | `col IS NULL` | `col IS NULL` | `col IS NULL` |

---

## Full Example

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterDep, FilterValues
from fastapi_query_filters.orm.sqlalchemy import apply_filters


class PostOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq"]})
    title: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    deleted_at: datetime | None = Field(None, json_schema_extra={"filters": ["isnull"]})

    class FilterConfig:
        soft_delete_field = "deleted_at"

    model_config = ConfigDict(from_attributes=True)


app = FastAPI()


@app.get("/posts", response_model=list[PostOut])
def list_posts(
    db: Session = Depends(get_db),
    filters: FilterValues = FilterDep(PostOut),
) -> list[PostOut]:
    stmt = select(Post)
    stmt = apply_filters(stmt, Post, filters)  # WHERE deleted_at IS NULL injected automatically
    return db.execute(stmt).scalars().all()
```

!!! tip
    See a complete working example in [examples/soft_delete_app/](https://github.com/ezeparziale/fastapi-query-filters/tree/main/examples/soft_delete_app).
