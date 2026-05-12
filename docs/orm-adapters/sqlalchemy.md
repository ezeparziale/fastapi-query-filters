# SQLAlchemy Adapter

The SQLAlchemy adapter is the primary way to use `fastapi-query-filters`. It is optimized for **SQLAlchemy 2.0** and supports `Select` statements.

---

## Installation

Ensure you have the `sqlalchemy` extra installed:

```bash
pip install "fastapi-query-filters[sqlalchemy]"
```

---

## Basic Usage

The easiest way to use the adapter is through the `apply_filters` utility function.

```python
from sqlalchemy import select
from fastapi_query_filters.orm.sqlalchemy import apply_filters

# 1. Create your base statement
stmt = select(User)

# 2. Apply filters (stmt is modified and returned)
stmt = apply_filters(stmt, User, filters)

# 3. Execute
result = db.execute(stmt).scalars().all()
```

---

## Features

### Automatic Joins
When you define a filter for a related model using double underscores (e.g., `author__username__eq`), the adapter automatically performs the necessary `JOIN` on the SQLAlchemy statement.

### Search Type Casting
If you use global search (`q`) on a non-string column (like an `Integer` or `UUID`), the adapter automatically casts that column to `String` before applying the `ILIKE` operator, ensuring the query doesn't fail.

### Aliases & Prefixes
The adapter respects `filter_alias` and global `prefix` configurations defined in your `FilterConfig`.

---

## Advanced: Manual Adapter Usage

If you need more control, you can instantiate the `SQLAlchemyFilterAdapter` directly.

```python
from fastapi_query_filters.orm.sqlalchemy import SQLAlchemyFilterAdapter

adapter = SQLAlchemyFilterAdapter()
stmt = adapter.apply_filters(stmt, User, filters)
```
