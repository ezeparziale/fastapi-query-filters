# `extra_filters`

- **Type:** `type[BaseModel] | None`
- **Default:** `None`

Allows you to define additional "virtual" filter fields that don't exist in your response schema but should be available as query parameters.

---

## When to Use It

The most common use case is filtering by a field from a related model that isn't exposed in your response schema.

For example: your `PostOut` schema doesn't include `author.age` directly, but you want to allow `GET /posts?f_author__age__gte=30`.

Without `extra_filters`, you would have to add `author__age` to `PostOut` just to enable this filter — polluting your response schema. With `extra_filters`, you keep them separate.

---

## Defining Extra Filters

Create a separate `BaseModel` with the virtual fields:

```python
from pydantic import BaseModel, Field

class PostFilterExtra(BaseModel):
    author__age: int | None = Field(
        default=None,
        json_schema_extra={"filters": ["gt", "lt", "gte", "lte", "in", "not_in"]},
    )
```

Then reference it in `FilterConfig`:

```python
class PostOut(BaseModel):
    title: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    author: UserOut

    class FilterConfig:
        extra_filters = PostFilterExtra
```

Now these parameters are available:

- `f_author__age__gt`
- `f_author__age__lt`
- `f_author__age__gte`
- `f_author__age__lte`
- `f_author__age__in`
- `f_author__age__not_in`

---

## Field Naming Convention

The field name in `extra_filters` uses double underscores to represent the relationship path. The library maps it to the correct nested column automatically:

| Field name in `extra_filters` | Resolves to |
| :--- | :--- |
| `author__age` | `users.age` (via JOIN on `posts.user_id`) |
| `author__team__name` | `teams.name` (via two JOINs) |

---

## Using Extra Filters with Prefix

If your schema has a `prefix`, it is automatically applied to `extra_filters` fields as well:

```python
class FilterConfig:
    prefix = "f_"
    extra_filters = PostFilterExtra
```

| Field | Query parameter |
| :--- | :--- |
| `author__age` | `f_author__age__gte` |

---

## Extra Filters in Strict Mode

Fields defined in `extra_filters` are fully recognized in [`strict`](strict.md) mode — only the operators you declare are valid:

```python
class PostFilterExtra(BaseModel):
    author__age: int | None = Field(
        default=None,
        json_schema_extra={"filters": ["gte", "lte"]},  # only these two
    )
```

| Request | Result |
| :--- | :--- |
| `GET /posts?f_author__age__gte=30` | ✅ 200 OK |
| `GET /posts?f_author__age__eq=30` | ❌ 422 — `eq` not declared |

---

## Full Example

```python
from pydantic import BaseModel, Field


class PostFilterExtra(BaseModel):
    author__age: int | None = Field(
        default=None,
        json_schema_extra={"filters": ["gt", "lt", "gte", "lte", "in", "not_in"]},
    )


class PostOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq", "in"]})
    title: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    author: UserOut

    class FilterConfig:
        prefix = "f_"
        strict = True
        extra_filters = PostFilterExtra
```

Available extra parameters:
- `f_author__age__gt`
- `f_author__age__lt`
- `f_author__age__gte`
- `f_author__age__lte`
- `f_author__age__in`
- `f_author__age__not_in`
