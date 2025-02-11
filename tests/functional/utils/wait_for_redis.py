import os
import time
import redis

if __name__ == "__main__":
    redis_host = os.getenv("REDIS_HOST", "theatre-redis")
    redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=True)

    while True:
        try:
            if redis_client.ping():
                print("Successfully connected to Redis")
                break
        except Exception as e:
            print(f"Waiting for Redis to be ready... Error: {e}")
        time.sleep(1)
