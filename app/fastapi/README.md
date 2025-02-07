## How to in development

1. Navigate to the app/api directory

2. Execute

```bash
uvicorn main:app --reload
```

3. Navigate to

http://localhost:8000/docs#/

4. Make sure

```config
ELASTICSEARCH_HOST=host.docker.internal
```


## How to in production

1. To check documentation

http://localhost:9000/docs#/


2. To check app health

http://localhost:9000/health

## Маршруты API

### Фильмы

- Главная страница: `/api/v1/films?sort=-imdb_rating&page_size=50&page_number=1`
- Жанр и популярные фильмы в нём: `/api/v1/films?genre=<uuid:UUID>&sort=-imdb_rating&page_size=50&page_number=1`
- Поиск по фильмам: `/api/v1/films/search?query=star&page_number=1&page_size=50`
- Полная информация по фильму: `/api/v1/films/<uuid:UUID>/`
- Покажем фильмы того же жанра: `/api/v1/films/<uuid:UUID>/similar`
- Популярные фильмы в жанре: `/api/v1/films/popular?genre=<uuid:UUID>&sort=-imdb_rating&page_size=50&page_number=1`

### Жанры

- Список жанров: `/api/v1/genres/`
- Данные по конкретному жанры: `/api/v1/genres/<uuid:UUID>/`

### Персоны

- Поиск по персонам: `/api/v1/persons/search?query=captain&page_number=1&page_size=50`
- Данные по персоне: `/api/v1/persons/<uuid:UUID>/`
- Фильмы по персоне: `/api/v1/persons/<uuid:UUID>/film/`


## Redis (кэш)

В данном коммите реализовано сохранение и поиск в кэше для всех маршрутов API.

Для подключения к redis добавлены переменные:
```.env
REDIS_HOST=<host_here>
REDIS_PORT=<port_here>
REDIS_CACHE_DB=<db_number_here>
```

### Изменения в docker compose
- Добавлен контейнер с redis

