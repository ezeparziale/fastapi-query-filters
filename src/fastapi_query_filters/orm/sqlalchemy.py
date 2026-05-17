import types
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast, get_args, get_origin

from pydantic import BaseModel

try:
    from sqlalchemy import (
        JSON,
        Boolean,
        Date,
        DateTime,
        Float,
        Integer,
        Numeric,
        String,
        Text,
        Time,
        and_,
        asc,
        desc,
        or_,
    )
    from sqlalchemy import cast as sa_cast
    from sqlalchemy.orm import DeclarativeBase, RelationshipProperty
    from sqlalchemy.sql import Select

    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

    if not TYPE_CHECKING:
        # Define dummy classes/types to avoid NameErrors during module load
        class DeclarativeBase:
            pass

        class Select:
            pass

        class RelationshipProperty:
            pass

        String = Text = and_ = asc = desc = or_ = sa_cast = Integer = Float = (
            Boolean
        ) = Date = DateTime = Time = Numeric = JSON = None


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
        filter_model_class: type[BaseModel] = type(filter_model)

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
        filter_model_class: type[BaseModel] | None = None,
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
                        # Handle JSON element in search
                        if hasattr(col, "as_string"):
                            search_filters.append(col.as_string().ilike(f"%{q}%"))
                        continue

                    # Only apply search to string-like columns or apply cast
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

                # Lookup real_path from filter model fields if available
                real_col_path: str | None = None
                target_type = None
                if filter_model_class is not None:
                    # col_path already includes the prefix if it was passed in sort_by
                    # Ensure we have the full name for lookup
                    full_name_for_lookup = col_path
                    if global_prefix and not full_name_for_lookup.startswith(
                        global_prefix
                    ):
                        full_name_for_lookup = global_prefix + full_name_for_lookup

                    for name, field_info in filter_model_class.model_fields.items():
                        if (
                            name.startswith(full_name_for_lookup + "__")
                            or name == full_name_for_lookup
                        ):
                            extra = field_info.json_schema_extra
                            if isinstance(extra, dict) and "real_path" in extra:
                                real_col_path = cast(str, extra["real_path"])
                                target_type = field_info.annotation
                                break

                path_to_resolve: str = real_col_path if real_col_path else col_path
                resolve_prefix = global_prefix if not real_col_path else ""

                stmt, col = self._resolve_column(
                    stmt,
                    model,
                    path_to_resolve,
                    joined_paths,
                    filter_model_class=filter_model_class,
                    global_prefix=resolve_prefix,
                )

                if col is not None:
                    # Apply casting for JSON fields during sorting
                    if hasattr(col, "as_string"):
                        # Force unquoted extraction
                        col = col.as_string()
                        if target_type is not None:
                            sa_type = self._map_python_to_sa_type(
                                self._unwrap_type(target_type)
                            )
                            if sa_type and sa_type is not String:
                                col = sa_cast(col, sa_type)

                    stmt = stmt.order_by(desc(col) if is_desc else asc(col))

        return stmt

    def _resolve_column(
        self,
        stmt: "Select[tuple[T]]",
        model: type[T],
        field_path: str,
        joined_paths: set[str],
        filter_model_class: type[BaseModel] | None = None,
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
                        real_name = cast(str, extra.get("original_field", part))
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
                elif isinstance(rel_attr.type, JSON):
                    # It's a JSON column but not final, so we assume the rest
                    # of the path parts are JSON keys.
                    current_column = rel_attr
                    for json_part in path_parts[i + 1 :]:
                        real_json_key = json_part
                        # Resolve alias for JSON key if possible
                        if filter_model_class is not None:
                            for (
                                _f_name,
                                field_info,
                            ) in filter_model_class.model_fields.items():
                                extra = field_info.json_schema_extra
                                if (
                                    isinstance(extra, dict)
                                    and extra.get("field_alias") == json_part
                                    and extra.get("original_field")
                                ):
                                    real_json_key = cast(str, extra["original_field"])
                                    break
                        current_column = current_column[real_json_key]
                    return stmt, current_column
                else:
                    # It's a non-JSON column but not final, so it's an invalid path
                    return stmt, None
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

        filter_model_class: type[BaseModel] = (
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

            # Extract target type and real_path from field metadata
            field_info = filter_model_class.model_fields.get(key)
            target_type = field_info.annotation if field_info else None
            extra = field_info.json_schema_extra if field_info else {}
            real_path = extra.get("real_path") if isinstance(extra, dict) else None

            # Use real_path for resolution if available to bypass alias complexity
            path_to_resolve = cast(str, real_path if real_path else field_path)
            resolve_prefix = global_prefix if not real_path else ""

            stmt, col = self._resolve_column(
                stmt,
                model,
                path_to_resolve,
                joined_paths,
                filter_model_class=filter_model_class,
                global_prefix=resolve_prefix,
            )

            if col is not None:
                filters.append(
                    self._get_operator_expression(
                        col, op, value, target_type=target_type
                    )
                )

        if filters:
            stmt = stmt.where(and_(*filters))

        return stmt

    def _get_operator_expression(
        self, column: Any, op: FilterOperator, value: Any, target_type: Any = None
    ) -> Any:
        """Maps FilterOperator to SQLAlchemy comparison expressions."""
        # JSON Casting logic: if the column is a JSON element and we have a target type, cast it.
        if hasattr(column, "as_string"):
            # Force unquoted extraction for all engines (->> in Postgres, JSON_EXTRACT in SQLite/MySQL)
            column = column.as_string()

            if target_type is not None:
                actual_type = self._unwrap_type(target_type)
                sa_type = self._map_python_to_sa_type(actual_type)

                if sa_type and sa_type is not String:
                    # Don't apply cast for NULL checks on JSON elements.
                    if op in (FilterOperator.ISNULL, FilterOperator.NOT_ISNULL):
                        pass
                    elif sa_type in (Date, DateTime, Time):
                        # Cross-db compatible temporal comparison for JSON:
                        # Use string-based comparison to avoid 'CAST AS DATE' issues in SQLite
                        # and type mismatch (VARCHAR vs DATE) in Postgres.
                        if hasattr(value, "isoformat"):
                            value = value.isoformat()
                        elif isinstance(value, (list, tuple)):
                            value = [
                                v.isoformat() if hasattr(v, "isoformat") else v
                                for v in value
                            ]
                    else:
                        column = sa_cast(column, sa_type)

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
        elif op == FilterOperator.CONTAINS:
            return column.contains(value)
        elif op == FilterOperator.STARTSWITH:
            return column.startswith(value)
        elif op == FilterOperator.ISTARTSWITH:
            return column.ilike(f"{value}%")
        elif op == FilterOperator.ENDSWITH:
            return column.endswith(value)
        elif op == FilterOperator.IENDSWITH:
            return column.ilike(f"%{value}")
        elif op == FilterOperator.IN:
            val_list = value if isinstance(value, list) else [value]
            return column.in_(val_list)
        elif op == FilterOperator.NOT_IN:
            val_list = value if isinstance(value, list) else [value]
            return ~column.in_(val_list)
        elif op == FilterOperator.ISNULL:
            return column.is_(None) if value is True else column.isnot(None)
        elif op == FilterOperator.NOT_ISNULL:
            return column.isnot(None) if value is True else column.is_(None)
        elif op == FilterOperator.BETWEEN:
            return column.between(value[0], value[1])
        return None

    def _map_python_to_sa_type(self, py_type: Any) -> Any:
        """Maps Python types to SQLAlchemy types for casting."""
        from datetime import date, datetime, time

        if py_type is int:
            return Integer
        if py_type is float:
            return Float
        if py_type is bool:
            return Boolean
        if py_type is str:
            return String
        if py_type is date:
            return Date
        if py_type is datetime:
            return DateTime
        if py_type is time:
            return Time
        return None

    def _unwrap_type(self, t: Any) -> Any:
        """Unwraps Optional and Union types to find the base type."""
        actual_type = t
        origin = get_origin(t)
        if origin is Union or (
            hasattr(types, "UnionType") and origin is types.UnionType
        ):
            args = get_args(t)
            actual_type = next((arg for arg in args if arg is not type(None)), t)

        # If it's a list (for IN/BETWEEN), get the inner type
        if get_origin(actual_type) is list:
            args = get_args(actual_type)
            actual_type = args[0] if args else actual_type

        return actual_type


def apply_filters(
    stmt: "Select[tuple[T]]",
    model: type[T],
    filter_values: FilterValues,
) -> "Select[tuple[T]]":
    """Standalone utility for applying filters using the SQLAlchemy adapter.

    This is the primary entry point for SQLAlchemy-based projects.
    """
    return SQLAlchemyFilterAdapter().apply_filters(stmt, model, filter_values)
