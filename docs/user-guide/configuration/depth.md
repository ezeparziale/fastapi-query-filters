# `max_depth`

- **Type:** `int`
- **Default:** `1`

Controls how many levels of nested relationships are traversed when generating filter fields from your schema.

---

## Understanding Depth

Consider this schema structure:

```
Post
 └── author (User)         ← depth 1
      └── team (Team)      ← depth 2
           └── org (Org)   ← depth 3
```

With `max_depth = 1`, only `Post` fields and direct `author` fields are available as filters.
With `max_depth = 2`, `team` fields become available too.

---

## Example

```python
class TeamOut(BaseModel):
    name: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})

class UserOut(BaseModel):
    email: str = Field(json_schema_extra={"filters": ["eq"]})
    team: TeamOut

class PostOut(BaseModel):
    title: str = Field(json_schema_extra={"filters": ["eq"]})
    author: UserOut

    class FilterConfig:
        max_depth = 1  # default
```

With `max_depth = 1`:

| Available | Not Available |
| :--- | :--- |
| `title__eq` | `author__team__name__eq` |
| `author__email__eq` | |

With `max_depth = 2`:

| Available |
| :--- |
| `title__eq` |
| `author__email__eq` |
| `author__team__name__eq` |
| `author__team__name__icontains` |

---

## Increasing Depth

```python
class FilterConfig:
    max_depth = 2
```

Request: `GET /posts?f_author__team__name__eq=SG-1`

The SQLAlchemy adapter will automatically perform the necessary joins:

```sql
JOIN users ON posts.user_id = users.id
JOIN teams ON users.team_id = teams.id
WHERE teams.name = 'SG-1'
```

---

!!! warning "Performance consideration"
    Increasing `max_depth` generates more filter fields and potentially more complex SQL joins. Only increase it as needed, and consider using [`sort_columns`](sorting.md) and explicit `filters` lists to limit what's actually exposed.

!!! tip
    `max_depth` only controls filter generation. The SQLAlchemy adapter always resolves joins dynamically at query time based on the filters actually provided in the request.
