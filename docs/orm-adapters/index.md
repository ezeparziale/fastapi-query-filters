# ORM Adapters

`fastapi-query-filters` is designed to be ORM-agnostic at its core. While it comes with first-class support for **SQLAlchemy**, you can easily implement your own adapter for any other ORM or database driver.

---

## The `ORMFilterAdapter` Interface

All adapters must implement the `ORMFilterAdapter` abstract base class. This ensures a consistent way to apply filters regardless of the underlying database technology.

```python
from abc import ABC, abstractmethod
from typing import Any
from fastapi_query_filters.dependencies import FilterValues

class ORMFilterAdapter(ABC):
    @abstractmethod
    def apply_filters(
        self,
        stmt: Any,
        model: type[Any],
        filter_values: FilterValues,
    ) -> Any:
        """Apply filter values to an ORM query/statement."""
        ...
```

### Key Responsibilities of an Adapter:
1. **Global Search**: Parse the `q` (or custom) parameter and apply `OR` clauses across specified columns.
2. **Dynamic Sorting**: Parse the `sort_by` parameter and apply ordering to the query.
3. **Filtering**: Map `FilterOperator` enums to native ORM comparison expressions.
4. **Relationship Handling**: Automatically join tables when nested filters (e.g., `user__username__eq`) are requested.

---

## Built-in Adapters

Currently, the following adapters are available:

- [SQLAlchemy](sqlalchemy.md) (Support for 2.0+)

---

## Implementing a Custom Adapter

If you want to support a new ORM (like Tortoise, Peewee, or SQLModel), you should:

1. Create a class inheriting from `ORMFilterAdapter`.
2. Implement the `apply_filters` method.
3. (Optional) Create a standalone `apply_filters` utility function for easier access, similar to the SQLAlchemy one.

!!! tip "Contribute!"
    If you implement an adapter for a popular ORM, please consider opening a Pull Request! We'd love to include more first-class adapters in the library.
