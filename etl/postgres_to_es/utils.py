import datetime as dt
from typing import Any, Generator, List, Tuple


def get_time() -> str:
    return str(dt.datetime.now(dt.timezone.utc))

def get_uuid_str(batch: List[Any]) -> str:
    """extra"""
    ids = [field.id for field in batch]
    # return f'({",".join(ids)})'
    return f'({str(ids)[1:-1]})'


def get_uuid_list(
        batch: Generator[List[Any], None, None]) -> str | Tuple[str]:
    """Преобразует данные в список id."""

    for data in batch:
        if len(data) == 1:
            return f"('{data[0].id}')"
        ids = [item.id for item in data]
    return tuple(ids)


def get_data_gen(batch: Generator) -> None | List[Any]:
    """
    Запускает цепочку генераторов и получает список значений.
    """

    if not isinstance(batch, Generator):
        return None
    result = [item for item in batch]
    if isinstance(result, Generator):
        get_data_gen(result)
    return result[0]
