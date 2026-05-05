import importlib
import sys
from unittest.mock import patch

import pytest


def test_sqlalchemy_missing_error() -> None:
    """Verify that a helpful ImportError is raised when sqlalchemy is not installed."""

    # 1. Clear the module from sys.modules to force a re-import
    module_name = "fastapi_query_filters.orm.sqlalchemy"
    if module_name in sys.modules:
        del sys.modules[module_name]

    # 2. Mock the import of sqlalchemy to fail
    with patch.dict(
        "sys.modules",
        {"sqlalchemy": None, "sqlalchemy.orm": None, "sqlalchemy.sql": None},
    ):
        # 3. Re-import the module; it should now hit the 'except ImportError' block
        import fastapi_query_filters.orm.sqlalchemy as sa_adapter

        importlib.reload(sa_adapter)

        # 4. Verify HAS_SQLALCHEMY is False
        assert sa_adapter.HAS_SQLALCHEMY is False

        # 5. Verify the descriptive error is raised
        with pytest.raises(ImportError) as excinfo:
            sa_adapter.SQLAlchemyFilterAdapter()
        assert "The 'sqlalchemy' extra is required" in str(excinfo.value)

        with pytest.raises(ImportError) as excinfo:
            sa_adapter.apply_filters(None, None, None)  # type: ignore
        assert "The 'sqlalchemy' extra is required" in str(excinfo.value)

    # Cleanup: Reload the module normally so other tests aren't affected
    if module_name in sys.modules:
        del sys.modules[module_name]
    importlib.import_module(module_name)
