# Sorting Configuration

Three parameters control dynamic sorting behavior:

| Parameter | Type | Default |
| :--- | :--- | :--- |
| `enable_sort` | `bool` | `True` |
| `sort_field` | `str` | `"sort_by"` |
| `sort_columns` | `list[str] | None` | `None` |

---

## `enable_sort`

Toggles dynamic sorting on or off entirely for a schema.

```python
class FilterConfig:
    enable_sort = False  # No sort parameter will be generated
```

When `False`, the `sort_field` parameter won't appear in the generated filter model.

---

## `sort_field`

The name of the query parameter used to specify sorting.

```python
class FilterConfig:
    sort_field = "order"  # default is "sort_by"
```

| Default | Custom |
| :--- | :--- |
| `GET /posts?sort_by=-created_at` | `GET /posts?order=-created_at` |

!!! info
    The `sort_field` parameter is always excluded from strict mode validation — it's always considered a valid parameter when `enable_sort = True`.

---

## `sort_columns`

An explicit list of field names allowed for sorting. When `None` (the default), all schema fields are sortable.

```python
class FilterConfig:
    sort_columns = ["id", "created_at", "title"]
```

!!! tip "Always define `sort_columns` in production"
    Leaving `sort_columns = None` allows sorting by any field, including non-indexed ones. This can lead to slow queries on large tables. Explicitly whitelisting columns gives you full control.

---

## How Sorting Works

### Ascending and Descending

Prefix the field name with `-` for descending order:

| Request | SQL |
| :--- | :--- |
| `GET /posts?sort_by=title` | `ORDER BY title ASC` |
| `GET /posts?sort_by=-title` | `ORDER BY title DESC` |

### Multiple Fields

Separate multiple fields with commas:

`GET /posts?sort_by=-is_active,created_at`

```sql
ORDER BY is_active DESC, created_at ASC
```

### Sorting by Nested Fields

You can sort by fields in related models. The field path follows the same double-underscore notation, including the prefix if one is set:

```python
class FilterConfig:
    prefix = "f_"
    sort_columns = ["id", "post_title", "author__team__name"]
```

Request: `GET /posts?sort_by=author__team__name`

The adapter automatically performs the necessary `JOIN` to resolve the column.

### Sorting by Aliased Fields

If a field has a `filter_alias` defined (see [json_schema_extra](json-schema-extra.md)), use the alias name in the sort parameter:

```python
class PostOut(BaseModel):
    title: str = Field(
        alias="post_title",
        json_schema_extra={"filters": ["eq"], "filter_alias": "post_title"},
    )

    class FilterConfig:
        sort_columns = ["post_title"]
```

Request: `GET /posts?sort_by=post_title` or `GET /posts?sort_by=-post_title`

---

## Unknown Sort Fields

If a user tries to sort by a field not in `sort_columns`:

- **Non-Strict Mode** (`strict = False`): The field is **silently ignored**. No error is raised, and the result is returned using the default database order.

```python
class FilterConfig:
    strict = False
    sort_columns = ["id", "created_at"]
```

Request: `GET /posts?sort_by=email`
Result: ✅ **200 OK** (sorting is ignored as `email` is not in `sort_columns`)

- **Strict Mode** (`strict = True`): The request is **rejected** with a validation error.

```python
class FilterConfig:
    strict = True
    sort_columns = ["id", "created_at"]
```

Request: `GET /posts?sort_by=email`
Result: ❌ **422 Unprocessable Entity** (error: `email` is not allowed)

---

## Full Example

```python
class PostOut(BaseModel):
    title: str = Field(
        alias="post_title",
        json_schema_extra={"filters": ["eq", "icontains"], "filter_alias": "post_title"},
    )
    created_at: datetime = Field(json_schema_extra={"filters": ["gte", "lte"]})
    author: UserOut

    class FilterConfig:
        enable_sort = True
        sort_field = "sort_by"
        sort_columns = ["id", "post_title", "created_at", "author__team__name"]

        prefix = "f_"
```
