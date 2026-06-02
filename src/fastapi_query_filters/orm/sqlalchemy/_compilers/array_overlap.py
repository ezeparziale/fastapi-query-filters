from typing import Any

from .._compat import HAS_SQLALCHEMY, Boolean, FunctionElement, compiles

if HAS_SQLALCHEMY:

    class array_overlap(FunctionElement[bool]):
        type = Boolean()
        inherit_cache = True

    @compiles(array_overlap, "postgresql")
    def _compile_array_overlap_postgresql(
        element: "array_overlap", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        value_sql = compiler.process(list(element.clauses)[1], **kw)
        return f"EXISTS (SELECT 1 FROM jsonb_array_elements(({value_sql})::jsonb) v WHERE ({column_sql})::jsonb @> v)"

    @compiles(array_overlap, "sqlite")
    def _compile_array_overlap_sqlite(
        element: "array_overlap", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        value_sql = compiler.process(list(element.clauses)[1], **kw)
        return f"EXISTS (SELECT 1 FROM json_each({column_sql}) WHERE json_each.value IN (SELECT value FROM json_each({value_sql})))"

    @compiles(array_overlap, "mysql")
    def _compile_array_overlap_mysql(
        element: "array_overlap", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        value_sql = compiler.process(list(element.clauses)[1], **kw)
        return f"JSON_OVERLAPS({column_sql}, {value_sql})"
else:
    array_overlap = None  # type: ignore[assignment, misc]
