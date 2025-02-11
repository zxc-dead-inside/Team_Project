import os
import time
from elasticsearch import Elasticsearch

if __name__ == '__main__':
    es_host = os.getenv('ELASTICSEARCH_HOST', 'elasticsearch')
    es_client = Elasticsearch(
        hosts=f'http://{es_host}:9200',
        verify_certs=False,
        ssl_show_warn=False
    )
    
    while True:
        try:
            if es_client.ping():
                print("Successfully connected to Elasticsearch")
                break
        except Exception as e:
            print(f"Waiting for Elasticsearch to be ready... Error: {e}")
        time.sleep(1)
