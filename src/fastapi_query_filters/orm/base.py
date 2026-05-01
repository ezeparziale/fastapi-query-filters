from abc import ABC, abstractmethod
from typing import Any

from ..dependencies import FilterValues


class ORMFilterAdapter(ABC):
    @abstractmethod
    def apply_filters(
        self,
        stmt: Any,
        model: type[Any],
        filter_values: FilterValues,
    ) -> Any:
        """Apply filter values to an ORM query/statement.

        This is the generic contract for ORM-specific filter adapters.
        The `stmt` argument is intentionally generic so each adapter can
        accept the ORM's native query or statement object.
        """
        ...
