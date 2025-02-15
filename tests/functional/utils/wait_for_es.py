# import os
import time

from elasticsearch import Elasticsearch
from settings import test_settings


if __name__ == "__main__":
    es_client = Elasticsearch(
        hosts=test_settings.es_url, verify_certs=False, ssl_show_warn=False
    )

    while True:
        try:
            if es_client.ping():
                print("Successfully connected to Elasticsearch")
                break
        except Exception as e:
            print(f"Waiting for Elasticsearch to be ready... Error: {e}")
        time.sleep(1)
