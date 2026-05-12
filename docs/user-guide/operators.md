# Operators Reference

This page describes all supported filter operators and how they translate to SQL queries.

---

## Operator Mapping

When you use a filter like `age__gt=18`, the library splits it into the field (`age`) and the operator (`gt`). Here is how each operator behaves:

| Operator | SQL Equivalent (SQLAlchemy) | Supported Types | Description |
| :--- | :--- | :--- | :--- |
| `eq` | `col = :val` | All | Exact match |
| `ne` | `col != :val` | All | Not equal |
| `gt` | `col > :val` | Number, Date, Time | Greater than |
| `lt` | `col < :val` | Number, Date, Time | Less than |
| `gte` | `col >= :val` | Number, Date, Time | Greater than or equal |
| `lte` | `col <= :val` | Number, Date, Time | Less than or equal |
| `like` | `col LIKE :val` | `str` | SQL LIKE (case-sensitive) |
| `ilike` | `col ILIKE :val` | `str` | SQL ILIKE (case-insensitive) |
| `icontains` | `col ILIKE '%val%'` | `str` | Case-insensitive substring match |
| `in` | `col IN (...)` | All | Match any value in a list |
| `not_in` | `col NOT IN (...)` | All | Match none of the values in a list |
| `isnull` | `col IS NULL` | All | Check for NULL (expects a boolean-like value) |

---

## Enabling Filters in your Schema

By default, no filters are enabled for your schema fields. You must explicitly define which operators are allowed for each field using the `json_schema_extra` metadata in Pydantic's `Field`.

!!! example "Explicit Filter Definition"
    ```python
    from pydantic import BaseModel, Field

    class ProductSchema(BaseModel):
        name: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
        price: float = Field(json_schema_extra={"filters": ["gt", "lt"]})
        is_available: bool = Field(json_schema_extra={"filters": ["eq"]})
    ```

This explicit approach ensures your API doesn't expose more filters than intended, keeping your queries optimized and your API documentation clean.

---

## Usage Examples

### Simple Filtering
`GET /posts?title__eq=Hello` -> `SELECT ... WHERE title = 'Hello'`

### List Filtering (Comma-separated)
`GET /posts?status__in=draft,published` -> `SELECT ... WHERE status IN ('draft', 'published')`

### Date Ranges
`GET /posts?created_at__gte=2024-01-01&created_at__lte=2024-12-31`
-> `SELECT ... WHERE created_at >= '2024-01-01' AND created_at <= '2024-12-31'`

### Case-Insensitive Search
`GET /posts?author__icontains=doe` -> `SELECT ... WHERE author ILIKE '%doe%'`

---

## Handling `isnull`

The `isnull` operator expects a boolean-like value. It supports all standard Pydantic boolean conversions:

- **Truthy (IS NULL)**: `true`, `yes`, `y`, `on`, `t`, `1`
- **Falsy (IS NOT NULL)**: `false`, `no`, `n`, `off`, `f`, `0`

!!! example "isnull usage"
    - `?deleted_at__isnull=true` -> `WHERE deleted_at IS NULL`
    - `?deleted_at__isnull=no` -> `WHERE deleted_at IS NOT NULL`
    - `?deleted_at__isnull=1` -> `WHERE deleted_at IS NULL`
