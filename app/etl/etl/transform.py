def transform_film_data(films: list[dict]) -> list[dict]:
    return [{
        "id": film["fw_id"],
        "imdb_rating": film["rating"],
        "title": film["title"],
        "description": film["description"],
        "actors": [{
            "id": person["id"],
            "name": person["name"]
        } for person in film["actors"]],
        "directors": [{
            "id": person["id"],
            "name": person["name"]
        } for person in film["directors"]],
        "writers": [{
            "id": person["id"],
            "name": person["name"]
        } for person in film["writers"]],
        "directors_names": [person["name"] for person in film["directors"]],
        "actors_names": [person["name"] for person in film["actors"]],
        "writers_names": [person["name"] for person in film["writers"]],
        "genres": film["genres"]
    } for film in films]
