from typing import TYPE_CHECKING, TypeVar

__all__ = [
    "HAS_SQLALCHEMY",
    "_check_sqlalchemy",
    "T",
    "JSON",
    "Boolean",
    "Date",
    "DateTime",
    "Float",
    "Integer",
    "String",
    "Text",
    "Time",
    "and_",
    "asc",
    "desc",
    "false",
    "literal",
    "or_",
    "true",
    "sa_cast",
    "DeclarativeBase",
    "RelationshipProperty",
    "Select",
    "FunctionElement",
    "compiles",
]

try:
    from sqlalchemy import (
        JSON,
        Boolean,
        Date,
        DateTime,
        Float,
        Integer,
        String,
        Text,
        Time,
        and_,
        asc,
        desc,
        false,
        literal,
        or_,
        true,
    )
    from sqlalchemy import cast as sa_cast
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.orm import DeclarativeBase, RelationshipProperty
    from sqlalchemy.sql import Select
    from sqlalchemy.sql.functions import FunctionElement

    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

    if not TYPE_CHECKING:
        # Define dummy classes/types to avoid NameErrors during module load
        class DeclarativeBase:
            pass

        class Select:
            pass

        class RelationshipProperty:
            pass

        String = Text = and_ = asc = desc = or_ = sa_cast = Integer = Float = (
            Boolean
        ) = Date = DateTime = Time = Numeric = JSON = false = true = literal = None

        FunctionElement = object
        compiles = lambda *a, **kw: lambda f: f  # noqa: E731


if TYPE_CHECKING:
    # This helps Mypy when sqlalchemy is not installed in the dev environment
    # but we are running in a mode that expects it.
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy.sql import Select

T = TypeVar("T", bound="DeclarativeBase")


def _check_sqlalchemy() -> None:
    if not HAS_SQLALCHEMY:
        raise ImportError(
            "The 'sqlalchemy' extra is required to use the SQLAlchemy adapter. "
            "Install it with: pip install 'fastapi-query-filters[sqlalchemy]'"
        )
