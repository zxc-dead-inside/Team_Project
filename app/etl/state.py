import abc
import json
import os
from typing import Any


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

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def save_state(self, state: dict[str, Any]) -> None:
        """Save state to JSON file."""
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


class State:
    """Class for state management with tracking."""

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage
        self._state = storage.retrieve_state()

        # Initialize counters if they don't exist
        if "total_processed" not in self._state:
            self._state["total_processed"] = 0
        if "total_failed" not in self._state:
            self._state["total_failed"] = 0
        if "processing_started_at" not in self._state:
            self._state["processing_started_at"] = None

    def set_state(self, key: str, value: Any) -> None:
        """Set state for a specific key."""
        self._state[key] = value
        self.storage.save_state(self._state)

    def get_state(self, key: str) -> Any:
        """Get state for a specific key."""
        return self._state.get(key)

    def increment_processed(self, count: int = 1) -> None:
        """Increment the number of successfully processed movies."""
        self._state["total_processed"] = self._state.get("total_processed", 0) + count
        self.storage.save_state(self._state)

    def increment_failed(self, count: int = 1) -> None:
        """Increment the number of failed movie processing attempts."""
        self._state["total_failed"] = self._state.get("total_failed", 0) + count
        self.storage.save_state(self._state)

    def get_statistics(self) -> dict[str, Any]:
        """Get processing statistics."""
        return {
            "total_processed": self._state.get("total_processed", 0),
            "total_failed": self._state.get("total_failed", 0),
            "last_modified": self._state.get("last_modified"),
            "processing_started_at": self._state.get("processing_started_at"),
        }
