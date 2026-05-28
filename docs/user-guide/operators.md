# Operators Reference

This page describes all supported filter operators and how they translate to SQL queries.

---

## Operator Mapping

When you use a filter like `age__gt=18`, the library splits it into the field (`age`) and the operator (`gt`). Here is how each operator behaves:

| Operator | SQL Equivalent (SQLAlchemy) | Supported Types | Description |
| :--- | :--- | :--- | :--- |
| `eq` | `col = :val` | all types (except `dict`, including `bool`) | Exact match |
| `ne` | `col != :val` | all types (except `dict`, including `bool`) | Not equal |
| `gt` | `col > :val` | `int`, `float`, `datetime`, `date`, `time` | Greater than |
| `lt` | `col < :val` | `int`, `float`, `datetime`, `date`, `time` | Less than |
| `gte` | `col >= :val` | `int`, `float`, `datetime`, `date`, `time` | Greater than or equal |
| `lte` | `col <= :val` | `int`, `float`, `datetime`, `date`, `time` | Less than or equal |
| `like` | `col LIKE :val` | `str` | SQL LIKE (case-sensitive) |
| `ilike` | `col ILIKE :val` | `str` | SQL ILIKE (case-insensitive) |
| `icontains` | `col ILIKE '%val%'` | `str` | Case-insensitive substring match |
| `contains` | `col LIKE '%val%'` | `str` | Case-sensitive substring match |
| `startswith` | `col LIKE 'val%'` | `str` | Starts with (case-sensitive) |
| `istartswith` | `col ILIKE 'val%'` | `str` | Starts with (case-insensitive) |
| `endswith` | `col LIKE '%val'` | `str` | Ends with (case-sensitive) |
| `iendswith` | `col ILIKE '%val'` | `str` | Ends with (case-insensitive) |
| `in` | `col IN (...)` | `int`, `str`, `datetime`, `date`, `time` | Match any value in a list |
| `not_in` | `col NOT IN (...)` | `int`, `str`, `datetime`, `date`, `time` | Match none of values in a list |
| `between` | `col BETWEEN :v1 AND :v2` | `int`, `float`, `str`, `datetime`, `date`, `time` | Value within inclusive range |
| `isnull` | `col IS NULL` | all types (including `dict`, `bool`) | Check for NULL |
| `not_isnull` | `col IS NOT NULL` | all types (including `dict`, `bool`) | Check for NOT NULL |
| `is_empty` | `col = '{}'` | `dict` | Check if dictionary is empty `{}` |
| `is_blank` | `col = '{}' OR col IS NULL` | `dict` | Check if dictionary is empty `{}` or NULL |
| `has_key` | dialect-specific JSON key existence check | `dict` | Check if dictionary contains a key |
| `has_any_keys` | dialect-specific JSON key existence check | `dict` | Check if dictionary contains at least one key from a list |
| `has_all_keys` | dialect-specific JSON key existence check | `dict` | Check if dictionary contains all keys from a list |
| `arr_contains` | dialect-specific array containment check | `list` | Check if an array contains a value |
| `arr_overlap` | dialect-specific array overlap check | `list` | Check if an array shares at least one value with a list |
| `arr_all` | dialect-specific array containment check | `list` | Check if an array contains all values from a list |
| `arr_any` | dialect-specific array overlap check | `list` | Check if an array contains any value from a list |
| `arr_len` | `array_length(col) = :n` | `list` | Check if an array has the expected length |

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

### Support for JSON / Dictionary Fields

You can query keys inside a JSON/dictionary field using double underscores `__` (which requires tipping the field with a Pydantic sub-model).

Additionally, you can perform queries on the entire JSON column/dictionary using the following operators:
- **`is_empty`**: Validates whether the dictionary is exactly `{}` (empty JSON object).
- **`is_blank`**: Validates whether the dictionary is exactly `{}` OR is `NULL` in the database.
- **`has_key`**: Validates whether the dictionary contains a specific key.
- **`has_any_keys`**: Validates whether the dictionary contains at least one key from a provided list.
- **`has_all_keys`**: Validates whether the dictionary contains all keys from a provided list.

These boolean operators are highly useful for filtering empty/blank fields and can be combined with `isnull` for more complex criteria.

### Support for Array Fields

