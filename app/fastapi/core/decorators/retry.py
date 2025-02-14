import asyncio
import logging
from functools import wraps
from typing import Callable, ParamSpec, TypeVar


# For handling function parameters.
# It allows the decorator to preserve the original function's parameter types and hints
P = ParamSpec("P")
# For the return type. It helps preserve the original function's return type annotation
T = TypeVar("T")

logger = logging.getLogger(__name__)


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exceptions: tuple = (Exception,),
):
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions:
                    retries += 1
                    if retries > max_retries:
                        raise

                    delay = min(base_delay * (2 ** (retries - 1)), max_delay)
                    await asyncio.sleep(delay)

        return wrapper

    return decorator
