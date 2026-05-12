# Field Configuration (`json_schema_extra`)

Each field in your Pydantic schema can carry metadata that controls how filters are generated for it. This is done through Pydantic's `json_schema_extra` parameter in `Field`.

```python
from pydantic import BaseModel, Field

class PostOut(BaseModel):
    title: str = Field(
        json_schema_extra={
            "filters": ["eq", "icontains"],
        }
    )
```

---

## Supported Keys

| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `filters` | `list[str]` | Yes (to enable filters) | List of operators allowed for this field |
| `filter_alias` | `str` | No | Custom name for the filter parameter in the query string |

---

## `filters`

Defines which operators are available for this field. If omitted or empty, no filter parameters are generated for the field.

```python
class PostOut(BaseModel):
    title: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    score: float = Field(json_schema_extra={"filters": ["gte", "lte"]})
    deleted_at: datetime | None = Field(None, json_schema_extra={"filters": ["isnull"]})
    description: str | None = Field(None)  # no filters — never filterable
```

See the full list of supported operators in [Operators Reference](../operators.md).

!!! tip
    Only declare the operators your API actually needs. Fewer operators = cleaner Swagger docs and a smaller attack surface.

---

## `filter_alias`

By default, the filter parameter name is derived from the field name or its Pydantic alias. Use `filter_alias` to override this with an explicit name for your API.

```python
class PostOut(BaseModel):
    title: str = Field(
        alias="post_title",           # Pydantic response alias
        json_schema_extra={
            "filters": ["eq", "icontains"],
            "filter_alias": "web_title",  # filter parameter uses this name
        },
    )
```

| Config | Generated Parameter |
| :--- | :--- |
| **With `filter_alias`** | `web_title__eq` |
| **Without `filter_alias`** (uses `alias`) | `post_title__eq` |
| **Without `alias`** (uses field name) | `title__eq` |

---

## Alias Priority

The library follows a specific priority when determining the name of the filter parameter:

1.  **`filter_alias`** in `json_schema_extra` (Highest priority)
2.  Pydantic's standard **`alias`**
3.  The Python **field name** (Lowest priority)

!!! tip
    If you want your filters to match your Pydantic aliases exactly, you don't need to specify `filter_alias` — it happens automatically.

---

## Combining All Keys

Here is a real-world example:

```python
class PostOut(BaseModel):
    id: int = Field(
        json_schema_extra={"filters": ["eq", "in", "not_in"]}
    )
    title: str = Field(
        alias="post_title",
        json_schema_extra={
            "filters": ["eq", "icontains"],
            "filter_alias": "post_title",
        },
    )
    user_id: int = Field(
        json_schema_extra={
            "filters": ["eq"],
            "filter_alias": "userId",
        },
    )
    deleted_at: datetime | None = Field(
        None,
        json_schema_extra={"filters": ["isnull"]},
    )
    description: str | None = Field(None)  # intentionally not filterable

    model_config = ConfigDict(from_attributes=True, validate_by_name=True)
```

Generated filter parameters (with `prefix = "f_"`):

- `f_id__eq`, `f_id__in`, `f_id__not_in`
- `f_post_title__eq`, `f_post_title__icontains`
- `f_userId__eq`
- `f_deleted_at__isnull`
