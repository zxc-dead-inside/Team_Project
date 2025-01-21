from typing import Dict, List

from es_request import es_requests


class Transform:
    """Класс для подготовки данных к отправке в es."""

    def get_people(self, people: List[Dict[str, str]]) -> List[str]:
        """Преобразует данные в сроку."""

        return [person['name'] for person in people]

    def prepare(self, batch, name, init: bool = False) -> List[str]:
        """Подготавливает пачку данных."""

        bulk = []
        count = 0
        for data in batch:
            for film_work in data:
                if (name == 'film_work') and (init):
                    bulk.extend(
                        es_requests.es_fw_list(
                            *film_work.get_fields()))
                elif name == 'person':
                    bulk.extend(es_requests.es_people_list(
                        *film_work.get_fields()))
                elif name == 'genre':
                    bulk.extend(es_requests.es_genre_list(
                        *film_work.get_fields()))
                elif (name == 'film_work') and (not init):
                    bulk.extend(
                        es_requests.es_changed_fw_list(
                            *film_work.get_fields()))
                count += 1
        return bulk
