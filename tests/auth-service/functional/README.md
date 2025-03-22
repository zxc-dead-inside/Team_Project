# DEPRECATED
# Running the tests

Start the service with Docker Compose:
```shell
docker compose --env-file=../../../app/auth-service/.env  up --build --force-recreate tests
```
Use `ctrl+c` to exit.

Start the service with Docker Compose in detach mode:
```shell
docker compose --env-file=../../../app/auth-service/.env  up -d --build --force-recreate
```

Remove volumes with cahce
```shell
docker compose down -v --remove-orphans
```

See logs:
```shell
docker compose logs tests
```

Use corect path to `.env` file. The file has to contain `REDIS_PASSWORD` variable for redis.

