from typing import Any

from .._compat import HAS_SQLALCHEMY, Boolean, FunctionElement, compiles

if HAS_SQLALCHEMY:

    class string_eq(FunctionElement[bool]):
        """Cross-dialect exact string equality."""

        type = Boolean()
        inherit_cache = True

    @compiles(string_eq)
    def _compile_string_eq_default(
        element: "string_eq", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        value_sql = compiler.process(list(element.clauses)[1], **kw)
        return f"({column_sql} = {value_sql})"

    @compiles(string_eq, "mysql")
    def _compile_string_eq_mysql(element: "string_eq", compiler: Any, **kw: Any) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        value_sql = compiler.process(list(element.clauses)[1], **kw)
        return f"({column_sql} COLLATE utf8mb4_bin = {value_sql} COLLATE utf8mb4_bin)"
else:
    string_eq = None  # type: ignore[assignment, misc]
