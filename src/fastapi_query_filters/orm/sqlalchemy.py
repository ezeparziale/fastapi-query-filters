from typing import TYPE_CHECKING, Any, TypeVar

try:
    from sqlalchemy import String, Text, and_, asc, desc, or_
    from sqlalchemy import cast as sa_cast
    from sqlalchemy.orm import DeclarativeBase, RelationshipProperty
    from sqlalchemy.sql import Select

    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

    if not TYPE_CHECKING:
        # Define dummy classes/types to avoid NameErrors during module load
        # These will never be used because we'll raise an error before they are accessed
        class DeclarativeBase:
            pass

        class Select:
            pass

        class RelationshipProperty:
            pass

        String = Text = and_ = asc = desc = or_ = sa_cast = None


from ..core import FilterConfig
from ..dependencies import FilterValues
from ..operators import FilterOperator
from .base import ORMFilterAdapter

if TYPE_CHECKING:
    # This helps Mypy when sqlalchemy is not installed in the dev environment
    # but we are running in a mode that expects it.
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy.sql import Select

T = TypeVar("T", bound="DeclarativeBase")


def _check_sqlalchemy() -> None:
    if not HAS_SQLALCHEMY:
        raise ImportError(
            "The 'sqlalchemy' extra is required to use the SQLAlchemy adapter. "
            "Install it with: pip install 'fastapi-query-filters[sqlalchemy]'"
        )


class SQLAlchemyFilterAdapter(ORMFilterAdapter):
    """Adapter for applying filters to SQLAlchemy select statements.

    This class implements the ORMFilterAdapter interface for SQLAlchemy 2.0.
    It handles dynamic filtering, joins, search, and sorting.
    """

    def __init__(self) -> None:
        _check_sqlalchemy()

    def apply_filters(
        self,
        stmt: "Select[tuple[T]]",
        model: type[T],
        filter_values: FilterValues,
    ) -> "Select[tuple[T]]":
        """Applies dynamic filters and sorting to a SQLAlchemy select statement."""
        _check_sqlalchemy()
        data = filter_values.dict()
        filter_model = filter_values.model
        filter_model_class = type(filter_model)

        # --- Configuration Retrieval ---
        embedded_config: type[FilterConfig] = getattr(
            filter_model_class, "_source_filter_config", FilterConfig
        )

        joined_paths: set[str] = set()

        # 1. Process Global Features (Search & Sort)
        stmt = self._apply_global_features(
            stmt, model, data, embedded_config, filter_model_class, joined_paths
        )

        # 2. Process Dynamic Filters
        stmt = self._apply_dynamic_filters(
            stmt, model, filter_model, data, embedded_config, joined_paths
        )

        return stmt

    def _apply_global_features(
        self,
        stmt: "Select[tuple[T]]",
        model: type[T],
        data: dict[str, Any],
        config: type[FilterConfig],
        filter_model_class: type[Any] | None = None,
        joined_paths: set[str] | None = None,
    ) -> "Select[tuple[T]]":
        """Handles global search and sorting logic."""
        if joined_paths is None:
            joined_paths = set()

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
        global_prefix = getattr(config, "prefix", "")

        q = data.pop(search_field, None) if search_field else None
        sort_by = data.pop(sort_field, None) if sort_field else None

        # --- Global Search (OR clauses) ---
        if q and search_columns:
            search_filters = []
            for col_path in search_columns:
                # Use resolve_column for search columns too, allowing nested search
                stmt, col = self._resolve_column(
                    stmt,
                    model,
                    col_path,
                    joined_paths,
                    filter_model_class=filter_model_class,
                    global_prefix="",  # Search columns usually don't have prefixes
                )
                if col is not None:
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
            allowed_sort_fields = getattr(
                filter_model_class, "_allowed_sort_fields", None
            )

            for field in sort_by.split(","):
                field = field.strip()
                is_desc = field.startswith("-")
                col_path = field[1:] if is_desc else field

                # Validation: Only allow fields defined in the schema
                if allowed_sort_fields is not None:
                    if col_path not in allowed_sort_fields:
                        continue

                stmt, col = self._resolve_column(
                    stmt,
                    model,
                    col_path,
                    joined_paths,
                    filter_model_class=filter_model_class,
                    global_prefix=global_prefix,
                )

                if col is not None:
                    stmt = stmt.order_by(desc(col) if is_desc else asc(col))

        return stmt

    def _resolve_column(
        self,
        stmt: "Select[tuple[T]]",
        model: type[T],
        field_path: str,
        joined_paths: set[str],
        filter_model_class: type[Any] | None = None,
        global_prefix: str = "",
    ) -> tuple["Select[tuple[T]]", Any]:
        """Resolves a field path to a SQLAlchemy column, handling joins and aliases."""
        # Strip global prefix if present
        if global_prefix and field_path.startswith(global_prefix):
            field_path = field_path[len(global_prefix) :]

        current_model: type[Any] = model
        current_column: Any = None

        path_parts = field_path.split("__")
        for i, part in enumerate(path_parts):
            real_name = part
            is_final = i == len(path_parts) - 1

            # Alias resolution: Look for the real field name in the filter model metadata
            if filter_model_class is not None:
                for _f_name, field_info in filter_model_class.model_fields.items():
                    extra = field_info.json_schema_extra
                    if not isinstance(extra, dict):
                        continue

                    if extra.get("field_alias") == part:
                        real_name = extra.get("original_field", part)
                        break

            if not is_final:
                # Relationship handling: Automatic Join
                if not hasattr(current_model, real_name):
                    return stmt, None

                rel_attr = getattr(current_model, real_name)
                if not hasattr(rel_attr, "property"):
                    return stmt, None

                rel = rel_attr.property
                if isinstance(rel, RelationshipProperty):
                    path_key = f"{current_model.__name__}.{real_name}"
                    if path_key not in joined_paths:
                        stmt = stmt.join(rel_attr)
                        joined_paths.add(path_key)
                    current_model = rel.mapper.class_
            else:
                # Final column resolution
                if hasattr(current_model, real_name):
                    current_column = getattr(current_model, real_name)

        return stmt, current_column

    def _apply_dynamic_filters(
        self,
        stmt: "Select[tuple[T]]",
        model: type[T],
        filter_model: Any,
        data: dict[str, Any],
        config: type[FilterConfig],
        joined_paths: set[str] | None = None,
    ) -> "Select[tuple[T]]":
        """Handles column-specific filters and automatic joins."""
        if joined_paths is None:
            joined_paths = set()

        filters: list[Any] = []
        global_prefix = getattr(config, "prefix", "")

        filter_model_class = (
            filter_model if isinstance(filter_model, type) else type(filter_model)
        )

        for key, value in data.items():
            if "__" not in key or value is None:
                continue

            parts = key.rsplit("__", 1)
            field_path, op_str = parts[0], parts[1]

            try:
                op = FilterOperator(op_str)
            except ValueError:
                continue

            stmt, col = self._resolve_column(
                stmt,
                model,
                field_path,
                joined_paths,
                filter_model_class=filter_model_class,
                global_prefix=global_prefix,
            )

            if col is not None:
                filters.append(self._get_operator_expression(col, op, value))

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
    stmt: "Select[tuple[T]]",
    model: type[T],
    filter_values: FilterValues,
) -> "Select[tuple[T]]":
    """Standalone utility for applying filters using the SQLAlchemy adapter.

    This is the primary entry point for SQLAlchemy-based projects.
    """
    return SQLAlchemyFilterAdapter().apply_filters(stmt, model, filter_values)
