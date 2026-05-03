from typing import cast

from sqlalchemy import select

from fastapi_query_filters import FilterValues
from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.operators import FilterOperator
from fastapi_query_filters.orm.sqlalchemy import SQLAlchemyFilterAdapter, apply_filters
from tests.models import User
from tests.schemas import UserOut


def test_apply_filters_skips_invalid_keys() -> None:
    """Ensure that filter keys without the double underscore separator or with None values are ignored."""
    FilterModel = create_filter_model(UserOut)
    filter_inst = FilterModel()
    data = {"invalid_key": "some_value", "email__eq": None}

    adapter = SQLAlchemyFilterAdapter()
    stmt = adapter._apply_dynamic_filters(
        select(User), User, filter_inst, data, FilterModel._source_filter_config
    )
    assert "WHERE" not in str(stmt)


def test_apply_filters_with_prefix() -> None:
    """Verify that the global filter prefix is correctly stripped when mapping to database columns."""

    class UserWithPrefix(UserOut):
        class FilterConfig:
            prefix = "user_"

    FilterModel = create_filter_model(UserWithPrefix)
    filters = FilterValues(FilterModel(user_id__eq=1))

    stmt = select(User)
    stmt = apply_filters(stmt, User, filters)
    assert "users.id = :id_1" in str(stmt)


def test_apply_filters_invalid_operator() -> None:
    """Ensure that filter keys with invalid operator suffixes are skipped."""
    FilterModel = create_filter_model(UserOut)
    filter_inst = FilterModel()
    data = {"email__notanoperator": "test"}

    adapter = SQLAlchemyFilterAdapter()
    stmt = adapter._apply_dynamic_filters(
        select(User), User, filter_inst, data, FilterModel._source_filter_config
    )
    assert "WHERE" not in str(stmt)


def test_get_operator_expression_extra_cases() -> None:
    """Test edge cases in _get_operator_expression, such as non-list values for NOT_IN and unhandled operators."""
    adapter = SQLAlchemyFilterAdapter()

    # NOT_IN with non-list value
    expr = adapter._get_operator_expression(User.id, FilterOperator.NOT_IN, 1)
    assert "NOT IN" in str(expr)

    # Return None for unhandled operator.
    result = adapter._get_operator_expression(
        User.email, cast(FilterOperator, "invalid"), "val"
    )
    assert result is None
