import abc
import json
import os
from typing import Any
from pathlib import Path


class BaseStorage(abc.ABC):
    """Abstract storage for state management."""

    @abc.abstractmethod
    def save_state(self, state: dict[str, Any]) -> None:
        """Save state to storage."""

    @abc.abstractmethod
    def retrieve_state(self) -> dict[str, Any]:
        """Retrieve state from storage."""


class JsonFileStorage(BaseStorage):
    """JSON file storage implementation."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def save_state(self, state: dict[str, Any]) -> None:
        """Save state to JSON file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def retrieve_state(self) -> dict[str, Any]:
        """Retrieve state from JSON file."""
        if not os.path.exists(self.file_path):
            return {}

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}


class SingletonMeta(type):
    """
    В Python класс Одиночка можно реализовать по-разному. Возможные способы
    включают себя базовый класс, декоратор, метакласс. Мы воспользуемся
    метаклассом, поскольку он лучше всего подходит для этой цели.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Данная реализация не учитывает возможное изменение передаваемых
        аргументов в `__init__`.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class State(metaclass=SingletonMeta):
    """Class for state management with tracking."""

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage
        self._state = storage.retrieve_state()

    def set_state(self, key: str, value: Any, index: str) -> None:
        """Set state for a specific key."""

        if self._state.get(index) is None:
            self._state[index] = {}
        self._state[index].update({key: value})
        self.storage.save_state(self._state)

    def get_state(self, key: str, index: str) -> Any:
        """Get state for a specific key."""

        if self._state.get(index) is None:
            return None
        return self._state.get(index).get(key)

    def increment_processed(self, index: str, count: int = 1) -> None:
        """Increment the number of successfully processed movies."""

        self._state[index]["total_processed"] = self._state[index].\
            get("total_processed", 0) + count
        self.storage.save_state(self._state)

    def increment_failed(self, index: int, count: int = 1) -> None:
        """Increment the number of failed movie processing attempts."""

        self._state[index]["total_failed"] = self._state[index].\
            get("total_failed", 0) + count
        self.storage.save_state(self._state)

    def get_statistics(self, index: str) -> dict[str, Any]:
        """Get processing statistics."""

        if self._state.get(index) is not None:
            return {
                "total_processed": self._state[index].get(
                    "total_processed", 0
                ),
                "total_failed": self._state[index].get("total_failed", 0),
                "last_modified": self._state[index].get("last_modified"),
                "processing_started_at": self._state[index].get(
                    "processing_started_at"
                )
            }
        else:
            return {
                "total_processed": 0,
                "total_failed": 0,
                "last_modified": None,
                "processing_started_at": None,
            }
