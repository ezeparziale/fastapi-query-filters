# `prefix`

- **Type:** `str`
- **Default:** `""`

A string prepended to every filter query parameter generated from the schema. This is useful to avoid collisions with pagination, sorting, or any other query parameters your API already uses.

---

## Basic Example

```python
class PostOut(BaseModel):
    title: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    is_active: bool = Field(json_schema_extra={"filters": ["eq"]})

    class FilterConfig:
        prefix = "f_"
```

With `prefix = "f_"`, the generated filter parameters become:

| Without prefix | With `prefix = "f_"` |
| :--- | :--- |
| `title__eq` | `f_title__eq` |
| `title__icontains` | `f_title__icontains` |
| `is_active__eq` | `f_is_active__eq` |

Request: `GET /posts?f_title__icontains=hello&f_is_active__eq=true`

---

## Prefix and Nested Fields

The prefix applies to all fields, including nested ones. It is prepended to the entire field path:

```python
class PostOut(BaseModel):
    title: str = Field(json_schema_extra={"filters": ["eq"]})
    author: UserOut  # nested schema

    class FilterConfig:
        prefix = "f_"
```

Generated parameters:
- `f_title__eq`
- `f_author__name__eq`
- `f_author__email__icontains`

---

## Prefix and Sort Columns

When using `sort_columns` together with a prefix, the library validates that the value in `sort_by` matches exactly one of the entries in your whitelist.

It is common to allow sorting by the **schema field names** (without the prefix), even if your filters are prefixed.

```python
class FilterConfig:
    prefix = "f_"
    # We allow sorting by 'id' (unprefixed)
    sort_columns = ["id", "post_title"]
```

| Request | Result (with `strict = True`) |
| :--- | :--- |
| `GET /posts?sort_by=id` | ✅ **200 OK** |
| `GET /posts?sort_by=f_id` | ❌ **422 Error** (f_id is not in `sort_columns`) |

---

## Disabling the Prefix

To remove the prefix (for example in a subclass or test variant), set it to an empty string:

```python
class PostOutNoPrefix(PostOut):
    class FilterConfig(PostOut.FilterConfig):
        prefix = ""
```

!!! warning "Strict mode and prefix enforcement"
    If `strict = True` is enabled, the prefix is strictly enforced for all **filter** fields (e.g., `f_title__eq`). A request using the unprefixed version of a filter parameter will be rejected with a **422** error.
