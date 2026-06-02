from typing import Any

from .._compat import HAS_SQLALCHEMY, Boolean, FunctionElement, compiles

if HAS_SQLALCHEMY:

    class json_has_key(FunctionElement[bool]):
        """Cross-dialect JSON key existence check."""

        type = Boolean()
        inherit_cache = True

    @compiles(json_has_key, "postgresql")
    def _compile_json_has_key_postgresql(
        element: "json_has_key", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        key_sql = compiler.process(list(element.clauses)[1], **kw)
        return f"(({column_sql})::jsonb ? {key_sql})"

    @compiles(json_has_key, "mysql")
    def _compile_json_has_key_mysql(
        element: "json_has_key", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        key_sql = compiler.process(list(element.clauses)[1], **kw)
        return f"JSON_CONTAINS_PATH({column_sql}, 'one', CONCAT('$.', JSON_QUOTE({key_sql}))) = 1"

    @compiles(json_has_key, "sqlite")
    def _compile_json_has_key_sqlite(
        element: "json_has_key", compiler: Any, **kw: Any
    ) -> str:
        column_sql = compiler.process(list(element.clauses)[0], **kw)
        key_sql = compiler.process(list(element.clauses)[1], **kw)
        return (
            f"EXISTS (SELECT 1 FROM json_each({column_sql}) "
            f"WHERE json_each.key = {key_sql})"
        )
else:
    json_has_key = None  # type: ignore[assignment, misc]
