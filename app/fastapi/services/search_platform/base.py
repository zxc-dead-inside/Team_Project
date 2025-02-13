from abc import ABC, abstractmethod
from typing import Any


class AbstractSearchPlatfrom(ABC):
    """Abstract class for search platform."""

    @abstractmethod
    async def get(
        self, index: str, obj_id: str) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def search(
        self, index: str, body: dict[str, Any]
        ) -> dict[str, Any] | None:
        pass