You can also expose `list[...]` fields in your schema and filter them with array-specific operators:

- **`arr_contains`**: Array contains the provided scalar value.
- **`arr_overlap`**: Array shares at least one value with the provided list.
- **`arr_all`**: Array contains all values from the provided list.
- **`arr_any`**: Array contains any value from the provided list.
- **`arr_len`**: Array length matches the provided integer.
- **`is_empty`**: Array is empty.
- **`is_blank`**: Array is empty or `NULL`.

!!! example "Array Filters"
    ```python
    from pydantic import BaseModel, Field

    class PostSchema(BaseModel):
        tags: list[str] = Field(
            default_factory=list,
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
            },
        )
    ```

    - `?tags__arr_contains=desert` -> Matches rows where `tags` contains `desert`.
    - `?tags__arr_overlap=desert,jaffa` -> Matches rows where `tags` contains at least one of those values.
    - `?tags__arr_all=desert,ancient` -> Matches rows where `tags` contains all values.
    - `?tags__arr_any=medical,inventory` -> Matches rows where `tags` contains any value.
    - `?tags__arr_len=3` -> Matches rows where `tags` has exactly 3 elements.
    - `?tags__is_empty=true` -> Matches rows where `tags` is `[]`.
    - `?tags__is_blank=true` -> Matches rows where `tags` is `[]` or `NULL`.

!!! example "Dictionary Filters"
    ```python
    from pydantic import BaseModel, Field

    class MissionSchema(BaseModel):
        # Allow checking if the metadata dict is empty or blank
        metadata: dict = Field(
            json_schema_extra={
                "filters": [
                    "is_empty",
                    "is_blank",
                    "isnull",
                    "has_key",
                    "has_any_keys",
                    "has_all_keys",
                ]
            }
        )
    ```

    - `?metadata__is_empty=true` -> Matches records where `metadata` is exactly `{}`.
    - `?metadata__is_empty=false` -> Matches records where `metadata` is NOT `{}` (and is not null).
    - `?metadata__is_blank=true` -> Matches records where `metadata` is `{}` OR `NULL`.
    - `?metadata__is_blank=false` -> Matches records where `metadata` is NOT `{}` AND NOT `NULL`.
    - `?metadata__has_key=commander` -> Matches records where key `commander` exists.
    - `?metadata__has_any_keys=commander,danger_level` -> Matches records where at least one of those keys exists.
    - `?metadata__has_all_keys=commander,danger_level` -> Matches records where all provided keys exist.

!!! tip "JSON Example"
    For a complete working example of filtering complex JSON structures, see the [examples/json_app/](https://github.com/ezeparziale/fastapi-query-filters/tree/main/examples/json_app) directory.

---

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

### Range Filtering (between)
`GET /posts?age__between=18,65` -> `SELECT ... WHERE age BETWEEN 18 AND 65`

### Case-Insensitive Search
`GET /posts?author__icontains=doe` -> `SELECT ... WHERE author ILIKE '%doe%'`

### Advanced Text Search
- **Starts with**: `GET /posts?title__startswith=Hello` -> `SELECT ... WHERE title LIKE 'Hello%'`
- **Ends with**: `GET /posts?email__iendswith=gmail.com` -> `SELECT ... WHERE email ILIKE '%gmail.com'`
- **Contains (Sensitive)**: `GET /posts?content__contains=Python` -> `SELECT ... WHERE content LIKE '%Python%'`

---

## Handling `isnull`

The `isnull` operator expects a boolean-like value. It supports all standard Pydantic boolean conversions:

- **Truthy (IS NULL)**: `true`, `yes`, `y`, `on`, `t`, `1`
- **Falsy (IS NOT NULL)**: `false`, `no`, `n`, `off`, `f`, `0`

!!! example "isnull usage"
    - `?deleted_at__isnull=true` -> `WHERE deleted_at IS NULL`
    - `?deleted_at__isnull=no` -> `WHERE deleted_at IS NOT NULL`
    - `?deleted_at__isnull=1` -> `WHERE deleted_at IS NULL`

### `not_isnull` usage
Identical truthiness rules as `isnull`, but with inverted logic.
- `?profile_bio__not_isnull=true` -> `WHERE profile_bio IS NOT NULL`
- `?profile_bio__not_isnull=false` -> `WHERE profile_bio IS NULL`
