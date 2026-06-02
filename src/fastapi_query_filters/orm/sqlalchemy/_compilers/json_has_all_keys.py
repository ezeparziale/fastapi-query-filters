from typing import Any

from .._compat import HAS_SQLALCHEMY, Boolean, FunctionElement, compiles

if HAS_SQLALCHEMY:

    class json_has_all_keys(FunctionElement[bool]):
        """Cross-dialect JSON all-keys existence check."""

        type = Boolean()
        inherit_cache = True

    @compiles(json_has_all_keys, "postgresql")
    def _compile_json_has_all_keys_postgresql(
        element: "json_has_all_keys", compiler: Any, **kw: Any
    ) -> str:
        clauses = list(element.clauses)
        column_sql = compiler.process(clauses[0], **kw)
        keys_sql = ", ".join(compiler.process(c, **kw) for c in clauses[1:])
        return f"(({column_sql})::jsonb ?& ARRAY[{keys_sql}])"

    @compiles(json_has_all_keys, "mysql")
    def _compile_json_has_all_keys_mysql(
        element: "json_has_all_keys", compiler: Any, **kw: Any
    ) -> str:
        clauses = list(element.clauses)
        column_sql = compiler.process(clauses[0], **kw)
        paths_sql = ", ".join(
            f"CONCAT('$.', JSON_QUOTE({compiler.process(c, **kw)}))"
            for c in clauses[1:]
        )
        return f"JSON_CONTAINS_PATH({column_sql}, 'all', {paths_sql}) = 1"

    @compiles(json_has_all_keys, "sqlite")
    def _compile_json_has_all_keys_sqlite(
        element: "json_has_all_keys", compiler: Any, **kw: Any
    ) -> str:
        clauses = list(element.clauses)
        column_sql = compiler.process(clauses[0], **kw)
        keys_sql = ", ".join(compiler.process(c, **kw) for c in clauses[1:])
        expected_count = len(clauses) - 1
        return (
            f"(SELECT COUNT(DISTINCT json_each.key) FROM json_each({column_sql}) "
            f"WHERE json_each.key IN ({keys_sql})) = {expected_count}"
        )
else:
    json_has_all_keys = None  # type: ignore[assignment, misc]
