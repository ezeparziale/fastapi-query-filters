from typing import Any

from .._compat import HAS_SQLALCHEMY, Boolean, FunctionElement, compiles

if HAS_SQLALCHEMY:

    class json_is_json_null(FunctionElement[bool]):
        """Cross-dialect check for JSON null literal (different from SQL NULL)."""

        type = Boolean()
        inherit_cache = True

    @compiles(json_is_json_null, "postgresql")
    def _compile_json_is_json_null_postgresql(
        element: "json_is_json_null", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        return f"(({column_sql})::jsonb = 'null'::jsonb)"

    @compiles(json_is_json_null, "mysql")
    def _compile_json_is_json_null_mysql(
        element: "json_is_json_null", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        return f"(JSON_TYPE({column_sql}) = 'NULL')"

    @compiles(json_is_json_null, "sqlite")
    def _compile_json_is_json_null_sqlite(
        element: "json_is_json_null", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        return f"(json_type({column_sql}) = 'null')"
else:
    json_is_json_null = None  # type: ignore[assignment, misc]
