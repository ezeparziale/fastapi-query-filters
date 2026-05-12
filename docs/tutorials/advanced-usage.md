# Advanced Usage

This tutorial covers the features you'll need for real-world APIs: nested relationship filtering, field aliases, extra virtual filters, prefix configuration, and strict mode.

It assumes you've already read [Basic Usage](basic-usage.md).

---

## What You'll Build

A `GET /posts` endpoint with a rich schema that supports:

- Filtering posts by fields of their author (`author__email__eq`, `author__rank__in`)
- Filtering by the author's team (`author__team__name__eq`) — two levels deep
- A virtual filter (`author__age__gte`) not present in the response schema
- A `f_` prefix on all filter parameters
- Strict mode that rejects unknown parameters with 422
- Field aliases (`post_title`, `userId`)

---

## 1. The Models

```python
from datetime import date, datetime, time
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

    members: Mapped[list["User"]] = relationship(back_populates="team")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    age: Mapped[int] = mapped_column()
    rank: Mapped[str] = mapped_column(String(50))
    is_alien: Mapped[bool] = mapped_column(Boolean, default=False)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)

    team: Mapped["Team | None"] = relationship(back_populates="members")
    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    casualties: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mission_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    author: Mapped["User"] = relationship(back_populates="posts")
```

---

## 2. The Schemas

### Nested schemas

```python
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TeamOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq"]})
    name: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: int = Field(json_schema_extra={"filters": ["eq", "in"]})
    name: str = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    email: EmailStr = Field(json_schema_extra={"filters": ["eq", "icontains"]})
    age: int = Field(json_schema_extra={"filters": ["eq", "gte", "lte"]})
    rank: str = Field(json_schema_extra={"filters": ["eq", "in", "not_in"]})
    is_alien: bool = Field(json_schema_extra={"filters": ["eq", "isnull"]})
    team: TeamOut

    model_config = ConfigDict(from_attributes=True)
```

### Extra virtual filters

`PostFilterExtra` defines filters for fields not in `PostOut` — in this case, `author.age`:

```python
class PostFilterExtra(BaseModel):
    author__age: int | None = Field(
        default=None,
        json_schema_extra={"filters": ["gt", "lt", "gte", "lte", "in", "not_in"]},
    )
```

The field name `author__age` uses double underscores to represent the path `Post → author → age`. The library resolves this automatically when building the SQL.

### Main schema

```python
from datetime import date, datetime
from pydantic import ConfigDict, Field


class PostOut(BaseModel):
    id: int = Field(
        json_schema_extra={"filters": ["eq", "gte", "lte", "in", "not_in"]}
    )
    title: str = Field(
        alias="post_title",                    # Pydantic response alias
        json_schema_extra={
            "filters": ["eq", "icontains"],
            "filter_alias": "post_title",      # filter param uses this name
        },
    )
    is_active: bool = Field(json_schema_extra={"filters": ["eq"]})
    casualties: int | None = Field(
        None, json_schema_extra={"filters": ["eq", "gte", "isnull"]}
    )
    mission_date: date | None = Field(
        None, json_schema_extra={"filters": ["eq", "gte", "lte", "isnull"]}
    )
    created_at: datetime = Field(json_schema_extra={"filters": ["gte", "lte"]})
    user_id: int = Field(
        json_schema_extra={
            "filters": ["eq"],
            "filter_alias": "userId",          # query param: f_userId__eq
        },
    )
    author: UserOut

    model_config = ConfigDict(from_attributes=True, validate_by_name=True)

    class FilterConfig:
        prefix = "f_"
        strict = True
        max_depth = 2                          # enables Post → User → Team
        extra_filters = PostFilterExtra
        search_field = "q"
        search_columns = ["title", "description"]
        sort_field = "sort_by"
        sort_columns = [
            "id",
            "post_title",
            "created_at",
            "f_author__team__name",            # sort by nested team name
        ]
```

---

## 3. The Endpoint

```python
from typing import Any
from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi_query_filters import FilterDep, FilterValues
from fastapi_query_filters.orm.sqlalchemy import apply_filters

app = FastAPI()


def get_db() -> Session:
    ...


@app.get("/posts", response_model=list[PostOut])
def list_posts(
    filters: FilterValues = FilterDep(PostOut),
    db: Session = Depends(get_db),
) -> Any:
    stmt = select(Post)
    stmt = apply_filters(stmt, Post, filters)
    return db.execute(stmt).scalars().all()
```

---

## 4. What You Can Do

### Filter by top-level fields

`GET /posts?f_is_active__eq=true`
`GET /posts?f_id__in=1,2,3`
`GET /posts?f_casualties__isnull=true`

### Filter by field alias

`GET /posts?f_post_title__icontains=stargate`
`GET /posts?f_userId__eq=1`

### Filter by nested author fields (depth 1)

`GET /posts?f_author__email__eq=j.oneill@sgc.mil`
`GET /posts?f_author__rank__in=Colonel,Major`
`GET /posts?f_author__is_alien__eq=false`

The adapter automatically joins `users` on `posts.user_id`:
```sql
JOIN users ON posts.user_id = users.id
WHERE users.email = 'j.oneill@sgc.mil'
```

### Filter by team fields (depth 2)

`GET /posts?f_author__team__name__eq=SG-1`

The adapter performs two joins:
```sql
JOIN users ON posts.user_id = users.id
JOIN teams ON users.team_id = teams.id
WHERE teams.name = 'SG-1'
```

### Use the virtual extra filter

`GET /posts?f_author__age__gte=40`

This works even though `age` is not in `PostOut` — it's declared in `PostFilterExtra`.

### Global search
`GET /posts?q=Chulak`

```sql
WHERE title ILIKE '%Chulak%'
   OR description ILIKE '%Chulak%'
```

### Sorting

`GET /posts?sort_by=-created_at`
`GET /posts?sort_by=f_author__team__name`  — sort by nested team name

### Combined

`GET /posts?f_author__rank__in=Colonel,Major&f_is_active__eq=true&sort_by=-created_at&q=mission`

---

## 5. Strict Mode in Action

With `strict = True` and `prefix = "f_"`:

| Request | Result |
| :--- | :--- |
| `?f_is_active__eq=true` | ✅ 200 OK |
| `?is_active__eq=true` | ❌ 422 — missing prefix |
| `?f_title__eq=hello` | ❌ 422 — `title` has `filter_alias = "post_title"` |
| `?f_post_title__eq=hello` | ✅ 200 OK |
| `?f_random_param=1` | ❌ 422 — unknown parameter |

---

## Next Steps

- Understand every `FilterConfig` option → [Configuration](../user-guide/configuration/index.md)
- See all `json_schema_extra` keys → [Field Configuration](../user-guide/configuration/json-schema-extra.md)
- See the full runnable example → [`examples/advanced_app`](https://github.com/ezeparziale/fastapi-query-filters/tree/main/examples/advanced_app)
