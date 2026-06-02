from typing import Any

from .._compat import HAS_SQLALCHEMY, Boolean, FunctionElement, compiles

if HAS_SQLALCHEMY:

    class json_is_empty_object(FunctionElement[bool]):
        """Cross-dialect check for empty JSON object {}."""

        type = Boolean()
        inherit_cache = True

    @compiles(json_is_empty_object, "postgresql")
    def _compile_json_is_empty_object_postgresql(
        element: "json_is_empty_object", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        return f"(({column_sql})::jsonb = '{{}}'::jsonb)"

    @compiles(json_is_empty_object, "mysql")
    def _compile_json_is_empty_object_mysql(
        element: "json_is_empty_object", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        return f"(JSON_TYPE({column_sql}) = 'OBJECT' AND JSON_LENGTH({column_sql}) = 0)"

    @compiles(json_is_empty_object, "sqlite")
    def _compile_json_is_empty_object_sqlite(
        element: "json_is_empty_object", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        return (
            f"(json_type({column_sql}) = 'object' AND "
            f"NOT EXISTS (SELECT 1 FROM json_each({column_sql})))"
        )
else:
    json_is_empty_object = None  # type: ignore[assignment, misc]
