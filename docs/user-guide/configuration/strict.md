# `strict`

- **Type:** `bool`
- **Default:** `False`

When `strict = True`, the library will reject any query parameter that doesn't correspond to a defined filter field, raising a **422 Unprocessable Entity** error.

By default (`strict = False`), unknown parameters are silently ignored.

---

## When to Use It

Enable strict mode when you want to:

- Prevent accidental typos in filter names from silently returning unfiltered results.
- Enforce a clean API contract where clients must only send known parameters.
- Catch frontend bugs early (a misspelled `f_tittle__eq` will return a 422 instead of all records).

---

## Example

```python
class PostOut(BaseModel):
    title: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    is_active: bool = Field(json_schema_extra={"filters": ["eq"]})

    class FilterConfig:
        strict = True
```

| Request | Result |
| :--- | :--- |
| `GET /posts?title__eq=hello` | ✅ 200 OK |
| `GET /posts?title__icontains=hello` | ✅ 200 OK |
| `GET /posts?unknown_param=value` | ❌ 422 Unprocessable Entity |
| `GET /posts?title__like=hello` | ❌ 422 — `like` not declared for `title` |

---

## Strict Mode and Dynamic Sorting

Strict mode also validates the **values** passed to the sort parameter (e.g., `sort_by`). Every field listed in the sort parameter must be present in the whitelist:

- If `sort_columns` is defined, only those fields are allowed.
- If `sort_columns` is `None` (default), only valid schema fields are allowed.

```python
class FilterConfig:
    strict = True
    sort_columns = ["id", "created_at"]
```

| Request | Result |
| :--- | :--- |
| `GET /posts?sort_by=id` | ✅ 200 OK |
| `GET /posts?sort_by=-created_at` | ✅ 200 OK |
| `GET /posts?sort_by=title` | ❌ 422 — `title` not in `sort_columns` |

---

## Strict Mode with `extra_filters`

Fields defined in [`extra_filters`](extra-filters.md) are also allowed in strict mode:

```python
class PostFilterExtra(BaseModel):
    author__age: int | None = Field(
        default=None,
        json_schema_extra={"filters": ["gte", "lte"]},
    )

class PostOut(BaseModel):
    title: str = Field(json_schema_extra={"filters": ["eq"]})

    class FilterConfig:
        strict = True
        extra_filters = PostFilterExtra
```

| Request | Result |
| :--- | :--- |
| `GET /posts?title__eq=hello` | ✅ 200 OK |
| `GET /posts?author__age__gte=30` | ✅ 200 OK — defined in `extra_filters` |
| `GET /posts?author__age__eq=30` | ❌ 422 — `eq` not declared for `author__age` |

---

## Strict Mode with Prefix

When using [`prefix`](prefix.md), strict mode enforces that the prefix is always present:

```python
class FilterConfig:
    prefix = "f_"
    strict = True
```

| Request | Result |
| :--- | :--- |
| `GET /posts?f_title__eq=hello` | ✅ 200 OK |
| `GET /posts?title__eq=hello` | ❌ 422 — missing prefix |

---

!!! warning "Common Friction Point"
    `strict = True` is the most common source of unexpected 422 errors. If you enable it, make sure your `search_field` and `sort_field` names are also accounted for — they are included as valid parameters automatically.
