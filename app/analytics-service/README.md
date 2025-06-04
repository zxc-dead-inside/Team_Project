# API сервис для передачи данных в Kafka

Перед первым запуском создайте файл `.env`, по аналогии с файлом `.env.template`.

Для быстрого запуска выполните комаду

```shell
docker compose up --build -d
```

Будет запущено:
- Backend приложение
- Кластер Kafka из 3х узлов
- clickhouse
- etl сервис

Для теста пайплайна
```shell
  docker exec -it analytics_etl_service python /app/src/etl/scripts/test_api_to_clickhouse.py
```

Веб интерфейсы:
- Документация по API доступна: http://localhost:8100/api/docs
- Веб интерфейс для работы с Kafka доступен: http://localhost:9080/


