from typing import Any

from .._compat import HAS_SQLALCHEMY, Boolean, FunctionElement, compiles

if HAS_SQLALCHEMY:

    class array_contains(FunctionElement[bool]):
        type = Boolean()
        inherit_cache = True

    @compiles(array_contains, "postgresql")
    def _compile_array_contains_postgresql(
        element: "array_contains", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        value_sql = compiler.process(list(element.clauses)[1], **kw)
        return f"(({column_sql})::jsonb @> ({value_sql})::jsonb)"

    @compiles(array_contains, "sqlite")
    def _compile_array_contains_sqlite(
        element: "array_contains", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        value_sql = compiler.process(list(element.clauses)[1], **kw)
        return f"EXISTS (SELECT 1 FROM json_each({column_sql}) WHERE json_each.value IN (SELECT value FROM json_each({value_sql})))"

    @compiles(array_contains, "mysql")
    def _compile_array_contains_mysql(
        element: "array_contains", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        value_sql = compiler.process(list(element.clauses)[1], **kw)
        return f"JSON_CONTAINS({column_sql}, {value_sql})"
else:
    array_contains = None  # type: ignore[assignment, misc]
