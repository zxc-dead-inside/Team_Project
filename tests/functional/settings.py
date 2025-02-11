from pydantic import Field
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    es_host: str = Field('elasticsearch', env='elasticsearch_host')
    es_port: int = Field(9200, env='elasticsearch_port')
    # es_index: str = Field('test_index', env='ELASTIC_INDEX')
    # es_id_field: str = Field('id', env='ELASTIC_ID_FIELD')

    redis_host: str = Field('theatre-redis', env='REDIS_HOST')
    redis_port: int = Field(6379, env='REDIS_PORT')

    # service_url: str = Field('http://localhost:9000', env='SERVICE_URL')
    # es_index_mapping: dict = ...

    @property
    def es_url(self) -> str:
        return f'http://{self.es_host}:{self.es_port}'


test_settings = TestSettings()
