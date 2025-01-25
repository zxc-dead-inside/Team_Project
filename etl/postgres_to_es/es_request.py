class EsRequest:
    """Методы формирующие строку для bulk запроса."""

    def es_fw_list(
            self, id, rating, genres, title, description,
            directors_names, actors_names, writers_names, directors,
            actors, writers):

        return [
            {
                "index": {
                    "_index": "movies",
                    "_id": f"{id}"
                }
            },
            {
                "id": id,
                "imdb_rating": rating,
                "genres": genres,
                "title": title,
                "description": description,
                "directors_names": directors_names,
                "actors_names": actors_names,
                "writers_names": writers_names,
                "directors": directors,
                "actors": actors,
                "writers": writers
            }
        ]

    def es_changed_fw_list(
            self, id, title, description, rating, type):

        return [
            {
                "update": {
                    "_index": "movies",
                    "_id": f"{id}"
                }
            },
            {
                "doc": {
                    "id": id,
                    "imdb_rating": rating,
                    "genres": type,
                    "title": title,
                    "description": description
                }
            }
        ]

    def es_people_list(
            self, id, directors_names, actors_names, writers_names,
            directors, actors, writers):

        return [
            {
                "update": {
                    "_index": "movies",
                    "_id": f"{id}"
                }
            },
            {
                "doc": {
                    "id": id,
                    "directors_names": directors_names,
                    "actors_names": actors_names,
                    "writers_names": writers_names,
                    "directors": directors,
                    "actors": actors,
                    "writers": writers
                }
            }
        ]

    def es_genre_list(
            self, id, genres):

        return [
            {
                "update": {
                    "_index": "movies",
                    "_id": f"{id}"
                }
            },
            {
                "doc": {
                    "id": id,
                    "genres": genres
                }
            }
        ]

es_requests = EsRequest()  # noqa
