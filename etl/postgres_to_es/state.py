import abc
import json
import logging
from typing import Any, Dict, List

from redis import Redis

from errors import ReadStorageError, SaveStorageError
from settings import STATE_NAME, STR_TIME_NOW

logger = logging.getLogger(__name__)


class BaseStorage(abc.ABC):
    """Абстрактное хранилище состояния."""

    @abc.abstractmethod
    def save_state(self, state: Dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""

    @abc.abstractmethod
    def read_state(self) -> Dict[str, Any]:
        """Прочитать состояние из хранилища."""


class RedisStorage(BaseStorage):
    """Хранилище Redis."""

    def __init__(self, redis: Redis):
        self._redis = redis

    def save_state(self, state: Dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""

        logger.debug('Сохранение в хранилище.')
        try:
            self._redis.set(STATE_NAME, json.dumps(state))
        except Exception as err:
            msg = 'При сохранении произошла ошибка'
            logger.error(msg, exc_info=err)
            raise SaveStorageError(msg)
        logger.debug('Данные сохранены в хранилище.')

    def read_state(self) -> Dict[str, Any]:
        """Прочитать состояние из хранилища."""

        logger.debug('Чтение данных из хранилища.')
        try:
            data = self._redis.get(STATE_NAME)
            if data is None:
                return {}
            data = json.loads(data)
        except Exception as err:
            msg = 'При чтении произошла ошибка'
            logger.error(msg, exc_info=err)
            raise ReadStorageError(msg)
        logger.debug('Данные прочитаны из хранилища.')
        return data


class State:
    """Класс для работы с состояниями."""

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа."""

        logger.debug('Установка состояния.')
        data = {key: value}
        try:
            self.storage.save_state(state=data)
        except SaveStorageError as err:
            msg = 'При установке состояния произошла ошибка.'
            logger.error(msg, exc_info=err)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу."""

        try:
            data = self.storage.read_state()
        except ReadStorageError as err:
            msg = 'При чтении состояния произошла ошибка.'
            logger.error(msg, exc_info=err)
        return data.get(key)

    def get_param(
            self,  current: List[Dict[str, str]],
            name: str, param_name: str) -> Any:
        """Возвращает значение параметра."""

        for item in current:
            if item['name'] == name:
                return item.get(param_name)

    def set_param(
            self,  current: List[Dict[str, str]],
            name: str, param_name: str, value: Any
            ) -> List[Dict[str, str]]:
        """Сохраняет значение параметра."""

        for item in current:
            if item['name'] == name:
                item[param_name] = value
                break
        return current

    def set_param_bulk(
            self, current: List[Dict[str, str]],
            param_name: str, value: Any
            ) -> List[Dict[str, str]]:
        """Устанавливает значение параметра во всех словарях."""

        for item in current:
            if item.get(param_name) is not None:
                item[param_name] = value
        return current

    def set_init(
            self,  current: List[Dict[str, Any]]
            ) -> List[Dict[str, str]]:
        """Меняет флаг процесса инициализации индекса."""

        for item in current:
            if item['name'] == 'film_work':
                item['init'] = not item['init']
                break
        return current

    def get_init(
            self,  current: List[Dict[str, str]]
            ) -> bool:
        """Возвращает статус флага инициализации индекса."""

        return self.get_param(current, 'film_work', 'init')

    def flush_offset(
            self, current: List[Dict[str, str]]
            ) -> List[Dict[str, str]]:
        """Обнуляет смещения."""

        return self.set_param_bulk(current, 'offset', 0)
