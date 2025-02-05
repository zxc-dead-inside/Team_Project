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

## End points

- Главная страница										+	/api/v1/films?sort=-imdb_rating&page_size=50&page_number=1
- Жанр и популярные фильмы в нём. Это просто фильтрация.	+	/api/v1/films?genre=<uuid:UUID>&sort=-imdb_rating&page_size=50&page_number=1
- Список жанров.											+	/api/v1/genres/
- Поиск по фильмам.										+	/api/v1/films/search?query=star&page_number=1&page_size=50
- Поиск по персонам.										+	/api/v1/persons/search?query=captain&page_number=1&page_size=50
- Полная информация по фильму.							+	/api/v1/films/<uuid:UUID>/
- покажем фильмы того же жанра.							+	/api/v1/films/<uuid:UUID>/similar
- Данные по персоне.										+	/api/v1/persons/<uuid:UUID>/
- Фильмы по персоне.										+	/api/v1/persons/<uuid:UUID>/film/
- Данные по конкретному жанру.							+	/api/v1/genres/<uuid:UUID>/
- Популярные фильмы в жанре.								+	/api/v1/films/popular?genre=<uuid:UUID>&sort=-imdb_rating&page_size=50&page_number=1

## Redis (кэш)

В данном коммите реализовано сохранение и поиск в кэше:
- Полная информация по фильму.							+	/api/v1/films/<uuid:UUID>/
- Поиск по фильмам.										+	/api/v1/films/search?query=star&page_number=1&page_size=50
