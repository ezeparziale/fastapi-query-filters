from typing import Any

from .._compat import HAS_SQLALCHEMY, FunctionElement, Integer, compiles

if HAS_SQLALCHEMY:

    class array_length(FunctionElement[int]):
        type = Integer()
        inherit_cache = True

    @compiles(array_length, "postgresql")
    def _compile_array_length_postgresql(
        element: "array_length", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        return f"jsonb_array_length(({column_sql})::jsonb)"

    @compiles(array_length, "sqlite")
    def _compile_array_length_sqlite(
        element: "array_length", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        return f"json_array_length({column_sql})"

    @compiles(array_length, "mysql")
    def _compile_array_length_mysql(
        element: "array_length", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        return f"JSON_LENGTH({column_sql})"
else:
    array_length = None  # type: ignore[assignment, misc]
