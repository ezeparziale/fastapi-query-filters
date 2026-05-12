# Search Configuration

Three parameters control global search behavior:

| Parameter | Type | Default |
| :--- | :--- | :--- |
| `enable_search` | `bool` | `True` |
| `search_field` | `str` | `"q"` |
| `search_columns` | `list[str]` | `[]` |

---

## `enable_search`

Toggles global search on or off entirely for a schema.

```python
class FilterConfig:
    enable_search = False  # No search parameter will be generated
```

When `False`, the `search_field` parameter won't appear in the generated filter model and any value sent for it will be ignored (or rejected in strict mode).

---

## `search_field`

The name of the query parameter used to trigger global search.

```python
class FilterConfig:
    search_field = "query"  # default is "q"
```

| Default | Custom |
| :--- | :--- |
| `GET /posts?q=hello` | `GET /posts?query=hello` |

!!! info
    The `search_field` parameter is always excluded from strict mode validation — it's always considered a valid parameter when `enable_search = True`.

---

## `search_columns`

A list of column names to search across. The library applies an `OR` clause with `ILIKE '%value%'` for each column.

```python
class PostOut(BaseModel):
    title: str = Field(json_schema_extra={"filters": ["eq"]})
    description: str | None = Field(None)

    class FilterConfig:
        search_columns = ["title", "description"]
```

Request: `GET /posts?q=stargate`

Generated SQL:
```sql
WHERE title ILIKE '%stargate%'
   OR description ILIKE '%stargate%'
```

!!! warning "Empty list = no search"
    If `search_columns = []` (the default), global search is effectively disabled even if `enable_search = True`. You must explicitly declare the columns.

---

## Searching Non-String Columns

If a column in `search_columns` is not a string type (e.g., `Integer`, `Float`, `UUID`), the adapter automatically casts it to `String` before applying `ILIKE`:

```python
class FilterConfig:
    search_columns = ["title", "id"]  # id is an Integer
```

Generated SQL:
```sql
WHERE title ILIKE '%42%'
   OR CAST(id AS VARCHAR) ILIKE '%42%'
```

---

## Searching Nested Fields

You can search across fields in related models by using the double-underscore notation:

```python
class FilterConfig:
    search_columns = ["title", "author__name", "author__email"]
```

The adapter will automatically perform the necessary `JOIN` and apply the search condition on the related table.

Request: `GET /posts?q=john`

Generated SQL:
```sql
JOIN users ON posts.user_id = users.id
WHERE posts.title ILIKE '%john%'
   OR users.name ILIKE '%john%'
   OR users.email ILIKE '%john%'
```

---

## Full Example

```python
class PostOut(BaseModel):
    title: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    description: str | None = Field(None)
    author: UserOut

    class FilterConfig:
        enable_search = True
        search_field = "q"
        search_columns = ["title", "description", "author__name"]
```
