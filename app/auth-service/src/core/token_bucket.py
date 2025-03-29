import time

from src.services.redis_service import RedisService


class TokenBucket:
    def __init__(
        self,
        redis_service: RedisService
    ):
        # Initialize the token bucket
        self.redis_service = redis_service

    async def take_token(self, key, capacity):
        # Attempt to take a token from the bucket
        # Ensure the bucket is refilled based on the elapsed time
        refill_rate = capacity / 60
        now = time.time()

        # Add tokens to the bucket based on the time elapsed since the last refill
        tokens = await self.redis_service.get(key=f'tokens_{key}')
        if not tokens:
            await self.redis_service.set(
                key=f'tokens_{key}', value=capacity-1)
            await self.redis_service.set(key=f'last_refill_{key}', value=now)
            return True
        
        tokens = float(tokens)
        last_refill = float(
            await self.redis_service.get(key=f'last_refill_{key}'))

        if tokens < capacity:
            # Calculate the number of tokens to add
            tokens_to_add = (now - last_refill) * refill_rate
            # Update the token count, ensuring it doesn't exceed the capacity
            tokens = min(capacity, tokens + tokens_to_add)

        await self.redis_service.set(key=f'last_refill_{key}', value=now)
        if tokens >= 1:
            # Deduct a token for the API call
            await self.redis_service.set(key=f'tokens_{key}', value=tokens-1)
            return True  # Indicate that the API call can proceed
        return False  # Indicate that the rate limit has been exceeded
