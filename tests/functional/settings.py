from pydantic import Field
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    es_host: str = Field('elasticsearch', env='elasticsearch_host')
    es_port: int = Field(9200, env='elasticsearch_port')

    redis_host: str = Field('theatre-redis', env='REDIS_HOST')
    redis_port: int = Field(6379, env='REDIS_PORT')

    # service_url: str = ... fast-api url set up

    @property
    def es_url(self) -> str:
        return f'http://{self.es_host}:{self.es_port}'


test_settings = TestSettings()
