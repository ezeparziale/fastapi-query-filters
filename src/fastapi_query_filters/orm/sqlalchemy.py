from typing import Any, TypeVar

from sqlalchemy import String, Text, and_, asc, desc, or_
from sqlalchemy import cast as sa_cast
from sqlalchemy.orm import DeclarativeBase, RelationshipProperty
from sqlalchemy.sql import Select

from ..core import FilterConfig
from ..dependencies import FilterValues
from ..operators import FilterOperator
from .base import ORMFilterAdapter

T = TypeVar("T", bound=DeclarativeBase)


class SQLAlchemyFilterAdapter(ORMFilterAdapter):
    """Adapter for applying filters to SQLAlchemy select statements.

    This class implements the ORMFilterAdapter interface for SQLAlchemy 2.0.
    It handles dynamic filtering, joins, search, and sorting.
    """

    def apply_filters(
        self,
        stmt: Select[tuple[T]],
        model: type[T],
        filter_values: FilterValues,
    ) -> Select[tuple[T]]:
        """Applies dynamic filters and sorting to a SQLAlchemy select statement."""
        data = filter_values.dict()
        filter_model = filter_values.model

        # --- Configuration Retrieval ---
        embedded_config: type[FilterConfig] = getattr(
            filter_model, "_source_filter_config", FilterConfig
        )

        # 1. Process Global Features (Search & Sort)
        stmt = self._apply_global_features(stmt, model, data, embedded_config)

        # 2. Process Dynamic Filters
        stmt = self._apply_dynamic_filters(
            stmt, model, filter_model, data, embedded_config
        )

        return stmt

    def _apply_global_features(
        self,
        stmt: Select[tuple[T]],
        model: type[T],
        data: dict[str, Any],
        config: type[FilterConfig],
    ) -> Select[tuple[T]]:
        """Handles global search and sorting logic."""
        search_field = (
            getattr(config, "search_field", "q")
            if getattr(config, "enable_search", True)
            else None
        )
        sort_field = (
            getattr(config, "sort_field", "sort_by")
            if getattr(config, "enable_sort", True)
            else None
        )
        search_columns: list[str] = list(getattr(config, "search_columns", []))

        q = data.pop(search_field, None) if search_field else None
        sort_by = data.pop(sort_field, None) if sort_field else None

        # --- Global Search (OR clauses) ---
        if q and search_columns:
            search_filters = []
            for col_name in search_columns:
                if hasattr(model, col_name):
                    col = getattr(model, col_name)
                    if not hasattr(col, "type"):
                        continue
                    if not isinstance(col.type, (String, Text)):
                        search_filters.append(sa_cast(col, String).ilike(f"%{q}%"))
                    else:
                        search_filters.append(col.ilike(f"%{q}%"))
            if search_filters:
                stmt = stmt.where(or_(*search_filters))

        # --- Dynamic Sorting ---
        if sort_by:
            for field in sort_by.split(","):
                field = field.strip()
                is_desc = field.startswith("-")
                col_name = field[1:] if is_desc else field
                if hasattr(model, col_name):
                    col = getattr(model, col_name)
                    stmt = stmt.order_by(desc(col) if is_desc else asc(col))

        return stmt

    def _apply_dynamic_filters(
        self,
        stmt: Select[tuple[T]],
        model: type[T],
        filter_model: Any,
        data: dict[str, Any],
        config: type[FilterConfig],
    ) -> Select[tuple[T]]:
        """Handles column-specific filters and automatic joins."""
        filters: list[Any] = []
        joined_paths: set[str] = set()
        global_prefix = getattr(config, "prefix", "")

        for key, value in data.items():
            if "__" not in key or value is None:
                continue

            parts = key.rsplit("__", 1)
            field_path, op_str = parts[0], parts[1]

            # Save the original key to lookup in pydantic model_fields
            pydantic_key = key

            # Strip global prefix if present for database mapping
            if global_prefix and field_path.startswith(global_prefix):
                field_path = field_path[len(global_prefix) :]

            try:
                op = FilterOperator(op_str)
            except ValueError:
                continue

            current_model: type[Any] = model
            current_column: Any = None

            # Resolve field paths, handling nested relationships (Joins)
            path_parts = field_path.split("__")
            for i, part in enumerate(path_parts):
                real_name = part
                is_final = i == len(path_parts) - 1

                # Metadata lookup for real database field name
                filter_field_info = filter_model.model_fields.get(pydantic_key)
                if filter_field_info:
                    extra = filter_field_info.json_schema_extra
                    if isinstance(extra, dict) and is_final:
                        original = extra.get("original_field", part)
                        real_name = original.split("__")[-1]

                if not is_final:
                    # Relationship handling: Automatic Join
                    if not hasattr(current_model, real_name):
                        break

                    rel_attr = getattr(current_model, real_name)
                    if not hasattr(rel_attr, "property"):
                        break

                    rel = rel_attr.property
                    if isinstance(rel, RelationshipProperty):
                        # Track joins by model/attr to avoid ambiguous joins
                        path_key = f"{current_model.__name__}.{real_name}"
                        if path_key not in joined_paths:
                            stmt = stmt.join(rel_attr)
                            joined_paths.add(path_key)

                        current_model = rel.mapper.class_
                else:
                    # Final column resolution.
                    if hasattr(current_model, real_name):
                        current_column = getattr(current_model, real_name)

            if current_column is not None:
                filters.append(self._get_operator_expression(current_column, op, value))

        if filters:
            stmt = stmt.where(and_(*filters))

        return stmt

    def _get_operator_expression(
        self, column: Any, op: FilterOperator, value: Any
    ) -> Any:
        """Maps FilterOperator to SQLAlchemy comparison expressions."""
        if op == FilterOperator.EQ:
            return column == value
        elif op == FilterOperator.NE:
            return column != value
        elif op == FilterOperator.GT:
            return column > value
        elif op == FilterOperator.LT:
            return column < value
        elif op == FilterOperator.GTE:
            return column >= value
        elif op == FilterOperator.LTE:
            return column <= value
        elif op == FilterOperator.LIKE:
            return column.like(value)
        elif op == FilterOperator.ILIKE:
            return column.ilike(value)
        elif op == FilterOperator.ICONTAINS:
            return column.ilike(f"%{value}%")
        elif op == FilterOperator.IN:
            val_list = value if isinstance(value, list) else [value]
            return column.in_(val_list)
        elif op == FilterOperator.NOT_IN:
            val_list = value if isinstance(value, list) else [value]
            return ~column.in_(val_list)
        elif op == FilterOperator.ISNULL:
            return column.is_(None) if value is True else column.isnot(None)
        return None


def apply_filters(
    stmt: Select[tuple[T]],
    model: type[T],
    filter_values: FilterValues,
) -> Select[tuple[T]]:
    """Standalone utility for applying filters using the SQLAlchemy adapter.

    This is the primary entry point for SQLAlchemy-based projects.
    """
    return SQLAlchemyFilterAdapter().apply_filters(stmt, model, filter_values)
