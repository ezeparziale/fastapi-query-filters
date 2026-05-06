import types
from datetime import datetime
from typing import Annotated, Any, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator

from .operators import DEFAULT_OPERATORS, FilterOperator

# --- Global Constants ---
# Operators that perform partial string matching
STRING_OPS = (FilterOperator.LIKE, FilterOperator.ILIKE, FilterOperator.ICONTAINS)


def _is_union_origin(origin: Any) -> bool:
    """True for typing.Union and PEP 604 unions (types.UnionType)."""
    return origin is Union or origin is types.UnionType


# Add datetime support to default operators if not present
if datetime not in DEFAULT_OPERATORS:
    DEFAULT_OPERATORS[datetime] = [
        FilterOperator.EQ,
        FilterOperator.GTE,
        FilterOperator.LTE,
        FilterOperator.ISNULL,
    ]


# --- Configuration Classes ---
class FilterConfig:
    """Configuration class for customizing filter generation behavior.

    This class should be defined as a nested 'FilterConfig' class within a Pydantic
    schema to control how the library generates filters for that specific schema.

    Attributes:
        search_field: The query parameter name for global search (default: "q").
        sort_field: The query parameter name for sorting (default: "sort_by").
        prefix: A global prefix added to all filter fields (default: "").
        enable_search: Whether to enable the global search functionality.
        enable_sort: Whether to enable the dynamic sorting functionality.
        search_columns: List of database column names to include in global search.
        max_depth: Maximum depth for recursive relationship filtering (default: 1).
        strict: Whether to forbid all unknown query parameters (default: False).
        extra_filters: An optional Pydantic model containing virtual fields
            to be included in the filter generation.
    """

    search_field: str = "q"
    sort_field: str = "sort_by"
    prefix: str = ""
    enable_search: bool = True
    enable_sort: bool = True
    search_columns: list[str] = []
    max_depth: int = 1
    strict: bool = False
    extra_filters: type[BaseModel] | None = None


