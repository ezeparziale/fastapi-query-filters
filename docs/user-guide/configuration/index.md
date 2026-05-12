# Configuration

All behavior in `fastapi-query-filters` is controlled through a nested `FilterConfig` class inside your Pydantic schema. If you don't define one, sensible defaults are used.

```python
class PostOut(BaseModel):
    title: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})

    class FilterConfig:
        prefix = "f_"
        strict = True
        search_columns = ["title"]
```

---

## Parameters at a Glance

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| [`prefix`](prefix.md) | `str` | `""` | Global prefix added to all filter query params |
| [`strict`](strict.md) | `bool` | `False` | Reject unknown query parameters with 422 |
| [`search_field`](search.md) | `str` | `"q"` | Query param name for global search |
| [`search_columns`](search.md) | `list[str]` | `[]` | Columns included in global search |
| [`enable_search`](search.md) | `bool` | `True` | Toggle global search on/off |
| [`sort_field`](sorting.md) | `str` | `"sort_by"` | Query param name for dynamic sorting |
| [`sort_columns`](sorting.md) | `list[str] | None` | `None` | Allowed columns for sorting (`None` = all) |
| [`enable_sort`](sorting.md) | `bool` | `True` | Toggle dynamic sorting on/off |
| [`max_depth`](depth.md) | `int` | `1` | Max depth for nested relationship filtering |
| [`extra_filters`](extra-filters.md) | `type[BaseModel] | None` | `None` | Additional virtual filter fields |

---

## Inheritance

`FilterConfig` supports class inheritance, which is useful when you want to extend an existing configuration without rewriting it.

```python
class PostOut(BaseModel):
    title: str = Field(json_schema_extra={"filters": ["eq"]})

    class FilterConfig:
        prefix = "f_"
        strict = True
        sort_columns = ["title", "created_at"]


# Variant with prefix disabled for internal use
class PostOutNoPrefix(PostOut):
    class FilterConfig(PostOut.FilterConfig):
        prefix = ""
```

!!! tip
    This pattern is especially useful in tests or when exposing the same resource with slightly different filter rules for different consumers (e.g., public API vs. admin API).
