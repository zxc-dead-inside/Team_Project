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