# --- Base Model for Generated Filters ---
class FilterBase(BaseModel):
    """Base Pydantic model for all generated filter models.

    Provides common configuration and shared validation logic, such as
    parsing comma-separated values from query parameters into lists.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    @model_validator(mode="before")
    @classmethod
    def split_comma_values(cls, data: Any) -> Any:
        """Parses comma-separated strings into lists for fields that expect a list.

        FastAPI often passes multiple values either as multiple keys or as a single
        comma-separated string. This validator ensures consistency.
        """
        if not isinstance(data, dict):
            return data

        new_data = data.copy()

        for key, value in data.items():
            string_value = None

            # Detect string values or single-item string lists for list fields
            if isinstance(value, str):
                string_value = value
            elif (
                isinstance(value, list)
                and len(value) == 1
                and isinstance(value[0], str)
            ):
                string_value = value[0]

            if string_value is None:
                continue

            field = cls.model_fields.get(key)
            if not field:
                continue

            target_type = field.annotation
            origin = get_origin(target_type)
            is_list = origin is list

            # Recursively check for List types within Union/Optional types
            if not is_list and _is_union_origin(origin):
                for arg in get_args(target_type):
                    if get_origin(arg) is list:
                        is_list = True
                        break

            if is_list and string_value is not None:
                new_data[key] = [v.strip() for v in string_value.split(",")]

        return new_data

    @model_validator(mode="before")
    @classmethod
    def validate_strict_filters(cls, data: Any) -> Any:
        """Validates that no unknown query parameters are provided if strict mode is enabled."""
        if not isinstance(data, dict):
            return data

        # Access the source configuration from the generated class
        config = getattr(cls, "_source_filter_config", None)
        if not config or not getattr(config, "strict", False):
            return data

        allowed_fields = set(cls.model_fields.keys())

        for key in data.keys():
            if key not in allowed_fields:
                raise ValueError(f"Extra inputs are not permitted: {key}")

        return data


# --- Internal Helper Functions ---
def _get_filter_config(schema: type[BaseModel]) -> type[FilterConfig]:
    """Retrieves the FilterConfig from a schema or returns default settings."""
    return getattr(schema, "FilterConfig", FilterConfig)


def _get_root_type(t: Any) -> Any:
    """Recursively unwraps Union, Optional and Annotated types to find the base type.

    This is necessary to handle specialized Pydantic types like EmailStr
    which are Annotated types in Pydantic v2.
    """
    origin = get_origin(t)
    if _is_union_origin(origin):
        args = get_args(t)
        # Filter out None to find the actual data type
        actual_types = [arg for arg in args if arg is not type(None)]
        if actual_types:
            return _get_root_type(actual_types[0])
    if origin is Annotated:
        # Unwrap Annotated[T, metadata] -> T
        return _get_root_type(get_args(t)[0])

    # Handle Pydantic special types that might be strings/ints
    if hasattr(t, "__name__"):
        if t.__name__ == "EmailStr":
            return str
        if t.__name__ == "HttpUrl":
            return str

    return t


def _fields_from_schema(
    base_schema: type[BaseModel],
    *,
    operators: dict[str, list[FilterOperator]] | None = None,
    use_alias: bool = True,
    prefix: str = "",
    depth: int = 1,
) -> dict[str, Any]:
    """Recursively extracts filter fields from a Pydantic schema.

    This function inspects the fields of a schema and generates appropriate
    filter fields based on type, metadata, and relationship depth.
    """
    fields: dict[str, Any] = {}

    for name, field_info in base_schema.model_fields.items():
        field_type = field_info.annotation
        if field_type is None:
            continue

        effective_name = (field_info.alias or name) if use_alias else name

        field_extra = field_info.json_schema_extra or {}
        if not isinstance(field_extra, dict):
            field_extra = {}

        if (
            use_alias
            and isinstance(field_extra, dict)
            and "filter_alias" in field_extra
        ):
            effective_name = str(field_extra["filter_alias"])

        # Resolve the base type (handling EmailStr, Annotated, Union, etc.)
        actual_type = _get_root_type(field_type)

        # Recursive support for nested models (relationships)
        if (
            isinstance(actual_type, type)
            and issubclass(actual_type, BaseModel)
            and depth > 0
        ):
            nested_prefix = f"{prefix}{effective_name}__"
            nested_fields = _fields_from_schema(
                actual_type,
                prefix=nested_prefix,
                depth=depth - 1,
                use_alias=use_alias,
                operators=operators,
            )

            extra_schema: type[BaseModel] | None = getattr(
                _get_filter_config(actual_type), "extra_filters", None
            )
            if extra_schema is not None:
                extra_fields = _fields_from_schema(
                    extra_schema,
                    prefix=nested_prefix,
                    depth=depth - 1,
                    use_alias=use_alias,
                    operators=operators,
                )
                nested_fields.update(extra_fields)

            fields.update(nested_fields)
            continue

        # Skip complex containers that cannot be directly filtered
        if get_origin(actual_type) in (list, dict):
            continue

        custom_filters = (operators or {}).get(name)

        # Determine which operators are requested
        requested_ops: list[FilterOperator] = []
        if isinstance(field_extra, dict) and "filters" in field_extra:
            field_filters = field_extra["filters"]
            if isinstance(field_filters, list):
                requested_ops = [FilterOperator(str(op)) for op in field_filters]
        elif custom_filters:
            requested_ops = custom_filters

        if not requested_ops:
            continue

        # --- Strict Operator Validation with Inheritance Support ---
        type_allowed_ops: list[FilterOperator] | None = None

        # 1. Try exact match first (prevents bool from matching int)
        if actual_type in DEFAULT_OPERATORS:
            type_allowed_ops = DEFAULT_OPERATORS[actual_type]
        else:
            # 2. Fallback to inheritance (useful for EmailStr, etc.)
            for base_type, ops in DEFAULT_OPERATORS.items():
                try:
                    if isinstance(actual_type, type) and issubclass(
                        actual_type, base_type
                    ):
                        type_allowed_ops = ops
                        break
                except TypeError:
                    continue

        if type_allowed_ops:
            allowed_ops = [op for op in requested_ops if op in type_allowed_ops]
        else:
            # Fallback for unknown types: only allow equality by default
            allowed_ops = [op for op in requested_ops if op == FilterOperator.EQ]

        for op in allowed_ops:
            filter_name = f"{prefix}{effective_name}__" + op.value

            new_extra: dict[str, Any] = {
                "original_field": name,
            }

            if effective_name != name:
                new_extra["field_alias"] = effective_name

            # Type mapping: Partial string matches use 'str', others use original type
            field_filter_type: Any
            if op == FilterOperator.ISNULL:
                field_filter_type = bool | None
            elif op in (FilterOperator.IN, FilterOperator.NOT_IN):
                field_filter_type = str | list[actual_type] | None  # type: ignore[valid-type]
            elif op in STRING_OPS:
                field_filter_type = str | None
            else:
                field_filter_type = actual_type | None

            fields[filter_name] = (
                field_filter_type,
                Field(
                    default=None,
                    description=field_info.description
                    or f"Filter {effective_name} by {op.value}",
                    alias=filter_name,
                    json_schema_extra=new_extra,
                ),
            )

    return fields


# --- Public API Functions ---
def create_filter_model(
    base_schema: type[BaseModel],
    *,
    operators: dict[str, list[FilterOperator]] | None = None,
    search_field: str | None = None,
    sort_field: str | None = None,
    prefix: str | None = None,
    use_alias: bool = True,
    depth: int | None = None,
) -> Any:
    """Dynamically creates a Pydantic model for filtering based on a base schema.

    Args:
        base_schema: The Pydantic model used as the basis for generating filters.
        operators: Explicit operator overrides for specific fields.
        search_field: Name of the global search parameter (overrides FilterConfig).
        sort_field: Name of the sorting parameter (overrides FilterConfig).
        prefix: A global prefix for all filter fields (overrides FilterConfig).
        use_alias: Whether to respect field aliases during generation.
        depth: Maximum depth for recursive relationship filtering.

    Returns:
        A new Pydantic model class tailored for query parameter validation.
    """
    # Read configuration from the base schema
    config = _get_filter_config(base_schema)
    enable_search = getattr(config, "enable_search", True)
    enable_sort = getattr(config, "enable_sort", True)

    # Explicit parameters take precedence over schema configuration
    if search_field is None:
        search_field = getattr(config, "search_field", "q") if enable_search else None
    if sort_field is None:
        sort_field = getattr(config, "sort_field", "sort_by") if enable_sort else None
    if prefix is None:
        prefix = getattr(config, "prefix", "")
    if depth is None:
        depth = getattr(config, "max_depth", 1)

    # Process standard schema fields
    fields = _fields_from_schema(
        base_schema,
        operators=operators,
        use_alias=use_alias,
        prefix=prefix,
        depth=depth,
    )

    # Process extra fields (virtual fields not present in the output schema)
    extra_schema: type[BaseModel] | None = getattr(config, "extra_filters", None)
    if extra_schema is not None:
        extra_fields = _fields_from_schema(
            extra_schema,
            operators=operators,
            use_alias=use_alias,
            prefix=prefix,
            depth=depth,
        )
        fields.update(extra_fields)

    # Add global control fields
    if search_field:
        fields[search_field] = (
            str | None,
            Field(default=None, description="Search across multiple fields"),
        )
    if sort_field:
        fields[sort_field] = (
            str | None,
            Field(
                default=None,
                description="Sort by field name. Supports multiple fields.",
            ),
        )

    filter_model = create_model(
        f"{base_schema.__name__}Filter", **fields, __base__=FilterBase
    )

    # Embed the configuration into the generated model for the SQLAlchemy engine to read
    filter_model._source_filter_config = config  # type: ignore[attr-defined]

    return filter_model
