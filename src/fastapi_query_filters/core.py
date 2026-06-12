import types
from typing import Annotated, Any, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator

from .operators import DEFAULT_OPERATORS, FilterOperator

# --- Global Constants ---
# Operators that perform partial string matching
STRING_OPS = (FilterOperator.LIKE, FilterOperator.ILIKE, FilterOperator.ICONTAINS)


def _is_union_origin(origin: Any) -> bool:
    """True for typing.Union and PEP 604 unions (types.UnionType)."""
    return origin is Union or origin is types.UnionType


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
        sort_columns: Explicit list of field names allowed for sorting.
            If None, all schema fields are allowed (default: None).
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
    sort_columns: list[str] | None = None
    max_depth: int = 1
    strict: bool = False
    extra_filters: type[BaseModel] | None = None
    soft_delete_field: str | None = None
    soft_delete_active_value: Any = None


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
    def validate_between_operators(cls, data: Any) -> Any:
        """Ensures that 'between' filters have exactly two elements."""
        if not isinstance(data, dict):
            return data

        for key, value in data.items():
            if key.endswith("__between") and value is not None:
                items: list[Any]
                # Extract values from string or list
                if isinstance(value, str):
                    items = [v.strip() for v in value.split(",")]
                elif (
                    isinstance(value, list)
                    and len(value) == 1
                    and isinstance(value[0], str)
                    and "," in value[0]
                ):
                    # Handle the case where we have a list with one string containing a comma
                    # (e.g., ["10,50"])
                    items = [v.strip() for v in value[0].split(",")]
                elif isinstance(value, list):
                    items = value
                else:
                    items = [value]

                if len(items) != 2:
                    raise ValueError(
                        f"Field '{key}' must have exactly two values for 'between' operator. "
                        f"Got {len(items)}: {items}"
                    )
        return data

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

        # --- Strict sort field validation ---
        sort_field = getattr(config, "sort_field", "sort_by")
        enable_sort = getattr(config, "enable_sort", True)

        if enable_sort and sort_field:
            sort_value = data.get(sort_field)
            if sort_value:
                allowed_sort_fields = getattr(cls, "_allowed_sort_fields", None)
                if allowed_sort_fields is not None:
                    for field in sort_value.split(","):
                        col_path = field.strip().lstrip("-")
                        if col_path not in allowed_sort_fields:
                            raise ValueError(
                                f"Sort field '{col_path}' is not allowed. "
                                f"Valid fields are: {sorted(allowed_sort_fields)}"
                            )

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
    real_prefix: str = "",
    depth: int = 1,
    valid_paths: set[str] | None = None,
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

        if use_alias and isinstance(field_extra, dict):
            if "filter_alias" in field_extra:
                effective_name = str(field_extra["filter_alias"])
            elif "field_alias" in field_extra:
                effective_name = str(field_extra["field_alias"])

        # Resolve the base type (handling EmailStr, Annotated, Union, etc.)
        actual_type = _get_root_type(field_type)
        field_path = f"{prefix}{effective_name}"
        current_real_path = f"{real_prefix}{name}"

        # Recursive support for nested models (relationships)
        if (
            isinstance(actual_type, type)
            and issubclass(actual_type, BaseModel)
            and depth > 0
        ):
            nested_prefix = f"{field_path}__"
            nested_real_prefix = f"{current_real_path}__"
            nested_fields = _fields_from_schema(
                actual_type,
                prefix=nested_prefix,
                real_prefix=nested_real_prefix,
                depth=depth - 1,
                use_alias=use_alias,
                operators=operators,
                valid_paths=valid_paths,
            )

            extra_schema: type[BaseModel] | None = getattr(
                _get_filter_config(actual_type), "extra_filters", None
            )
            if extra_schema is not None:
                extra_fields = _fields_from_schema(
                    extra_schema,
                    prefix=nested_prefix,
                    real_prefix=nested_real_prefix,
                    depth=depth - 1,
                    use_alias=use_alias,
                    operators=operators,
                    valid_paths=valid_paths,
                )
                nested_fields.update(extra_fields)

            fields.update(nested_fields)
            continue

        # Skip complex containers that cannot be directly filtered.
        # We only allow dict/list if they have explicit filters or are simple containers.
        if get_origin(actual_type) is dict or actual_type is dict:
            # Check if this dict field has explicit filters
            if not isinstance(field_extra, dict) or "filters" not in field_extra:
                continue

        # If it's a leaf node, it's a valid path for sorting/searching
        if valid_paths is not None:
            valid_paths.add(field_path)

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

        # 1. Try match first (including generic origins like dict[str, Any])
        lookup_type = get_origin(actual_type) or actual_type
        if lookup_type in DEFAULT_OPERATORS:
            type_allowed_ops = DEFAULT_OPERATORS[lookup_type]
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

        # Determine inner type for list-based fields to use in operators
        inner_type = actual_type
        if get_origin(actual_type) is list:
            args = get_args(actual_type)
            inner_type = args[0] if args else Any

        for op in allowed_ops:
            filter_name = f"{prefix}{effective_name}__" + op.value

            new_extra: dict[str, Any] = {
                "original_field": name,
                "real_path": current_real_path,
            }

            if effective_name != name:
                new_extra["field_alias"] = effective_name

            if get_origin(actual_type) is list or actual_type is list:
                new_extra["container_type"] = "list"

            # Type mapping: Partial string matches use 'str', others use original type
            field_filter_type: Any
            if op in (
                FilterOperator.ISNULL,
                FilterOperator.NOT_ISNULL,
                FilterOperator.IS_EMPTY,
                FilterOperator.IS_BLANK,
            ):
                field_filter_type = bool | None
            elif op in (
                FilterOperator.IN,
                FilterOperator.NOT_IN,
                FilterOperator.BETWEEN,
                FilterOperator.ARR_OVERLAP,
                FilterOperator.ARR_ALL,
                FilterOperator.ARR_ANY,
            ):
                field_filter_type = list[inner_type] | None  # type: ignore[valid-type]
            elif op == FilterOperator.ARR_CONTAINS:
                field_filter_type = inner_type | None
            elif op == FilterOperator.ARR_LENGTH:
                field_filter_type = int | None
            elif op in (
                FilterOperator.HAS_ANY_KEYS,
                FilterOperator.HAS_ALL_KEYS,
            ):
                field_filter_type = list[str] | None
            elif op == FilterOperator.HAS_KEY:
                field_filter_type = str | None
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
    valid_paths: set[str] = set()
    fields = _fields_from_schema(
        base_schema,
        operators=operators,
        use_alias=use_alias,
        prefix=prefix,
        depth=depth,
        valid_paths=valid_paths,
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
            valid_paths=valid_paths,
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

    # Explicitly configured sort columns take precedence
    sort_columns = getattr(config, "sort_columns", None)
    if sort_columns is not None:
        filter_model._allowed_sort_fields = set(sort_columns)  # type: ignore[attr-defined]
    else:
        filter_model._allowed_sort_fields = valid_paths  # type: ignore[attr-defined]

    return filter_model
