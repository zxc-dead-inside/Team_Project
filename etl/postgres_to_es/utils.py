from typing import Any, Generator, List, Tuple


def get_uuid_list(
        batch: Generator[List[Any], None, None]) -> Tuple[str]:
    """Преобразует данные в список id."""

    for data in batch:
        if len(data) == 1:
            return f"('{data[0].id}')"
        ids = [item.id for item in data]
    return tuple(ids)
