import socket
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar
from urllib.error import URLError

import backoff
from backoff import on_exception


P = ParamSpec("P")
R = TypeVar("R")


class RetryDecorators:
    """Factory class for creating backoff retry decorators with configurable defaults.

    Creates retry decorators with exponential backoff strategy, allowing customization
    of retry attempts, timeout periods, and backoff parameters.
    """

    def __init__(
        self,
        default_max_tries: int = 3,
        default_max_time: int = 5,
        default_base: float = 1.0,
    ) -> None:
        """Initialize RetryDecorators with configurable default parameters.

        Args:
            default_max_tries: Maximum number of retry attempts. Must be >= 1.
            default_max_time: Maximum total time in seconds. Must be >= 1.
            default_base: Base value for exponential backoff. Must be > 0.

        Raises:
            ValueError: If any parameter is invalid.
        """
        self._validate_init_params(default_max_tries, default_max_time, default_base)

        self.default_max_tries = default_max_tries
        self.default_max_time = default_max_time
        self.default_base = default_base

    @staticmethod
    def _validate_init_params(
        max_tries: int,
        max_time: int,
        base: float,
    ) -> None:
        """Validate initialization parameters.

        Args:
            max_tries: Maximum number of retry attempts
            max_time: Maximum total time in seconds
            base: Base value for exponential backoff

        Raises:
            ValueError: If any parameter is invalid
        """
        if max_tries < 1:
            raise ValueError("default_max_tries must be at least 1")
        if max_time < 1:
            raise ValueError("default_max_time must be at least 1")
        if base <= 0:
            raise ValueError("default_base must be positive")

    def _create_decorator(
        self,
        exceptions: tuple[type[Exception], ...],
        max_tries: int | None = None,
        max_time: int | None = None,
        base: float | None = None,
        **kwargs: Any,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Create a retry decorator with specified parameters.

        Args:
            exceptions: Exception types to catch and retry
            max_tries: Override for default_max_tries
            max_time: Override for default_max_time
            base: Override for default_base
            **kwargs: Additional arguments for backoff.on_exception

        Returns:
            Configured retry decorator function
        """
        kwargs.setdefault("jitter", backoff.full_jitter)

        return on_exception(
            wait_gen=backoff.expo,
            exception=exceptions,
            max_tries=max_tries or self.default_max_tries,
            max_time=max_time or self.default_max_time,
            base=base or self.default_base,
            **kwargs,
        )

    def custom(
        self,
        exceptions: tuple[type[Exception], ...],
        **kwargs: Any,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Create a custom retry decorator for specific exceptions.

        Args:
            exceptions: Exception types to catch and retry
            **kwargs: Override default parameters and add additional options

        Returns:
            Configured retry decorator
        """
        return self._create_decorator(exceptions=exceptions, **kwargs)

    def network_errors(
        self,
        *,
        max_tries: int | None = None,
        max_time: int | None = None,
        base: float | None = None,
        additional_exceptions: tuple[type[Exception], ...] = (),
        **kwargs: Any,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Create a retry decorator for common network-related exceptions.

        Args:
            max_tries: Override default_max_tries
            max_time: Override default_max_time
            base: Override default_base
            additional_exceptions: Additional exception types to include
            **kwargs: Additional arguments for backoff.on_exception

        Returns:
            Configured network retry decorator
        """
        network_exceptions = (
            ConnectionError,
            TimeoutError,
            socket.timeout,
            socket.gaierror,
            URLError,
            ConnectionResetError,
            ConnectionAbortedError,
            ConnectionRefusedError,
            *additional_exceptions,
        )
        return self._create_decorator(
            exceptions=network_exceptions,
            max_tries=max_tries,
            max_time=max_time,
            base=base,
            **kwargs,
        )


exponential_backoff = RetryDecorators()
