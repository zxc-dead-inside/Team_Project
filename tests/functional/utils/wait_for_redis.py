import time

import redis
from settings import test_settings


if __name__ == "__main__":
    redis_client = redis.Redis(
        host=test_settings.redis_host,
        port=test_settings.redis_port,
        decode_responses=True,
    )

    while True:
        try:
            if redis_client.ping():
                print("Successfully connected to Redis")
                break
        except Exception as e:
            print(f"Waiting for Redis to be ready... Error: {e}")
        time.sleep(1)
