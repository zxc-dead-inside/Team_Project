# UGC Service

Сервис пользовательского контента для онлайн-кинотеатра, реализующий CRUD операции для закладок, лайков и рецензий с использованием MongoDB.

## Функциональность

### Закладки (Bookmarks)
- Создание закладки на фильм
- Получение всех закладок пользователя
- Удаление закладки
- Проверка существования закладки

### Лайки (Likes)
- Создание/обновление оценки фильма (1-10)
- Получение всех оценок пользователя
- Получение средней оценки фильма
- Удаление оценки
- Получение оценки пользователя для конкретного фильма

### Рецензии (Reviews)
- Создание рецензии с текстом и опциональной оценкой
- Получение рецензий фильма с пагинацией
- Поиск рецензий по тексту
- Обновление рецензии
- Удаление рецензии
- Получение всех рецензий пользователя

## API Endpoints

### Закладки
- `POST /api/v1/bookmarks/` - Создать закладку
- `GET /api/v1/bookmarks/user/{user_id}` - Получить закладки пользователя
- `DELETE /api/v1/bookmarks/user/{user_id}/film/{film_id}` - Удалить закладку
- `GET /api/v1/bookmarks/user/{user_id}/film/{film_id}/exists` - Проверить существование закладки

### Лайки
- `POST /api/v1/likes/` - Создать лайк с оценкой
- `GET /api/v1/likes/user/{user_id}` - Получить лайки пользователя
- `GET /api/v1/likes/film/{film_id}/rating` - Получить среднюю оценку фильма
- `DELETE /api/v1/likes/user/{user_id}/film/{film_id}` - Удалить лайк
- `GET /api/v1/likes/user/{user_id}/film/{film_id}/rating` - Получить оценку пользователя

### Рецензии
- `POST /api/v1/reviews/` - Создать рецензию
- `GET /api/v1/reviews/film/{film_id}` - Получить рецензии фильма
- `GET /api/v1/reviews/search` - Поиск рецензий
- `PUT /api/v1/reviews/{review_id}` - Обновить рецензию
- `DELETE /api/v1/reviews/{review_id}` - Удалить рецензию
- `GET /api/v1/reviews/user/{user_id}` - Получить рецензии пользователя

### Здоровье сервиса
- `GET /api/v1/health/` - Проверка здоровья сервиса

## Запуск

### Локальный запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Запустите MongoDB:
```bash
docker run -d -p 27017:27017 --name mongodb mongo:6.0
```

3. Запустите сервис:
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

### Запуск через Docker

1. Запустите сервис с MongoDB:
```bash
docker-compose up --build
```

### Запуск в составе основного проекта

1. Перейдите в папку `app/`:
```bash
cd app/
```

2. Запустите весь проект:
```bash
docker-compose up --build
```

## Документация API

После запуска сервиса документация доступна по адресам:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc
